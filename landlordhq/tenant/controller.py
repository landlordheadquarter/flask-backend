"""Tenant controller."""

from flask import Blueprint, jsonify
from flask import request
from sqlalchemy import or_
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from landlordhq.extensions import db
from landlordhq.extensions import bcrypt
from landlordhq.billing_period.model import BillingPeriod
from landlordhq.tenant.model import Tenant
from landlordhq.user.model import User
from landlordhq.unit.model import Unit
from landlordhq.utils import log_audit_action, require_roles

blueprint = Blueprint("tenant", __name__)


def _parse_due_date(value):
    if value is None or value == "":
        return None
    try:
        day = int(value)
    except (TypeError, ValueError):
        return None
    if day < 1 or day > 31:
        return None
    return day


def _parse_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in ("true", "1", "yes", "y", "on"):
            return True
        if normalized in ("false", "0", "no", "n", "off", ""):
            return False
    return default


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


def _serialize_tenant(tenant):
    return {
        "id": tenant.id,
        "name": tenant.name,
        "address": tenant.address,
        "unit_id": tenant.unit_id,
        "unit_rent_amount": tenant.unit_rent_amount,
        "due_date": tenant.due_date,
        "contact_no": tenant.contact_no,
        "email": tenant.email,
        "is_fixed_power_rate": tenant.is_fixed_power_rate,
        "monthly_fixed_power_rate": tenant.monthly_fixed_power_rate,
        "initial_electric_sub_meter_reading": tenant.initial_electric_sub_meter_reading,
        "is_fixed_water_rate": tenant.is_fixed_water_rate,
        "monthly_fixed_water_rate": tenant.monthly_fixed_water_rate,
        "initial_water_sub_meter_reading": tenant.initial_water_sub_meter_reading,
        "start_date": tenant.start_date,
        "end_date": tenant.created_at,
        "status": tenant.status,
    }


def _serialize_tenant_billing_period(period):
    paid_amount = float(period.paid_amount or 0)
    total_amount = float(period.total_amount or 0)
    return {
        "id": period.id,
        "from_date": str(period.from_date),
        "end_date": str(period.end_date),
        "monthly_rent_amount": period.monthly_rent_amount,
        "electric_charge_amount": period.electric_charge_amount,
        "water_charge_amount": period.water_charge_amount,
        "late_fee_amount": period.late_fee_amount,
        "total_amount": period.total_amount,
        "status": period.status,
        "paid_amount": paid_amount,
        "outstanding_amount": total_amount - paid_amount,
        "notes": period.notes,
        "due_date": period.due_date.isoformat() if period.due_date else None,
        "created_at": period.created_at.isoformat() if period.created_at else None,
    }

