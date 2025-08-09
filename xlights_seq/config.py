import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "devkey")
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    UPLOAD_FOLDER = os.path.abspath("uploads")
    OUTPUT_FOLDER = os.path.abspath("generated")
    ALLOWED_XML = {"xml"}
    ALLOWED_AUDIO = {"mp3","wav","m4a","aac"}
