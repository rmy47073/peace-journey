# -*- coding: utf-8 -*-
from app_factory import create_app
from app.config.config import Config


if __name__ == "__main__":
    app = create_app()
    app.run(host='0.0.0.0', port=Config.PORT, debug=Config.DEBUG)
