"""Quick mix diagnostics shown in the studio: loudness, peak, clipping and loop seam."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from .dsp import SR


@dataclass(frozen=True)
class Analysis:
    duration: float  # seconds
    samples: int
    rms_db: float  # overall loudness, dBFS
    peak_db: float
    clipped: int  # samples above 0.98 in either channel
    seam_ratio: float  # jump at the loop point relative to the average sample-to-sample change

    @property
    def seam_clean(self) -> bool:
        return self.seam_ratio < 4

    def to_dict(self) -> dict:
        return asdict(self) | {"seam_clean": self.seam_clean}


def _db(x: float) -> float:
    return float(20 * np.log10(max(x, 1e-9)))


def analyze(audio: np.ndarray) -> Analysis:
    """Analyse a ``(2, n)`` stereo track."""
    left = audio[0].astype(np.float64)
    n = audio.shape[1]
    peak_per_sample = np.max(np.abs(audio), axis=0)
    # how much the waveform normally moves between neighbouring samples…
    typical_step = float(np.mean(np.abs(np.diff(left)))) if n > 1 else 0.0
    # …versus the jump from the last sample back to the first one when looping
    seam = float(np.max(np.abs(audio[:, 0] - audio[:, -1])))
    return Analysis(
        duration=n / SR,
        samples=n,
        rms_db=_db(float(np.sqrt(np.mean(audio.astype(np.float64) ** 2)))),
        peak_db=_db(float(peak_per_sample.max(initial=0.0))),
        clipped=int(np.count_nonzero(peak_per_sample > 0.98)),
        seam_ratio=seam / (typical_step or 1e-9),
    )
