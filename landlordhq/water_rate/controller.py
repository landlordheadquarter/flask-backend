"""Water Rate Controller."""
from datetime import datetime

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from landlordhq.extensions import db
from landlordhq.water_rate.model import WaterRate


blueprint = Blueprint("water_rate", __name__)


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


@blueprint.route("/water_rate", methods=["POST"])
@jwt_required()
def create_water_rate():
    """Create a new water rate."""
    data = request.get_json() or {}

    rate = _parse_rate(data.get("rate"))
    rate_date = _parse_rate_date(data.get("rate_date"))

    if rate is None:
        return {"error": "Valid rate is required"}, 400
    if rate_date is None:
        return {"error": "Valid rate_date is required (YYYY-MM-DD)"}, 400

    current_user_id = get_jwt_identity()["id"]

    water_rate = WaterRate(rate=rate, rate_date=rate_date, user_id=current_user_id)

    db.session.add(water_rate)
    db.session.commit()

    return {"message": "Water rate created successfully", "water_rate": water_rate.to_dict()}, 201


@blueprint.route("/water_rate/<int:water_rate_id>", methods=["PUT"])
@jwt_required()
def update_water_rate(water_rate_id):
    """Update a water rate."""
    data = request.get_json() or {}
    current_user_id = get_jwt_identity()["id"]

    water_rate = WaterRate.query.filter_by(id=water_rate_id, user_id=current_user_id).first()
    if not water_rate:
        return {"error": "Water rate not found"}, 404

    if "rate" in data:
        rate = _parse_rate(data.get("rate"))
        if rate is None:
            return {"error": "Valid rate is required"}, 400
        water_rate.rate = rate

    if "rate_date" in data:
        rate_date = _parse_rate_date(data.get("rate_date"))
        if rate_date is None:
            return {"error": "Valid rate_date is required (YYYY-MM-DD)"}, 400
        water_rate.rate_date = rate_date

    db.session.commit()

    return {"message": "Water rate updated successfully", "water_rate": water_rate.to_dict()}, 200


@blueprint.route("/water-rates", methods=["GET"])
@jwt_required()
def get_water_rates():
    """Get all water rates for the current user."""
    current_user_id = get_jwt_identity()["id"]

    water_rates = (
        WaterRate.query.filter_by(user_id=current_user_id)
        .order_by(WaterRate.rate_date.desc(), WaterRate.id.desc())
        .all()
    )
    return {"water_rates": [water_rate.to_dict() for water_rate in water_rates]}, 200


@blueprint.route("/water_rate/<int:water_rate_id>", methods=["DELETE"])
@jwt_required()
def delete_water_rate(water_rate_id):
    """Delete a water rate."""
    current_user_id = get_jwt_identity()["id"]

    water_rate = WaterRate.query.filter_by(id=water_rate_id, user_id=current_user_id).first()
    if not water_rate:
        return {"error": "Water rate not found"}, 404

    db.session.delete(water_rate)
    db.session.commit()

    return {"message": "Water rate deleted successfully"}, 200
