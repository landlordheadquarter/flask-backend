"""Unit controller."""

import json
import os
import uuid

from flask import Blueprint, jsonify, request, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

from landlordhq.extensions import db
from landlordhq.unit.model import Unit
from landlordhq.user.model import User

blueprint = Blueprint("unit", __name__)


def _parse_non_negative_float(value):
    if value in (None, ""):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number < 0:
        return None
    return number


def _unit_upload_dir():
    folder = os.path.join('instance', 'uploads', 'units')
    os.makedirs(folder, exist_ok=True)
    return folder


def _save_unit_photos(files):
    photo_urls = []
    upload_dir = _unit_upload_dir()

    for file_item in files:
        if not file_item or not file_item.filename:
            continue

        filename = secure_filename(file_item.filename)
        if not filename:
            continue

        ext = os.path.splitext(filename)[1]
        generated = f"{uuid.uuid4().hex}{ext}"
        file_path = os.path.join(upload_dir, generated)
        file_item.save(file_path)
        photo_urls.append(f"/api/unit/photo/{generated}")

    return photo_urls


def _parse_photo_urls(raw_value):
    if not raw_value:
        return []
    try:
        parsed = json.loads(raw_value)
        if isinstance(parsed, list):
            return parsed
    except (TypeError, ValueError, json.JSONDecodeError):
        return []
    return []


def _serialize_unit(unit):
    return {
        "id": unit.id,
        "unit_no": unit.unit_no,
        "description": unit.description,
        "rate": unit.rate,
        "photo_urls": _parse_photo_urls(unit.photo_urls),
        "electric_meter_no": unit.electric_meter_no,
        "water_meter_no": unit.water_meter_no,
        "created_at": unit.created_at,
        "updated_at": unit.updated_at,
    }


def _filename_from_photo_url(photo_url):
    prefix = '/api/unit/photo/'
    if not photo_url or not photo_url.startswith(prefix):
        return None
    return photo_url[len(prefix):]


def _delete_photo_file(photo_url):
    filename = _filename_from_photo_url(photo_url)
    if not filename:
        return

    safe_filename = os.path.basename(filename)
    if safe_filename != filename:
        return

    file_path = os.path.join(_unit_upload_dir(), safe_filename)
    if os.path.exists(file_path):
        os.remove(file_path)


@blueprint.route('/unit/photo/<path:filename>', methods=['GET'])
def get_unit_photo(filename):
    return send_from_directory(_unit_upload_dir(), filename)

@blueprint.route("/unit", methods=["POST"])
@jwt_required()
def create_unit():
    """Create a new unit."""
    data = request.get_json() if request.is_json else request.form

    if not data.get("unit_no"):
        return {"error": "Unit number is required"}, 400

    parsed_rate = _parse_non_negative_float(data.get("rate"))
    if data.get("rate") not in (None, "") and parsed_rate is None:
        return {"error": "Rate must be a non-negative number"}, 400

    uploaded_photo_urls = _save_unit_photos(request.files.getlist('photos'))

    current_user_id = get_jwt_identity()["id"]

    # Check if the user exists
    user = User.query.get(current_user_id)
    if not user:
        return {"error": "User not found"}, 404

    # Create a new unit
    unit = Unit(
        unit_no=data["unit_no"],
        description=data.get("description"),
        rate=parsed_rate,
        photo_urls=json.dumps(uploaded_photo_urls),
        electric_meter_no=data.get("electric_meter_no"),
        water_meter_no=data.get("water_meter_no"),
        user_id=current_user_id,
    )

    db.session.add(unit)
    db.session.commit()

    return {"message": "Unit created successfully", "unit_id": unit.id, "unit": _serialize_unit(unit)}, 201


@blueprint.route("/unit/<int:unit_id>", methods=["PUT"])
@jwt_required()
def update_unit(unit_id):
    """Update a unit's details."""
    data = request.get_json() if request.is_json else request.form

    current_user_id = get_jwt_identity()["id"]

    # Find the unit by ID and ensure it belongs to the current user
    unit = Unit.query.filter_by(id=unit_id, user_id=current_user_id).first()
    if not unit:
        return {"error": "Unit not found or does not belong to the current user"}, 404

    # Update unit details
    if data.get("unit_no"):
        unit.unit_no = data["unit_no"]
    if "description" in data:
        unit.description = data.get("description")
    if "rate" in data:
        parsed_rate = _parse_non_negative_float(data.get("rate"))
        if data.get("rate") not in (None, "") and parsed_rate is None:
            return {"error": "Rate must be a non-negative number"}, 400
        unit.rate = parsed_rate
    if "electric_meter_no" in data:
        unit.electric_meter_no = data.get("electric_meter_no")
    if "water_meter_no" in data:
        unit.water_meter_no = data.get("water_meter_no")

    existing_photo_urls = _parse_photo_urls(unit.photo_urls)
    new_photo_urls = _save_unit_photos(request.files.getlist('photos'))
    if new_photo_urls:
        unit.photo_urls = json.dumps(existing_photo_urls + new_photo_urls)

    db.session.commit()

    return {"message": "Unit updated successfully"}, 200


@blueprint.route('/unit/<int:unit_id>/photos', methods=['POST'])
@jwt_required()
def add_unit_photos(unit_id):
    current_user_id = get_jwt_identity()["id"]
    unit = Unit.query.filter_by(id=unit_id, user_id=current_user_id).first()
    if not unit:
        return {"error": "Unit not found or does not belong to the current user"}, 404

    new_photo_urls = _save_unit_photos(request.files.getlist('photos'))
    if not new_photo_urls:
        return {"error": "No photos uploaded"}, 400

    existing_photo_urls = _parse_photo_urls(unit.photo_urls)
    unit.photo_urls = json.dumps(existing_photo_urls + new_photo_urls)
    db.session.commit()

    return jsonify({"message": "Photos uploaded successfully", "unit": _serialize_unit(unit)}), 200


@blueprint.route('/unit/<int:unit_id>/photos', methods=['DELETE'])
@jwt_required()
def delete_unit_photo(unit_id):
    current_user_id = get_jwt_identity()["id"]
    unit = Unit.query.filter_by(id=unit_id, user_id=current_user_id).first()
    if not unit:
        return {"error": "Unit not found or does not belong to the current user"}, 404

    data = request.get_json() or {}
    photo_url = data.get('photo_url')
    if not photo_url:
        return {"error": "photo_url is required"}, 400

    photo_urls = _parse_photo_urls(unit.photo_urls)
    if photo_url not in photo_urls:
        return {"error": "Photo not found in unit"}, 404

    unit.photo_urls = json.dumps([item for item in photo_urls if item != photo_url])
    _delete_photo_file(photo_url)
    db.session.commit()

    return jsonify({"message": "Photo removed successfully", "unit": _serialize_unit(unit)}), 200

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
    unit_list = [_serialize_unit(unit) for unit in available_units]

    return jsonify({"available_units": unit_list}), 200

@blueprint.route("/units", methods=["GET"])
@jwt_required()
def get_units():
    """Get all units for the current logged-in user."""
    current_user_id = get_jwt_identity()["id"]

    units = Unit.query.filter_by(user_id=current_user_id).all()

    unit_list = [_serialize_unit(unit) for unit in units]

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

    for photo_url in _parse_photo_urls(unit.photo_urls):
        _delete_photo_file(photo_url)

    db.session.delete(unit)
    db.session.commit()

    return {"message": "Unit deleted successfully"}, 200