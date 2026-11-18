"""The vectorised DSP must match straightforward per-sample reference implementations."""

import numpy as np
import pytest

from retrosynth import dsp


def ref_svf(x, cutoff, damping, out="low", clamp=True):
    """Chamberlin state-variable filter, one sample at a time."""
    y = np.zeros_like(x)
    low = band = 0.0
    for i, v in enumerate(x):
        c = cutoff(i / dsp.SR) if callable(cutoff) else cutoff
        f = 2 * np.sin(np.pi * (min(c, dsp.SR / 6) if clamp else c) / dsp.SR)
        low += f * band
        high = v - low - damping * band
        band += f * high
        y[i] = {"low": low, "high": high, "band": band}[out]
    return y


def ref_karplus(n, burst, blend, feedback):
    ring, y, idx = burst.copy(), np.zeros(n), 0
    for i in range(n):
        a, c = ring[idx], ring[(idx + 1) % len(ring)]
        ring[idx] = (a * (1 - blend) + c * blend) * feedback
        y[i] = a
        idx = (idx + 1) % len(ring)
    return y


def ref_reverb_core(x, size):
    """Schroeder combs + all-passes, before the final low-pass."""
    combs = [{"d": round(n * size), "i": 0} for n in (1557, 1617, 1491, 1422, 1277, 1356)]
    for c in combs:
        c["buf"] = np.zeros(c["d"])
    aps = [{"d": n, "buf": np.zeros(n), "i": 0} for n in (225, 556, 441)]
    out = np.zeros_like(x)
    for i, v in enumerate(x):
        s = 0.0
        for c in combs:
            y = c["buf"][c["i"]]
            c["buf"][c["i"]] = v + y * 0.8
            c["i"] = (c["i"] + 1) % c["d"]
            s += y
        s /= 6
        for a in aps:
            y = a["buf"][a["i"]]
            nv = -s * 0.5 + y
            a["buf"][a["i"]] = s + y * 0.5
            a["i"] = (a["i"] + 1) % a["d"]
            s = nv
        out[i] = s
    return out


@pytest.fixture
def signal():
    rng = np.random.default_rng(0)
    return rng.uniform(-1, 1, 3000)


@pytest.mark.parametrize("cutoff,q", [(200, 0.7), (1800, 1.2), (12_000, 0.7)])
def test_lowpass_matches_reference(signal, cutoff, q):
    np.testing.assert_allclose(dsp.lowpass(signal, cutoff, q), ref_svf(signal, cutoff, 1 / q), atol=1e-9)


def test_highpass_and_bandpass_match_reference(signal):
    np.testing.assert_allclose(dsp.highpass(signal, 5000), ref_svf(signal, 5000, 1.4, "high", clamp=False), atol=1e-9)
    np.testing.assert_allclose(dsp.bandpass(signal, 1100, 2), ref_svf(signal, 1100, 0.5, "band", clamp=False), atol=1e-9)


def test_swept_lowpass_tracks_reference(signal):
    """The cutoff is updated every 32 samples instead of every sample: tiny difference only."""
    sweep = lambda t: 300 + 2200 * np.exp(-18 * t)  # noqa: E731
    fast, slow = dsp.lowpass(signal, sweep, 1.2), ref_svf(signal, sweep, 1 / 1.2)
    assert np.max(np.abs(fast - slow)) < 0.02 * np.max(np.abs(slow))


@pytest.mark.parametrize("freq,blend,feedback", [(1760, 0.55, 0.9985), (440, 0.55, 0.9985), (98, 0.3, 0.995)])
def test_karplus_strong_matches_reference(freq, blend, feedback):
    dsp.seed(3)
    period = max(2, round(dsp.SR / freq))
    burst = np.random.default_rng(3).random(period) * 2 - 1
    got = dsp.karplus_strong(0.2, freq, blend=blend, feedback=feedback)
    np.testing.assert_allclose(got, ref_karplus(len(got), burst, blend, feedback), atol=1e-9)


def test_reverb_matches_reference():
    x = np.zeros(6000)
    x[[0, 1500, 4000]] = [1.0, -0.5, 0.25]
    expected = dsp.lowpass(ref_reverb_core(x, 1.1), 6000)
    np.testing.assert_allclose(dsp.reverb(x, 1.1), expected, atol=1e-9)


def test_oscillator_shapes():
    for wave in ("sine", "tri", "saw", "square"):
        x = dsp.osc(0.1, 440, wave)
        assert len(x) == dsp.samples(0.1)
        assert x.min() >= -1.0 - 1e-12 and x.max() <= 1.0 + 1e-12
    square = dsp.osc(0.1, 441, "square", duty=0.25)
    assert abs(np.mean(square > 0) - 0.25) < 0.02  # duty cycle respected


def test_oscillator_pitch():
    x = dsp.osc(1.0, 440, "sine")
    spectrum = np.abs(np.fft.rfft(x))
    assert abs(np.argmax(spectrum) * dsp.SR / len(x) - 440) < 1.5


def test_adsr_shape():
    env = dsp.adsr(np.ones(dsp.samples(1.0)), attack=0.1, decay=0.1, sustain=0.5, release=0.2, hold=0.5)
    at = lambda t: env[int(t * dsp.SR)]  # noqa: E731
    assert at(0.05) == pytest.approx(0.5, abs=1e-3)  # halfway up the attack
    assert at(0.1) == pytest.approx(1.0, abs=1e-3)  # peak
    assert at(0.3) == pytest.approx(0.5)  # sustain
    assert at(0.6) == pytest.approx(0.25, abs=1e-3)  # halfway through the release
    assert at(0.9) == 0.0


def test_seed_makes_output_deterministic():
    dsp.seed(42)
    a = dsp.noise(0.1)
    dsp.seed(42)
    np.testing.assert_array_equal(a, dsp.noise(0.1))


def test_midi_conversion():
    assert dsp.midi(69) == 440
    assert dsp.midi(81) == pytest.approx(880)