@blueprint.route("/tenant", methods=["POST"])
@jwt_required()
@require_roles('owner', 'admin')
def create_tenant():
    """create a new tenant."""
    data = request.get_json()
    
    if not data.get("name") or not data.get("address") or not data.get("contact_no"):
        return {"error": "Name, address, and contact number are required"}, 400

    tenant_email = (data.get("email") or "").strip().lower()
    tenant_password = data.get("password")
    if not tenant_email or not tenant_password:
        return {"error": "Tenant email and password are required"}, 400

    existing_tenant = Tenant.query.filter(Tenant.email == tenant_email).first()
    if existing_tenant:
        return {"error": "Tenant email already exists"}, 400

    parsed_due_date = _parse_due_date(data.get("due_date"))
    if data.get("due_date") not in (None, "") and parsed_due_date is None:
        return {"error": "Due date must be a day of month between 1 and 31"}, 400

    is_fixed_power_rate = _parse_bool(data.get("is_fixed_power_rate"), default=False)
    is_fixed_water_rate = _parse_bool(data.get("is_fixed_water_rate"), default=False)
    monthly_fixed_power_rate = _parse_non_negative_float(data.get("monthly_fixed_power_rate"))
    monthly_fixed_water_rate = _parse_non_negative_float(data.get("monthly_fixed_water_rate"))
    initial_electric_sub_meter_reading = _parse_non_negative_float(
        data.get("initial_electric_sub_meter_reading")
    )
    initial_water_sub_meter_reading = _parse_non_negative_float(
        data.get("initial_water_sub_meter_reading")
    )

    if is_fixed_power_rate and monthly_fixed_power_rate is None:
        return {
            "error": "Monthly fixed electric rate is required when electric bill is fixed"
        }, 400

    if is_fixed_water_rate and monthly_fixed_water_rate is None:
        return {
            "error": "Monthly fixed water rate is required when water bill is fixed"
        }, 400

    if (not is_fixed_power_rate) and initial_electric_sub_meter_reading is None:
        return {
            "error": "Initial electric sub meter reading is required when electric bill is meter-based"
        }, 400

    if (not is_fixed_water_rate) and initial_water_sub_meter_reading is None:
        return {
            "error": "Initial water sub meter reading is required when water bill is meter-based"
        }, 400
    
    current_user_id = get_jwt_identity()["id"]
    
    user = User.query.get(current_user_id)
    if not user:
        return {"error": "User not found"}, 404
    
    tenant = Tenant(
        name=data["name"],
        address=data["address"],
        contact_no=data["contact_no"],
        email=tenant_email,
        password=bcrypt.generate_password_hash(tenant_password).decode("utf-8"),
        unit_id=data.get("unit_id"),
        unit_rent_amount=data.get("unit_rent_amount"),
        due_date=parsed_due_date,
        is_fixed_power_rate=is_fixed_power_rate,
        monthly_fixed_power_rate=monthly_fixed_power_rate,
        initial_electric_sub_meter_reading=initial_electric_sub_meter_reading,
        is_fixed_water_rate=is_fixed_water_rate,
        monthly_fixed_water_rate=monthly_fixed_water_rate,
        initial_water_sub_meter_reading=initial_water_sub_meter_reading,
        start_date=data.get("start_date"),
        terms=data.get("terms"),
        billing_day=data.get("billing_day"),
        advance_payment=data.get("advance_payment"),
        deposit_amount=data.get("deposit_amount"),
        user_id=current_user_id,
    )
    
    db.session.add(tenant)
    db.session.commit()

    log_audit_action(current_user_id, 'create', 'tenant', tenant.id, f'Tenant created: {tenant.name}')
    db.session.commit()
    
    return {"message": "Tenant created successfully"}, 201

@blueprint.route("/tenants", methods=["GET"])
@jwt_required()
def get_tenants():
    """Get all tenants, for the current logged in user."""

    current_user_id = get_jwt_identity()["id"]
    query = Tenant.query.filter_by(user_id=current_user_id)

    keyword = request.args.get('q', '').strip()
    status = request.args.get('status', '').strip().lower()

    if keyword:
        like_query = f"%{keyword}%"
        query = query.filter(
            or_(
                Tenant.name.ilike(like_query),
                Tenant.address.ilike(like_query),
                Tenant.contact_no.ilike(like_query),
            )
        )

    if status:
        query = query.filter(Tenant.status == status)

    tenants = query.order_by(Tenant.id.desc()).all()
    
    tenant_list = [_serialize_tenant(tenant) for tenant in tenants]
    
    return jsonify({"tenants": tenant_list}), 200

@blueprint.route("/tenant/<int:tenant_id>/archive", methods=["PATCH"])
@jwt_required()
@require_roles('owner', 'admin')
def archive_tenant(tenant_id):
    """Archive a tenant."""
    # Get the current logged-in user's ID
    current_user_id = get_jwt_identity()["id"]

    # Find the tenant by ID and ensure it belongs to the current user
    tenant = Tenant.query.filter_by(id=tenant_id, user_id=current_user_id).first()
    if not tenant:
        return {"error": "Tenant not found or does not belong to the current user"}, 404

    # Archive the tenant
    tenant.status = "archived"
    db.session.commit()

    log_audit_action(current_user_id, 'archive', 'tenant', tenant.id, f'Tenant archived: {tenant.name}')
    db.session.commit()

    return {"message": "Tenant archived successfully"}, 200
