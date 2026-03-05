import os
import uuid
import json

from flask import Blueprint, jsonify, request, send_from_directory
from landlordhq.user.model import User
from landlordhq.unit.model import Unit
from landlordhq.extensions import db
from landlordhq.extensions import bcrypt
from werkzeug.utils import secure_filename

from flask_jwt_extended import create_access_token
from flask_jwt_extended import jwt_required
from flask_jwt_extended import get_jwt

blacklist = set()

blueprint = Blueprint("account", __name__)


def _profile_upload_dir():
    folder = os.path.join('instance', 'uploads', 'profiles')
    os.makedirs(folder, exist_ok=True)
    return folder


def _serialize_user(user):
    return {
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "contact_no": user.contact_no,
        "address": user.address,
        "profile_photo_url": user.profile_photo_url,
        "latitude": user.latitude,
        "longitude": user.longitude,
    }


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


def _serialize_public_unit(unit):
    return {
        "id": unit.id,
        "unit_no": unit.unit_no,
        "description": unit.description,
        "rate": unit.rate,
        "photo_urls": _parse_photo_urls(unit.photo_urls),
    }


def _serialize_public_user(user):
    return {
        "id": user.id,
        "name": user.name,
        "contact_no": user.contact_no,
        "address": user.address,
        "profile_photo_url": user.profile_photo_url,
        "latitude": user.latitude,
        "longitude": user.longitude,
    }


def _parse_lat_lng(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _delete_profile_photo(photo_url):
    prefix = '/api/account/profile-photo/'
    if not photo_url or not photo_url.startswith(prefix):
        return

    filename = photo_url[len(prefix):]
    safe_filename = os.path.basename(filename)
    if safe_filename != filename:
        return

    file_path = os.path.join(_profile_upload_dir(), safe_filename)
    if os.path.exists(file_path):
        os.remove(file_path)


def _save_profile_photo(file_item):
    if not file_item or not file_item.filename:
        return None

    filename = secure_filename(file_item.filename)
    if not filename:
        return None

    ext = os.path.splitext(filename)[1]
    generated = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(_profile_upload_dir(), generated)
    file_item.save(file_path)
    return f"/api/account/profile-photo/{generated}"


@blueprint.route('/account/profile-photo/<path:filename>', methods=['GET'])
def get_profile_photo(filename):
    return send_from_directory(_profile_upload_dir(), filename)


@blueprint.route('/account/public-random', methods=['GET'])
def get_random_public_profile():
    random_user = (
        User.query
        .filter(User.name.isnot(None))
        .filter(User.email.isnot(None))
        .filter(User.password.isnot(None))
        .order_by(db.func.rand())
        .first()
    )

    if not random_user:
        return jsonify({"user": None}), 200

    return jsonify({
        "user": _serialize_public_user(random_user),
    }), 200


@blueprint.route('/account/public-random-list', methods=['GET'])
def get_random_public_profile_list():
    limit = request.args.get('limit', default=10, type=int)
    if not limit or limit < 1:
        limit = 10
    limit = min(limit, 30)

    users = (
        User.query
        .filter(User.name.isnot(None))
        .filter(User.email.isnot(None))
        .filter(User.password.isnot(None))
        .order_by(db.func.rand())
        .limit(limit)
        .all()
    )

    return jsonify({
        "users": [_serialize_public_user(user) for user in users],
    }), 200


@blueprint.route('/account/public/<int:user_id>', methods=['GET'])
def get_public_profile(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    units = Unit.query.filter_by(user_id=user.id).order_by(Unit.id.desc()).all()

    return jsonify({
        "user": _serialize_public_user(user),
        "units": [_serialize_public_unit(unit) for unit in units],
    }), 200

@blueprint.route("/account/register", methods=["POST"])
def register():
    """Account register view."""
    data = request.get_json()
    
    if not data.get("email") or not data.get("password"):
        return jsonify({"error": "Name email and password are required"}), 400
    
    existing_user = User.query.filter_by(email=data["email"]).first()
    
    if existing_user:
        return jsonify({"error": "Email already exists"}), 400
    
    hashed_password = bcrypt.generate_password_hash(data["password"]).decode("utf-8")
    
    new_user = User(
        name=data["name"],
        email=data["email"],
        role=data.get("role") or "owner",
        password=hashed_password,
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({"message": "User registered successfully"}), 201


@blueprint.route("/account/protected", methods=["GET"])
@jwt_required()
def protected():
    """Protected route example."""
    return jsonify({"message": "Access granted"}), 200

@blueprint.route("/account/login", methods=["POST"])
def account_login():
    """Account login view."""
    data = request.get_json()
    
    if not data.get("email") or not data.get("password"):
        return jsonify({"error": "Email and password are required"}), 400
    
    user = User.query.filter_by(email=data["email"]).first()
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    if not bcrypt.check_password_hash(user.password, data["password"]):
        return jsonify({"error": "Invalid password"}), 401
    
    access_token = create_access_token(identity={"id": user.id, "email": user.email, "role": user.role})

    return jsonify({
        "message": "Login successful", 
        "access_token": access_token,
        "user": _serialize_user(user)
    }), 200


@blueprint.route("/account/me", methods=["GET"])
@jwt_required()
def account_me():
    from flask_jwt_extended import get_jwt_identity

    current_user_id = get_jwt_identity()["id"]
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "user": _serialize_user(user)
    }), 200


@blueprint.route('/account/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    from flask_jwt_extended import get_jwt_identity

    current_user_id = get_jwt_identity()["id"]
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json() if request.is_json else request.form

    if "address" in data:
        user.address = data.get("address") or None

    if "contact_no" in data:
        user.contact_no = data.get("contact_no") or None

    latitude = _parse_lat_lng(data.get('latitude')) if 'latitude' in data else user.latitude
    longitude = _parse_lat_lng(data.get('longitude')) if 'longitude' in data else user.longitude

    if 'latitude' in data and data.get('latitude') not in (None, "") and latitude is None:
        return jsonify({"error": "Latitude must be a valid number"}), 400

    if 'longitude' in data and data.get('longitude') not in (None, "") and longitude is None:
        return jsonify({"error": "Longitude must be a valid number"}), 400

    if latitude is not None and (latitude < -90 or latitude > 90):
        return jsonify({"error": "Latitude must be between -90 and 90"}), 400

    if longitude is not None and (longitude < -180 or longitude > 180):
        return jsonify({"error": "Longitude must be between -180 and 180"}), 400

    user.latitude = latitude
    user.longitude = longitude

    uploaded_photo = _save_profile_photo(request.files.get('profile_photo'))
    if uploaded_photo:
        _delete_profile_photo(user.profile_photo_url)
        user.profile_photo_url = uploaded_photo

    db.session.commit()

    return jsonify({
        "message": "Profile updated successfully",
        "user": _serialize_user(user),
    }), 200

@blueprint.route("/account/logout", methods=["POST"])
@jwt_required()
def account_logout():
    """Account logout view."""
    data = request.get_json()
    
    if not data.get("email"):
        return jsonify({"error": "Email is required"}), 400
    
    jti = get_jwt()["jti"]

    # Add the token to the blacklist
    blacklist.add(jti)
    
    return jsonify({"message": "Logout successful"}), 200