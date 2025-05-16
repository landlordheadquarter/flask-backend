"""Due Date controller module."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from landlordhq.extensions import db
from landlordhq.due_date.model import DueDate
from landlordhq.user.model import User
from landlordhq.tenant.model import Tenant

blueprint = Blueprint("due_date", __name__)
@blueprint.route("/due_date", methods=["POST"])
@jwt_required()
def create_due_date():
    """Create a new due date."""
    data = request.get_json()

    if not data.get("due_date") or not data.get("description"):
        return {"error": "Due date and description are required"}, 400

    current_user_id = get_jwt_identity()["id"]

    # Check if the user exists
    user = User.query.get(current_user_id)
    if not user:
        return {"error": "User not found"}, 404

    # Check if the tenant exists
    tenant = Tenant.query.filter_by(id=data["tenant_id"], user_id=current_user_id).first()
    if not tenant:
        return {"error": "Tenant not found"}, 404

    # Create a new due date
    due_date = DueDate(
        due_date=data["due_date"],
        description=data["description"],
        user_id=current_user_id,
        tenant_id=tenant.id,
    )

    db.session.add(due_date)
    db.session.commit()

    return {"message": "Due date created successfully", "due_date_id": due_date.id}, 201
@blueprint.route("/due_date/<int:due_date_id>", methods=["PUT"])
@jwt_required()
def update_due_date(due_date_id):
    """Update a due date."""
    data = request.get_json()

    # Get the current logged-in user's ID
    current_user_id = get_jwt_identity()["id"]

    # Find the due date by ID and ensure it belongs to the current user
    due_date = DueDate.query.filter_by(id=due_date_id, user_id=current_user_id).first()
    if not due_date:
        return {"error": "Due date not found or does not belong to the current user"}, 404

    # Update due date details
    if data.get("due_date"):
        due_date.due_date = data["due_date"]
    if data.get("description"):
        due_date.description = data["description"]

    db.session.commit()

    return {"message": "Due date updated successfully"}, 200

@blueprint.route("/due_dates", methods=["GET"])
@jwt_required()
def get_due_dates():
    """Get all due dates for the current logged-in user."""
    current_user_id = get_jwt_identity()["id"]

    due_dates = DueDate.query.filter_by(user_id=current_user_id).all()
    return {"due_dates": [due_date.to_dict() for due_date in due_dates]}, 200

@blueprint.route("/due_date/<int:due_date_id>", methods=["DELETE"])
@jwt_required()
def delete_due_date(due_date_id):
    """Delete a due date."""
    current_user_id = get_jwt_identity()["id"]

    # Find the due date by ID and ensure it belongs to the current user
    due_date = DueDate.query.filter_by(id=due_date_id, user_id=current_user_id).first()
    if not due_date:
        return {"error": "Due date not found or does not belong to the current user"}, 404

    db.session.delete(due_date)
    db.session.commit()

    return {"message": "Due date deleted successfully"}, 200

@blueprint.route("/due_date/<int:due_date_id>", methods=["GET"])
@jwt_required()
def get_due_date(due_date_id):
    """Get a specific due date."""
    current_user_id = get_jwt_identity()["id"]

    # Find the due date by ID and ensure it belongs to the current user
    due_date = DueDate.query.filter_by(id=due_date_id, user_id=current_user_id).first()
    if not due_date:
        return {"error": "Due date not found or does not belong to the current user"}, 404

    return {"due_date": due_date.to_dict()}, 200

@blueprint.route("/due_dates/tenant/<int:tenant_id>", methods=["GET"])
@jwt_required()
def get_due_dates_by_tenant(tenant_id):
    """Get all due dates for a specific tenant."""
    current_user_id = get_jwt_identity()["id"]

    # Check if the tenant exists
    tenant = Tenant.query.filter_by(id=tenant_id, user_id=current_user_id).first()
    if not tenant:
        return {"error": "Tenant not found"}, 404

    due_dates = DueDate.query.filter_by(tenant_id=tenant.id).all()
    return {"due_dates": [due_date.to_dict() for due_date in due_dates]}, 200