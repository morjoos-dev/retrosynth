"""The studio: a local web app to write, hear, analyse and export songs.

Security model — the studio runs Python code sent from the browser, so it must only
ever accept requests from its own page:

* it binds to ``127.0.0.1`` by default;
* every ``/api`` request must carry a random per-session token, which is embedded in the
  page. Other websites cannot read it, and the custom header forces a CORS preflight
  that this server never approves (protects against CSRF);
* the ``Host`` header must be a loopback name (protects against DNS rebinding).
"""

from __future__ import annotations

import hashlib
import os
import re
import secrets
import subprocess
import sys
from collections import OrderedDict
from contextlib import asynccontextmanager
from importlib import resources
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import __version__, dsp
from .analysis import analyze
from .arrange import ProjectError, describe_options, from_code, to_code
from .audio_io import export, find_ffmpeg, to_wav_bytes
from .instruments import inst
from .presets import PRESETS
from .runner import RenderResult, SongError, describe
from .song import CHORDS
from .worker import RenderWorker

NAME_RE = re.compile(r"^[A-Za-z0-9_-]{1,60}$")
TOKEN_HEADER = "X-Studio-Token"
LOOPBACK = ("localhost", "127.0.0.1", "[::1]")

WEB_DIR = Path(str(resources.files("retrosynth") / "web"))
EXAMPLES_DIR = Path(str(resources.files("retrosynth") / "examples"))


class SongRequest(BaseModel):
    """A song given either as code or as a visual-editor project (converted to code)."""

    name: str = "untitled"  # validated where it becomes a file name (save, export)
    code: str | None = Field(default=None, max_length=500_000)
    project: dict | None = None

    def source(self) -> str:
        if self.project is not None:
            try:
                return to_code(self.project)
            except ProjectError as e:
                raise HTTPException(400, f"Invalid project: {e}") from None
        if self.code is None:
            raise HTTPException(400, "Send either 'code' or 'project'")
        return self.code


class ProjectRequest(BaseModel):
    project: dict


class NameRequest(BaseModel):
    name: str


def _hostname(host_header: str) -> str:
    """``localhost:5177`` → ``localhost``; ``[::1]:5177`` → ``[::1]``."""
    if host_header.startswith("["):
        return host_header.split("]")[0] + "]"
    return host_header.rsplit(":", 1)[0]


def _check_name(name: str) -> str:
    if not NAME_RE.fullmatch(name):
        raise HTTPException(400, "Invalid name: use letters, digits, '_' or '-' (max 60)")
    return name


def _list_songs(folder: Path) -> list[dict]:
    if not folder.is_dir():
        return []
    items = []
    for path in sorted(folder.glob("*.py"), key=lambda p: p.stat().st_mtime, reverse=True):
        code = path.read_text(encoding="utf-8")
        items.append({"name": path.stem, "description": describe(code), "code": code, "project": from_code(code),
                      "modified": path.stat().st_mtime})
    return items


def open_folder(path: Path) -> None:
    """Open a folder in the system file manager."""
    if sys.platform == "win32":
        os.startfile(path)  # type: ignore[attr-defined]  # noqa: S606
    else:
        subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", str(path)])


