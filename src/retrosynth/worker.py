"""Render song scripts in a separate process.

The studio executes code typed in the browser. Running it in a child process keeps the
web server responsive, and lets us stop a script that hangs (``while True: ...``) or
takes too long: the process is killed and a fresh one is started for the next render.
"""

from __future__ import annotations

import multiprocessing as mp
import threading

from .runner import RenderResult, SongError


def _serve(conn) -> None:  # runs in the child process
    from .runner import run_code  # imported here so numpy/scipy load once, at start-up

    while True:
        try:
            code, name = conn.recv()
        except (EOFError, OSError):
            return
        try:
            r = run_code(code, name)
            conn.send(("ok", (r.audio, r.seconds, r.log)))
        except SongError as e:
            conn.send(("error", (e.message, e.line)))
        except BaseException as e:  # noqa: BLE001 — report anything, never die silently
            conn.send(("error", (f"{type(e).__name__}: {e}", None)))


class RenderWorker:
    """One warm worker process; renders are serialised and time-limited."""

    def __init__(self, timeout: float = 120.0):
        self.timeout = timeout
        self._lock = threading.Lock()
        self._proc = None
        self._conn = None
        self._cancelled = False

    def _ensure(self) -> None:
        if self._proc is not None and self._proc.is_alive():
            return
        ctx = mp.get_context("spawn")
        self._conn, child = ctx.Pipe()
        self._proc = ctx.Process(target=_serve, args=(child,), daemon=True, name="retrosynth-render")
        self._proc.start()
        child.close()

    def _kill(self) -> None:
        if self._proc is not None:
            self._proc.kill()
            self._proc.join(5)
        if self._conn is not None:
            self._conn.close()
        self._proc = self._conn = None

    def start(self) -> None:
        """Start the process ahead of time so the first render is fast."""
        with self._lock:
            self._ensure()

    def render(self, code: str, name: str) -> RenderResult:
        """Render in the worker. A new request cancels the one in progress (latest edit wins)."""
        busy = self._proc
        if self._lock.locked() and busy is not None:
            self._cancelled = True
            busy.kill()  # the waiting call sees the pipe close and reports the cancellation
        with self._lock:
            self._cancelled = False
            self._ensure()
            self._conn.send((code, name))
            if not self._conn.poll(self.timeout):
                self._kill()
                raise SongError(f"Rendering took longer than {self.timeout:.0f} s and was stopped")
            try:
                status, payload = self._conn.recv()
            except (EOFError, OSError):
                cancelled = self._cancelled
                self._kill()
                raise SongError("Cancelled: a newer render was requested" if cancelled
                                else "The render process crashed (out of memory?)") from None
        if status == "ok":
            return RenderResult(*payload)
        raise SongError(*payload)

    def close(self) -> None:
        with self._lock:
            self._kill()