@blueprint.route("/tenant/<int:tenant_id>/unarchive", methods=["PATCH"])
@jwt_required()
@require_roles('owner', 'admin')
def unarchive_tenant(tenant_id):
    """Unarchive a tenant."""
    # Get the current logged-in user's ID
    current_user_id = get_jwt_identity()["id"]

    # Find the tenant by ID and ensure it belongs to the current user
    tenant = Tenant.query.filter_by(id=tenant_id, user_id=current_user_id).first()
    if not tenant:
        return {"error": "Tenant not found or does not belong to the current user"}, 404

    # Unarchive the tenant
    tenant.status = "active"
    db.session.commit()

    log_audit_action(current_user_id, 'unarchive', 'tenant', tenant.id, f'Tenant unarchived: {tenant.name}')
    db.session.commit()

    return {"message": "Tenant unarchived successfully"}, 200


@blueprint.route("/tenant/<int:tenant_id>", methods=["PUT"])
@jwt_required()
@require_roles('owner', 'admin')
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
    if "email" in data:
        normalized_email = (data.get("email") or "").strip().lower()
        if not normalized_email:
            return {"error": "Tenant email is required"}, 400

        existing_tenant = Tenant.query.filter(
            Tenant.email == normalized_email,
            Tenant.id != tenant.id,
        ).first()
        if existing_tenant:
            return {"error": "Tenant email already exists"}, 400
        tenant.email = normalized_email

    if "password" in data and data.get("password"):
        tenant.password = bcrypt.generate_password_hash(data.get("password")).decode("utf-8")
    if data.get("start_date"):
        tenant.start_date = data["start_date"]
    if data.get("end_date"):
        tenant.end_date = data["end_date"]
    if data.get("billing_day"):
        tenant.billing_day = data["billing_day"]
    if data.get("advance_payment"):
        tenant.advance_payment = data["advance_payment"]
    if data.get("deposit_amount"):
        tenant.deposit_amount = data["deposit_amount"]
    if "unit_rent_amount" in data:
        tenant.unit_rent_amount = data.get("unit_rent_amount")
    if "due_date" in data:
        parsed_due_date = _parse_due_date(data.get("due_date"))
        if data.get("due_date") not in (None, "") and parsed_due_date is None:
            return {"error": "Due date must be a day of month between 1 and 31"}, 400
        tenant.due_date = parsed_due_date
    if "is_fixed_power_rate" in data:
        tenant.is_fixed_power_rate = _parse_bool(data.get("is_fixed_power_rate"), default=False)
    if "monthly_fixed_power_rate" in data:
        parsed_monthly_fixed_power_rate = _parse_non_negative_float(data.get("monthly_fixed_power_rate"))
        if data.get("monthly_fixed_power_rate") not in (None, "") and parsed_monthly_fixed_power_rate is None:
            return {"error": "Monthly fixed electric rate must be a non-negative number"}, 400
        tenant.monthly_fixed_power_rate = parsed_monthly_fixed_power_rate
    if "initial_electric_sub_meter_reading" in data:
        parsed_initial_electric = _parse_non_negative_float(data.get("initial_electric_sub_meter_reading"))
        if data.get("initial_electric_sub_meter_reading") not in (None, "") and parsed_initial_electric is None:
            return {"error": "Initial electric sub meter reading must be a non-negative number"}, 400
        tenant.initial_electric_sub_meter_reading = parsed_initial_electric
    if "is_fixed_water_rate" in data:
        tenant.is_fixed_water_rate = _parse_bool(data.get("is_fixed_water_rate"), default=False)
    if "monthly_fixed_water_rate" in data:
        parsed_monthly_fixed_water_rate = _parse_non_negative_float(data.get("monthly_fixed_water_rate"))
        if data.get("monthly_fixed_water_rate") not in (None, "") and parsed_monthly_fixed_water_rate is None:
            return {"error": "Monthly fixed water rate must be a non-negative number"}, 400
        tenant.monthly_fixed_water_rate = parsed_monthly_fixed_water_rate
    if "initial_water_sub_meter_reading" in data:
        parsed_initial_water = _parse_non_negative_float(data.get("initial_water_sub_meter_reading"))
        if data.get("initial_water_sub_meter_reading") not in (None, "") and parsed_initial_water is None:
            return {"error": "Initial water sub meter reading must be a non-negative number"}, 400
        tenant.initial_water_sub_meter_reading = parsed_initial_water
    if data.get("terms"):
        tenant.terms = data["terms"]
    if data.get("emergency_contact"):
        tenant.emergency_contact = data["emergency_contact"]
    if data.get("emergency_contact_no"):
        tenant.emergency_contact_no = data["emergency_contact_no"]
    if "unit_id" in data:
        tenant.unit_id = data.get("unit_id")
    if data.get('status'):
        tenant.status = data["status"]

    if tenant.is_fixed_power_rate and tenant.monthly_fixed_power_rate is None:
        return {
            "error": "Monthly fixed electric rate is required when electric bill is fixed"
        }, 400

    if tenant.is_fixed_water_rate and tenant.monthly_fixed_water_rate is None:
        return {
            "error": "Monthly fixed water rate is required when water bill is fixed"
        }, 400

    if (not tenant.is_fixed_power_rate) and tenant.initial_electric_sub_meter_reading is None:
        return {
            "error": "Initial electric sub meter reading is required when electric bill is meter-based"
        }, 400

    if (not tenant.is_fixed_water_rate) and tenant.initial_water_sub_meter_reading is None:
        return {
            "error": "Initial water sub meter reading is required when water bill is meter-based"
        }, 400

    # Commit changes to the database
    db.session.commit()

    log_audit_action(current_user_id, 'update', 'tenant', tenant.id, f'Tenant updated: {tenant.name}')
    db.session.commit()

    return {"message": "Tenant updated successfully"}, 200


