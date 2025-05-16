from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from landlordhq.extensions import db
from landlordhq.meter_reading.model import MeterReading
from landlordhq.user.model import User
from landlordhq.tenant.model import Tenant
from landlordhq.constants import UTILITY_TYPES


blueprint = Blueprint("meter_reading", __name__)

@blueprint.route("/meter_reading", methods=["POST"])
@jwt_required()
def create_meter_reading():
    """Create a new meter reading."""
    data = request.get_json()

    if not data.get("utility_type") or not data.get("reading_date") or not data.get("reading"):
        return {"error": "Utility type, reading date, and reading are required"}, 400

    if data["utility_type"] not in UTILITY_TYPES:
        return {"error": f"Invalid utility type. Must be one of {UTILITY_TYPES}"}, 400

    current_user_id = get_jwt_identity()["id"]

    # Check if the user exists
    user = User.query.get(current_user_id)
    if not user:
        return {"error": "User not found"}, 404

    # Check if the tenant exists
    tenant = Tenant.query.filter_by(id=data["tenant_id"], user_id=current_user_id).first()
    if not tenant:
        return {"error": "Tenant not found"}, 404

    # Create a new meter reading
    meter_reading = MeterReading(
        utility_type=data["utility_type"],
        reading_date=data["reading_date"],
        reading=data["reading"],
        user_id=current_user_id,
        tenant_id=tenant.id,
    )

    db.session.add(meter_reading)
    db.session.commit()

    return {"message": "Meter reading created successfully", "meter_reading_id": meter_reading.id}, 201

@blueprint.route("/meter_reading/<int:meter_reading_id>", methods=["PUT"])
@jwt_required()
def update_meter_reading(meter_reading_id):
    """Update a meter reading."""
    data = request.get_json()

    # Get the current logged-in user's ID
    current_user_id = get_jwt_identity()["id"]

    # Find the meter reading by ID and ensure it belongs to the current user
    meter_reading = MeterReading.query.filter_by(id=meter_reading_id, user_id=current_user_id).first()
    if not meter_reading:
        return {"error": "Meter reading not found or does not belong to the current user"}, 404

    # Update meter reading details
    if data.get("utility_type"):
        if data["utility_type"] not in UTILITY_TYPES:
            return {"error": f"Invalid utility type. Must be one of {UTILITY_TYPES}"}, 400
        meter_reading.utility_type = data["utility_type"]
    if data.get("reading_date"):
        meter_reading.reading_date = data["reading_date"]
    if data.get("reading"):
        meter_reading.reading = data["reading"]

    db.session.commit()

    return {"message": "Meter reading updated successfully"}, 200

@blueprint.route("/meter_readings", methods=["GET"])
@jwt_required()
def get_meter_readings():
    """Get all meter readings for the current user."""
    current_user_id = get_jwt_identity()["id"]

    meter_readings = MeterReading.query.filter_by(user_id=current_user_id).all()
    return {"meter_readings": [meter_reading.to_dict() for meter_reading in meter_readings]}, 200

@blueprint.route("/meter_reading/<int:meter_reading_id>", methods=["DELETE"])
@jwt_required()
def delete_meter_reading(meter_reading_id):
    """Delete a meter reading."""
    current_user_id = get_jwt_identity()["id"]

    # Find the meter reading by ID and ensure it belongs to the current user
    meter_reading = MeterReading.query.filter_by(id=meter_reading_id, user_id=current_user_id).first()
    if not meter_reading:
        return {"error": "Meter reading not found or does not belong to the current user"}, 404

    db.session.delete(meter_reading)
    db.session.commit()

    return {"message": "Meter reading deleted successfully"}, 200

@blueprint.route("/meter_reading/<int:meter_reading_id>", methods=["GET"])
@jwt_required()
def get_meter_reading(meter_reading_id):
    """Get a specific meter reading."""
    current_user_id = get_jwt_identity()["id"]

    # Find the meter reading by ID and ensure it belongs to the current user
    meter_reading = MeterReading.query.filter_by(id=meter_reading_id, user_id=current_user_id).first()
    if not meter_reading:
        return {"error": "Meter reading not found or does not belong to the current user"}, 404

    return {"meter_reading": meter_reading.to_dict()}, 200

@blueprint.route("/meter_readings/tenant/<int:tenant_id>", methods=["GET"])
@jwt_required()
def get_meter_readings_by_tenant(tenant_id):
    """Get all meter readings for a specific tenant."""
    current_user_id = get_jwt_identity()["id"]

    # Check if the tenant exists
    tenant = Tenant.query.filter_by(id=tenant_id, user_id=current_user_id).first()
    if not tenant:
        return {"error": "Tenant not found"}, 404

    meter_readings = MeterReading.query.filter_by(tenant_id=tenant.id).all()
    return {"meter_readings": [meter_reading.to_dict() for meter_reading in meter_readings]}, 200