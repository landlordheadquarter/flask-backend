from flask import Flask 

from landlordhq import tenant
from landlordhq import unit
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    #app.config.from_object("landlordhq.settings.DevConfig")
    register_blueprints(app)
    return app 


def register_blueprints(app):
    app.register_blueprint(tenant.views.blueprint)
    app.register_blueprint(unit.views.blueprint)
    