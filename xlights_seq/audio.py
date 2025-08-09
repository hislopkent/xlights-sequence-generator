import librosa
import numpy as np


def analyze_beats(audio_path: str):
    """Analyze an audio file for beat times and coarse section changes.

    In addition to the per-beat timing returned by ``librosa.beat.beat_track``,
    this function estimates high-level sections ("Intro", "Verse", "Chorus") by
    grouping beats based on onset strength.  Section boundaries are marked when
    the beat-synchronous onset strength crosses quantile thresholds.

    Returns a dictionary with keys ``bpm``, ``beat_times``, ``duration_s`` and
    ``sections`` (a list of ``{"time": float, "label": str}``).
    """

    # Load mono for speed
    y, sr = librosa.load(audio_path, mono=True)

    # Beat tracking gives us the tempo and beat frame indices
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, trim=True)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)

    # Onset strength envelope to gauge musical intensity
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    # Sample the onset envelope at beat locations
    beat_env = onset_env[beat_frames]

    sections = []
    if len(beat_env) > 0:
        # Quantile-based grouping into three rough energy bands
        q1, q2 = np.quantile(beat_env, [1 / 3, 2 / 3])
        labels = np.digitize(beat_env, [q1, q2])  # 0,1,2 -> low, mid, high
        section_names = ["Intro", "Verse", "Chorus"]

        prev_label = labels[0]
        for i in range(1, len(labels)):
            if labels[i] != prev_label:
                sections.append({
                    "time": float(beat_times[i]),
                    "label": section_names[labels[i]],
                })
                prev_label = labels[i]

    duration = float(librosa.get_duration(y=y, sr=sr))
    return {
        "bpm": float(tempo),
        "beat_times": beat_times.tolist(),
        "duration_s": duration,
        "sections": sections,
    }
