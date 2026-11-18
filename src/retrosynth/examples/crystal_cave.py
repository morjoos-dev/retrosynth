"""Crystal Cave — A minor, 72 bpm: music box, choir pad, cello drone and random water drops."""

from retrosynth import *

s = Song(bpm=72, bars=8)
chart = progression("Am:4 Fmaj7:4 C:4 G:4  Am:4 F:4 Dm:4 E:4")

for bar, ch in enumerate(chart):
    c = ch.notes
    pad(s, bar, c[:3], 4, instrument="choir", gain=0.05, wet=0.6)
    s.put(inst.cello(midi(c[0] - 12), s.beat * 3.6), s.at(bar), gain=0.07, wet=0.5)
    if bar % 2 == 0:
        s.put(inst.bell(midi(c[0] + 12), s.beat * 4), s.at(bar), gain=0.04, pan=-0.4, wet=0.7)

# water drops: short high notes from the A minor pentatonic at random moments.
# rand() is seeded per song, so the "random" drops are identical on every render.
drops = [note(n) for n in ("A6", "C7", "D7", "E7", "G7")]
for _ in range(40):
    when = rand() * s.length
    pitch = drops[int(rand() * len(drops))]
    s.put(inst.marimba(midi(pitch), 0.1), when, gain=0.015 + 0.02 * rand(), pan=rand() * 1.6 - 0.8, wet=0.8)

melody = mel("""
    E6:2 C6:1 A5:1     F5:1 A5:1 C6:1 E6:1     G6:2 E6:1 C6:1     D6:3 B5:1
    C6:1 E6:1 A6:2     G6:1 F6:1 E6:1 C6:1     D6:2 F6:1 A5:1     G#5:2 B5:1 E6:1
""")
s.melody("music_box", 0, melody, gain=0.16, pan=0.1, wet=0.55)
s.melody("flute", 4, lower(melody[12:]), gain=0.08, pan=-0.15, wet=0.6, legato=0.98)

song = s.render(reverb_size=1.6, loudness=0.1)
