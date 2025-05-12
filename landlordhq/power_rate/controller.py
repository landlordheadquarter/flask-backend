""" Power Rate Controller """
from flask import Blueprint, request
from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from landlordhq.extensions import db
from landlordhq.power_rate.model import PowerRate
from landlordhq.user.model import User

@blueprint.route("/power_rate", methods=["POST"])
@jwt_required()
def create_power_rate():
    """Create a new power rate."""
    data = request.get_json()

    if not data.get("rate") or not data.get("rate_date"):
        return {"error": "Rate and rate date are required"}, 400

    current_user_id = get_jwt_identity()["id"]

    user = User.query.get(current_user_id)
    if not user:
        return {"error": "User not found"}, 404

    power_rate = PowerRate(
        rate=data["rate"],
        rate_date=data["rate_date"],
        user_id=current_user_id,
    )

    db.session.add(power_rate)
    db.session.commit()

    return {"message": "Power rate created successfully"}, 201

@Blueprint.route("/power_rate/<int:power_rate_id>", methods=["PUT"])
@jwt_required()
def update_power_rate(power_rate_id):
    """Update a power rate."""
    data = request.get_json()

    # Get the current logged-in user's ID
    current_user_id = get_jwt_identity()["id"]

    # Find the power rate by ID and ensure it belongs to the current user
    power_rate = PowerRate.query.filter_by(id=power_rate_id, user_id=current_user_id).first()
    if not power_rate:
        return {"error": "Power rate not found or does not belong to the current user"}, 404

    # Update power rate details
    if data.get("rate"):
        power_rate.rate = data["rate"]
    if data.get("rate_date"):
        power_rate.rate_date = data["rate_date"]

    db.session.commit()

    return {"message": "Power rate updated successfully"}, 200

@blueprint.route("/power-rates", methods=["GET"])
@jwt_required()
def get_power_rates():
    """Get all power rates for the current user."""
    current_user_id = get_jwt_identity()["id"]

    power_rates = PowerRate.query.filter_by(user_id=current_user_id).all()
    return {"power_rates": [power_rate.to_dict() for power_rate in power_rates]}, 200

@blueprint.route("/power_rate/<int:power_rate_id>", methods=["DELETE"])
@jwt_required()
def delete_power_rate(power_rate_id):
    """Delete a power rate."""
    current_user_id = get_jwt_identity()["id"]

    power_rate = PowerRate.query.filter_by(id=power_rate_id, user_id=current_user_id).first()
    if not power_rate:
        return {"error": "Power rate not found or does not belong to the current user"}, 404

    db.session.delete(power_rate)
    db.session.commit()

    return {"message": "Power rate deleted successfully"}, 200

