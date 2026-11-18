"""Victory Fanfare — C major, 120 bpm, one-shot (no loop): brass, timpani and a final crash."""

from retrosynth import *

s = Song(bpm=120, bars=4, loop=False)
chart = progression("C:4 F:4 G:4 C:4")

for bar, ch in enumerate(chart):
    pad(s, bar, ch.notes, 4 if bar == 3 else 0.9, instrument="brass", gain=0.05, wet=0.35)
    s.put(inst.timpani(midi(ch.notes[0] - 12)), s.at(bar), gain=0.4, wet=0.25)

# snare and timpani roll building into the last bar
for k in range(16):
    s.put(inst.snare(), s.at(2, k * 0.25), gain=0.06 + 0.012 * k, pan=0.15, wet=0.2)
    if k >= 8:
        s.put(inst.timpani(midi(note("G2"))), s.at(2, k * 0.25), gain=0.08 + 0.02 * (k - 8), wet=0.25)
s.put(inst.cymbal(), s.at(3), gain=0.3, pan=0.3, wet=0.4)

fanfare = mel("G4:0.5 C5:0.5 E5:0.5 G5:1.5 E5:0.5 G5:0.5  A5:1.5 F5:0.5 A5:0.5 C6:1.5  B5:1 G5:1 D6:1 B5:1  C6:4")
s.melody("brass", 0, fanfare, gain=0.22, wet=0.3, legato=0.92)
s.melody("lead", 0, fanfare, gain=0.05, pan=0.3, wet=0.3, legato=0.85)

song = s.render(reverb_size=1.2, loudness=0.15)
