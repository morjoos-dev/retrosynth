import numpy as np
import pytest

from retrosynth.analysis import analyze
from retrosynth.runner import SongError, describe, run_code, run_file
from retrosynth.server import EXAMPLES_DIR

EXAMPLES = sorted(EXAMPLES_DIR.glob("*.py"))


def test_there_are_examples():
    assert len(EXAMPLES) >= 5


@pytest.mark.parametrize("path", EXAMPLES, ids=lambda p: p.stem)
def test_examples_render_cleanly(path):
    result = run_file(path)
    audio = result.audio
    assert audio.shape[0] == 2 and audio.shape[1] > 44_100
    a = analyze(audio)
    assert a.clipped == 0
    assert -24 < a.rms_db < -12
    assert describe(path.read_text(encoding="utf-8"))  # every example has a description


def test_rendering_is_deterministic():
    code = "s = Song(120, 1)\ns.put(noise(0.5), 0)\nsong = s"
    np.testing.assert_array_equal(run_code(code, "a").audio, run_code(code, "a").audio)
    assert not np.array_equal(run_code(code, "a").audio, run_code(code, "b").audio)


def test_song_variable_is_required():
    with pytest.raises(SongError, match="song"):
        run_code("s = Song(120, 1)")


def test_runtime_error_reports_the_line():
    with pytest.raises(SongError) as e:
        run_code("s = Song(120, 1)\n\ns.melody('flute', 0, 'C5:1 X9:1')\nsong = s")
    assert e.value.line == 3
    assert "X9" in e.value.message


def test_syntax_error_reports_the_line():
    with pytest.raises(SongError) as e:
        run_code("s = Song(120, 1)\nsong = s.render(\n")
    assert e.value.line in (2, 3)
    assert e.value.message.startswith("SyntaxError")


def test_print_output_is_captured():
    result = run_code("print('hello')\nsong = Song(120, 1)")
    assert result.log == "hello\n"


def test_describe():
    assert describe('"""Title — C major."""\nx = 1') == "Title — C major."
    assert describe("# First line\n# second\nx = 1") == "First line second"
