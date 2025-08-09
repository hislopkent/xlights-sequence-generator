"""Audio analysis utilities for tempo and beat detection."""

from __future__ import annotations

import librosa
import numpy as np


def analyze_beats(audio_path: str) -> dict:
    """Analyze the tempo and beat locations of an audio file.

    Parameters
    ----------
    audio_path:
        Path to the audio file to analyze.

    Returns
    -------
    dict
        A dictionary containing:

        - ``bpm``: Estimated tempo in beats per minute.
        - ``beat_times``: List of beat times in seconds.
        - ``duration_s``: Duration of the audio in seconds.
    """

    y, sr = librosa.load(audio_path, mono=True)
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr, trim=True, units="time")
    beat_times = beats  # already seconds when units="time"
    duration = float(librosa.get_duration(y=y, sr=sr))
    return {
        "bpm": float(tempo),
        "beat_times": beat_times.tolist(),
        "duration_s": duration,
    }


__all__ = ["analyze_beats"]

