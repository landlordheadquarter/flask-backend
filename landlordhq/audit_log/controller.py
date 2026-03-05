"""Audit Log Controller."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from landlordhq.audit_log.model import AuditLog
from landlordhq.utils import get_current_user, require_roles


blueprint = Blueprint('audit_log', __name__)


@blueprint.route('/audit-logs', methods=['GET'])
@jwt_required()
@require_roles('owner', 'admin')
def get_audit_logs():
    current_user = get_current_user()
    limit = request.args.get('limit', default=50, type=int)

    logs = (
        AuditLog.query
        .filter_by(user_id=current_user.id)
        .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        .limit(max(1, min(limit, 200)))
        .all()
    )

    return jsonify({'audit_logs': [item.to_dict() for item in logs]}), 200
