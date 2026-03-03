"""Unit controller."""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from landlordhq.extensions import db
from landlordhq.unit.model import Unit
from landlordhq.user.model import User

blueprint = Blueprint("unit", __name__)

@blueprint.route("/unit", methods=["POST"])
@jwt_required()
def create_unit():
    """Create a new unit."""
    data = request.get_json()

    if not data.get("unit_no"):
        return {"error": "Unit number is required"}, 400

    current_user_id = get_jwt_identity()["id"]

    # Check if the user exists
    user = User.query.get(current_user_id)
    if not user:
        return {"error": "User not found"}, 404

    # Create a new unit
    unit = Unit(
        unit_no=data["unit_no"],
        electric_meter_no=data.get("electric_meter_no"),
        water_meter_no=data.get("water_meter_no"),
        user_id=current_user_id,
    )

    db.session.add(unit)
    db.session.commit()

    return {"message": "Unit created successfully", "unit_id": unit.id}, 201


@blueprint.route("/unit/<int:unit_id>", methods=["PUT"])
@jwt_required()
def update_unit(unit_id):
    """Update a unit's details."""
    data = request.get_json()

    current_user_id = get_jwt_identity()["id"]

    # Find the unit by ID and ensure it belongs to the current user
    unit = Unit.query.filter_by(id=unit_id, user_id=current_user_id).first()
    if not unit:
        return {"error": "Unit not found or does not belong to the current user"}, 404

    # Update unit details
    if data.get("unit_no"):
        unit.unit_no = data["unit_no"]
    if "electric_meter_no" in data:
        unit.electric_meter_no = data.get("electric_meter_no")
    if "water_meter_no" in data:
        unit.water_meter_no = data.get("water_meter_no")

    db.session.commit()

    return {"message": "Unit updated successfully"}, 200

@blueprint.route("/unit/available-units", methods=["GET"])
@jwt_required()
def get_available_units():
    """Get all available units for the current logged-in user."""
    current_user_id = get_jwt_identity()["id"]
    
    # Get all tenants associated with the current user
    tenants = Unit.query.filter_by(user_id=current_user_id).all()
    unit_ids = [tenant.unit_id for tenant in tenants]


    # Query to get units that are not in the tenant_unit_association table
    available_units = Unit.query.filter(
        Unit.user_id == current_user_id,
        Unit.id.notin_(unit_ids)
    ).all()

    # Format the response
    unit_list = [
        {
            "id": unit.id,
            "unit_no": unit.unit_no,
            "electric_meter_no": unit.electric_meter_no,
            "water_meter_no": unit.water_meter_no,
            "created_at": unit.created_at,
            "updated_at": unit.updated_at,
        }
        for unit in available_units
    ]

    return jsonify({"available_units": unit_list}), 200

@blueprint.route("/units", methods=["GET"])
@jwt_required()
def get_units():
    """Get all units for the current logged-in user."""
    current_user_id = get_jwt_identity()["id"]

    units = Unit.query.filter_by(user_id=current_user_id).all()

    unit_list = [
        {
            "id": unit.id,
            "unit_no": unit.unit_no,
            "electric_meter_no": unit.electric_meter_no,
            "water_meter_no": unit.water_meter_no,
            "created_at": unit.created_at,
            "updated_at": unit.updated_at,
        }
        for unit in units
    ]

    return jsonify({"units": unit_list}), 200


@blueprint.route("/unit/<int:unit_id>", methods=["DELETE"])
@jwt_required()
def delete_unit(unit_id):
    """Delete a unit."""
    current_user_id = get_jwt_identity()["id"]

    # Find the unit by ID and ensure it belongs to the current user
    unit = Unit.query.filter_by(id=unit_id, user_id=current_user_id).first()
    if not unit:
        return {"error": "Unit not found or does not belong to the current user"}, 404

    db.session.delete(unit)
    db.session.commit()

    return {"message": "Unit deleted successfully"}, 200