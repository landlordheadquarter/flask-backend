from flask import Flask 

from landlordhq import account
from landlordhq import billing_period
from landlordhq import tenant
from landlordhq import unit
from landlordhq.settings import DevConfig
from landlordhq.extensions import db, migrate, bcrypt, jwt

def create_app(config_object=DevConfig):
    app = Flask(__name__)
    app.config.from_object(config_object)
    
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    jwt.init_app(app)

    from landlordhq.user.model import User
    from landlordhq.tenant.model import Tenant
    from landlordhq.unit.model import Unit
    from landlordhq.meter_reading.model import MeterReading
    from landlordhq.billing_period.model import BillingPeriod
    
    register_blueprints(app)
    
    return app 


def register_blueprints(app):
    app.register_blueprint(account.controller.blueprint, url_prefix="/api")
    app.register_blueprint(billing_period.controller.blueprint, url_prefix="/api")
    app.register_blueprint(tenant.controller.blueprint, url_prefix="/api")
    app.register_blueprint(unit.controller.blueprint, url_prefix="/api")
    
def register_extensions(arg):
    """Register flask extensions."""