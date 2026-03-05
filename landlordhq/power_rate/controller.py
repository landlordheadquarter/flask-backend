"""Power Rate Controller."""
from datetime import datetime

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from landlordhq.extensions import db
from landlordhq.power_rate.model import PowerRate


blueprint = Blueprint("power_rate", __name__)


def _parse_rate(value):
    if value in (None, ""):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number < 0:
        return None
    return number


def _parse_rate_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except (TypeError, ValueError):
        return None


@blueprint.route("/power_rate", methods=["POST"])
@jwt_required()
def create_power_rate():
    """Create a new power rate."""
    data = request.get_json() or {}

    rate = _parse_rate(data.get("rate"))
    rate_date = _parse_rate_date(data.get("rate_date"))

    if rate is None:
        return {"error": "Valid rate is required"}, 400
    if rate_date is None:
        return {"error": "Valid rate_date is required (YYYY-MM-DD)"}, 400

    current_user_id = get_jwt_identity()["id"]

    power_rate = PowerRate(rate=rate, rate_date=rate_date, user_id=current_user_id)

    db.session.add(power_rate)
    db.session.commit()

    return {"message": "Power rate created successfully", "power_rate": power_rate.to_dict()}, 201


@blueprint.route("/power_rate/<int:power_rate_id>", methods=["PUT"])
@jwt_required()
def update_power_rate(power_rate_id):
    """Update a power rate."""
    data = request.get_json() or {}
    current_user_id = get_jwt_identity()["id"]

    power_rate = PowerRate.query.filter_by(id=power_rate_id, user_id=current_user_id).first()
    if not power_rate:
        return {"error": "Power rate not found"}, 404

    if "rate" in data:
        rate = _parse_rate(data.get("rate"))
        if rate is None:
            return {"error": "Valid rate is required"}, 400
        power_rate.rate = rate

    if "rate_date" in data:
        rate_date = _parse_rate_date(data.get("rate_date"))
        if rate_date is None:
            return {"error": "Valid rate_date is required (YYYY-MM-DD)"}, 400
        power_rate.rate_date = rate_date

    db.session.commit()

    return {"message": "Power rate updated successfully", "power_rate": power_rate.to_dict()}, 200


@blueprint.route("/power-rates", methods=["GET"])
@jwt_required()
def get_power_rates():
    """Get all power rates for the current user."""
    current_user_id = get_jwt_identity()["id"]

    power_rates = (
        PowerRate.query.filter_by(user_id=current_user_id)
        .order_by(PowerRate.rate_date.desc(), PowerRate.id.desc())
        .all()
    )
    return {"power_rates": [power_rate.to_dict() for power_rate in power_rates]}, 200


@blueprint.route("/power_rate/<int:power_rate_id>", methods=["DELETE"])
@jwt_required()
def delete_power_rate(power_rate_id):
    """Delete a power rate."""
    current_user_id = get_jwt_identity()["id"]

    power_rate = PowerRate.query.filter_by(id=power_rate_id, user_id=current_user_id).first()
    if not power_rate:
        return {"error": "Power rate not found"}, 404

    db.session.delete(power_rate)
    db.session.commit()

    return {"message": "Power rate deleted successfully"}, 200

