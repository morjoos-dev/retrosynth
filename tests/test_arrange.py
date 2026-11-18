import copy

import pytest

from retrosynth.analysis import analyze
from retrosynth.arrange import ProjectError, from_code, normalize, to_code
from retrosynth.presets import PRESETS
from retrosynth.runner import run_code

BASE = PRESETS[0]["project"]


@pytest.mark.parametrize("preset", PRESETS, ids=lambda p: p["id"])
def test_presets_render(preset):
    code = to_code(preset["project"])
    result = run_code(code, preset["id"])
    a = analyze(result.audio)
    assert a.clipped == 0 and a.seam_clean
    assert a.duration == pytest.approx(preset["project"]["bars"] * 4 * 60 / preset["project"]["bpm"], abs=1e-3)


@pytest.mark.parametrize("preset", PRESETS, ids=lambda p: p["id"])
def test_project_round_trips_through_code(preset):
    assert from_code(to_code(preset["project"])) == normalize(preset["project"])


def test_every_style_combination_renders():
    p = copy.deepcopy(BASE)
    p["bars"] = 2
    for chord_style in ("pad", "arpeggio", "fast_arpeggio", "stabs", "off"):
        for bass_style in ("root", "root_fifth", "eighths", "octaves", "off"):
            p["tracks"]["chords"]["style"], p["tracks"]["bass"]["style"] = chord_style, bass_style
            assert run_code(to_code(p)).audio.shape[0] == 2


def test_defaults_fill_an_empty_project():
    p = normalize({})
    assert p["bars"] == 8 and len(p["tracks"]["chords"]["chords"]) == 8
    assert run_code(to_code({"tracks": {"chords": {"chords": ["C", "G"]}}})).audio.shape[1] > 0


def test_values_are_clamped():
    p = normalize({"bpm": 9999, "bars": 0, "reverb": -5, "tracks": {"melody": {"volume": 50, "pan": -9}}})
    assert p["bpm"] == 240 and p["bars"] == 1 and p["reverb"] == 0.3
    assert p["tracks"]["melody"]["volume"] == 1.5 and p["tracks"]["melody"]["pan"] == -1


def test_notes_outside_the_song_are_dropped():
    notes = [{"pitch": 60, "start": 0, "length": 4}, {"pitch": 60, "start": 16, "length": 4},
             {"pitch": 200, "start": 1, "length": 1}]
    p = normalize({"bars": 1, "tracks": {"melody": {"notes": notes}}})
    assert [n["start"] for n in p["tracks"]["melody"]["notes"]] == [0]


def test_chords_repeat_to_fill_the_bars():
    p = normalize({"bars": 5, "tracks": {"chords": {"chords": ["C", "G"]}}})
    assert p["tracks"]["chords"]["chords"] == ["C", "G", "C", "G", "C"]


@pytest.mark.parametrize("bad", [
    {"tracks": {"melody": {"instrument": "__import__('os')"}}},
    {"tracks": {"melody": {"instrument": "kick"}}},  # drums are not melodic
    {"tracks": {"chords": {"chords": ["C'); import os; ('"]}}},
    {"tracks": {"chords": {"style": "pad); import os; ("}}},
    {"tracks": {"drums": {"rows": {"kick); import os; (": "x"}}}},
    {"key": "H"},
    {"tracks": {"melody": {"notes": [{"pitch": "60; import os"}]}}},
])
def test_rejects_anything_that_could_inject_code(bad):
    with pytest.raises(ProjectError):
        to_code(bad)


def test_free_text_cannot_escape_the_docstring():
    p = copy.deepcopy(BASE)
    p["title"] = 'x"""\nimport os\nos.system("echo hacked")\n"""'
    code = to_code(p)
    first, rest = code.split("\n", 1)
    assert first.startswith('"""') and first.count('"""') == 2  # the title stays inside one docstring line
    executable = [line for line in rest.splitlines() if not line.lstrip().startswith("#")]
    assert not any("os.system" in line for line in executable)  # only in comments, never in code
    run_code(code)  # still a valid script


def test_drum_patterns_are_sanitised():
    p = normalize({"tracks": {"drums": {"rows": {"kick": "x'x\"x\\x" + "x" * 40}}}})
    assert p["tracks"]["drums"]["rows"]["kick"] == "x.x.x.x" + "x" * 9


def test_code_is_readable():
    code = to_code(BASE)
    assert "from retrosynth import *" in code
    assert "inst.lead(" in code and "chord_symbol(name)" in code
    assert "song = s.render(" in code


def test_from_code_ignores_plain_scripts():
    assert from_code("song = Song(120, 1)") is None
    assert from_code("# retrosynth-project: {not json") is None
