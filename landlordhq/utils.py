"""Helper utilities and decorators for the LandlordHQ package."""
from datetime import datetime
from functools import wraps

from flask_jwt_extended import get_jwt_identity
from flask import jsonify
    
def jwt_identity(jwt):
    """Extract the identity from a JWT token."""
    return jwt['sub'] if 'sub' in jwt else None

def identity_loader(identity):
    """Load the identity from the database."""
    return identity

def date_to_str(date):
    """Convert a date to a string in the format YYYY-MM-DD."""
    return date.strftime('%Y-%m-%d') if date else None

def str_to_date(date_str):
    """Convert a string in the format YYYY-MM-DD to a date."""

    return datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None


def get_current_user():
    from landlordhq.user.model import User

    identity = get_jwt_identity() or {}
    user_id = identity.get('id')
    if not user_id:
        return None
    return User.query.get(user_id)


def require_roles(*allowed_roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if not user:
                return jsonify({'error': 'Unauthorized'}), 401

            user_role = (user.role or 'staff').lower()
            normalized_roles = {role.lower() for role in allowed_roles}
            if user_role not in normalized_roles:
                return jsonify({'error': 'Forbidden: insufficient role permissions'}), 403

            return func(*args, **kwargs)

        return wrapper

    return decorator


def log_audit_action(user_id, action, entity_type, entity_id=None, details=None):
    from landlordhq.extensions import db
    from landlordhq.audit_log.model import AuditLog

    entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
    )
    db.session.add(entry)