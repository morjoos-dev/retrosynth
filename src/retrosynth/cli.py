"""Command line interface.

    retrosynth studio                 open the web studio
    retrosynth render my_song.py      render a song file to output/
    retrosynth render crystal_cave    render a bundled example
    retrosynth list                   list examples and instruments
"""

from __future__ import annotations

import argparse
import sys
import threading
import webbrowser
from pathlib import Path

from . import __version__


def _find_song(target: str) -> Path:
    path = Path(target)
    if path.suffix == ".py" and path.is_file():
        return path
    from .server import EXAMPLES_DIR

    example = EXAMPLES_DIR / f"{target}.py"
    if example.is_file():
        return example
    raise SystemExit(f"error: {target!r} is neither a .py file nor a bundled example (see `retrosynth list`)")


def cmd_render(args: argparse.Namespace) -> int:
    from .analysis import analyze
    from .audio_io import export
    from .runner import SongError, run_file

    formats = [f.strip() for f in args.formats.split(",") if f.strip()]
    status = 0
    for target in args.songs:
        path = _find_song(target)
        try:
            result = run_file(path)
        except SongError as e:
            where = f"{path}:{e.line}" if e.line else str(path)
            print(f"{where}: {e.message}", file=sys.stderr)
            status = 1
            continue
        files = export(result.audio, path.stem, args.out, formats)
        a = analyze(result.audio)
        print(f"{path.stem}: {a.duration:.1f} s of audio in {result.seconds:.1f} s | "
              f"{a.rms_db:.1f} dB RMS | peak {a.peak_db:.1f} dB -> {', '.join(str(f) for f in files)}")
        if files.warning:
            print(f"  warning: {files.warning}", file=sys.stderr)
    return status


def cmd_list(_: argparse.Namespace) -> int:
    from .instruments import inst
    from .runner import describe
    from .server import EXAMPLES_DIR

    print("Examples:")
    for path in sorted(EXAMPLES_DIR.glob("*.py")):
        print(f"  {path.stem:<18} {describe(path.read_text(encoding='utf-8'))}")
    for kind in ("melodic", "drum", "fx"):
        print(f"\n{kind.capitalize()} instruments:")
        for i in inst:
            if i.kind == kind:
                print(f"  {i.name:<18} {i.description}")
    return 0


def cmd_studio(args: argparse.Namespace) -> int:
    import uvicorn

    from .server import create_app

    app = create_app(args.songs, args.out)
    url = f"http://{'localhost' if args.host in ('127.0.0.1', 'localhost', '0.0.0.0') else args.host}:{args.port}"
    print(f"retrosynth studio on {url}  (Ctrl+C to stop)")
    print(f"  your songs: {Path(args.songs).resolve()}\n  exports:    {Path(args.out).resolve()}")
    if not args.no_browser:
        threading.Timer(1.0, webbrowser.open, args=(url,)).start()
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="retrosynth", description="Synthesize 16-bit style game music from Python.")
    parser.add_argument("--version", action="version", version=f"retrosynth {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("studio", help="open the web studio")
    p.add_argument("--host", default="127.0.0.1", help="interface to bind (default: 127.0.0.1)")
    p.add_argument("--port", type=int, default=5177)
    p.add_argument("--songs", default="songs", help="folder for your songs (default: ./songs)")
    p.add_argument("--out", default="output", help="folder for exported audio (default: ./output)")
    p.add_argument("--no-browser", action="store_true", help="do not open a browser tab")
    p.set_defaults(func=cmd_studio)

    p = sub.add_parser("render", help="render song files or bundled examples to audio")
    p.add_argument("songs", nargs="+", metavar="SONG", help="path to a .py song, or the name of an example")
    p.add_argument("-o", "--out", default="output", help="output folder (default: ./output)")
    p.add_argument("-f", "--formats", default="wav,ogg,mp3", help="comma-separated: wav, ogg, mp3 (default: all)")
    p.set_defaults(func=cmd_render)

    p = sub.add_parser("list", help="list bundled examples and instruments")
    p.set_defaults(func=cmd_list)
    return parser


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):  # never crash on a console that can't print some character
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
