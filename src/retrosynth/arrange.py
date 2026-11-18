"""Visual-editor projects → song scripts.

The visual editor describes a song as a small JSON document: tempo, key, number of bars
and four tracks (melody, chords, bass, drums). :func:`to_code` turns it into an ordinary,
readable song script, and *that script is what gets executed*, so "show me the code" is
never out of sync with what you hear. The project itself is embedded in the script on a
marker line, so a saved song can be reopened in the visual editor (:func:`from_code`).

Because the generated code is run, :func:`normalize` validates everything strictly:
instruments must exist, chords must match a strict pattern and free text never reaches
the code except inside a sanitised docstring.
"""

from __future__ import annotations

import json
import math
from typing import Any

from .instruments import inst
from .song import CHORD_SYMBOL_RE

MARKER = "# retrosynth-project: "
STEPS_PER_BEAT = 4
STEPS_PER_BAR = 16  # the grid is in sixteenth notes (4/4 time)

KEYS = ("C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B")
SCALES = {
    "major": (0, 2, 4, 5, 7, 9, 11),
    "minor": (0, 2, 3, 5, 7, 8, 10),
    "phrygian_dominant": (0, 1, 4, 5, 7, 8, 10),
}
CHORD_STYLES = ("pad", "arpeggio", "fast_arpeggio", "stabs", "off")
BASS_STYLES = ("root", "root_fifth", "eighths", "octaves", "off")

# drum row id → instrument, extra options (code), base gain, pan
DRUM_ROWS: dict[str, tuple[str, str, float, float]] = {
    "kick": ("kick", "", 0.55, 0.0),
    "snare": ("snare", "", 0.35, 0.05),
    "hihat": ("hihat", "", 0.08, -0.3),
    "open_hat": ("hihat", ", open=True", 0.07, -0.3),
    "claps": ("claps", "", 0.3, 0.1),
    "tom": ("tom", "", 0.35, -0.15),
    "shaker": ("shaker", "", 0.07, 0.4),
    "tambourine": ("tambourine", "", 0.09, 0.45),
    "doum": ("doum", "", 0.35, 0.0),
    "tek": ("tek", "", 0.2, 0.2),
    "crash": ("cymbal", "", 0.2, 0.4),
}

# base gain of each track at volume 1.0
_GAIN = {"melody": 0.3, "pad": 0.07, "arpeggio": 0.1, "fast_arpeggio": 0.05, "stabs": 0.06, "bass": 0.32}
_MAX_NOTES = 4000


class ProjectError(ValueError):
    """The project document is invalid."""


# ── Validation ──────────────────────────────────────────────────────────────
def _num(value: Any, lo: float, hi: float, default: float) -> float:
    try:
        x = float(value)
    except (TypeError, ValueError):
        return default
    return default if math.isnan(x) else min(hi, max(lo, x))


def _melodic(name: Any, default: str) -> str:
    if name is None:
        return default
    if not isinstance(name, str) or name not in inst or inst[name].kind != "melodic":
        raise ProjectError(f"unknown melodic instrument {name!r}")
    return name


def _choice(value: Any, options, default: str, what: str) -> str:
    if value is None:
        return default
    if value not in options:
        raise ProjectError(f"invalid {what} {value!r}; expected one of {', '.join(options)}")
    return value


def _title(value: Any) -> str:
    text = str(value or "Untitled")
    text = "".join(ch for ch in text if ch.isprintable() and ch not in '"\\')
    return text.strip()[:60] or "Untitled"


