from flask import Blueprint, jsonify
from flask import request
from landlordhq.user.model import User
from landlordhq.extensions import db
from landlordhq.extensions import bcrypt

from flask_jwt_extended import create_access_token
from flask_jwt_extended import current_user
from flask_jwt_extended import jwt_required
from flask_jwt_extended import jwt_required, get_jwt

blacklist = set()

blueprint = Blueprint("account", __name__)

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
    
    access_token = create_access_token(identity={"id": user.id, "email": user.email})

    return jsonify({
        "message": "Login successful", 
        "access_token": access_token,
        "user": {"name": user.name, "email": user.email}
    }), 200

@jwt_required()
@blueprint.route("/account/logout", methods=["POST"])
def account_logout():
    """Account logout view."""
    data = request.get_json()
    
    if not data.get("email"):
        return jsonify({"error": "Email is required"}), 400
    
    jti = get_jwt()["jti"]

    # Add the token to the blacklist
    blacklist.add(jti)
    
    return jsonify({"message": "Logout successful"}), 200