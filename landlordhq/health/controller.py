import os
from datetime import datetime, timezone

from flask import Blueprint, current_app, g, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy import text

from landlordhq.extensions import db
from landlordhq.utils import require_roles


blueprint = Blueprint("health", __name__)


def _tail_lines(file_path, limit):
    with open(file_path, 'r', encoding='utf-8', errors='replace') as file_obj:
        lines = file_obj.readlines()
    return [line.rstrip('\n') for line in lines[-limit:]]


@blueprint.route('/health/db', methods=['GET'])
def health_db():
    """Public DB health check endpoint for browser-based production checks."""
    try:
        ping_value = db.session.execute(text('SELECT 1')).scalar()

        return jsonify({
            "status": "ok",
            "database": {
                "connected": True,
                "ping": int(ping_value or 0),
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }), 200
    except Exception as error:  # pragma: no cover
        current_app.logger.exception('DB health check failed | request_id=%s', getattr(g, 'request_id', None))
        payload = {
            "status": "error",
            "database": {
                "connected": False,
            },
            "error": "Database connection failed",
            "request_id": getattr(g, 'request_id', None),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if current_app.config.get('EXPOSE_ERROR_DETAILS', False):
            payload['details'] = str(error)
        return jsonify(payload), 500


@blueprint.route('/health/errors', methods=['GET'])
@jwt_required()
@require_roles('owner', 'admin')
def health_errors():
    """Get recent backend error log lines (owner/admin only)."""
    log_file = current_app.config.get('ERROR_LOG_FILE', 'instance/logs/backend_errors.log')
    lines = request.args.get('lines', default=100, type=int)
    if not lines or lines < 1:
        lines = 100
    lines = min(lines, 500)

    if not os.path.exists(log_file):
        return jsonify({
            'status': 'ok',
            'entries': [],
            'count': 0,
            'message': 'No error log file yet',
        }), 200

    entries = _tail_lines(log_file, lines)

    return jsonify({
        'status': 'ok',
        'entries': entries,
        'count': len(entries),
        'request_id': getattr(g, 'request_id', None),
    }), 200