def normalize(project: dict) -> dict:
    """Validate a project and fill in defaults. Raises :class:`ProjectError`."""
    if not isinstance(project, dict):
        raise ProjectError("project must be an object")
    bars = int(_num(project.get("bars"), 1, 32, 8))
    total_steps = bars * STEPS_PER_BAR
    tracks = project.get("tracks") or {}
    melody, chords, bass, drums = (tracks.get(k) or {} for k in ("melody", "chords", "bass", "drums"))

    notes = []
    for n in (melody.get("notes") or [])[:_MAX_NOTES]:
        try:
            pitch, start, length = int(n["pitch"]), int(n["start"]), int(n["length"])
        except (KeyError, TypeError, ValueError):
            raise ProjectError(f"invalid melody note {n!r}") from None
        if 24 <= pitch <= 108 and 0 <= start < total_steps and length >= 1:
            notes.append({"pitch": pitch, "start": start, "length": min(length, 64)})
    notes.sort(key=lambda n: (n["start"], n["pitch"]))

    symbols = [str(c or "") for c in (chords.get("chords") or [])][:bars]
    for c in symbols:
        if c and not CHORD_SYMBOL_RE.match(c):
            raise ProjectError(f"invalid chord {c!r}")
    if symbols:
        symbols += [symbols[i % len(symbols)] for i in range(len(symbols), bars)]  # repeat to fill
    else:
        symbols = [""] * bars

    rows = {}
    for row, pattern in (drums.get("rows") or {}).items():
        if row not in DRUM_ROWS:
            raise ProjectError(f"unknown drum row {row!r}")
        cells = "".join(ch if ch in "xX" else "." for ch in str(pattern))[:STEPS_PER_BAR]
        rows[row] = cells.ljust(STEPS_PER_BAR, ".")

    return {
        "version": 1,
        "title": _title(project.get("title")),
        "bpm": int(_num(project.get("bpm"), 40, 240, 110)),
        "key": _choice(project.get("key"), KEYS, "C", "key"),
        "scale": _choice(project.get("scale"), SCALES, "major", "scale"),
        "bars": bars,
        "reverb": round(_num(project.get("reverb"), 0.3, 2.5, 1.2), 2),
        "loop": bool(project.get("loop", True)),
        "tracks": {
            "melody": {
                "instrument": _melodic(melody.get("instrument"), "flute"),
                "volume": round(_num(melody.get("volume"), 0, 1.5, 1), 2),
                "pan": round(_num(melody.get("pan"), -1, 1, 0.1), 2),
                "reverb": round(_num(melody.get("reverb"), 0, 1, 0.4), 2),
                "notes": notes,
            },
            "chords": {
                "instrument": _melodic(chords.get("instrument"), "strings"),
                "style": _choice(chords.get("style"), CHORD_STYLES, "pad", "chord style"),
                "volume": round(_num(chords.get("volume"), 0, 1.5, 1), 2),
                "chords": symbols,
            },
            "bass": {
                "instrument": _melodic(bass.get("instrument"), "bass"),
                "style": _choice(bass.get("style"), BASS_STYLES, "root_fifth", "bass style"),
                "volume": round(_num(bass.get("volume"), 0, 1.5, 1), 2),
            },
            "drums": {
                "volume": round(_num(drums.get("volume"), 0, 1.5, 1), 2),
                "rows": rows,
            },
        },
    }


# ── Code generation ─────────────────────────────────────────────────────────
def _g(x: float) -> str:
    """Compact number formatting for generated code."""
    return f"{round(x, 3):g}"


def _note_name(pitch: int) -> str:
    names = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
    return f"{names[pitch % 12]}{pitch // 12 - 1}"


