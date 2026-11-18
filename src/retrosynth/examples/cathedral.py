"""Cathedral — D minor, 60 bpm: pipe organ, formant choir and church bells in a large hall."""

from retrosynth import *

s = Song(bpm=60, bars=8)
chart = progression("Dm:4 Gm:4 C:4 F:4  Bb:4 Gm:4 A:4 A7:4")

for bar, ch in enumerate(chart):
    c = ch.notes
    pad(s, bar, c[:3], 4, instrument="organ", gain=0.05, wet=0.5)  # organ chord, octave 4
    s.put(inst.organ(midi(c[0] - 12), s.beat * 3.9), s.at(bar), gain=0.08, wet=0.4)  # pedal
    pad(s, bar, c[:3], 4, instrument="voice_o", gain=0.035, wet=0.6)  # choir "oh"

for bar in (0, 4):
    s.put(inst.church_bell(midi(note("D4")), 6), s.at(bar), gain=0.1, pan=-0.3, wet=0.7)

soprano = mel("A5:4  Bb5:2 G5:2  G5:2 E5:2  F5:2 A5:2  D6:3 C6:1  Bb5:2 D6:1 C6:1  C#6:2 A5:2  E5:4")
s.melody("voice_a", 0, soprano, gain=0.09, pan=0.1, wet=0.6, legato=1.0)

song = s.render(reverb_size=1.8, loudness=0.1)