@blueprint.route('/tenant/portal/login', methods=['POST'])
def tenant_portal_login():
    data = request.get_json() or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password')

    if not email or not password:
        return {"error": "Email and password are required"}, 400

    tenant = Tenant.query.filter(Tenant.email == email).first()
    if not tenant or not tenant.password:
        return {"error": "Tenant not found"}, 404

    if not bcrypt.check_password_hash(tenant.password, password):
        return {"error": "Invalid password"}, 401

    access_token = create_access_token(identity={
        "type": "tenant",
        "tenant_id": tenant.id,
        "user_id": tenant.user_id,
        "email": tenant.email,
    })

    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "tenant": {
            "id": tenant.id,
            "name": tenant.name,
            "email": tenant.email,
        },
    }), 200


@blueprint.route('/tenant/portal/billing-history', methods=['GET'])
@jwt_required()
def tenant_portal_billing_history():
    identity = get_jwt_identity() or {}
    if identity.get('type') != 'tenant' or not identity.get('tenant_id'):
        return {"error": "Tenant authorization required"}, 403

    tenant = Tenant.query.filter_by(id=identity.get('tenant_id')).first()
    if not tenant:
        return {"error": "Tenant not found"}, 404

    billing_periods = (
        BillingPeriod.query
        .filter_by(tenant_id=tenant.id)
        .order_by(BillingPeriod.end_date.desc(), BillingPeriod.id.desc())
        .all()
    )

    return jsonify({
        "tenant": {
            "id": tenant.id,
            "name": tenant.name,
            "email": tenant.email,
            "address": tenant.address,
            "contact_no": tenant.contact_no,
            "unit_rent_amount": tenant.unit_rent_amount,
            "due_date": tenant.due_date,
        },
        "billing_periods": [_serialize_tenant_billing_period(item) for item in billing_periods],
    }), 200


@blueprint.route("/tenant/<int:tenant_id>", methods=["DELETE"])
@jwt_required()
@require_roles('owner', 'admin')
def delete_tenant(tenant_id):
    """Delete a tenant."""
    # Get the current logged-in user's ID
    current_user_id = get_jwt_identity()["id"]

    # Find the tenant by ID and ensure it belongs to the current user
    tenant = Tenant.query.filter_by(id=tenant_id, user_id=current_user_id).first()
    if not tenant:
        return {"error": "Tenant not found or does not belong to the current user"}, 404

    # Delete the tenant
    tenant_name = tenant.name
    db.session.delete(tenant)
    db.session.commit()

    log_audit_action(current_user_id, 'delete', 'tenant', tenant_id, f'Tenant deleted: {tenant_name}')
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