"""retrosynth — a dependency-light music synthesizer for 16-bit style game music.

Song scripts usually start with ``from retrosynth import *``, which brings in
everything needed to write music: :class:`Song`, the instrument library ``inst``,
note / melody / chord helpers and the low-level DSP functions.
"""

from .dsp import (
    SAMPLE_RATE,
    SR,
    adsr,
    bandpass,
    decay,
    highpass,
    karplus_strong,
    lowpass,
    midi,
    mix,
    noise,
    osc,
    partials,
    rand,
    reverb,
    samples,
    saturate,
    sine_sweep,
    time_axis,
)
from .instruments import Instrument, inst
from .song import (
    CHORDS,
    ChordEvent,
    Note,
    Song,
    arpeggio,
    beats_of,
    chord,
    chord_symbol,
    drum_pattern,
    lower,
    mel,
    note,
    note_name,
    pad,
    progression,
    rock_drums,
    soft_limit,
    transpose,
)

__version__ = "1.0.0"

__all__ = [
    "SAMPLE_RATE", "SR", "adsr", "bandpass", "decay", "highpass", "karplus_strong", "lowpass", "midi", "mix",
    "noise", "osc", "partials", "rand", "reverb", "samples", "saturate", "sine_sweep", "time_axis",
    "Instrument", "inst",
    "CHORDS", "ChordEvent", "Note", "Song", "arpeggio", "beats_of", "chord", "chord_symbol", "drum_pattern", "lower", "mel",
    "note", "note_name", "pad", "progression", "rock_drums", "soft_limit", "transpose",
    "np",
]

import numpy as np  # noqa: E402  (re-exported for song scripts)
