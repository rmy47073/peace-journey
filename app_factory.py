# -*- coding: utf-8 -*-
from flask import Flask
from flask_cors import CORS

from app.api import api_bp, smart_api_bp
from app.config.config import Config


def create_app():
    app = Flask(__name__)
    CORS(
        app,
        origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "Origin", "X-Requested-With"],
        supports_credentials=True,
    )
    app.config.from_object(Config)
    app.register_blueprint(api_bp, url_prefix=Config.API_PREFIX)
    app.register_blueprint(smart_api_bp, url_prefix=Config.SMART_API_PREFIX)
    return app
