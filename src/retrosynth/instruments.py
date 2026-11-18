"""The instrument library.

Each instrument is a plain function that returns a mono numpy array. There are three
kinds, which differ only in their call signature:

* ``melodic`` — ``fn(freq_hz, duration_s, **options)``
* ``drum``    — ``fn(**options)`` (some accept a tuning frequency, e.g. ``tom(70)``)
* ``fx``      — ``fn(duration_s)`` (risers, reversed cymbals, crowd…)

``duration`` is how long the note is *held*; most instruments ring a little longer
(release tail). Access them as ``inst.flute(...)`` or ``inst["flute"](...)``.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Literal

import numpy as np
from scipy.signal import lfilter

from .dsp import (
    adsr,
    bandpass,
    decay,
    highpass,
    karplus_strong,
    lowpass,
    mix,
    noise,
    osc,
    partials,
    rand,
    samples,
    saturate,
    sine_sweep,
    time_axis,
)

Kind = Literal["melodic", "drum", "fx"]


@dataclass(frozen=True)
class Instrument:
    name: str
    kind: Kind
    description: str
    fn: Callable[..., np.ndarray]
    glide: bool = False  # accepts ``glide_from`` (portamento between notes)

    def __call__(self, *args, **kwargs) -> np.ndarray:
        return self.fn(*args, **kwargs)

    def play(self, freq: float, duration: float) -> np.ndarray:
        """Uniform entry point (used by the on-screen keyboard)."""
        if self.kind == "melodic":
            return self.fn(freq, duration)
        if self.kind == "fx":
            return self.fn(max(duration, 0.3))
        return self.fn()


class Registry:
    """Name → instrument, with attribute access: ``inst.harp(midi(60), 1.0)``."""

    def __init__(self) -> None:
        self._items: dict[str, Instrument] = {}

    def add(self, kind: Kind, description: str, *, name: str | None = None, glide: bool = False):
        def register(fn: Callable[..., np.ndarray]) -> Callable[..., np.ndarray]:
            key = name or fn.__name__
            self._items[key] = Instrument(key, kind, description, fn, glide)
            return fn

        return register

    def __getitem__(self, name: str) -> Instrument:
        try:
            return self._items[name]
        except KeyError:
            raise KeyError(f"unknown instrument {name!r}; available: {', '.join(self._items)}") from None

    def __getattr__(self, name: str) -> Instrument:
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            return self[name]
        except KeyError as e:
            raise AttributeError(str(e)) from None

    def __contains__(self, name: object) -> bool:
        return name in self._items

    def __iter__(self) -> Iterator[Instrument]:
        return iter(self._items.values())

    def __len__(self) -> int:
        return len(self._items)

    def names(self) -> list[str]:
        return list(self._items)


inst = Registry()
melodic = lambda d, **kw: inst.add("melodic", d, **kw)  # noqa: E731
drum = lambda d, **kw: inst.add("drum", d, **kw)  # noqa: E731
fx = lambda d, **kw: inst.add("fx", d, **kw)  # noqa: E731


def _detuned(duration: float, freq: float, detunes, wave="saw", gain=1.0, **opts) -> np.ndarray:
    """Several slightly detuned oscillators summed (ensemble / chorus effect)."""
    out = np.zeros(samples(duration))
    for det in detunes:
        out = mix(out, osc(duration, freq * (1 + det), wave, **opts), gain)
    return out


# ── Leads and melody ────────────────────────────────────────────────────────
@melodic("Soft flute: triangle plus a sine octave, late vibrato")
def flute(f, dur):
    n = dur + 0.25
    x = osc(n, f, "tri", vibrato=0.008, vibrato_delay=0.25) + 0.18 * osc(n, f * 2, "sine", vibrato=0.008, vibrato_delay=0.25)
    return lowpass(adsr(x, 0.04, 0.1, 0.8, 0.25, dur), 3200)


@melodic("16-bit square lead with vibrato; glides between notes with glide=True", glide=True)
def lead(f, dur, glide_from=0.0):
    n = dur + 0.12
    x = osc(n, f, "square", duty=0.25, vibrato=0.012, vibrato_delay=0.12, vibrato_rate=6, glide_from=glide_from, glide=0.035)
    x = x + 0.35 * osc(n, f * 1.003, "square")
    return lowpass(adsr(x, 0.006, 0.08, 0.75, 0.12, dur), 5200)


@melodic("Accordion: pulse + saw with bellows tremolo")
def accordion(f, dur):
    n = dur + 0.08
    x = osc(n, f, "square", duty=0.32, vibrato=0.006, vibrato_delay=0.1) + 0.5 * osc(n, f * 1.004, "saw")
    x *= 0.85 + 0.15 * np.sin(2 * np.pi * 6 * time_axis(len(x)))
    return lowpass(adsr(x, 0.03, 0.1, 0.8, 0.08, dur), 2600)


@melodic("Ney (reed flute): breathy triangle that scoops into pitch")
def ney(f, dur):
    n = dur + 0.15
    x = osc(n, f, "tri", vibrato=0.016, vibrato_rate=5.2, vibrato_delay=0.18, glide_from=f * 0.965, glide=0.07)
    x = x + 0.12 * bandpass(noise(n), f * 2, 3)
    return lowpass(adsr(x, 0.06, 0.1, 0.85, 0.15, dur), 3800)


# ── Plucked and struck ──────────────────────────────────────────────────────
@melodic("Harp / plucked string (Karplus-Strong)")
def harp(f, dur):
    length = max(dur, 1.2)
    return lowpass(adsr(karplus_strong(length, f), 0.002, 0.05, 0.9, 0.4, length - 0.4), 4200)


@melodic("Pizzicato strings: short damped pluck")
def pizzicato(f, dur):
    return decay(harp(f, 0.35), 9)


@melodic("Oud: bright pluck that dies faster than the harp")
def oud(f, dur):
    x = karplus_strong(max(dur, 0.8), f, blend=0.3, feedback=0.995)
    return lowpass(decay(x, 2.4), 3800)


@melodic("Marimba: sine with a short fourth-harmonic strike")
def marimba(f, dur):
    return partials(max(dur, 0.7), f, [(1, 1, 7), (4, 0.25, 30)])


@melodic("Music box: pure tine with a faint inharmonic overtone")
def music_box(f, dur):
    t = time_axis(samples(1.4))
    x = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 3.01 * t) * np.exp(-6 * t)
    return x * np.exp(-3.2 * t)


@melodic("FM bell")
def bell(f, dur):
    t = time_axis(samples(max(dur, 2.5)))
    mod = 2.2 * np.sin(2 * np.pi * f * 3.5 * t) * np.exp(-3 * t)
    return np.sin(2 * np.pi * f * t + mod) * np.exp(-1.6 * t)


@melodic("Large church bell with hum and tierce partials")
def church_bell(f, dur):
    spec = [(0.5, 0.5, 0.4), (1, 1, 0.6), (1.19, 0.6, 0.8), (1.5, 0.4, 1), (2, 0.5, 1.2), (2.52, 0.25, 1.6), (3, 0.2, 2)]
    x = partials(max(dur, 4.5), f, spec)
    return 0.4 * x * np.minimum(1.0, time_axis(len(x)) / 0.004)


# ── Sustained ───────────────────────────────────────────────────────────────
@melodic("String pad: three detuned saws, slow attack")
def strings(f, dur):
    x = _detuned(dur + 0.6, f, (-0.006, 0, 0.007), gain=0.33, vibrato=0.003, vibrato_rate=4.5, vibrato_delay=0)
    return lowpass(adsr(x, 0.35, 0.3, 0.8, 0.6, dur), 1800)


@melodic("Soft synth choir pad (two formants)")
def choir(f, dur):
    x = _detuned(dur + 0.8, f, (-0.004, 0.004), "tri", gain=0.5, vibrato=0.004, vibrato_rate=5, vibrato_delay=0)
    return adsr(bandpass(x, 700, 2) + 0.7 * bandpass(x, 1100, 2), 0.6, 0.3, 0.85, 0.8, dur)


@melodic("Pipe organ: drawbar harmonics with gentle tremolo")
def organ(f, dur):
    t = time_axis(samples(dur + 0.35))
    drawbars = [(1, 1), (2, 0.6), (3, 0.35), (4, 0.3), (6, 0.15), (8, 0.1), (0.5, 0.45)]
    x = sum(g * np.sin(2 * np.pi * f * h * t) for h, g in drawbars)
    x = 0.35 * x * (1 + 0.07 * np.sin(2 * np.pi * 5.8 * t))
    return lowpass(adsr(x, 0.06, 0.1, 0.9, 0.3, dur), 3500)


@melodic("Brass section: saws with a filter that opens on the attack")
def brass(f, dur):
    x = _detuned(dur + 0.15, f, (-0.004, 0.004), gain=0.5, vibrato=0.005, vibrato_delay=0.2)
    x = lowpass(x, lambda t: 1500 + 2800 * np.minimum(1, t / 0.06) * np.exp(-2.5 * t))
    return adsr(x, 0.02, 0.15, 0.7, 0.15, dur)


def _bowed(f, dur, body=((450, 0.55, 2), (2800, 0.35, 3)), cut=4800, vib=0.011, attack=0.07):
    """Bowed string: two saws with a violinist's late vibrato, bow noise and body resonances."""
    n = dur + 0.35
    src = osc(n, f, "saw", vibrato=vib, vibrato_rate=5.8, vibrato_delay=0.2)
    src = src + 0.35 * osc(n, f * 1.003, "saw", vibrato=vib * 0.8, vibrato_rate=5.3, vibrato_delay=0.24)
    src = src + 0.05 * decay(highpass(noise(n), 3000), 12)  # bow scratch on the attack
    out = lowpass(src, cut, 0.8)
    for fc, g, q in body:
        out = out + g * bandpass(src, fc, q)
    return adsr(out, attack, 0.12, 0.85, 0.2, dur)


