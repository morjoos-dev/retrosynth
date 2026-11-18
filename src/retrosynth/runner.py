"""Running song scripts.

A song script is ordinary Python. It starts with ``from retrosynth import *`` (optional
when run by the studio, which pre-imports it), builds a :class:`~retrosynth.song.Song`
and assigns the result to a variable named ``song``::

    from retrosynth import *

    s = Song(bpm=100, bars=8)
    s.melody("flute", 0, "C5:1 E5:1 G5:2")
    song = s.render(reverb_size=1.2, loudness=0.12)   # or simply: song = s

The first line of the module docstring (or of the leading comments) is used as the
song's description in the studio.
"""

from __future__ import annotations

import ast
import contextlib
import io
import time
import traceback
import zlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import dsp
from .song import Song

FILENAME = "<song>"


class SongError(Exception):
    """A song script failed; ``line`` points at the offending line when known."""

    def __init__(self, message: str, line: int | None = None):
        super().__init__(message)
        self.message = message
        self.line = line


@dataclass
class RenderResult:
    audio: np.ndarray  # (2, n) float32
    seconds: float  # time spent rendering
    log: str = ""  # whatever the script printed


def seed_for(name: str) -> int:
    """Stable per-song random seed, so a song always sounds the same."""
    return zlib.crc32(name.encode("utf-8"))


def _error_line(exc: BaseException) -> int | None:
    if isinstance(exc, SyntaxError) and exc.filename == FILENAME:
        return exc.lineno
    line = None
    for frame in traceback.extract_tb(exc.__traceback__):
        if frame.filename == FILENAME:
            line = frame.lineno
    return line


def run_code(code: str, name: str = "song") -> RenderResult:
    """Execute a song script and return the rendered stereo audio."""
    dsp.seed(seed_for(name))
    namespace: dict = {"__name__": "__song__"}
    exec("from retrosynth import *", namespace)
    started = time.perf_counter()
    printed = io.StringIO()
    try:
        with contextlib.redirect_stdout(printed):
            exec(compile(code, FILENAME, "exec"), namespace)
            result = namespace.get("song")
            if isinstance(result, Song):
                result = result.render()
    except SyntaxError as e:
        raise SongError(f"SyntaxError: {e.msg}", _error_line(e)) from None
    except Exception as e:
        raise SongError(f"{type(e).__name__}: {e}", _error_line(e)) from None
    if not (isinstance(result, np.ndarray) and result.ndim == 2 and result.shape[0] == 2):
        raise SongError("The script must end by assigning the track to `song`, e.g. `song = s.render()` or `song = s`")
    if not np.all(np.isfinite(result)):
        raise SongError("The rendered audio contains NaN or infinite values")
    return RenderResult(result.astype(np.float32, copy=False), time.perf_counter() - started, printed.getvalue())


def run_file(path: str | Path) -> RenderResult:
    path = Path(path)
    return run_code(path.read_text(encoding="utf-8"), path.stem)


def describe(code: str) -> str:
    """First line of the module docstring, or of the leading ``#`` comments."""
    try:
        doc = ast.get_docstring(ast.parse(code))
    except SyntaxError:
        doc = None
    if doc:
        return doc.strip().splitlines()[0]
    lines = []
    for line in code.splitlines():
        if not line.startswith("#"):
            break
        lines.append(line.lstrip("# ").strip())
    return " ".join(lines).strip()
