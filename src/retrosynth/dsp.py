"""Low-level DSP building blocks: oscillators, envelopes, filters, noise and reverb.

Every function works on mono ``float64`` numpy arrays sampled at :data:`SAMPLE_RATE`.
Recursive algorithms (state-variable filters, Karplus-Strong strings, Schroeder reverb)
are expressed as linear IIR filters and run through :func:`scipy.signal.lfilter`, so
there are no per-sample Python loops on the hot path.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal, Union

import numpy as np
from scipy.signal import lfilter

SAMPLE_RATE = 44_100
SR = SAMPLE_RATE

Cutoff = Union[float, Callable[[np.ndarray], np.ndarray]]  # noqa: UP007 (runtime alias, Python 3.10)
Wave = Literal["sine", "tri", "saw", "square"]

# ── Randomness ──────────────────────────────────────────────────────────────
# A single module-level generator, re-seeded before every render, makes the output
# fully deterministic: the same song code always produces the same audio.
_rng = np.random.default_rng(1)


def seed(value: int) -> None:
    """Reset the random generator used by oscillators and noise."""
    global _rng
    _rng = np.random.default_rng(value)


def rand(size: int | None = None):
    """Uniform random numbers in ``[0, 1)`` from the shared generator."""
    return _rng.random(size)


# ── Units ───────────────────────────────────────────────────────────────────
def samples(seconds: float) -> int:
    """Duration in seconds → number of samples (at least one)."""
    return max(1, round(seconds * SR))


def time_axis(n: int) -> np.ndarray:
    """Time in seconds of each of the first ``n`` samples."""
    return np.arange(n) / SR


def midi(note: float) -> float:
    """MIDI note number → frequency in Hz (A4 = 69 = 440 Hz)."""
    return 440.0 * 2.0 ** ((note - 69) / 12)


def mix(a: np.ndarray, b: np.ndarray, gain: float = 1.0) -> np.ndarray:
    """Return ``a + gain * b``; the result has the length of ``a`` (``b`` is cut or padded)."""
    out = a.copy()
    n = min(len(a), len(b))
    out[:n] += gain * b[:n]
    return out


# ── Oscillators and noise ───────────────────────────────────────────────────
def osc(
    duration: float,
    freq: float,
    wave: Wave = "square",
    *,
    duty: float = 0.5,
    vibrato: float = 0.0,
    vibrato_rate: float = 5.5,
    vibrato_delay: float = 0.15,
    glide_from: float = 0.0,
    glide: float = 0.04,
) -> np.ndarray:
    """Naive (non band-limited) oscillator with delayed vibrato and an optional glide.

    ``vibrato`` is the depth as a fraction of the frequency; it fades in over 0.2 s
    after ``vibrato_delay``. ``glide_from`` slides linearly from that frequency to
    ``freq`` during the first ``glide`` seconds (portamento).
    """
    n = samples(duration)
    t = time_axis(n)
    f = np.full(n, float(freq))
    if glide_from:
        g = t < glide
        f[g] = glide_from + (freq - glide_from) * (t[g] / glide)
    if vibrato:
        depth = vibrato * np.clip((t - vibrato_delay) / 0.2, 0.0, 1.0)
        f *= 1.0 + depth * np.sin(2 * np.pi * vibrato_rate * t)
    phase = (rand() + np.cumsum(f) / SR) % 1.0
    if wave == "sine":
        return np.sin(2 * np.pi * phase)
    if wave == "tri":
        return 4.0 * np.abs(phase - 0.5) - 1.0
    if wave == "saw":
        return 2.0 * phase - 1.0
    if wave == "square":
        return np.where(phase < duty, 1.0, -1.0)
    raise ValueError(f"unknown wave {wave!r}")


def sine_sweep(duration: float, freq: Callable[[np.ndarray], np.ndarray]) -> np.ndarray:
    """Sine whose frequency follows ``freq(t)`` (phase-continuous). Used for drums."""
    t = time_axis(samples(duration))
    return np.sin(2 * np.pi * np.cumsum(freq(t)) / SR)


def partials(duration: float, freq: float, spec) -> np.ndarray:
    """Sum of decaying sine partials: ``spec`` is a list of ``(ratio, gain, decay)``."""
    t = time_axis(samples(duration))
    out = np.zeros_like(t)
    for ratio, gain, decay in spec:
        out += gain * np.sin(2 * np.pi * freq * ratio * t) * np.exp(-t * decay)
    return out


def noise(duration: float, color: Literal["white", "brown"] = "white") -> np.ndarray:
    """White noise in ``[-1, 1)`` or brown (integrated, leaky) noise."""
    w = rand(samples(duration)) * 2.0 - 1.0
    if color == "brown":
        # br[n] = (br[n-1] + 0.02 w[n]) / 1.02, scaled by 3.5
        return lfilter([0.02 / 1.02 * 3.5], [1.0, -1.0 / 1.02], w)
    return w


# ── Envelopes and shaping ───────────────────────────────────────────────────
def adsr(x: np.ndarray, attack: float, decay: float, sustain: float, release: float, hold: float) -> np.ndarray:
    """Apply a linear ADSR envelope. ``hold`` is the time (s) at which the note is released."""
    t = time_axis(len(x))
    attack, decay, release = max(attack, 1e-9), max(decay, 1e-9), max(release, 1e-9)
    env = np.select(
        [t < attack, t < attack + decay, t < hold],
        [t / attack, 1.0 - (1.0 - sustain) * (t - attack) / decay, sustain],
        sustain * np.maximum(0.0, 1.0 - (t - hold) / release),
    )
    return x * env


def decay(x: np.ndarray, rate: float) -> np.ndarray:
    """Multiply by an exponential decay ``exp(-rate * t)``."""
    return x * np.exp(-time_axis(len(x)) * rate)


def saturate(x: np.ndarray, drive: float) -> np.ndarray:
    """Soft clipping with ``tanh``; output peak stays at ±1 for input ±1."""
    return np.tanh(x * drive) / np.tanh(drive)


# ── State-variable filter ───────────────────────────────────────────────────
# Chamberlin SVF, per sample:
#     low  += f * band
#     high  = x - low - d * band
#     band += f * high
# It is linear and time-invariant for fixed f and d, so each output is an IIR filter
# with denominator 1 + (f² + f·d - 2) z⁻¹ + (1 - f·d) z⁻². See tests/test_dsp.py for the
# check against the per-sample reference.
def _svf(cutoff: float, damping: float, clamp: bool) -> tuple[float, list[float]]:
    if clamp:
        cutoff = min(cutoff, SR / 6)
    f = 2.0 * np.sin(np.pi * cutoff / SR)
    return f, [1.0, f * f + f * damping - 2.0, 1.0 - f * damping]


def lowpass(x: np.ndarray, cutoff: Cutoff, q: float = 0.7) -> np.ndarray:
    """Resonant 12 dB/oct low-pass. ``cutoff`` may be a function of time ``t -> Hz``."""
    if callable(cutoff):
        return _swept_lowpass(x, cutoff, q)
    f, a = _svf(cutoff, 1.0 / q, clamp=True)
    return lfilter([0.0, f * f], a, x)


def highpass(x: np.ndarray, cutoff: float) -> np.ndarray:
    """12 dB/oct high-pass (fixed damping 1.4)."""
    _, a = _svf(cutoff, 1.4, clamp=False)
    return lfilter([1.0, -2.0, 1.0], a, x)


def bandpass(x: np.ndarray, cutoff: float, q: float = 1.5) -> np.ndarray:
    """Band-pass centred on ``cutoff``; higher ``q`` = narrower."""
    f, a = _svf(cutoff, 1.0 / q, clamp=False)
    return lfilter([f, -f], a, x)


_SWEEP_BLOCK = 32


def _swept_lowpass(x: np.ndarray, cutoff: Callable[[np.ndarray], np.ndarray], q: float) -> np.ndarray:
    """Low-pass whose cutoff changes over time, updated every 32 samples.

    The SVF state (low, band) is carried exactly from block to block by converting it
    to and from the transposed direct-form state that ``lfilter`` uses.
    """
    damping = 1.0 / q
    out = np.empty_like(x)
    cut = np.broadcast_to(np.asarray(cutoff(time_axis(len(x))), dtype=float), x.shape)
    low = band = 0.0
    for start in range(0, len(x), _SWEEP_BLOCK):
        stop = start + _SWEEP_BLOCK
        f, a = _svf(float(cut[start]), damping, clamp=True)
        zi = [low + f * band, -a[2] * low]
        y, zf = lfilter([0.0, f * f, 0.0], a, x[start:stop], zi=zi)
        out[start:stop] = y
        low = y[-1]
        band = (zf[0] - low) / f
    return out


# ── Plucked string (Karplus-Strong) ─────────────────────────────────────────
def karplus_strong(duration: float, freq: float, *, blend: float = 0.55, feedback: float = 0.9985) -> np.ndarray:
    """Plucked string: a noise burst circulating in a delay line of one period.

    Recurrence: ``y[n] = g·((1-blend)·y[n-L] + blend·y[n-L+1])`` with the first ``L``
    samples being the noise burst. Low notes (long delay) are computed block by block;
    high notes use ``lfilter`` directly, which is faster when the delay is short.
    """
    n = samples(duration)
    period = max(2, round(SR / freq))
    burst = rand(period) * 2.0 - 1.0
    g_old, g_new = feedback * (1.0 - blend), feedback * blend
    if period < 64:
        x = np.zeros(n)
        k = min(period, n)
        x[:k] = burst[:k]
        if period - 1 < n:  # the recurrence would add g_new·y[0] to y[L-1]: cancel it
            x[period - 1] -= g_new * burst[0]
        a = np.zeros(period + 1)
        a[0], a[period - 1], a[period] = 1.0, -g_new, -g_old
        return lfilter([1.0], a, x)
    blocks = -(-n // period)
    y = np.empty((blocks, period))
    y[0] = burst
    for k in range(1, blocks):
        prev = y[k - 1]
        y[k, :-1] = g_old * prev[:-1] + g_new * prev[1:]
        y[k, -1] = g_old * prev[-1] + g_new * y[k, 0]
    return y.ravel()[:n]


# ── Reverb ──────────────────────────────────────────────────────────────────
def _delay(x: np.ndarray, d: int) -> np.ndarray:
    out = np.zeros_like(x)
    if d < len(x):
        out[d:] = x[: len(x) - d]
    return out


def _feedback(x: np.ndarray, d: int, g: float) -> np.ndarray:
    """``w[n] = x[n] + g·w[n-d]``, vectorised by folding the signal into rows of ``d``."""
    n = len(x)
    rows = -(-n // d)
    padded = np.zeros(rows * d)
    padded[:n] = x
    return lfilter([1.0], [1.0, -g], padded.reshape(rows, d), axis=0).ravel()[:n]


_COMBS = (1557, 1617, 1491, 1422, 1277, 1356)
_ALLPASSES = (225, 556, 441)


def reverb(x: np.ndarray, size: float = 1.0) -> np.ndarray:
    """Schroeder reverb (wet signal only): six parallel combs, three series all-passes."""
    acc = np.zeros_like(x)
    for length in _COMBS:
        d = max(1, round(length * size))
        acc += _delay(_feedback(x, d, 0.8), d)
    s = acc / len(_COMBS)
    for d in _ALLPASSES:
        s = -0.5 * s + _delay(_feedback(s, d, 0.5), d)
    return lowpass(s, 6000)
