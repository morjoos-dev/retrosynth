"""Starting points for the visual editor: one ready-to-play project per musical style."""

from __future__ import annotations

from .arrange import STEPS_PER_BEAT, normalize
from .song import mel


def _melody(text: str) -> list[dict]:
    """Melody notation (``"E5:1 G5:0.5 r:1"``) → visual-editor notes in sixteenth steps."""
    notes, step = [], 0
    for n in mel(text):
        length = round(n.beats * STEPS_PER_BEAT)
        if n.pitch is not None:
            notes.append({"pitch": n.pitch, "start": step, "length": length})
        step += length
    return notes


def _drums(**rows: str) -> dict:
    return {"rows": {k: v.replace(" ", "") for k, v in rows.items()}}


def _project(title, bpm, key, scale, chords, *, melody, melody_inst, chord_inst, chord_style, bass_inst, bass_style,
             drums, reverb=1.2):
    return normalize({
        "title": title, "bpm": bpm, "key": key, "scale": scale, "bars": len(chords.split()), "reverb": reverb,
        "tracks": {
            "melody": {"instrument": melody_inst, "notes": _melody(melody) if melody else []},
            "chords": {"instrument": chord_inst, "style": chord_style, "chords": chords.split()},
            "bass": {"instrument": bass_inst, "style": bass_style},
            "drums": drums,
        },
    })


