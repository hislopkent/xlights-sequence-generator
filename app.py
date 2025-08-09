from flask import Flask
from xlights_seq.config import Config
from xlights_seq import main_bp
import os


def create_app(config_class=Config):
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config.from_object(config_class)

    # Ensure directories exist
    for folder in (app.config['UPLOAD_FOLDER'], app.config['OUTPUT_FOLDER']):
        os.makedirs(folder, exist_ok=True)

    app.register_blueprint(main_bp)
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000)
