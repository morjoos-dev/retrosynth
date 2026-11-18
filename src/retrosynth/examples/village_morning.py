"""Village Morning — F major, 96 bpm: harp arpeggios, flute, strings and a gentle shaker."""

from retrosynth import *

s = Song(bpm=96, bars=16)
chart = progression("""
    F:4 Dm:4 Bb:4 C:4   F:4 Dm:4 Gm:4 C:4
    Bb:4 C:4 Am:4 Dm:4  Gm:4 C:4 F:4 C7:4
""")

for bar, ch in enumerate(chart):
    c = ch.notes
    arpeggio(s, bar, c, [0, 1, 2, 3, 2, 1, 0, 1], step=0.5, gain=0.09, pan=-0.3, wet=0.4)
    s.put(inst.bass(midi(c[0] - 12), s.beat * 1.8), s.at(bar, 0), gain=0.32, wet=0.1)
    s.put(inst.bass(midi(c[2] - 12), s.beat * 1.8), s.at(bar, 2), gain=0.26, wet=0.1)
    s.put(inst.kick(), s.at(bar), gain=0.22, wet=0.05)
    if bar >= 8:  # second half: warmer, with a string pad and a little rhythm
        pad(s, bar, c[:3], 4, gain=0.05)
        drum_pattern(s, bar, "..x...x...x...x.", "shaker", gain=0.05, pan=0.4)

melody = mel("""
    A5:1.5 G5:0.5 F5:1 C5:1   D5:1.5 E5:0.5 F5:1 A5:1    Bb5:1.5 A5:0.5 G5:1 F5:1   G5:2 E5:1 C5:1
    A5:1.5 G5:0.5 F5:1 A5:1   D6:1.5 C6:0.5 A5:1 F5:1    G5:1 Bb5:1 A5:1 G5:1       C5:1 E5:1 G5:2
    F5:1 Bb5:1 D6:2           C6:1 Bb5:0.5 A5:0.5 G5:2   A5:1 C6:1 E6:1.5 D6:0.5    D6:1 A5:1 F5:2
    G5:1 Bb5:1 D6:1 C6:1      Bb5:1 A5:1 G5:1 E5:1       F5:2 A5:1 C6:1             G5:2 E5:1 C5:1
""")
s.melody("flute", 0, melody, gain=0.24, wet=0.4, legato=0.92)
# a music-box echo of the long notes in the second half, one octave up
s.melody("music_box", 8, [n.transposed(12) if n.beats >= 2 else Note(None, n.beats) for n in melody[30:]],
         gain=0.05, pan=0.35, wet=0.5)

song = s.render(reverb_size=1.2, loudness=0.12)