@melodic("Violin (bowed, body resonances)")
def violin(f, dur):
    return _bowed(f, dur)


@melodic("Cello (bowed, darker body)")
def cello(f, dur):
    return _bowed(f, dur, body=((220, 0.6, 2), (1300, 0.25, 3)), cut=2600, vib=0.008, attack=0.09)


VOWELS = {
    "a": [(730, 1, 7), (1090, 0.5, 9), (2440, 0.22, 11)],
    "o": [(570, 1, 7), (840, 0.45, 9), (2410, 0.18, 11)],
    "u": [(300, 1, 6), (870, 0.22, 8), (2240, 0.08, 10)],
}


def voice(f, dur, vowel="a"):
    """Formant choir: four detuned saws filtered by the formants of a vowel."""
    n = dur + 0.6
    src = np.zeros(samples(n))
    for i, det in enumerate((-0.007, -0.0025, 0.003, 0.0075)):
        src = src + 0.25 * osc(n, f * (1 + det), "saw", vibrato=0.006, vibrato_rate=4.6 + i * 0.35, vibrato_delay=0.25)
    out = sum(g * bandpass(src, fc, q) for fc, g, q in VOWELS[vowel])
    return adsr(out, 0.3, 0.3, 0.85, 0.55, dur)


for _v in VOWELS:
    melodic(f"Formant choir singing '{_v}'", name=f"voice_{_v}")(lambda f, dur, _v=_v: voice(f, dur, _v))


