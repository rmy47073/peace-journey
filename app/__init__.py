from flask import Flask
from flask_cors import CORS
from app.routes import api_bp
from app.config.config import Config


def create_app():
    """
    Create Flask app instance
    :return: Flask
    """
    app = Flask(__name__)
    # ≈‰÷√CORS£¨‘ –Ì«∞∂À∑√Œ 
    CORS(app, 
         origins=['http://localhost:3000', 'http://127.0.0.1:3000'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
         allow_headers=['Content-Type', 'Authorization', 'Origin', 'X-Requested-With'],
         supports_credentials=True)
    app.config.from_object(Config)
    app.register_blueprint(api_bp, url_prefix='/api')

    return app
