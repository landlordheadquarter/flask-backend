# -*- coding: utf-8 -*-
"""Create an application instance."""
from flask.helpers import get_debug_flag
import os
from dotenv import load_dotenv
from flask_migrate import upgrade


def _in_docker() -> bool:
    return os.path.exists('/.dockerenv')


load_dotenv(override=not _in_docker())

from landlordhq.app import create_app
from landlordhq.settings import DevConfig
from landlordhq.settings import ProdConfig
from landlordhq.extensions import db 

CONFIG = DevConfig if get_debug_flag() else ProdConfig

app = create_app(CONFIG)

# Run migrations automatically on startup
if os.environ.get("RUN_MIGRATIONS", "false").lower() == "true":
    with app.app_context():
        upgrade()

@app.route("/")
@app.route("/index")
def index():
    return "HELLO"


if __name__ == "__main__":
    app.run(debug=bool(getattr(CONFIG, 'DEBUG', False)), port=8000)