PRESETS: list[dict] = [
    {
        "id": "adventure", "icon": "⚔️", "name": {"en": "Adventure", "es": "Aventura"},
        "description": {"en": "Bright and heroic, ready to explore", "es": "Luminosa y heroica, para explorar"},
        "project": _project(
            "Adventure", 120, "C", "major", "C Am F G C Am F G",
            melody="E5:1 G5:1 C6:2 C6:1 B5:1 A5:2 A5:1 F5:1 C6:1.5 A5:0.5 G5:4 "
                   "E5:1 G5:1 C6:2 D6:1 C6:1 A5:2 F5:1 A5:1 G5:1 F5:1 E5:2 D5:2",
            melody_inst="lead", chord_inst="strings", chord_style="pad", bass_inst="bass", bass_style="root_fifth",
            drums=_drums(kick="x... .... x.x. ....", snare=".... x... .... x...", hihat="x.x. x.x. x.x. x.x.")),
    },
    {
        "id": "village", "icon": "🏡", "name": {"en": "Village", "es": "Pueblo"},
        "description": {"en": "Calm and pastoral: harp and flute", "es": "Tranquila y bucólica: arpa y flauta"},
        "project": _project(
            "Village", 96, "F", "major", "F Dm Bb C F Dm Gm C",
            melody="A5:1.5 G5:0.5 F5:1 C5:1 D5:1.5 E5:0.5 F5:1 A5:1 Bb5:1.5 A5:0.5 G5:1 F5:1 G5:2 E5:1 C5:1 "
                   "A5:1.5 G5:0.5 F5:1 A5:1 D6:1.5 C6:0.5 A5:1 F5:1 G5:1 Bb5:1 A5:1 G5:1 C5:1 E5:1 G5:2",
            melody_inst="flute", chord_inst="harp", chord_style="arpeggio", bass_inst="bass", bass_style="root_fifth",
            drums=_drums(kick="x... .... .... ....", shaker="..x. ..x. ..x. ..x.")),
    },
    {
        "id": "cave", "icon": "💎", "name": {"en": "Cave", "es": "Cueva"},
        "description": {"en": "Mysterious and slow, lots of echo", "es": "Misteriosa y lenta, con mucho eco"},
        "project": _project(
            "Cave", 72, "A", "minor", "Am F C G Am F Dm E",
            melody="E6:2 C6:1 A5:1 F5:1 A5:1 C6:1 E6:1 G6:2 E6:1 C6:1 D6:3 B5:1 "
                   "C6:1 E6:1 A6:2 G6:1 F6:1 E6:1 C6:1 D6:2 F6:1 A5:1 G#5:2 B5:1 E6:1",
            melody_inst="music_box", chord_inst="choir", chord_style="pad", bass_inst="cello", bass_style="root",
            drums=_drums(), reverb=1.7),
    },
    {
        "id": "battle", "icon": "🔥", "name": {"en": "Battle", "es": "Combate"},
        "description": {"en": "Fast and intense, guitars and drums", "es": "Rápida e intensa, guitarras y batería"},
        "project": _project(
            "Battle", 160, "E", "minor", "Em Em C D Em Em C B",
            melody="E5:0.5 G5:0.5 B5:1 A5:0.5 G5:0.5 B5:1 E6:1.5 D6:0.5 B5:2 "
                   "C6:0.5 B5:0.5 A5:0.5 G5:0.5 E5:1 G5:1 F#5:1.5 A5:0.5 D6:2 "
                   "E5:0.5 G5:0.5 B5:1 A5:0.5 G5:0.5 B5:1 G6:1.5 F#6:0.5 E6:2 "
                   "E6:0.5 D6:0.5 C6:0.5 B5:0.5 A5:1 G5:1 F#5:1 A5:1 D#6:2",
            melody_inst="lead", chord_inst="brass", chord_style="stabs", bass_inst="rock_bass", bass_style="eighths",
            drums=_drums(kick="x.x. ..x. x.x. ..x.", snare=".... x... .... x...", hihat="x.x. x.x. x.x. x.x."),
            reverb=0.9),
    },
    {
        "id": "desert", "icon": "🏜️", "name": {"en": "Desert", "es": "Desierto"},
        "description": {"en": "Exotic scale, oud and hand drums", "es": "Escala exótica, laúd y percusión de mano"},
        "project": _project(
            "Desert", 104, "E", "phrygian_dominant", "E E E E Am Am F E",
            melody="r:2 B5:1 C6:1 B5:1.5 A5:0.5 G#5:1 F5:1 E5:2 F5:0.5 G#5:0.5 A5:1 B5:4 "
                   "C6:1.5 B5:0.5 A5:1 C6:1 E6:2 D6:1 C6:1 C6:1 A5:1 G#5:1 F5:1 E5:3",
            melody_inst="ney", chord_inst="oud", chord_style="arpeggio", bass_inst="cello", bass_style="root",
            drums=_drums(doum="x... .... x... ....", tek="..x. x... ..x. x.x.", tambourine=".... ..x. .... ..x."),
            reverb=1.3),
    },
    {
        "id": "chiptune", "icon": "👾", "name": {"en": "Chiptune", "es": "Chiptune"},
        "description": {"en": "8-bit console sound, fast arpeggios", "es": "Sonido de consola de 8 bits, arpegios rápidos"},
        "project": _project(
            "Chiptune", 150, "G", "major", "G Em C D G Em C D",
            melody="B5:0.5 D6:0.5 G6:1 F#6:0.5 E6:0.5 D6:1 E6:0.5 G6:0.5 B6:1 A6:0.5 G6:0.5 E6:1 "
                   "C6:0.5 E6:0.5 G6:1 E6:0.5 D6:0.5 C6:1 D6:1.5 A5:0.5 F#5:1 A5:1 "
                   "B5:0.5 D6:0.5 G6:1 A6:0.5 B6:0.5 G6:1 E6:1 B5:1 E6:0.5 F#6:0.5 G6:1 "
                   "A6:1 G6:0.5 E6:0.5 C6:1 E6:1 D6:1 F#6:1 A6:1 F#6:1",
            melody_inst="lead", chord_inst="lead", chord_style="fast_arpeggio", bass_inst="bass", bass_style="octaves",
            drums=_drums(kick="x... x... x... x.x.", snare=".... x... .... x...", hihat="x.x. x.x. x.x. x.xx"),
            reverb=0.8),
    },
    {
        "id": "blank", "icon": "✨", "name": {"en": "Blank", "es": "En blanco"},
        "description": {"en": "Just chords: draw your own melody", "es": "Solo acordes: dibuja tu propia melodía"},
        "project": _project(
            "My song", 100, "C", "major", "C Am F G C Am F G", melody="",
            melody_inst="flute", chord_inst="strings", chord_style="pad", bass_inst="bass", bass_style="root",
            drums=_drums()),
    },
]
