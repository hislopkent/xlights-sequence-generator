from flask import Flask, render_template, request, jsonify, send_file, g
import os, uuid, json, shutil, time, re, zipfile
from werkzeug.exceptions import RequestEntityTooLarge
from xlights_seq.config import Config
from xlights_seq.parsers import (
    parse_models,
    parse_tree,
    flatten_models,
    parse_tree_with_index,
)
from xlights_seq.recommend import recommend_groups
from xlights_seq.audio import analyze_beats_plus
from xlights_seq.xsq_writer import build_xsq, write_xsq
from xlights_seq.versioning import build_version
from logger import get_json_logger

OFFLINE = os.environ.get("OFFLINE", "1") == "1"

APP_VERSION = build_version()

app = Flask(__name__)
app.config.from_object(Config)
app.config["VERSION"] = APP_VERSION
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["OUTPUT_FOLDER"], exist_ok=True)

# Configure JSON logger
app.logger = get_json_logger(app.config["LOG_FILE"])


@app.before_request
def log_request_start():
    g.start_time = time.time()
    app.logger.info(
        "request_started",
        extra={"path": request.path, "ip": request.remote_addr},
    )


@app.after_request
def log_request_end(response):
    if hasattr(g, "start_time"):
        duration = (time.time() - g.start_time) * 1000
        app.logger.info(
            "request_completed",
            extra={
                "path": request.path,
                "ip": request.remote_addr,
                "status": response.status_code,
                "duration_ms": round(duration, 2),
            },
        )
    return response


@app.after_request
def no_tracking(resp):
    # no external beacons; tighten headers
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "no-referrer"
    return resp


@app.errorhandler(RequestEntityTooLarge)
def handle_large(_):
    app.logger.error(
        "request_too_large",
        extra={"path": request.path, "ip": request.remote_addr},
    )
    max_mb = app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024)
    return jsonify({"ok": False, "error": f"File too large (max {max_mb} MB)."}), 413


@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.exception(
        "unhandled_exception",
        extra={"path": request.path, "ip": request.remote_addr, "error": str(e)},
    )
    return jsonify({"ok": False, "error": "Internal server error"}), 500

@app.get("/")
def index():
    return render_template("index.html")

@app.get("/health")
def health():
    return jsonify(ok=True, version=APP_VERSION)


@app.get("/version")
def version():
    return jsonify(version=app.config["VERSION"])


@app.post("/inspect-layout")
def inspect_layout():
    layout = request.files.get("layout")
    if not layout or not layout.filename.lower().endswith(".xml"):
        return jsonify(ok=False, error="Upload a layout .xml"), 400
    tmp = os.path.join(app.config["UPLOAD_FOLDER"], f"inspect-{uuid.uuid4()}.xml")
    layout.save(tmp)
    tree = parse_tree(tmp)
    models = flatten_models(tree)

    def to_dict(n):
        return {
            "name": n.name,
            "type": n.type,
            "strings": n.strings,
            "nodes": n.nodes,
            "children": [to_dict(c) for c in n.children],
        }

    return jsonify(ok=True, modelCount=len(models), tree=to_dict(tree))


@app.post("/recommend-groups")
def recommend_groups_api():
    layout = request.files.get("layout")
    if not layout or not layout.filename.lower().endswith(".xml"):
        return jsonify(ok=False, error="Upload a layout .xml"), 400
    tmp = os.path.join(app.config["UPLOAD_FOLDER"], f"rec-{uuid.uuid4()}.xml")
    layout.save(tmp)
    tree, _ = parse_tree_with_index(tmp)
    recs = recommend_groups(tree)
    return jsonify(ok=True, recommendations=recs, count=len(recs))

