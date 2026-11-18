"""Songs: placing sounds on a timeline, melodies, chords and the final mixdown.

A song is a fixed number of bars at a fixed tempo. Sounds are mixed into a stereo dry
bus and a stereo reverb send; :meth:`Song.render` adds the reverb, folds the tail that
rings past the end back onto the start (so the track loops seamlessly), normalises the
loudness and applies a soft limiter.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass

import numpy as np

from .dsp import SR, midi, reverb, samples
from .instruments import Instrument, inst

# ── Notes and melodies ──────────────────────────────────────────────────────
_NOTE_RE = re.compile(r"^([A-Ga-g])([#b]?)(-?\d)$")
_STEPS = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def note(name: str) -> int:
    """Note name → MIDI number: ``note("C4") == 60``, ``note("F#3") == 54``, ``note("Bb2") == 46``."""
    m = _NOTE_RE.match(name.strip())
    if not m:
        raise ValueError(f"invalid note {name!r} (expected e.g. C4, F#3, Bb5)")
    letter, accidental, octave = m.groups()
    return 12 * (int(octave) + 1) + _STEPS[letter.upper()] + {"#": 1, "b": -1, "": 0}[accidental]


def note_name(number: int) -> str:
    """MIDI number → note name: ``note_name(61) == "C#4"``."""
    return f"{NOTE_NAMES[number % 12]}{number // 12 - 1}"


@dataclass(frozen=True)
class Note:
    pitch: int | None  # MIDI number, or None for a rest
    beats: float

    def transposed(self, semitones: int) -> Note:
        return self if self.pitch is None else Note(self.pitch + semitones, self.beats)


def mel(text: str) -> list[Note]:
    """Parse a melody written as ``"pitch:beats"`` tokens, ``r`` for a rest.

    >>> mel("C5:1 E5:0.5 r:0.5")
    [Note(pitch=72, beats=1.0), Note(pitch=76, beats=0.5), Note(pitch=None, beats=0.5)]
    """
    notes = []
    for token in text.split():
        pitch, sep, beats = token.partition(":")
        if not sep:
            raise ValueError(f"melody token {token!r} needs a duration, e.g. {token}:1")
        notes.append(Note(None if pitch.lower() == "r" else note(pitch), float(beats)))
    return notes


def transpose(notes: Iterable[Note], semitones: int) -> list[Note]:
    """Shift every note of a melody (rests are kept)."""
    return [n.transposed(semitones) for n in notes]


def lower(notes: Iterable[Note], semitones: int = 12) -> list[Note]:
    """Melody one octave (or ``semitones``) lower."""
    return transpose(notes, -semitones)


def beats_of(notes: Iterable[Note]) -> float:
    return sum(n.beats for n in notes)


# ── Chords ──────────────────────────────────────────────────────────────────
CHORDS: dict[str, tuple[int, ...]] = {
    "maj": (0, 4, 7),
    "min": (0, 3, 7),
    "dim": (0, 3, 6),
    "aug": (0, 4, 8),
    "sus2": (0, 2, 7),
    "sus4": (0, 5, 7),
    "maj7": (0, 4, 7, 11),
    "min7": (0, 3, 7, 10),
    "dom7": (0, 4, 7, 10),
    "add9": (0, 4, 7, 14),
}
# suffixes accepted by progression(): "C", "Am", "G7", "Fmaj7", "Dsus4"…
_SUFFIX = {"": "maj", "m": "min", "7": "dom7", "m7": "min7", "maj7": "maj7", "dim": "dim",
           "aug": "aug", "sus2": "sus2", "sus4": "sus4", "add9": "add9"}


def chord(root: str, kind: str = "maj") -> list[int]:
    """MIDI notes of a chord in root position: ``chord("A2", "min") == [45, 48, 52]``."""
    if kind not in CHORDS:
        raise ValueError(f"unknown chord kind {kind!r}; available: {', '.join(CHORDS)}")
    base = note(root)
    return [base + step for step in CHORDS[kind]]


@dataclass(frozen=True)
class ChordEvent:
    beat: float  # start, in beats from the beginning
    notes: list[int]
    beats: float


CHORD_SYMBOL_RE = re.compile(r"^([A-G][#b]?)(maj7|m7|sus2|sus4|add9|dim|aug|m|7)?$")


def chord_symbol(symbol: str, octave: int = 3) -> list[int]:
    """Chord from a symbol, root placed in ``octave``: ``chord_symbol("Am") == [57, 60, 64]``.

    Accepted suffixes: (none) major, ``m``, ``7``, ``m7``, ``maj7``, ``dim``, ``aug``, ``sus2``,
    ``sus4``, ``add9``.
    """
    m = CHORD_SYMBOL_RE.match(symbol.strip())
    if not m:
        raise ValueError(f"invalid chord {symbol!r} (expected e.g. C, F#m, G7, Bbmaj7)")
    root, suffix = m.groups()
    return chord(f"{root}{octave}", _SUFFIX[suffix or ""])


def progression(text: str, octave: int = 3) -> list[ChordEvent]:
    """Parse a chord chart like ``"C:4 Am:4 F:2 G7:2"`` into timed chords.

    Roots are placed in ``octave`` (C–B), so ``"A:4"`` in octave 3 is A3.
    """
    events, beat = [], 0.0
    for token in text.split():
        symbol, _, beats = token.partition(":")
        try:
            notes, length = chord_symbol(symbol, octave), float(beats)
        except ValueError:
            raise ValueError(f"invalid chord {token!r} (expected e.g. C:4, F#m:2, G7:1)") from None
        events.append(ChordEvent(beat, notes, length))
        beat += length
    return events


# ── Song ────────────────────────────────────────────────────────────────────
InstrumentRef = str | Instrument | Callable[..., np.ndarray]


def _resolve(instrument: InstrumentRef) -> Callable[..., np.ndarray]:
    return inst[instrument] if isinstance(instrument, str) else instrument


class Song:
    """A timeline of ``bars`` bars at ``bpm`` beats per minute.

    ``loop=True`` (default) makes a seamless loop: whatever rings past the last bar is
    mixed back into the beginning. Use ``loop=False`` for one-shot cues (fanfares,
    stingers); the reverb tail is then kept at the end.
    """

    def __init__(self, bpm: float, bars: int, beats_per_bar: int = 4, *, loop: bool = True, tail: float = 3.0):
        if bpm <= 0 or bars <= 0:
            raise ValueError("bpm and bars must be positive")
        self.bpm = bpm
        self.bars = bars
        self.beats_per_bar = beats_per_bar
        self.loop = loop
        self.beat = 60.0 / bpm  # seconds per beat
        self.length = bars * beats_per_bar * self.beat  # seconds, without tail
        size = samples(self.length + tail)
        self.dry = np.zeros((2, size))
        self.send = np.zeros((2, size))

    def at(self, bar: float, beat: float = 0.0) -> float:
        """Time in seconds of ``beat`` within ``bar`` (both zero-based)."""
        return (bar * self.beats_per_bar + beat) * self.beat

    def put(self, sound: np.ndarray, time: float, *, gain: float = 1.0, pan: float = 0.0, wet: float = 0.25) -> None:
        """Mix a mono ``sound`` in at ``time`` seconds.

        ``pan`` goes from -1 (left) to 1 (right) with an equal-power law; ``wet`` is how
        much of it is sent to the reverb.
        """
        start = round(time * SR)
        if start < 0 or start >= self.dry.shape[1]:
            return
        seg = np.asarray(sound, dtype=float)[: self.dry.shape[1] - start]
        angle = (pan + 1.0) * np.pi / 4.0
        gains = gain * np.array([[np.cos(angle)], [np.sin(angle)]])
        end = start + len(seg)
        self.dry[:, start:end] += gains * seg
        if wet:
            self.send[:, start:end] += (gains * wet) * seg

    def melody(
        self,
        instrument: InstrumentRef,
        start_bar: float,
        notes: Sequence[Note] | str,
        *,
        gain: float = 1.0,
        pan: float = 0.0,
        wet: float = 0.25,
        legato: float = 0.95,
        transpose: int = 0,
        glide: bool = False,
    ) -> float:
        """Play a melody from ``start_bar``; returns its length in beats.

        ``legato`` is the fraction of each note's value that is held. ``glide=True``
        slides between consecutive notes (only for instruments that support it).
        """
        if isinstance(notes, str):
            notes = mel(notes)
        fn = _resolve(instrument)
        can_glide = glide and getattr(fn, "glide", False)
        beat, previous = 0.0, None
        for n in notes:
            if n.pitch is not None:
                kwargs = {"glide_from": midi(previous + transpose)} if can_glide and previous is not None else {}
                sound = fn(midi(n.pitch + transpose), n.beats * self.beat * legato, **kwargs)
                self.put(sound, self.at(start_bar, beat), gain=gain, pan=pan, wet=wet)
                previous = n.pitch
            beat += n.beats
        return beat

    def render(self, reverb_size: float = 1.0, loudness: float = 0.15) -> np.ndarray:
        """Mix down to a ``(2, n)`` float32 array.

        ``reverb_size`` scales the room; ``loudness`` is the target RMS level of the
        whole track (0.15 ≈ -16.5 dBFS), so every song comes out equally loud.
        """
        mixed = self.dry.copy()
        mixed[0] += reverb(self.send[0], reverb_size)
        mixed[1] += reverb(self.send[1], reverb_size * 1.07)  # slightly different room: wider image
        if self.loop:
            n = samples(self.length)
            out = mixed[:, :n].copy()
            tail = mixed[:, n:]
            for k in range(0, tail.shape[1], n):  # wrap the tail onto the start
                chunk = tail[:, k : k + n]
                out[:, : chunk.shape[1]] += chunk
        else:
            out = mixed
        rms = float(np.sqrt(np.mean(out**2))) or 1.0
        return soft_limit(out * (loudness / rms)).astype(np.float32)


def soft_limit(x: np.ndarray, threshold: float = 0.7, ceiling: float = 0.98) -> np.ndarray:
    """Leave everything below ``threshold`` untouched; squash peaks smoothly below ``ceiling``."""
    knee = ceiling - threshold
    a = np.abs(x)
    over = a > threshold
    out = x.copy()
    out[over] = np.sign(x[over]) * (threshold + knee * np.tanh((a[over] - threshold) / knee))
    return out


# ── Arrangement helpers ─────────────────────────────────────────────────────
def pad(song: Song, bar: float, notes: Sequence[int], beats: float, *, gain: float = 0.07, wet: float = 0.45,
        octave: int = 12, instrument: InstrumentRef = "strings", beat: float = 0.0) -> None:
    """Hold a chord on a pad instrument, voices spread across the stereo field."""
    fn = _resolve(instrument)
    spread = len(notes) - 1 or 1
    for i, n in enumerate(notes):
        song.put(fn(midi(n + octave), song.beat * beats), song.at(bar, beat),
                 gain=gain, pan=(2 * i / spread - 1) * 0.3, wet=wet)


def arpeggio(song: Song, bar: float, notes: Sequence[int], pattern: Sequence[int], *, step: float = 0.5,
             instrument: InstrumentRef = "harp", gain: float = 0.1, pan: float = 0.0, wet: float = 0.4,
             octave: int = 12) -> None:
    """Play chord tones by index (``pattern=[0, 1, 2, 1]``) every ``step`` beats.

    Indices past the end of the chord wrap up an octave: ``3`` on a triad is the root + 12.
    """
    fn = _resolve(instrument)
    for k, idx in enumerate(pattern):
        n = notes[idx % len(notes)] + 12 * (idx // len(notes)) + octave
        song.put(fn(midi(n), song.beat * step), song.at(bar, k * step), gain=gain, pan=pan, wet=wet)


def drum_pattern(song: Song, bar: float, pattern: str, instrument: InstrumentRef, *, gain: float = 0.5,
                 pan: float = 0.0, wet: float = 0.1, accent: float = 1.4, **options) -> None:
    """Step-sequencer style: ``"x...x...X..x.x.."`` over one bar.

    Each character is one step (the bar is divided evenly): ``x`` hit, ``X`` accented
    hit, anything else silent. Extra ``options`` are passed to the drum (e.g. ``open=True``).
    """
    steps = pattern.replace(" ", "")
    fn = _resolve(instrument)
    size = song.beats_per_bar / len(steps)
    for k, ch in enumerate(steps):
        if ch in "xX":
            song.put(fn(**options), song.at(bar, k * size), gain=gain * (accent if ch == "X" else 1.0), pan=pan, wet=wet)


def rock_drums(song: Song, bar: float, *, double_kick: bool = False, crash: bool = False, soft: float = 1.0) -> None:
    """A bar of rock drums: kick, backbeat snare, eighth-note hi-hats."""
    if double_kick:
        for k in range(16):
            song.put(inst.kick(), song.at(bar, k * 0.25), gain=(0.8 if k % 4 == 0 else 0.45) * soft, wet=0.04)
    else:
        for b in (0, 2, 2.5):
            song.put(inst.kick(), song.at(bar, b), gain=0.8 * soft, wet=0.05)
    for b in (1, 3):
        song.put(inst.snare(), song.at(bar, b), gain=0.45 * soft, pan=0.05, wet=0.2)
    for k in range(8):
        song.put(inst.hihat(open=k == 7), song.at(bar, k * 0.5), gain=(0.11 if k % 2 else 0.17) * soft, pan=-0.35, wet=0.08)
    if crash:
        song.put(inst.cymbal(), song.at(bar), gain=0.22 * soft, pan=0.4, wet=0.3)
