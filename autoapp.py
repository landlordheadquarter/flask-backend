# -*- coding: utf-8 -*-
"""Create an application instance."""
from flask.helpers import get_debug_flag
from flask_migrate import Migrate

from landlordhq.app import create_app
from landlordhq.settings import DevConfig
from landlordhq.settings import ProdConfig
from landlordhq.extensions import db 

CONFIG = DevConfig if get_debug_flag() else ProdConfig

app = create_app(DevConfig)
migrate = Migrate(app, db)


@app.route("/")
@app.route("/index")
def index():
    return "HELLO"


if __name__ == "__main__":
    app.run(debug=True, port=8000)
