"""Pixel Runner — G major, 150 bpm: chiptune with square leads, fast arpeggios and a triangle bass."""

from retrosynth import *

s = Song(bpm=150, bars=8)
chart = progression("G:4 Em:4 C:4 D:4  G:4 Em:4 C:4 D:4")

for bar, ch in enumerate(chart):
    c = ch.notes
    # sixteenth-note arpeggio, the classic way to fake chords on a single sound channel
    arpeggio(s, bar, c, [0, 1, 2, 3] * 4, step=0.25, instrument="lead", gain=0.04, pan=-0.35, wet=0.15)
    s.melody("bass", bar, [Note(c[0] - 12, 0.5), Note(c[0], 0.5)] * 4, gain=0.3, wet=0.05, legato=0.8)
    drum_pattern(s, bar, "x...x...x...x.x.", "kick", gain=0.5, wet=0.03)
    drum_pattern(s, bar, "....x.......x...", "snare", gain=0.3, wet=0.1)
    drum_pattern(s, bar, "x.x.x.x.x.x.x.xx", "hihat", gain=0.06, pan=0.3, wet=0.05)

melody = mel("""
    B5:0.5 D6:0.5 G6:1 F#6:0.5 E6:0.5 D6:1    E6:0.5 G6:0.5 B6:1 A6:0.5 G6:0.5 E6:1
    C6:0.5 E6:0.5 G6:1 E6:0.5 D6:0.5 C6:1     D6:1.5 A5:0.5 F#5:1 A5:1
    B5:0.5 D6:0.5 G6:1 A6:0.5 B6:0.5 G6:1     E6:1 B5:1 E6:0.5 F#6:0.5 G6:1
    A6:1 G6:0.5 E6:0.5 C6:1 E6:1              D6:1 F#6:1 A6:1 F#6:1
""")
s.melody("lead", 0, melody, gain=0.17, pan=0.1, wet=0.2, legato=0.85)

song = s.render(reverb_size=0.8, loudness=0.15)
