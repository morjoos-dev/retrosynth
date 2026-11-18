"""Writing audio: 16-bit WAV (standard library only) and OGG / MP3 through ffmpeg."""

from __future__ import annotations

import io
import os
import shutil
import subprocess
import wave
from pathlib import Path

import numpy as np

from .dsp import SR

FORMATS = ("wav", "ogg", "mp3")
_FFMPEG_ARGS = {
    "ogg": ["-c:a", "libvorbis", "-q:a", "5"],
    "mp3": ["-c:a", "libmp3lame", "-b:a", "192k"],
}


def to_wav_bytes(audio: np.ndarray) -> bytes:
    """Encode a ``(channels, n)`` float array in ``[-1, 1]`` as a 16-bit PCM WAV file."""
    audio = np.atleast_2d(audio)
    pcm = (np.clip(audio, -1.0, 1.0) * 32767).round().astype("<i2")
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(audio.shape[0])
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.T.tobytes())  # interleave channels
    return buf.getvalue()


def write_wav(path: str | Path, audio: np.ndarray) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(to_wav_bytes(audio))
    return path


def find_ffmpeg() -> str | None:
    """ffmpeg from the ``FFMPEG`` environment variable, or from the PATH."""
    return os.environ.get("FFMPEG") or shutil.which("ffmpeg")


class ExportResult(list):
    """List of written files, plus a ``warning`` if some formats were skipped."""

    warning: str | None = None


def export(audio: np.ndarray, name: str, out_dir: str | Path, formats=FORMATS) -> ExportResult:
    """Write ``<out_dir>/<name>.<fmt>`` for each format. OGG and MP3 need ffmpeg."""
    out_dir = Path(out_dir)
    unknown = set(formats) - set(FORMATS)
    if unknown:
        raise ValueError(f"unknown format(s): {', '.join(sorted(unknown))}")
    wav = write_wav(out_dir / f"{name}.wav", audio)
    result = ExportResult()
    if "wav" in formats:
        result.append(wav)
    compressed = [f for f in formats if f != "wav"]
    ffmpeg = find_ffmpeg() if compressed else None
    if compressed and not ffmpeg:
        result.warning = "ffmpeg not found: only the WAV file was written"
        if "wav" not in formats:
            result.append(wav)
    for fmt in compressed if ffmpeg else []:
        target = out_dir / f"{name}.{fmt}"
        subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", str(wav), *_FFMPEG_ARGS[fmt], str(target)],
                       check=True, capture_output=True)
        result.append(target)
    if "wav" not in formats and len(result) == len(compressed):
        wav.unlink()  # only an intermediate file; keep it as a fallback if ffmpeg was missing
    return result
