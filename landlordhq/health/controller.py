from datetime import datetime, timezone

from flask import Blueprint, jsonify
from sqlalchemy import text

from landlordhq.extensions import db


blueprint = Blueprint("health", __name__)


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
        return jsonify({
            "status": "error",
            "database": {
                "connected": False,
            },
            "error": str(error),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }), 500
