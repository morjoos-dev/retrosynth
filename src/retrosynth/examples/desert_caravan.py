"""Desert Caravan — E Phrygian dominant, 104 bpm: oud ostinato, ney melody and a maqsum rhythm."""

from retrosynth import *

s = Song(bpm=104, bars=8)

# one eighth-note oud figure per harmony; the bars follow E E E E Am Am F E
figures = {
    "E": mel("E3:0.5 F3:0.5 G#3:0.5 E3:0.5 A3:0.5 G#3:0.5 F3:0.5 E3:0.5"),
    "Am": mel("A3:0.5 B3:0.5 C4:0.5 A3:0.5 E4:0.5 C4:0.5 B3:0.5 A3:0.5"),
    "F": mel("F3:0.5 A3:0.5 C4:0.5 A3:0.5 G#3:0.5 F3:0.5 E3:0.5 F3:0.5"),
}
for bar, harmony in enumerate(["E", "E", "E", "E", "Am", "Am", "F", "E"]):
    s.melody("oud", bar, figures[harmony], gain=0.15, pan=-0.25, wet=0.25, legato=0.9)
    root = figures[harmony][0].pitch
    s.put(inst.cello(midi(root - 12), s.beat * 3.8), s.at(bar), gain=0.05, wet=0.4)  # low drone
    # maqsum: DUM tek . tek DUM . tek .
    drum_pattern(s, bar, "x...x...", "doum", gain=0.35, wet=0.12)
    drum_pattern(s, bar, ".x.x..x.", "tek", gain=0.2, pan=0.2, wet=0.12)
    if bar >= 4:
        drum_pattern(s, bar, "..x...x.", "tambourine", gain=0.08, pan=0.45, wet=0.2)

melody = mel("""
    r:2 B5:1 C6:1        B5:1.5 A5:0.5 G#5:1 F5:1     E5:2 F5:0.5 G#5:0.5 A5:1     B5:4
    C6:1.5 B5:0.5 A5:1 C6:1   E6:2 D6:1 C6:1      C6:1 A5:1 G#5:1 F5:1         E5:3 r:1
""")
s.melody("ney", 0, melody, gain=0.22, pan=0.15, wet=0.45, legato=0.95)

song = s.render(reverb_size=1.3, loudness=0.13)
