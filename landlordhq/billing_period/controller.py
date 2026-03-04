from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from landlordhq.billing_period.model import BillingPeriod
from landlordhq.extensions import db
from landlordhq.tenant.model import Tenant


blueprint = Blueprint("billing_period", __name__)


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


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


@blueprint.route('/billing_period', methods=['POST'])
@jwt_required()
def create_billing_period():
    data = request.get_json() or {}

    tenant_id = data.get('tenant_id')
    from_date = _parse_date(data.get('from_date'))
    end_date = _parse_date(data.get('end_date'))

    if not tenant_id or not from_date or not end_date:
        return {"error": "tenant_id, from_date, and end_date are required"}, 400

    if from_date > end_date:
        return {"error": "from_date must be on or before end_date"}, 400

    current_user_id = get_jwt_identity()["id"]

    tenant = Tenant.query.filter_by(id=tenant_id, user_id=current_user_id).first()
    if not tenant:
        return {"error": "Tenant not found"}, 404

    monthly_rent_amount = _parse_non_negative_float(data.get('monthly_rent_amount'))
    monthly_rent_amount = monthly_rent_amount if monthly_rent_amount is not None else float(tenant.unit_rent_amount or 0)

    electric_charge_amount = None
    water_charge_amount = None

    current_electric_sub_meter_reading = _parse_non_negative_float(data.get('current_electric_sub_meter_reading'))
    current_water_sub_meter_reading = _parse_non_negative_float(data.get('current_water_sub_meter_reading'))

    if tenant.is_fixed_power_rate:
        if tenant.monthly_fixed_power_rate is None:
            return {"error": "Tenant fixed electric rate is not configured"}, 400
        electric_charge_amount = float(tenant.monthly_fixed_power_rate)
        current_electric_sub_meter_reading = None
    else:
        if current_electric_sub_meter_reading is None:
            return {"error": "Current electric sub meter reading is required for meter-based electric billing"}, 400

    if tenant.is_fixed_water_rate:
        if tenant.monthly_fixed_water_rate is None:
            return {"error": "Tenant fixed water rate is not configured"}, 400
        water_charge_amount = float(tenant.monthly_fixed_water_rate)
        current_water_sub_meter_reading = None
    else:
        if current_water_sub_meter_reading is None:
            return {"error": "Current water sub meter reading is required for meter-based water billing"}, 400

    total_amount = monthly_rent_amount + float(electric_charge_amount or 0) + float(water_charge_amount or 0)

    billing_period = BillingPeriod(
        user_id=current_user_id,
        tenant_id=tenant.id,
        from_date=from_date,
        end_date=end_date,
        monthly_rent_amount=monthly_rent_amount,
        electric_charge_amount=electric_charge_amount,
        water_charge_amount=water_charge_amount,
        current_electric_sub_meter_reading=current_electric_sub_meter_reading,
        current_water_sub_meter_reading=current_water_sub_meter_reading,
        total_amount=total_amount,
        notes=data.get('notes'),
    )

    db.session.add(billing_period)
    db.session.commit()

    return jsonify({
        "message": "Billing period created successfully",
        "billing_period": {
            "id": billing_period.id,
            "tenant_id": billing_period.tenant_id,
            "from_date": str(billing_period.from_date),
            "end_date": str(billing_period.end_date),
            "monthly_rent_amount": billing_period.monthly_rent_amount,
            "electric_charge_amount": billing_period.electric_charge_amount,
            "water_charge_amount": billing_period.water_charge_amount,
            "current_electric_sub_meter_reading": billing_period.current_electric_sub_meter_reading,
            "current_water_sub_meter_reading": billing_period.current_water_sub_meter_reading,
            "total_amount": billing_period.total_amount,
        },
    }), 201
