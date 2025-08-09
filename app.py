from flask import Flask, render_template, request, jsonify, send_file, g
import os, uuid, json, shutil, time, logging, math, threading
import librosa
from werkzeug.exceptions import RequestEntityTooLarge
from xlights_seq.config import Config
from xlights_seq.parsers import parse_models
from xlights_seq.audio import analyze_beats
from xlights_seq.generator import build_rgbeffects, write_rgbeffects

app = Flask(__name__)
app.config.from_object(Config)
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["OUTPUT_FOLDER"], exist_ok=True)

# Configure logging
handler = logging.FileHandler(app.config["LOG_FILE"])
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)


@app.before_request
def log_request_start():
    g.start_time = time.time()
    app.logger.info(f"Started {request.method} {request.path}")


@app.after_request
def log_request_end(response):
    if hasattr(g, "start_time"):
        duration = (time.time() - g.start_time) * 1000
        app.logger.info(
            f"Completed {request.method} {request.path} with status {response.status_code} in {duration:.2f}ms"
        )
    return response


@app.errorhandler(RequestEntityTooLarge)
def handle_large(_):
    app.logger.error(f"Request too large for {request.path}")
    max_mb = app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024)
    return jsonify({"ok": False, "error": f"File too large (max {max_mb} MB)."}), 413


@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.exception(f"Error handling request: {request.method} {request.path}")
    return jsonify({"ok": False, "error": "Internal server error"}), 500

@app.get("/")
def index():
    return render_template("index.html", version=app.config["VERSION"])

@app.get("/health")
def health():
    return jsonify(ok=True)


@app.get("/version")
def version():
    return jsonify(version=app.config["VERSION"])

@app.post("/generate")
def generate():
    layout = request.files.get("layout")
    audio = request.files.get("audio")
    preset = request.form.get("preset", "solid_pulse")
    manual_bpm = float(request.form.get("manual_bpm") or 0) or None
    start_offset_ms = int(request.form.get("start_offset_ms") or 0)

    if not layout or not audio:
        return jsonify({"ok": False, "error": "Both layout XML and audio are required."}), 400

    ALLOWED_XML = app.config["ALLOWED_XML"]
    ALLOWED_AUDIO = app.config["ALLOWED_AUDIO"]

    def _ok(name, allowed):
        return "." in name and name.rsplit(".", 1)[1].lower() in allowed

    if not _ok(layout.filename, ALLOWED_XML):
        return jsonify(ok=False, error="Layout must be .xml"), 400
    if not _ok(audio.filename, ALLOWED_AUDIO):
        return jsonify(ok=False, error="Audio must be mp3/wav/m4a/aac"), 400

    max_bytes = app.config["MAX_CONTENT_LENGTH"]
    max_mb = max_bytes // (1024 * 1024)

    def _size_ok(f):
        f.stream.seek(0, os.SEEK_END)
        size = f.stream.tell()
        f.stream.seek(0)
        return size <= max_bytes

    if not _size_ok(layout):
        return jsonify(ok=False, error=f"Layout file too large (max {max_mb}MB)."), 400
    if not _size_ok(audio):
        return jsonify(ok=False, error=f"Audio file too large (max {max_mb}MB)."), 400

    layout_ext = layout.filename.rsplit(".", 1)[-1].lower()
    audio_ext = audio.filename.rsplit(".", 1)[-1].lower()

    job = str(uuid.uuid4())
    xml_path = os.path.join(app.config["UPLOAD_FOLDER"], f"{job}-layout.xml")
    audio_path = os.path.join(app.config["UPLOAD_FOLDER"], f"{job}-audio.{audio_ext}")

    layout.save(xml_path)
    audio.save(audio_path)

    try:
        models = parse_models(xml_path)
    except Exception as e:
        return jsonify({"ok": False, "error": f"Failed to parse XML: {e}"}), 400

    result = {}

    def _worker():
        try:
            result["analysis"] = analyze_beats(audio_path)
        except Exception as e:
            result["error"] = e

    t = threading.Thread(target=_worker)
    t.start()
    t.join(app.config["ANALYSIS_TIMEOUT"])

    if t.is_alive():
        app.logger.error(
            f"Audio analysis timed out after {app.config['ANALYSIS_TIMEOUT']}s"
        )
        try:
            duration_s = float(librosa.get_duration(path=audio_path))
        except Exception as e:
            return jsonify({"ok": False, "error": f"Failed to analyze audio: {e}"}), 400
        bpm_val = 120.0
        period_s = 60.0 / bpm_val
        total = int(math.ceil(duration_s / period_s))
        beat_times = [i * period_s for i in range(total)]
        sections = []
    else:
        if "error" in result:
            return jsonify({"ok": False, "error": f"Failed to analyze audio: {result['error']}"}), 400
        analysis = result["analysis"]
        duration_s = float(analysis["duration_s"])
        if manual_bpm:
            period_s = 60.0 / manual_bpm
            total = int(math.ceil(duration_s / period_s))
            beat_times = [i * period_s for i in range(total)]
            bpm_val = manual_bpm
        else:
            beat_times = analysis["beat_times"]
            bpm_val = analysis.get("bpm")
        sections = analysis.get("sections")

    duration_ms = int(duration_s * 1000)
    beat_times = [max(0.0, (t * 1000 + start_offset_ms) / 1000.0) for t in beat_times]

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
            "preset": preset,
            "manual_bpm": manual_bpm,
            "start_offset_ms": start_offset_ms
        }, f, indent=2)

    return jsonify({
        "ok": True,
        "jobId": job,
        "bpm": bpm_val,
        "manualBpm": manual_bpm,
        "durationMs": duration_ms,
        "modelCount": len(models),
        "modelNames": [m.name for m in models],
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
