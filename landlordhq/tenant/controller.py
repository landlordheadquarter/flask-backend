"""Tenant controller."""

from flask import Blueprint, jsonify
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from landlordhq.extensions import db
from landlordhq.tenant.model import Tenant
from landlordhq.user.model import User

blueprint = Blueprint("tenant", __name__)

@blueprint.route("/tenant", methods=["POST"])
@jwt_required()
def create_tenant():
    """create a new tenant."""
    data = request.get_json()
    
    if not data.get("name") or not data.get("address") or not data.get("contact_no"):
        return {"error": "Name, address, and contact number are required"}, 400
    
    current_user_id = get_jwt_identity()["id"]
    
    user = User.query.get(current_user_id)
    if not user:
        return {"error": "User not found"}, 404
    
    tenant = Tenant(
        name=data["name"],
        address=data["address"],
        contact_no=data["contact_no"],
        start_date=data.get("start_date"),
        user_id=current_user_id,
    )
    
    db.session.add(tenant)
    db.session.commit()
    
    return {"message": "Tenant created successfully"}, 201

@blueprint.route("/tenant/<int:tenant_id>", methods=["PUT"])
@jwt_required()
def update_tenant(tenant_id):
    """Update a tenant's details."""
    data = request.get_json()

    # Get the current logged-in user's ID
    current_user_id = get_jwt_identity()["id"]

    # Find the tenant by ID and ensure it belongs to the current user
    tenant = Tenant.query.filter_by(id=tenant_id, user_id=current_user_id).first()
    if not tenant:
        return {"error": "Tenant not found or does not belong to the current user"}, 404

    # Update tenant details
    if data.get("name"):
        tenant.name = data["name"]
    if data.get("address"):
        tenant.address = data["address"]
    if data.get("contact_no"):
        tenant.contact_no = data["contact_no"]
    if data.get("start_date"):
        tenant.start_date = data["start_date"]
    if data.get("end_date"):
        tenant.end_date = data["end_date"]

    # Commit changes to the database
    db.session.commit()

    return {"message": "Tenant updated successfully"}, 200

@blueprint.route("/tenants", methods=["GET"])
@jwt_required()
def get_tenants():
    """Get all tenants, for the current logged in user."""
    
    tenants = Tenant.query.filter_by(user_id=get_jwt_identity()["id"]).all()
    
    tenant_list = [
        {
            "id": tenant.id,
            "name": tenant.name,
            "address": tenant.address,
            "contact_no": tenant.contact_no,
            "start_date": tenant.start_date,
            "end_date": tenant.created_at,
        }
        for tenant in tenants
    ]
    
    return jsonify({"tenants": tenant_list}), 200


@blueprint.route("/tenant/<int:tenant_id>", methods=["PUT"])
@jwt_required()
def update_tenant(tenant_id):
    """Update a tenant's details."""
    data = request.get_json()

    # Get the current logged-in user's ID
    current_user_id = get_jwt_identity()["id"]

    # Find the tenant by ID and ensure it belongs to the current user
    tenant = Tenant.query.filter_by(id=tenant_id, user_id=current_user_id).first()
    if not tenant:
        return {"error": "Tenant not found or does not belong to the current user"}, 404

    # Update tenant details
    if data.get("name"):
        tenant.name = data["name"]
    if data.get("address"):
        tenant.address = data["address"]
    if data.get("contact_no"):
        tenant.contact_no = data["contact_no"]
    if data.get("start_date"):
        tenant.start_date = data["start_date"]
    if data.get("end_date"):
        tenant.end_date = data["end_date"]

    # Commit changes to the database
    db.session.commit()

    return {"message": "Tenant updated successfully"}, 200


@blueprint.route("/tenant/<int:tenant_id>", methods=["DELETE"])
@jwt_required()
def delete_tenant(tenant_id):
    """Delete a tenant."""
    # Get the current logged-in user's ID
    current_user_id = get_jwt_identity()["id"]

    # Find the tenant by ID and ensure it belongs to the current user
    tenant = Tenant.query.filter_by(id=tenant_id, user_id=current_user_id).first()
    if not tenant:
        return {"error": "Tenant not found or does not belong to the current user"}, 404

    # Delete the tenant
    db.session.delete(tenant)
    db.session.commit()

    return {"message": "Tenant deleted successfully"}, 200

@blueprint.route("/tenant/<int:tenant_id>/assign-unit/<int:unit_id>", methods=["POST"])
@jwt_required()
def assign_tenant_to_unit(tenant_id, unit_id):
    """Assign a tenant to a specific unit."""
    # Get the current logged-in user's ID
    current_user_id = get_jwt_identity()["id"]

    # Find the tenant and ensure it belongs to the current user
    tenant = Tenant.query.filter_by(id=tenant_id, user_id=current_user_id).first()
    if not tenant:
        return {"error": "Tenant not found or does not belong to the current user"}, 404

    # Find the unit and ensure it belongs to the current user
    unit = Unit.query.filter_by(id=unit_id, user_id=current_user_id).first()
    if not unit:
        return {"error": "Unit not found or does not belong to the current user"}, 404

    # Assign the tenant to the unit
    if unit not in tenant.units:
        tenant.units.append(unit)
        db.session.commit()
        return {"message": f"Tenant {tenant.name} assigned to unit {unit.unit_no} successfully"}, 200

    return {"message": f"Tenant {tenant.name} is already assigned to unit {unit.unit_no}"}, 200

@blueprint.route("/tenant/<int:tenant_id>/assign-unit/<int:unit_id>", methods=["POST"])
@jwt_required()
def assign_tenant_to_unit(tenant_id, unit_id):
    """Assign a tenant to a specific unit."""
    # Get the current logged-in user's ID
    current_user_id = get_jwt_identity()["id"]

    # Find the tenant and ensure it belongs to the current user
    tenant = Tenant.query.filter_by(id=tenant_id, user_id=current_user_id).first()
    if not tenant:
        return {"error": "Tenant not found or does not belong to the current user"}, 404

    # Find the unit and ensure it belongs to the current user
    unit = Unit.query.filter_by(id=unit_id, user_id=current_user_id).first()
    if not unit:
        return {"error": "Unit not found or does not belong to the current user"}, 404

    # Assign the tenant to the unit
    if unit not in tenant.units:
        tenant.units.append(unit)
        db.session.commit()
        return {"message": f"Tenant {tenant.name} assigned to unit {unit.unit_no} successfully"}, 200

    return {"message": f"Tenant {tenant.name} is already assigned to unit {unit.unit_no}"}, 200