# ── Bass and guitar ─────────────────────────────────────────────────────────
@melodic("Round bass: triangle with a touch of square")
def bass(f, dur):
    n = dur + 0.05
    return lowpass(adsr(osc(n, f, "tri") + 0.25 * osc(n, f, "square"), 0.005, 0.08, 0.8, 0.05, dur), 900)


@melodic("Rock bass: saw with a snappy closing filter")
def rock_bass(f, dur):
    x = lowpass(osc(dur + 0.03, f, "saw"), lambda t: 300 + 2200 * np.exp(-18 * t), 1.2)
    return adsr(x, 0.003, 0.05, 0.7, 0.03, dur)


@melodic("Plucked bass (low-passed string)")
def plucked_bass(f, dur):
    return lowpass(harp(f, max(dur, 0.5)), 700)


@melodic("Distorted power-chord guitar; mute=True for palm-muted chugs")
def guitar(f, dur, mute=False):
    n = dur + 0.05
    x = np.zeros(samples(n))
    for ratio, g in ((1, 1), (1.4983, 0.8), (2, 0.5)):
        x = x + _detuned(n, f * ratio, (-0.003, 0.003), gain=g * 0.4)
    x = lowpass(saturate(x, 3.5), 1300 if mute else 2600)
    return adsr(x, 0.003, 0.06, 0.4 if mute else 0.85, 0.05, dur)


