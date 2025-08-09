"""Main application blueprint for xLights sequence generation."""

import os
import uuid
from flask import Blueprint, render_template, request, jsonify, current_app

from .utils import secure_ext, path_in
from .parsers import parse_models


main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def index():
    """Render the upload form."""

    return render_template("index.html")


@main_bp.post("/generate")
def generate():
    """Handle uploads of an xLights effect file and audio file.

    The files are validated for correct extension and MIME type and then saved
    into the configured upload folder. A short JSON response describing the
    job is returned on success.
    """

    uploads = current_app.config["UPLOAD_FOLDER"]
    xml = request.files.get("xml")
    audio = request.files.get("audio")

    if not xml or xml.filename == "":
        return jsonify(ok=False, error="xml file required"), 400
    if not audio or audio.filename == "":
        return jsonify(ok=False, error="audio file required"), 400

    xml_name = secure_ext(xml.filename, current_app.config["ALLOWED_XML"])
    if not xml_name or xml.mimetype not in ("text/xml", "application/xml"):
        return jsonify(ok=False, error="invalid xml"), 400

    audio_name = secure_ext(audio.filename, current_app.config["ALLOWED_AUDIO"])
    if not audio_name or not audio.mimetype.startswith("audio/"):
        return jsonify(ok=False, error="invalid audio"), 400

    max_size = current_app.config.get("MAX_CONTENT_LENGTH")
    for file in (xml, audio):
        if max_size and file.content_length and file.content_length > max_size:
            return jsonify(ok=False, error="file too large"), 400

    os.makedirs(uploads, exist_ok=True)
    xml_path = path_in(uploads, xml_name)
    xml.save(xml_path)
    audio.save(path_in(uploads, audio_name))

    models = [mi.__dict__ for mi in parse_models(xml_path)]
    job_id = uuid.uuid4().hex
    response = {
        "ok": True,
        "jobId": job_id,
        "models": models,
        "durationMs": 0,
        "bpm": 0,
    }
    return jsonify(response)
