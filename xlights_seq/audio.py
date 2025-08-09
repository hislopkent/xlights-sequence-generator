import librosa
import numpy as np


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
    y, sr = librosa.load(audio_path, mono=True)

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