@melodic("Cinematic 'braam': huge saturated low brass")
def braam(f, dur):
    x = saturate(_detuned(dur + 0.5, f, (-0.008, -0.003, 0.003, 0.008), gain=0.3), 2.2)
    x = lowpass(x, lambda t: 200 + 1600 * np.minimum(1, t / 0.4) * np.exp(-0.6 * t))
    return adsr(x, 0.05, 0.4, 0.75, 0.5, dur)


# ── Drums and percussion ────────────────────────────────────────────────────
@drum("Kick drum: pitch-dropping sine plus a click")
def kick():
    body = sine_sweep(0.35, lambda t: 45 + 110 * np.exp(-28 * t))
    body = decay(body, 9)
    click = lowpass(adsr(noise(0.01), 0.0005, 0.005, 0, 0.004, 0.005), 3000)
    return mix(body, click, 0.5)


@drum("Snare: band-passed noise plus a tonal body")
def snare():
    rattle = adsr(bandpass(noise(0.25), 1900, 0.8), 0.001, 0.04, 0.3, 0.12, 0.05)
    tone = adsr(osc(0.12, 185, "tri"), 0.001, 0.05, 0.2, 0.05, 0.05)
    return mix(rattle, tone, 0.6)


@drum("Hi-hat; open=True for an open hat")
def hihat(open=False):
    return adsr(highpass(noise(0.3 if open else 0.06), 7000), 0.001, 0.12 if open else 0.03, 0.05, 0.15 if open else 0.02, 0.01)


@drum("Crash cymbal")
def cymbal():
    return adsr(highpass(noise(1.6), 5000), 0.002, 0.3, 0.35, 1.2, 0.3)


@drum("Tom / war drum, tunable: tom(70)")
def tom(freq=70.0):
    body = decay(sine_sweep(0.9, lambda t: freq + 40 * np.exp(-12 * t)), 4.5)
    thump = lowpass(adsr(noise(0.15, "brown"), 0.001, 0.05, 0.3, 0.08, 0.05), 400)
    return mix(body, thump, 0.8)


@drum("Timpani, tunable: timpani(90)")
def timpani(freq=90.0):
    return tom(freq)


@drum("Shaker")
def shaker():
    return adsr(highpass(noise(0.05), 6000), 0.004, 0.02, 0.2, 0.02, 0.02)


@drum("Sleigh bells")
def sleigh_bells():
    n = samples(0.35)
    out = np.zeros(n)
    for offset in (0.0, 0.045, 0.085):
        start = samples(offset) if offset else 0
        t = time_axis(n - start)
        jingle = np.sin(2 * np.pi * 5200 * t) + 0.7 * np.sin(2 * np.pi * 6650 * t) + 0.5 * np.sin(2 * np.pi * 8100 * t)
        jingle = jingle + 0.6 * (rand(len(t)) * 2 - 1)
        out[start:] += 0.25 * jingle * np.exp(-35 * t)
    return highpass(out, 4000)


