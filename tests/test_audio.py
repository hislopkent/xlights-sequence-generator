import numpy as np
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import librosa
from xlights_seq.audio import analyze_beats, analyze_beats_plus


def test_analyze_beats_mocked(monkeypatch):
    monkeypatch.setattr(librosa, "load", lambda path, mono: (np.zeros(4), 22050))
    monkeypatch.setattr(librosa.beat, "beat_track", lambda y, sr, trim: (120.0, np.array([0,1,2,3])))
    monkeypatch.setattr(librosa, "frames_to_time", lambda frames, sr: np.array([0.0,0.5,1.0,1.5]))
    monkeypatch.setattr(librosa.onset, "onset_strength", lambda y, sr: np.array([0.1,0.2,0.8,0.4]))
    monkeypatch.setattr(librosa, "get_duration", lambda y, sr: 2.0)

    result = analyze_beats("dummy.wav")
    assert result["bpm"] == 120.0
    assert result["beat_times"] == [0.0, 0.5, 1.0, 1.5]
    assert result["onset_strength"] == [0.1, 0.2, 0.8, 0.4]
    assert result["duration_s"] == 2.0
    assert result["sections"] == [{"time": 1.0, "label": "Section 2"}]


def test_analyze_beats_plus_mocked(monkeypatch):
    monkeypatch.setattr(librosa, "load", lambda path, mono: (np.zeros(4), 22050))

    def fake_beat_track(*args, **kwargs):
        if kwargs.get("units") == "time":
            return 120.0, np.array([0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5])
        return 120.0, np.array([0, 1, 2, 3, 4, 5, 6, 7])

    monkeypatch.setattr(librosa.beat, "beat_track", fake_beat_track)
    monkeypatch.setattr(
        librosa.onset, "onset_strength", lambda y, sr: np.array([0.1, 0.2, 0.8, 0.4])
    )
    monkeypatch.setattr(
        librosa, "frames_to_time", lambda frames, sr: np.array([0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5])
    )
    monkeypatch.setattr(librosa, "get_duration", lambda y, sr: 30.0)

    result = analyze_beats_plus("dummy.wav")
    assert result["bpm"] == 120.0
    assert result["beat_times"] == [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5]
    assert result["downbeat_times"] == [0.0, 2.0]
    assert result["section_times"][0] == 0.0
    assert result["duration_s"] == 30.0
