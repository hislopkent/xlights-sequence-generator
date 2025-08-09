import numpy as np
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import librosa
from xlights_seq.audio import analyze_beats


def test_analyze_beats_mocked(monkeypatch):
    monkeypatch.setattr(librosa, "load", lambda path, mono: (np.zeros(4), 22050))
    monkeypatch.setattr(librosa.beat, "beat_track", lambda y, sr, trim: (120.0, np.array([0,1,2,3])))
    monkeypatch.setattr(librosa, "frames_to_time", lambda frames, sr: np.array([0.0,0.5,1.0,1.5]))
    monkeypatch.setattr(librosa.onset, "onset_strength", lambda y, sr: np.array([0.1,0.2,0.8,0.4]))
    monkeypatch.setattr(librosa, "get_duration", lambda y, sr: 2.0)

    result = analyze_beats("dummy.wav")
    assert result["bpm"] == 120.0
    assert result["beat_times"] == [0.0,0.5,1.0,1.5]
    assert result["duration_s"] == 2.0
    assert result["sections"] == [
        {"time": 0.5, "label": "Verse"},
        {"time": 1.0, "label": "Chorus"},
    ]