def create_app(
    songs_dir: str | Path = "songs",
    out_dir: str | Path = "output",
    *,
    token: str | None = None,
    worker: RenderWorker | None = None,
    allowed_hosts: tuple[str, ...] = LOOPBACK,
) -> FastAPI:
    songs_dir, out_dir = Path(songs_dir).resolve(), Path(out_dir).resolve()
    token = token or secrets.token_urlsafe(24)
    worker = worker or RenderWorker()
    renders: OrderedDict[str, RenderResult] = OrderedDict()  # small cache of recent renders

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        worker.start()  # warm up: numpy/scipy are imported before the first render
        yield
        worker.close()

    app = FastAPI(title="retrosynth studio", version=__version__, lifespan=lifespan,
                  docs_url=None, redoc_url=None, openapi_url=None)
    app.state.token = token
    app.state.worker = worker

    @app.middleware("http")
    async def guard(request: Request, call_next):
        if _hostname(request.headers.get("host", "")) not in allowed_hosts:
            return JSONResponse({"error": "Forbidden host"}, status_code=403)
        if request.url.path.startswith("/api/") and not secrets.compare_digest(
            request.headers.get(TOKEN_HEADER, ""), token
        ):
            return JSONResponse({"error": "Missing or invalid studio token"}, status_code=403)
        response = await call_next(request)
        if request.url.path.startswith("/static/"):
            response.headers["Cache-Control"] = "no-cache"  # always revalidate: no stale scripts after an update
        return response

    @app.exception_handler(HTTPException)
    async def http_error(_: Request, exc: HTTPException):
        body = exc.detail if isinstance(exc.detail, dict) else {"error": exc.detail}
        return JSONResponse(body, status_code=exc.status_code)

    # ── Page ────────────────────────────────────────────────────────────────
    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        return (WEB_DIR / "index.html").read_text(encoding="utf-8").replace("{{TOKEN}}", token)

    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

    # ── API ─────────────────────────────────────────────────────────────────
    @app.get("/api/info")
    def info() -> dict:
        return {
            "version": __version__,
            "instruments": [{"name": i.name, "kind": i.kind, "description": i.description} for i in inst],
            "chords": list(CHORDS),
            "visual": describe_options(),
            "presets": PRESETS,
            "ffmpeg": bool(find_ffmpeg()),
            "songs_dir": str(songs_dir),
            "out_dir": str(out_dir),
        }

    @app.get("/api/songs")
    def songs() -> dict:
        return {"mine": _list_songs(songs_dir), "examples": _list_songs(EXAMPLES_DIR)}

    def _render(req: SongRequest) -> tuple[str, RenderResult]:
        code = req.source()
        key = hashlib.sha256(f"{req.name}\0{code}".encode()).hexdigest()[:20]
        if key not in renders:
            try:
                renders[key] = worker.render(code, req.name)
            except SongError as e:
                raise HTTPException(422, {"error": e.message, "line": e.line}) from None
            while len(renders) > 6:
                renders.popitem(last=False)
        renders.move_to_end(key)
        return key, renders[key]

    @app.post("/api/render")
    def render(req: SongRequest) -> dict:
        key, result = _render(req)
        return {
            "id": key,
            "seconds": result.seconds,
            "log": result.log,
            "analysis": analyze(result.audio).to_dict(),
        }

    @app.get("/api/audio/{key}")
    def audio(key: str) -> Response:
        if key not in renders:
            raise HTTPException(404, "Render not found (it may have expired); render again")
        return Response(to_wav_bytes(renders[key].audio), media_type="audio/wav")

    @app.get("/api/note")
    def play_note(instrument: str, pitch: int, duration: float = 0.5) -> Response:
        if instrument not in inst:
            raise HTTPException(404, f"Unknown instrument {instrument!r}")
        if not (0 <= pitch <= 127 and 0.02 <= duration <= 8):
            raise HTTPException(400, "pitch must be 0–127 and duration 0.02–8 s")
        dsp.seed(7 + pitch)
        return Response(to_wav_bytes(inst[instrument].play(dsp.midi(pitch), duration)), media_type="audio/wav")

    @app.post("/api/project/code")
    def project_code(req: ProjectRequest) -> dict:
        """The song script generated for a visual-editor project."""
        try:
            code = to_code(req.project)
        except ProjectError as e:
            raise HTTPException(400, f"Invalid project: {e}") from None
        return {"code": code, "project": from_code(code)}

    @app.post("/api/save")
    def save(req: SongRequest) -> dict:
        path = songs_dir / f"{_check_name(req.name)}.py"
        code = req.source()
        songs_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(code, encoding="utf-8")
        return {"path": str(path)}

    @app.post("/api/delete")
    def delete(req: NameRequest) -> dict:
        path = songs_dir / f"{_check_name(req.name)}.py"
        path.unlink(missing_ok=True)
        return {"deleted": req.name}

    @app.post("/api/export")
    def export_song(req: SongRequest) -> dict:
        _check_name(req.name)
        _, result = _render(req)
        files = export(result.audio, req.name, out_dir)
        return {"folder": str(out_dir), "files": [f.name for f in files], "warning": files.warning}

    @app.post("/api/open-output")
    def open_output() -> dict:
        out_dir.mkdir(parents=True, exist_ok=True)
        try:
            open_folder(out_dir)
        except OSError:  # no file manager (e.g. inside Docker): the page shows the path instead
            return {"folder": str(out_dir), "opened": False}
        return {"folder": str(out_dir), "opened": True}

    return app
