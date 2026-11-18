"""Iron Gauntlet — E minor, 160 bpm: battle theme with palm-muted guitars, gliding lead and double kick."""

from retrosynth import *

s = Song(bpm=160, bars=16)
chart = progression("""
    Em:4 Em:4 C:4 D:4    Em:4 Em:4 C:4 B:4
    Am:4 C:4 D:4 Em:4    Am:4 C:4 B:4 B:4
""")

for bar, ch in enumerate(chart):
    root = ch.notes[0] - 12  # octave 2
    chorus = bar >= 8
    rock_drums(s, bar, double_kick=chorus, crash=bar % 4 == 0)
    for k in range(8):  # eighth-note chugs: guitar and bass lock together
        s.put(inst.guitar(midi(root), s.beat * 0.4, mute=True), s.at(bar, k * 0.5), gain=0.09, pan=-0.45, wet=0.08)
        s.put(inst.guitar(midi(root), s.beat * 0.4, mute=True), s.at(bar, k * 0.5), gain=0.09, pan=0.45, wet=0.08)
        s.put(inst.rock_bass(midi(root - 12), s.beat * 0.45), s.at(bar, k * 0.5), gain=0.3, wet=0.03)
    if chorus:  # brass stabs on the downbeat and the "and" of 2
        for beat in (0, 1.5):
            for i, n in enumerate(ch.notes[:3]):
                s.put(inst.brass(midi(n + 12), s.beat * 0.4), s.at(bar, beat), gain=0.06, pan=(i - 1) * 0.4, wet=0.25)

lead = mel("""
    E5:0.5 G5:0.5 B5:1 A5:0.5 G5:0.5 B5:1     E6:1.5 D6:0.5 B5:2
    C6:0.5 B5:0.5 A5:0.5 G5:0.5 E5:1 G5:1     F#5:1.5 A5:0.5 D6:2
    E5:0.5 G5:0.5 B5:1 A5:0.5 G5:0.5 B5:1     G6:1.5 F#6:0.5 E6:2
    E6:0.5 D6:0.5 C6:0.5 B5:0.5 A5:1 G5:1     F#5:1 A5:1 D#6:2
    A5:1 C6:1 E6:1.5 D6:0.5                   C6:1 E6:1 G6:2
    F#6:1 E6:0.5 D6:0.5 A5:1 D6:1             B5:2 G5:1 E5:1
    A5:0.5 B5:0.5 C6:1 E6:1 A6:1              G6:1.5 E6:0.5 C6:2
    D#6:1 F#6:1 B6:2                          A6:1 F#6:1 D#6:1 B5:1
""")
s.melody("lead", 0, lead, gain=0.2, pan=0.05, wet=0.25, legato=0.9, glide=True)
s.melody("guitar", 8, lower(lead[36:]), gain=0.05, pan=-0.2, wet=0.2, legato=0.9)  # chorus doubled an octave down

song = s.render(reverb_size=0.9, loudness=0.17)
