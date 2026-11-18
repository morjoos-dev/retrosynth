import io
import wave

import pytest
from fastapi.testclient import TestClient

from retrosynth.runner import run_code
from retrosynth.server import create_app

TOKEN = "test-token"
CODE = "s = Song(120, 1)\ns.melody('flute', 0, 'C5:1 E5:1 G5:2')\nsong = s.render()"


class InlineWorker:
    """Runs renders in-process: the real worker uses a subprocess, tested separately."""

    def start(self):
        pass

    def close(self):
        pass

    def render(self, code, name):
        return run_code(code, name)


@pytest.fixture
def client(tmp_path):
    app = create_app(tmp_path / "songs", tmp_path / "out", token=TOKEN, worker=InlineWorker(),
                     allowed_hosts=("testserver", "localhost"))
    with TestClient(app, headers={"X-Studio-Token": TOKEN}) as c:
        yield c


def test_page_embeds_token(client):
    r = client.get("/")
    assert r.status_code == 200 and TOKEN in r.text
    assert client.get("/static/app.js").status_code == 200


def test_api_requires_token(client):
    assert client.get("/api/info", headers={"X-Studio-Token": "wrong"}).status_code == 403
    assert client.post("/api/render", json={"code": CODE}, headers={"X-Studio-Token": ""}).status_code == 403


def test_foreign_host_is_rejected(client):
    """DNS-rebinding protection: the Host header must be a loopback name."""
    assert client.get("/", headers={"Host": "evil.example:5177"}).status_code == 403
    assert client.get("/api/info", headers={"Host": "localhost:5177"}).status_code == 200


def test_info_lists_instruments(client):
    info = client.get("/api/info").json()
    names = {i["name"] for i in info["instruments"]}
    assert {"flute", "kick", "riser"} <= names
    assert "maj" in info["chords"]


def test_render_then_fetch_audio(client):
    r = client.post("/api/render", json={"name": "demo", "code": CODE})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["analysis"]["duration"] == pytest.approx(2.0)
    wav = client.get(f"/api/audio/{body['id']}")
    assert wav.headers["content-type"] == "audio/wav"
    with wave.open(io.BytesIO(wav.content)) as w:
        assert w.getnchannels() == 2 and w.getframerate() == 44_100 and w.getnframes() == 88_200


def test_render_error_has_line(client):
    r = client.post("/api/render", json={"code": "s = Song(120, 1)\nboom()\nsong = s"})
    assert r.status_code == 422
    assert r.json()["line"] == 2 and "boom" in r.json()["error"]


def test_note_endpoint(client):
    r = client.get("/api/note", params={"instrument": "harp", "pitch": 60, "duration": 0.3})
    assert r.status_code == 200 and r.content[:4] == b"RIFF"
    assert client.get("/api/note", params={"instrument": "nope", "pitch": 60}).status_code == 404
    assert client.get("/api/note", params={"instrument": "harp", "pitch": 300}).status_code == 400


def test_save_list_delete(client, tmp_path):
    assert client.post("/api/save", json={"name": "my_tune", "code": '"""My tune."""\n' + CODE}).status_code == 200
    mine = client.get("/api/songs").json()["mine"]
    assert [s["name"] for s in mine] == ["my_tune"] and mine[0]["description"] == "My tune."
    assert (tmp_path / "songs" / "my_tune.py").exists()
    client.post("/api/delete", json={"name": "my_tune"})
    assert client.get("/api/songs").json()["mine"] == []


@pytest.mark.parametrize("name", ["../escape", "a/b", "", "x" * 61, "dot.py"])
def test_names_cannot_escape_the_songs_folder(client, name):
    assert client.post("/api/save", json={"name": name, "code": "x"}).status_code == 400
    assert client.post("/api/delete", json={"name": name}).status_code == 400


def test_export_writes_wav(client, tmp_path):
    r = client.post("/api/export", json={"name": "demo", "code": CODE})
    assert r.status_code == 200, r.text
    assert "demo.wav" in r.json()["files"]
    assert (tmp_path / "out" / "demo.wav").exists()


def test_examples_are_listed(client):
    examples = client.get("/api/songs").json()["examples"]
    assert len(examples) >= 5 and all(e["description"] for e in examples)


def test_visual_project_render_save_and_reopen(client):
    from retrosynth.presets import PRESETS

    project = PRESETS[1]["project"]
    r = client.post("/api/render", json={"name": "v", "project": project})
    assert r.status_code == 200, r.text
    code = client.post("/api/project/code", json={"project": project}).json()["code"]
    assert code.startswith('"""Village')
    assert client.post("/api/save", json={"name": "visual_song", "project": project}).status_code == 200
    mine = client.get("/api/songs").json()["mine"]
    assert mine[0]["project"]["title"] == "Village"


def test_invalid_project_is_a_400(client):
    r = client.post("/api/render", json={"project": {"tracks": {"melody": {"instrument": "nope"}}}})
    assert r.status_code == 400 and "Invalid project" in r.json()["error"]
    assert client.post("/api/render", json={"name": "x"}).status_code == 400


def test_info_has_presets_and_visual_options(client):
    info = client.get("/api/info").json()
    assert len(info["presets"]) >= 5 and "phrygian_dominant" in info["visual"]["scales"]