@drum("Tambourine")
def tambourine():
    return mix(adsr(highpass(noise(0.12), 7500), 0.001, 0.03, 0.2, 0.06, 0.02), sleigh_bells(), 0.25)


@drum("Doumbek low stroke ('doum')")
def doum():
    return tom(105)


@drum("Doumbek high stroke ('tek')")
def tek():
    crack = adsr(bandpass(noise(0.09), 3200, 1.2), 0.0005, 0.02, 0.15, 0.05, 0.02)
    ring = adsr(osc(0.05, 420, "tri"), 0.0005, 0.02, 0.2, 0.02, 0.02)
    return mix(crack, ring, 0.4)


@drum("Hand claps (several hands at once)")
def claps():
    out = np.zeros(samples(0.25))
    for offset in (0.0, 0.006, 0.013, 0.021):
        hit = adsr(bandpass(noise(0.2), 1000 + rand() * 600, 1.2), 0.0008, 0.03, 0.1, 0.06, 0.01)
        start = samples(offset) if offset else 0
        out[start:] = mix(out[start:], hit, 0.5)
    return out


@drum("Anvil strike, tunable: anvil(820)")
def anvil(freq=820.0):
    ring = partials(1.6, freq, [(1, 1, 5), (2.76, 0.6, 7), (5.4, 0.4, 10), (8.93, 0.25, 14), (13.3, 0.15, 18)])
    return mix(ring, adsr(highpass(noise(0.05), 2500), 0.0005, 0.01, 0.2, 0.02, 0.01), 0.8)


@drum("Cinematic impact: falling sub boom with a crack")
def impact():
    body = decay(sine_sweep(2.4, lambda t: 32 + 90 * np.exp(-14 * t)), 1.6)
    body = mix(body, lowpass(adsr(noise(0.6, "brown"), 0.001, 0.15, 0.2, 0.4, 0.1), 600), 0.9)
    return mix(body, adsr(highpass(noise(0.05), 2500), 0.0005, 0.02, 0, 0.02, 0.01), 0.5)


@drum("Group shout 'hey!', tunable: shout(180)")
def shout(freq=180.0):
    n = 0.4
    src = np.zeros(samples(n))
    for det in (-0.012, -0.005, 0.002, 0.008, 0.014):
        f = freq * (1 + det)
        src = src + 0.2 * osc(n, f, "saw", glide_from=f * 1.1, glide=0.09)
    src = src + 0.06 * highpass(noise(n), 1500)
    out = sum(g * bandpass(src, fc, q) for fc, g, q in [(730, 1, 5), (1090, 0.6, 6), (2440, 0.3, 8)])
    return adsr(out, 0.008, 0.08, 0.6, 0.12, 0.17)


# ── Effects ─────────────────────────────────────────────────────────────────
@fx("Noise riser: filter and volume swell into a hit")
def riser(dur):
    x = noise(dur)
    x *= np.linspace(0, 1, len(x), endpoint=False) ** 2.2
    return lowpass(x, lambda t: 300 + 9000 * np.minimum(1, t / dur) ** 2, 1.4)


@fx("Reversed cymbal swell")
def reverse_cymbal(dur):
    x = highpass(noise(dur), 4000)
    return x * np.linspace(0, 1, len(x), endpoint=False) ** 3


@fx("Stadium crowd roar with random swells")
def crowd(dur):
    n = dur + 0.8
    x = sum(g * bandpass(noise(n), fc, q) for fc, q, g in [(420, 1.2, 1), (850, 1.5, 0.75), (1700, 2, 0.4), (3100, 2, 0.18)])
    # a new random loudness target every 50 ms, smoothed by a one-pole filter (starts at 0.6)
    k = 0.0006
    target = np.repeat(0.35 + rand(-(-len(x) // 2205)) * 0.65, 2205)[: len(x)]
    wave = lfilter([k], [1, k - 1], target, zi=[0.6 * (1 - k)])[0]
    return adsr(x * wave, min(0.9, dur * 0.3), 0.2, 0.9, 0.8, dur)
