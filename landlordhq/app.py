import logging
import os
import uuid
from logging.handlers import RotatingFileHandler

from flask import Flask, g, jsonify
from werkzeug.exceptions import HTTPException

from landlordhq import account
from landlordhq import audit_log
from landlordhq import billing_period
from landlordhq import health
from landlordhq import notification
from landlordhq import payment
from landlordhq import power_rate
from landlordhq import tenant
from landlordhq import unit
from landlordhq import water_rate
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
    from landlordhq.audit_log.model import AuditLog
    from landlordhq.notification.model import Notification
    from landlordhq.payment.model import Payment
    from landlordhq.water_rate.model import WaterRate
    
    register_blueprints(app)
    register_error_observability(app)
    
    return app 


def register_blueprints(app):
    app.register_blueprint(account.controller.blueprint, url_prefix="/api")
    app.register_blueprint(audit_log.controller.blueprint, url_prefix="/api")
    app.register_blueprint(billing_period.controller.blueprint, url_prefix="/api")
    app.register_blueprint(health.controller.blueprint, url_prefix="/api")
    app.register_blueprint(notification.controller.blueprint, url_prefix="/api")
    app.register_blueprint(payment.controller.blueprint, url_prefix="/api")
    app.register_blueprint(power_rate.controller.blueprint, url_prefix="/api")
    app.register_blueprint(tenant.controller.blueprint, url_prefix="/api")
    app.register_blueprint(unit.controller.blueprint, url_prefix="/api")
    app.register_blueprint(water_rate.controller.blueprint, url_prefix="/api")


def register_error_observability(app):
    log_file = app.config.get('ERROR_LOG_FILE', 'instance/logs/backend_errors.log')
    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    has_error_file_handler = any(
        isinstance(handler, RotatingFileHandler)
        and getattr(handler, 'baseFilename', '').endswith(os.path.basename(log_file))
        for handler in app.logger.handlers
    )

    if not has_error_file_handler:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=app.config.get('ERROR_LOG_MAX_BYTES', 1048576),
            backupCount=app.config.get('ERROR_LOG_BACKUP_COUNT', 5),
        )
        file_handler.setLevel(logging.ERROR)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s'
        ))
        app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO if app.debug else logging.ERROR)

    @app.before_request
    def add_request_id():
        g.request_id = str(uuid.uuid4())

    @app.after_request
    def append_request_id_header(response):
        if getattr(g, 'request_id', None):
            response.headers['X-Request-ID'] = g.request_id
        return response

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        if error.code and error.code >= 500:
            app.logger.error(
                'HTTPException | request_id=%s | status=%s | description=%s',
                getattr(g, 'request_id', 'n/a'),
                error.code,
                error.description,
            )

        return jsonify({
            'error': error.description,
            'request_id': getattr(g, 'request_id', None),
        }), error.code or 500

    @app.errorhandler(Exception)
    def handle_unexpected_exception(error):
        request_id = getattr(g, 'request_id', None)
        app.logger.exception('UnhandledException | request_id=%s', request_id)

        payload = {
            'error': 'Internal server error',
            'request_id': request_id,
        }
        if app.config.get('EXPOSE_ERROR_DETAILS', False):
            payload['details'] = str(error)

        return jsonify(payload), 500
    
def register_extensions(arg):
    """Register flask extensions."""