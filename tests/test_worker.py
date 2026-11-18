import pytest

from retrosynth.runner import SongError
from retrosynth.worker import RenderWorker


@pytest.fixture(scope="module")
def worker():
    w = RenderWorker(timeout=20)
    yield w
    w.close()


def test_renders_in_a_subprocess(worker):
    result = worker.render("s = Song(120, 1)\ns.put(inst.kick(), 0)\nsong = s", "kick")
    assert result.audio.shape == (2, 88_200)


def test_errors_cross_the_process_boundary(worker):
    with pytest.raises(SongError) as e:
        worker.render("x = 1\nraise ValueError('nope')", "bad")
    assert e.value.line == 2 and "nope" in e.value.message


def test_new_render_cancels_a_running_one():
    import threading
    import time

    w = RenderWorker(timeout=60)
    errors = []

    def runaway():
        try:
            w.render("while True:\n    pass", "loop")
        except SongError as e:
            errors.append(e.message)

    try:
        w.start()
        t = threading.Thread(target=runaway)
        t.start()
        time.sleep(1.0)  # let the runaway script start
        started = time.perf_counter()
        assert w.render("song = Song(120, 1)", "next").audio.shape[1] == 88_200
        t.join(10)
        assert time.perf_counter() - started < 30  # did not wait for the 60 s timeout
        assert errors and errors[0].startswith("Cancelled")
    finally:
        w.close()


def test_runaway_script_is_stopped_and_worker_recovers():
    w = RenderWorker(timeout=3)
    try:
        with pytest.raises(SongError, match="longer than"):
            w.render("while True:\n    pass", "loop")
        assert w.render("song = Song(120, 1)", "after").audio.shape[1] == 88_200
    finally:
        w.close()