@app.post("/generate")
def generate():
    app.logger.info(
        "generate_start", extra={"path": request.path, "ip": request.remote_addr}
    )
    layout = request.files.get("layout")
    audio = request.files.get("audio")
    networks = request.files.get("networks")
    preset = request.form.get("preset", "solid_pulse")
    export_format = request.form.get("export_format", "xsq")
    export_title = (request.form.get("package_title") or "My Sequence").strip()
    safe_title = "".join(ch for ch in export_title if ch not in "\\/:*?\"<>|").strip() or "My Sequence"
    palette_str = request.form.get("palette", "").strip()
    palette = None
    if palette_str:
        palette = []
        for part in palette_str.split(","):
            part = part.strip()
            if not part:
                continue
            if not part.startswith("#"):
                part = "#" + part
            if re.fullmatch(r"#([0-9a-fA-F]{6})", part):
                palette.append(part.upper())
        if not palette:
            palette = None

    selected_recs = request.form.get("selected_recommendations")
    try:
        selected_recs = json.loads(selected_recs) if selected_recs else []
    except Exception:
        selected_recs = []

    if not layout or not audio:
        return (
            jsonify({"ok": False, "error": "Both layout XML and audio are required."}),
            400,
        )

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
    networks_path = None

    layout.save(xml_path)
    audio.save(audio_path)
    layout_bytes = os.path.getsize(xml_path)
    audio_bytes = os.path.getsize(audio_path)
    extra = {"layout_bytes": layout_bytes, "audio_bytes": audio_bytes}
    if networks and networks.filename:
        if not networks.filename.lower().endswith(".xml"):
            return jsonify(ok=False, error="Networks must be .xml"), 400
        if not _size_ok(networks):
            return (
                jsonify(
                    ok=False,
                    error=f"Networks file too large (max {max_mb}MB).",
                ),
                400,
            )
        networks_path = os.path.join(
            app.config["UPLOAD_FOLDER"], f"{job}-networks.xml"
        )
        networks.save(networks_path)
        extra["networks_bytes"] = os.path.getsize(networks_path)
    app.logger.info("generate_files", extra=extra)

    try:
        models = parse_models(xml_path)
    except Exception as e:
        return jsonify({"ok": False, "error": f"Failed to parse XML: {e}"}), 400

    analysis = analyze_beats_plus(audio_path)
    duration_ms = int(analysis["duration_s"] * 1000)
    beat_times = analysis["beat_times"]
    downbeat_times = analysis.get("downbeat_times", [])
    section_times = analysis.get("section_times", [])
    beat_count = len(beat_times)
    downbeat_count = len(downbeat_times)
    section_count = len(section_times)
    selected_model_count = len(models)
    total_model_count = selected_model_count
    sections = [
        {"time": float(t), "label": f"Section {i+1}"}
        for i, t in enumerate(section_times[1:], start=2)
    ]
    xsq_tree = build_xsq(
        models,
        beat_times,
        duration_ms,
        downbeat_times=downbeat_times,
        section_times=section_times,
        preset=preset,
    )
    bpm_val = analysis.get("bpm")

    job_dir = os.path.join(app.config["OUTPUT_FOLDER"], job)
    os.makedirs(job_dir, exist_ok=True)

    xsq_path = os.path.join(job_dir, f"{safe_title}.xsq")
    write_xsq(xsq_tree, xsq_path)

    layout_canonical = os.path.join(job_dir, "xlights_rgbeffects.xml")
    shutil.copyfile(xml_path, layout_canonical)
    if networks_path:
        shutil.copy(networks_path, os.path.join(job_dir, "xlights_networks.xml"))

    download_name = os.path.basename(xsq_path)
    download_path = xsq_path
    if export_format == "xsqz":
        xsqz_path = os.path.join(job_dir, f"{safe_title}.xsqz")
        with zipfile.ZipFile(xsqz_path, "w", zipfile.ZIP_DEFLATED) as z:
            z.write(xsq_path, arcname=os.path.basename(xsq_path))
            z.write(layout_canonical, arcname="xlights_rgbeffects.xml")
            if networks_path:
                z.write(networks_path, arcname="xlights_networks.xml")
            if os.path.exists(audio_path):
                z.write(
                    audio_path,
                    arcname=os.path.join("media", os.path.basename(audio_path)),
                )
        download_name, download_path = os.path.basename(xsqz_path), xsqz_path

    with open(os.path.join(job_dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(
            {
                "job": job,
                "bpm": analysis.get("bpm"),
                "durationMs": duration_ms,
                "models": [m.__dict__ for m in models],
                "preset": preset,
                "export_format": export_format,
                "title": export_title,
                "safe_title": safe_title,
                "has_networks": bool(networks_path),
                "has_media": os.path.exists(audio_path),
                "version": APP_VERSION,
                "downbeat_times": downbeat_times,
                "section_times": section_times,
            },
            f,
            indent=2,
        )

    with open(os.path.join(job_dir, "preview.json"), "w", encoding="utf-8") as f:
        json.dump(
            {
                "beatTimes": beat_times,
                "downbeatTimes": downbeat_times,
                "sectionTimes": section_times,
                "sections": sections,
            },
            f,
        )

    app.logger.info(
        "generate_complete",
        extra={"bpm": bpm_val, "path": request.path, "ip": request.remote_addr},
    )
    return jsonify(
        {
            "ok": True,
            "jobId": job,
            "bpm": analysis.get("bpm"),
            "durationMs": duration_ms,
            "beatCount": beat_count,
            "downbeatCount": downbeat_count,
            "sectionCount": section_count,
            "modelCount": selected_model_count,
            "selectedModelCount": selected_model_count,
            "totalModelCount": total_model_count,
            "version": APP_VERSION,
            "exportFormat": export_format,
            "title": export_title,
            "downloadUrl": f"/download/{job}/{download_name}",
        }
    )


@app.get("/preview.json")
def preview():
    job = request.args.get("job")
    if not job:
        return jsonify({"ok": False, "error": "Missing job"}), 400
    preview_path = os.path.join(app.config["OUTPUT_FOLDER"], job, "preview.json")
    if not os.path.isfile(preview_path):
        return jsonify({"ok": False, "error": "Not found"}), 404
    with open(preview_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return jsonify(
        {
            "ok": True,
            "beatTimes": data.get("beatTimes", []),
            "downbeatTimes": data.get("downbeatTimes", []),
            "sections": data.get("sections", []),
            "sectionTimes": data.get("sectionTimes", []),
        }
    )


@app.get("/download/<job>/<name>")
def download_artifact(job, name):
    path = os.path.join(app.config["OUTPUT_FOLDER"], job, name)
    return (
        send_file(path, as_attachment=True, download_name=name)
        if os.path.isfile(path)
        else ("Not found", 404)
    )

@app.get("/download/<job>")
def download(job):
    job_dir = os.path.join(app.config["OUTPUT_FOLDER"], job)
    if not os.path.isdir(job_dir):
        return ("Not found", 404)
    export_format = "xsq"
    safe_title = "My Sequence"
    meta_path = os.path.join(job_dir, "metadata.json")
    if os.path.isfile(meta_path):
        with open(meta_path, "r", encoding="utf-8") as f:
            try:
                meta = json.load(f)
                export_format = meta.get("export_format", export_format)
                safe_title = meta.get("safe_title", safe_title)
            except Exception:
                pass
    if export_format == "rgbeffects_xml":
        file_path = os.path.join(job_dir, "xlights_rgbeffects.xml")
        return send_file(
            file_path,
            as_attachment=True,
            download_name="xlights_rgbeffects.xml",
        )
    if export_format == "xsq":
        file_path = os.path.join(job_dir, f"{safe_title}.xsq")
        return send_file(
            file_path,
            as_attachment=True,
            download_name=f"{safe_title}.xsq",
        )
    if export_format == "xsqz":
        file_path = os.path.join(job_dir, f"{safe_title}.xsqz")
        return send_file(
            file_path,
            as_attachment=True,
            download_name=f"{safe_title}.xsqz",
        )
    zip_path = shutil.make_archive(job_dir, "zip", job_dir)
    return send_file(zip_path, as_attachment=True, download_name=f"xlights_{job}.zip")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
