import librosa

def analyze_beats(audio_path: str):
    # Load mono for speed
    y, sr = librosa.load(audio_path, mono=True)
    tempo, beat_times = librosa.beat.beat_track(y=y, sr=sr, trim=True, units="time")
    duration = float(librosa.get_duration(y=y, sr=sr))
    return { "bpm": float(tempo), "beat_times": beat_times.tolist(), "duration_s": duration }