def to_code(project: dict) -> str:
    """Generate the song script for a project (validated first)."""
    p = normalize(project)
    t = p["tracks"]
    mel, chd, bas, drm = t["melody"], t["chords"], t["bass"], t["drums"]
    has_chords = any(p_ for p_ in chd["chords"])
    out = [
        f'"""{p["title"]} — {p["key"]} {p["scale"].replace("_", " ")}, {p["bpm"]} bpm. Made with the visual editor."""',
        MARKER + json.dumps(p, separators=(",", ":"), ensure_ascii=False),
        "",
        "from retrosynth import *",
        "",
        f"s = Song(bpm={p['bpm']}, bars={p['bars']}{'' if p['loop'] else ', loop=False'})",
        f"chords = {chd['chords']!r}  # one chord per bar ('' = silence)",
    ]

    style = chd["style"]
    if has_chords and style != "off" and chd["volume"] > 0:
        gain = _g(_GAIN[style] * chd["volume"])
        i = repr(chd["instrument"])
        out += ["", f"# Chords: {chd['instrument']}, {style.replace('_', ' ')}",
                "for bar, name in enumerate(chords):",
                "    if not name:",
                "        continue",
                "    c = chord_symbol(name)"]
        if style == "pad":
            out.append(f"    pad(s, bar, c, 4, instrument={i}, gain={gain}, wet=0.45)")
        elif style == "arpeggio":
            out.append(f"    arpeggio(s, bar, c, [0, 1, 2, 3, 2, 1, 0, 1], step=0.5, instrument={i}, gain={gain}, pan=-0.25)")
        elif style == "fast_arpeggio":
            out.append(f"    arpeggio(s, bar, c, [0, 1, 2, 3] * 4, step=0.25, instrument={i}, gain={gain}, pan=-0.3, wet=0.2)")
        else:  # stabs: short rhythmic chords
            out += ["    for beat in (0, 1.5, 3):",
                    "        for k, n in enumerate(c):",
                    f"            s.put(inst.{chd['instrument']}(midi(n + 12), s.beat * 0.6), s.at(bar, beat), "
                    f"gain={gain}, pan=(k - 1) * 0.35, wet=0.25)"]

    if has_chords and bas["style"] != "off" and bas["volume"] > 0:
        gain = _g(_GAIN["bass"] * bas["volume"])
        b = f"inst.{bas['instrument']}"
        out += ["", f"# Bass: {bas['instrument']}, {bas['style'].replace('_', ' ')}",
                "for bar, name in enumerate(chords):",
                "    if not name:",
                "        continue",
                "    root = chord_symbol(name)[0] - 12  # one octave below the chords"]
        if bas["style"] == "root":
            out.append(f"    s.put({b}(midi(root), s.beat * 3.8), s.at(bar), gain={gain}, wet=0.1)")
        elif bas["style"] == "root_fifth":
            out += [f"    s.put({b}(midi(root), s.beat * 1.8), s.at(bar, 0), gain={gain}, wet=0.1)",
                    f"    s.put({b}(midi(root + 7), s.beat * 1.8), s.at(bar, 2), gain={_g(float(gain) * 0.85)}, wet=0.1)"]
        elif bas["style"] == "eighths":
            out += ["    for k in range(8):",
                    f"        s.put({b}(midi(root), s.beat * 0.45), s.at(bar, k * 0.5), gain={gain}, wet=0.05)"]
        else:  # octaves
            out += ["    for k in range(8):",
                    f"        s.put({b}(midi(root + 12 * (k % 2)), s.beat * 0.45), s.at(bar, k * 0.5), gain={gain}, wet=0.05)"]

    rows = {r: pat for r, pat in drm["rows"].items() if "x" in pat.lower()}
    if rows and drm["volume"] > 0:
        out += ["", "# Drums: the same 16-step pattern every bar (x = hit, X = accent, . = silence)",
                "for bar in range(s.bars):"]
        for row, pattern in rows.items():
            name, options, base, pan = DRUM_ROWS[row]
            out.append(f"    drum_pattern(s, bar, {pattern!r}, {name!r}, gain={_g(base * drm['volume'])}, "
                       f"pan={_g(pan)}, wet=0.08{options})")

    if mel["notes"] and mel["volume"] > 0:
        out += ["", f"# Melody: {mel['instrument']}. Each note is (pitch, start, length), measured in",
                "# sixteenth-note steps: 4 steps = 1 beat, 16 steps = 1 bar.",
                "melody = ["]
        row = []
        for n in mel["notes"]:
            row.append(f"({_note_name(n['pitch'])!r}, {n['start']}, {n['length']})")
            if len(row) == 6:
                out.append("    " + ", ".join(row) + ",")
                row = []
        if row:
            out.append("    " + ", ".join(row) + ",")
        out += ["]",
                "for pitch, start, length in melody:",
                f"    sound = inst.{mel['instrument']}(midi(note(pitch)), length / 4 * s.beat * 0.95)",
                f"    s.put(sound, start / 4 * s.beat, gain={_g(_GAIN['melody'] * mel['volume'])}, "
                f"pan={_g(mel['pan'])}, wet={_g(mel['reverb'])})"]

    out += ["", f"song = s.render(reverb_size={_g(p['reverb'])}, loudness=0.13)", ""]
    return "\n".join(out)


def from_code(code: str) -> dict | None:
    """The project embedded in a script generated by :func:`to_code`, if any."""
    for line in code.splitlines()[:5]:
        if line.startswith(MARKER):
            try:
                return normalize(json.loads(line[len(MARKER):]))
            except (ValueError, ProjectError):
                return None
    return None


def describe_options() -> dict:
    """Everything the visual editor needs to build its menus."""
    return {
        "keys": list(KEYS),
        "scales": {k: list(v) for k, v in SCALES.items()},
        "chord_styles": list(CHORD_STYLES),
        "bass_styles": list(BASS_STYLES),
        "drum_rows": [{"id": r, "instrument": v[0]} for r, v in DRUM_ROWS.items()],
        "steps_per_bar": STEPS_PER_BAR,
    }
