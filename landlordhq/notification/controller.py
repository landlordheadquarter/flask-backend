"""Notification Controller."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from landlordhq.extensions import db
from landlordhq.notification.model import Notification


blueprint = Blueprint('notification', __name__)


@blueprint.route('/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    current_user_id = get_jwt_identity()['id']
    unread_only = str(request.args.get('unread_only', 'false')).lower() == 'true'

    query = Notification.query.filter_by(user_id=current_user_id)
    if unread_only:
        query = query.filter_by(is_read=False)

    notifications = query.order_by(Notification.created_at.desc(), Notification.id.desc()).all()
    return jsonify({'notifications': [notification.to_dict() for notification in notifications]}), 200


@blueprint.route('/notification/<int:notification_id>/read', methods=['PATCH', 'PUT'])
@jwt_required()
def mark_notification_read(notification_id):
    current_user_id = get_jwt_identity()['id']

    notification = Notification.query.filter_by(id=notification_id, user_id=current_user_id).first()
    if not notification:
        return {'error': 'Notification not found'}, 404

    notification.is_read = True
    db.session.commit()

    return {'message': 'Notification marked as read'}, 200
