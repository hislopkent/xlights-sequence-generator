import librosa
import numpy as np
import os
import subprocess
import tempfile


def analyze_beats(audio_path: str):
    """Analyze an audio file for beat times and musical sections.

    Besides tempo and beat locations this function also computes an
    onset-strength envelope and performs a very coarse segmentation by
    looking for large increases in that envelope.  Each detected jump
    marks the beginning of a new "Section".  The results are suitable for
    driving a secondary timing track in xLights.

    Returns a dictionary with the following keys:

    ``bpm``
        Estimated tempo in beats-per-minute.
    ``beat_times``
        List of beat locations (seconds).
    ``onset_strength``
        Beat-synchronous onset strength values.
    ``duration_s``
        Total duration of the audio in seconds.
    ``sections``
        List of ``{"time": float, "label": str}`` entries marking when a
        new section starts.
    """

    # Load mono for speed
    try:
        y, sr = librosa.load(audio_path, mono=True)
    except Exception:
        # Attempt to convert the input to a temporary 44.1kHz mono wav
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    audio_path,
                    "-ac",
                    "1",
                    "-ar",
                    "44100",
                    tmp_path,
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            y, sr = librosa.load(tmp_path, mono=True)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    # Beat tracking gives us the tempo and beat frame indices
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, trim=True)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)

    # Compute onset strength and sample it at the beat locations
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    beat_env = onset_env[beat_frames]

    sections = []
    if len(beat_env) > 1:
        # Look for large increases in onset strength to mark new sections
        diff_env = np.diff(beat_env, prepend=beat_env[0])
        threshold = 0.5 * np.max(beat_env)
        section_no = 2  # section 1 starts at t=0
        for i in range(1, len(beat_env)):
            if diff_env[i] > threshold:
                sections.append({
                    "time": float(beat_times[i]),
                    "label": f"Section {section_no}",
                })
                section_no += 1

    duration = float(librosa.get_duration(y=y, sr=sr))
    return {
        "bpm": float(tempo),
        "beat_times": beat_times.tolist(),
        "onset_strength": beat_env.tolist(),
        "duration_s": duration,
        "sections": sections,
    }


def analyze_beats_plus(audio_path: str):
    y, sr = librosa.load(audio_path, mono=True)
    tempo, beats_time = librosa.beat.beat_track(y=y, sr=sr, units="time", trim=True)
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    _, beats_frames = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr, trim=True)
    beats_time2 = librosa.frames_to_time(beats_frames, sr=sr)
    downbeats_time = beats_time2[::4] if len(beats_time2) else np.array([])
    duration = float(librosa.get_duration(y=y, sr=sr))
    sections_time = np.arange(0.0, duration, 15.0)  # coarse 15s grid MVP
    return {
        "bpm": float(tempo),
        "beat_times": beats_time.tolist(),
        "downbeat_times": downbeats_time.tolist(),
        "section_times": sections_time.tolist(),
        "duration_s": duration,
    }
