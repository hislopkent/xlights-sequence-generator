from flask import Flask, render_template, request, jsonify, send_file
import os, uuid, json, shutil
from xlights_seq.config import Config
from xlights_seq.parsers import parse_models
from xlights_seq.audio import analyze_beats
from xlights_seq.generator import build_rgbeffects, write_rgbeffects

app = Flask(__name__)
app.config.from_object(Config)
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["OUTPUT_FOLDER"], exist_ok=True)

@app.get("/")
def index():
    return render_template("index.html")

@app.get("/health")
def health():
    return jsonify(ok=True)

@app.post("/generate")
def generate():
    layout = request.files.get("layout")
    audio = request.files.get("audio")
    preset = request.form.get("preset", "solid_pulse")
    manual_bpm = request.form.get("bpm")
    manual_bpm = float(manual_bpm) if manual_bpm else None
    offset_ms = request.form.get("start_offset_ms")
    offset_ms = float(offset_ms) if offset_ms else 0.0

    if not layout or not audio:
        return jsonify({"ok": False, "error": "Both layout XML and audio are required."}), 400

    job = str(uuid.uuid4())
    xml_path = os.path.join(app.config["UPLOAD_FOLDER"], f"{job}-layout.xml")
    audio_ext = (audio.filename.rsplit(".",1)[-1] or "mp3").lower()
    audio_path = os.path.join(app.config["UPLOAD_FOLDER"], f"{job}-audio.{audio_ext}")

    layout.save(xml_path)
    audio.save(audio_path)

    try:
        models = parse_models(xml_path)
    except Exception as e:
        return jsonify({"ok": False, "error": f"Failed to parse XML: {e}"}), 400

    try:
        analysis = analyze_beats(audio_path)
    except Exception:
        # Safe fallback if beat detection fails
        analysis = {
            "bpm": None,
            "duration_s": 180.0,
            "beat_times": [i * 0.5 for i in range(int(180 / 0.5))],
            "sections": [],
        }

    duration_s = float(analysis["duration_s"])
    duration_ms = int(duration_s * 1000)

    if manual_bpm:
        step_s = 60.0 / manual_bpm
        beat_times = [i * step_s for i in range(int(duration_s / step_s) + 1)]
        offset_s = offset_ms / 1000.0
        beat_times = [t + offset_s for t in beat_times]
        beat_times = [t for t in beat_times if 0 <= t <= duration_s]
        bpm_val = manual_bpm
    else:
        beat_times = analysis["beat_times"]
        bpm_val = analysis.get("bpm")

    sections = analysis.get("sections")

    tree = build_rgbeffects(models, beat_times, duration_ms, preset, sections)

    job_dir = os.path.join(app.config["OUTPUT_FOLDER"], job)
    os.makedirs(job_dir, exist_ok=True)
    out_xml = os.path.join(job_dir, "rgbeffects.xml")
    write_rgbeffects(tree, out_xml)

    with open(os.path.join(job_dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump({
            "job": job,
            "bpm": bpm_val,
            "durationMs": duration_ms,
            "models": [m.__dict__ for m in models],
            "preset": preset
        }, f, indent=2)

    return jsonify({
        "ok": True,
        "jobId": job,
        "bpm": bpm_val,
        "modelCount": len(models),
        "downloadUrl": f"/download/{job}"
    })

@app.get("/download/<job>")
def download(job):
    job_dir = os.path.join(app.config["OUTPUT_FOLDER"], job)
    if not os.path.isdir(job_dir):
        return ("Not found", 404)
    zip_path = shutil.make_archive(job_dir, "zip", job_dir)
    return send_file(zip_path, as_attachment=True, download_name=f"xlights_{job}.zip")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
