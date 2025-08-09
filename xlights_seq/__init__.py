import os
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, jsonify, current_app
from .utils import allowed_file

main_bp = Blueprint('main', __name__)

@main_bp.get('/')
def index():
    return render_template('index.html')

@main_bp.post('/generate')
def generate():
    uploads = current_app.config['UPLOAD_FOLDER']
    saved = {}
    xml = request.files.get('xml')
    if xml and allowed_file(xml.filename, current_app.config['ALLOWED_XML']):
        filename = secure_filename(xml.filename)
        xml.save(os.path.join(uploads, filename))
        saved['xml'] = filename
    audio = request.files.get('audio')
    if audio and allowed_file(audio.filename, current_app.config['ALLOWED_AUDIO']):
        filename = secure_filename(audio.filename)
        audio.save(os.path.join(uploads, filename))
        saved['audio'] = filename
    return jsonify(saved)
