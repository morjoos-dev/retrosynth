import numpy as np
import pytest

from retrosynth import SR, Note, Song, beats_of, chord, inst, lower, mel, note, note_name, progression, soft_limit


def test_note_names():
    assert note("C4") == 60
    assert note("A4") == 69
    assert note("F#3") == 54
    assert note("Bb2") == 46
    assert note_name(61) == "C#4"
    with pytest.raises(ValueError):
        note("H2")


def test_melody_parsing():
    m = mel("C5:1  E5:0.5\n r:0.5")
    assert m == [Note(72, 1.0), Note(76, 0.5), Note(None, 0.5)]
    assert beats_of(m) == 2
    assert lower(m)[0].pitch == 60 and lower(m)[2].pitch is None
    with pytest.raises(ValueError, match="duration"):
        mel("C5")


def test_chords_and_progressions():
    assert chord("A2", "min") == [45, 48, 52]
    events = progression("C:4 Am:2 G7:2", octave=3)
    assert [e.beat for e in events] == [0, 4, 6]
    assert events[1].notes == chord("A3", "min")
    assert len(events[2].notes) == 4
    with pytest.raises(ValueError):
        progression("C4")


def test_put_pans_with_equal_power():
    s = Song(bpm=120, bars=1)
    s.put(np.ones(10), 0, gain=1.0, pan=-1.0, wet=0)
    assert s.dry[0, 0] == pytest.approx(1.0) and s.dry[1, 0] == pytest.approx(0.0, abs=1e-12)
    s.put(np.ones(10), 0.5, gain=1.0, pan=0.0, wet=0)
    i = round(0.5 * SR)
    assert s.dry[0, i] == pytest.approx(np.sqrt(0.5)) and s.dry[1, i] == pytest.approx(np.sqrt(0.5))


def test_loop_wraps_tail_to_start():
    """A note that rings past the end must come back at the beginning of the loop."""
    s = Song(bpm=120, bars=1)  # 2 seconds long
    s.put(np.ones(SR), 1.5, wet=0)  # one second: half of it past the end
    out = s.render(loudness=0.1)
    assert out.shape == (2, 2 * SR)
    assert np.all(out[:, : SR // 2 - 10] != 0)  # tail folded onto the start
    assert np.all(out[:, SR // 2 + 10 : int(1.5 * SR) - 10] == 0)


def test_one_shot_keeps_the_tail():
    s = Song(bpm=120, bars=1, loop=False, tail=1.0)
    out = s.render()
    assert out.shape[1] == 3 * SR


def test_render_normalises_loudness():
    s = Song(bpm=120, bars=2)
    s.melody("flute", 0, "C5:2 E5:2 G5:4")
    out = s.render(loudness=0.1)
    assert out.dtype == np.float32
    assert np.sqrt(np.mean(out.astype(float) ** 2)) == pytest.approx(0.1, rel=0.05)


def test_soft_limit_is_transparent_below_threshold():
    x = np.linspace(-0.7, 0.7, 101)
    np.testing.assert_array_equal(soft_limit(x), x)
    assert np.max(np.abs(soft_limit(np.array([5.0, -5.0])))) <= 0.98


def test_melody_returns_length_and_glides():
    s = Song(bpm=120, bars=1)
    assert s.melody("lead", 0, "C5:1 r:1 E5:2", glide=True) == 4


@pytest.mark.parametrize("instrument", list(inst), ids=lambda i: i.name)
def test_every_instrument_produces_sound(instrument):
    x = instrument.play(440.0, 0.4)
    assert x.ndim == 1 and len(x) > 0
    assert np.all(np.isfinite(x))
    assert np.max(np.abs(x)) > 1e-3
