from flask import Flask 

from landlordhq import tenant
from landlordhq import unit
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from landlordhq.settings import DevConfig
from landlordhq.extensions import db 

migrate = Migrate()

def create_app(config_object=DevConfig):
    app = Flask(__name__)
    app.config.from_object(config_object)
    
    db.init_app(app)
    migrate.init_app(app, db)  # Ensure Flask-Migrate is initialized here

    register_blueprints(app)
    
    return app 


def register_blueprints(app):
    app.register_blueprint(tenant.controller.blueprint, url_prefix="/api/")
    app.register_blueprint(unit.controller.blueprint, url_prefix="/api/")
    
def register_extensions(arg):
    """Register flask extensions."""