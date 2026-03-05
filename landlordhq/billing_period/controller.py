from calendar import monthrange
from datetime import date, datetime
import csv
from io import StringIO

from flask import Blueprint, jsonify, request, Response
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import and_, or_

from landlordhq.billing_period.model import BillingPeriod
from landlordhq.extensions import db
from landlordhq.notification.model import Notification
from landlordhq.power_rate.model import PowerRate
from landlordhq.tenant.model import Tenant
from landlordhq.utils import log_audit_action, require_roles
from landlordhq.water_rate.model import WaterRate


blueprint = Blueprint("billing_period", __name__)


def _serialize_billing_period(billing_period):
    paid_amount = float(billing_period.paid_amount or 0)
    total_amount = float(billing_period.total_amount or 0)
    return {
        "id": billing_period.id,
        "tenant_id": billing_period.tenant_id,
        "tenant_name": billing_period.tenant.name if billing_period.tenant else None,
        "tenant_address": billing_period.tenant.address if billing_period.tenant else None,
        "tenant_contact_no": billing_period.tenant.contact_no if billing_period.tenant else None,
        "from_date": str(billing_period.from_date),
        "end_date": str(billing_period.end_date),
        "monthly_rent_amount": billing_period.monthly_rent_amount,
        "electric_charge_amount": billing_period.electric_charge_amount,
        "water_charge_amount": billing_period.water_charge_amount,
        "previous_electric_sub_meter_reading": billing_period.previous_electric_sub_meter_reading,
        "previous_water_sub_meter_reading": billing_period.previous_water_sub_meter_reading,
        "current_electric_sub_meter_reading": billing_period.current_electric_sub_meter_reading,
        "current_water_sub_meter_reading": billing_period.current_water_sub_meter_reading,
        "used_electric_kwh": billing_period.used_electric_kwh,
        "used_water_cubic_meter": billing_period.used_water_cubic_meter,
        "electric_rate_per_kwh": billing_period.electric_rate_per_kwh,
        "water_rate_per_cubic_meter": billing_period.water_rate_per_cubic_meter,
        "due_date": billing_period.due_date.isoformat() if billing_period.due_date else None,
        "late_fee_amount": billing_period.late_fee_amount,
        "total_amount": billing_period.total_amount,
        "status": billing_period.status,
        "paid_amount": paid_amount,
        "outstanding_amount": total_amount - paid_amount,
        "notes": billing_period.notes,
        "created_at": billing_period.created_at.isoformat() if billing_period.created_at else None,
        "payments": [payment.to_dict() for payment in billing_period.payments],
    }


def _compute_due_date(end_date, due_day):
    if not due_day:
        return None
    last_day = monthrange(end_date.year, end_date.month)[1]
    safe_day = min(max(int(due_day), 1), last_day)
    return date(end_date.year, end_date.month, safe_day)


def _sync_billing_status(billing_period, today=None):
    today = today or date.today()
    total_amount = float(billing_period.total_amount or 0)
    paid_amount = float(billing_period.paid_amount or 0)
    outstanding = total_amount - paid_amount

    if outstanding <= 0:
        billing_period.status = 'paid'
        return

    if paid_amount > 0:
        billing_period.status = 'partially_paid'
        return

    if billing_period.due_date and billing_period.due_date < today:
        billing_period.status = 'overdue'
    else:
        billing_period.status = 'issued'


def _create_overdue_notification(user_id, tenant_id, billing_period_id, amount):
    existing = Notification.query.filter_by(
        user_id=user_id,
        tenant_id=tenant_id,
        billing_period_id=billing_period_id,
        notification_type='overdue',
    ).first()
    if existing:
        return

    notification = Notification(
        user_id=user_id,
        tenant_id=tenant_id,
        billing_period_id=billing_period_id,
        notification_type='overdue',
        title='Overdue Billing',
        message=f'Billing period #{billing_period_id} is overdue. Outstanding: {amount:.2f}',
    )
    db.session.add(notification)


@blueprint.route('/billing_period/history', methods=['GET'])
@jwt_required()
def get_all_billing_history():
    current_user_id = get_jwt_identity()["id"]

    tenant_id = request.args.get('tenant_id', type=int)
    status = request.args.get('status', type=str)
    from_date = _parse_date(request.args.get('from_date'))
    to_date = _parse_date(request.args.get('to_date'))
    q = (request.args.get('q') or '').strip().lower()

    query = BillingPeriod.query.filter(BillingPeriod.user_id == current_user_id)

    if tenant_id:
        query = query.filter(BillingPeriod.tenant_id == tenant_id)

    if status:
        query = query.filter(BillingPeriod.status == status)

    if from_date:
        query = query.filter(BillingPeriod.end_date >= from_date)

    if to_date:
        query = query.filter(BillingPeriod.end_date <= to_date)

    if q:
        query = query.join(Tenant, and_(Tenant.id == BillingPeriod.tenant_id, Tenant.user_id == current_user_id)).filter(
            or_(
                Tenant.name.ilike(f'%{q}%'),
                Tenant.address.ilike(f'%{q}%'),
            )
        )

    billing_periods = query.order_by(BillingPeriod.end_date.desc(), BillingPeriod.id.desc()).all()

    return jsonify({
        "billing_periods": [_serialize_billing_period(period) for period in billing_periods],
    }), 200


@blueprint.route('/billing_period/history/export-csv', methods=['GET'])
@jwt_required()
def export_billing_history_csv():
    current_user_id = get_jwt_identity()["id"]
    tenant_id = request.args.get('tenant_id', type=int)
    status = request.args.get('status', type=str)

    query = BillingPeriod.query.filter(BillingPeriod.user_id == current_user_id)
    if tenant_id:
        query = query.filter(BillingPeriod.tenant_id == tenant_id)
    if status:
        query = query.filter(BillingPeriod.status == status)

    billing_periods = query.order_by(BillingPeriod.end_date.desc(), BillingPeriod.id.desc()).all()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'bill_id', 'tenant_name', 'from_date', 'end_date', 'due_date', 'status',
        'monthly_rent_amount', 'electric_charge_amount', 'water_charge_amount',
        'late_fee_amount', 'total_amount', 'paid_amount', 'outstanding_amount',
    ])

    for bill in billing_periods:
        serialized = _serialize_billing_period(bill)
        writer.writerow([
            serialized['id'],
            serialized['tenant_name'] or '',
            serialized['from_date'],
            serialized['end_date'],
            serialized['due_date'] or '',
            serialized['status'],
            serialized['monthly_rent_amount'] or 0,
            serialized['electric_charge_amount'] or 0,
            serialized['water_charge_amount'] or 0,
            serialized['late_fee_amount'] or 0,
            serialized['total_amount'] or 0,
            serialized['paid_amount'] or 0,
            serialized['outstanding_amount'] or 0,
        ])

    csv_content = output.getvalue()
    output.close()

    return Response(
        csv_content,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=billing_history.csv'},
    )


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


def _get_effective_rate(rate_model, user_id, end_date):
    rate_entry = (
        rate_model.query
        .filter(rate_model.user_id == user_id)
        .filter(db.func.date(rate_model.rate_date) <= end_date)
        .order_by(rate_model.rate_date.desc(), rate_model.id.desc())
        .first()
    )

    if not rate_entry:
        rate_entry = (
            rate_model.query
            .filter(rate_model.user_id == user_id)
            .order_by(rate_model.rate_date.desc(), rate_model.id.desc())
            .first()
        )

    return float(rate_entry.rate) if rate_entry else None


def _get_latest_reading(tenant_id, user_id, utility):
    latest_billing = (
        BillingPeriod.query
        .filter_by(tenant_id=tenant_id, user_id=user_id)
        .order_by(BillingPeriod.end_date.desc(), BillingPeriod.id.desc())
        .first()
    )

    if not latest_billing:
        return None

    if utility == 'electric':
        return latest_billing.current_electric_sub_meter_reading

    return latest_billing.current_water_sub_meter_reading


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

    monthly_rent_amount = float(tenant.unit_rent_amount or 0)

    electric_charge_amount = None
    water_charge_amount = None
    previous_electric_sub_meter_reading = None
    previous_water_sub_meter_reading = None
    used_electric_kwh = None
    used_water_cubic_meter = None
    electric_rate_per_kwh = None
    water_rate_per_cubic_meter = None

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

        previous_electric_sub_meter_reading = _get_latest_reading(tenant.id, current_user_id, 'electric')
        if previous_electric_sub_meter_reading is None:
            previous_electric_sub_meter_reading = tenant.initial_electric_sub_meter_reading

        if previous_electric_sub_meter_reading is None:
            return {"error": "Previous electric sub meter reading is not configured"}, 400

        if current_electric_sub_meter_reading < float(previous_electric_sub_meter_reading):
            return {"error": "Current electric sub meter reading cannot be less than previous reading"}, 400

        used_electric_kwh = float(current_electric_sub_meter_reading) - float(previous_electric_sub_meter_reading)
        electric_rate_per_kwh = _get_effective_rate(PowerRate, current_user_id, end_date)

        if electric_rate_per_kwh is None:
            return {"error": "Power rate is not configured"}, 400

        electric_charge_amount = used_electric_kwh * electric_rate_per_kwh

    if tenant.is_fixed_water_rate:
        if tenant.monthly_fixed_water_rate is None:
            return {"error": "Tenant fixed water rate is not configured"}, 400
        water_charge_amount = float(tenant.monthly_fixed_water_rate)
        current_water_sub_meter_reading = None
    else:
        if current_water_sub_meter_reading is None:
            return {"error": "Current water sub meter reading is required for meter-based water billing"}, 400

        previous_water_sub_meter_reading = _get_latest_reading(tenant.id, current_user_id, 'water')
        if previous_water_sub_meter_reading is None:
            previous_water_sub_meter_reading = tenant.initial_water_sub_meter_reading

        if previous_water_sub_meter_reading is None:
            return {"error": "Previous water sub meter reading is not configured"}, 400

        if current_water_sub_meter_reading < float(previous_water_sub_meter_reading):
            return {"error": "Current water sub meter reading cannot be less than previous reading"}, 400

        used_water_cubic_meter = float(current_water_sub_meter_reading) - float(previous_water_sub_meter_reading)
        water_rate_per_cubic_meter = _get_effective_rate(WaterRate, current_user_id, end_date)

        if water_rate_per_cubic_meter is None:
            return {"error": "Water rate is not configured"}, 400

        water_charge_amount = used_water_cubic_meter * water_rate_per_cubic_meter

    total_amount = monthly_rent_amount + float(electric_charge_amount or 0) + float(water_charge_amount or 0)
    computed_due_date = _compute_due_date(end_date, tenant.due_date)

    billing_period = BillingPeriod(
        user_id=current_user_id,
        tenant_id=tenant.id,
        from_date=from_date,
        end_date=end_date,
        monthly_rent_amount=monthly_rent_amount,
        electric_charge_amount=electric_charge_amount,
        previous_electric_sub_meter_reading=previous_electric_sub_meter_reading,
        water_charge_amount=water_charge_amount,
        previous_water_sub_meter_reading=previous_water_sub_meter_reading,
        current_electric_sub_meter_reading=current_electric_sub_meter_reading,
        current_water_sub_meter_reading=current_water_sub_meter_reading,
        used_electric_kwh=used_electric_kwh,
        used_water_cubic_meter=used_water_cubic_meter,
        electric_rate_per_kwh=electric_rate_per_kwh,
        water_rate_per_cubic_meter=water_rate_per_cubic_meter,
        due_date=computed_due_date,
        late_fee_amount=0,
        total_amount=total_amount,
        paid_amount=0,
        status='issued',
        notes=data.get('notes'),
    )

    _sync_billing_status(billing_period)

    db.session.add(billing_period)
    db.session.commit()

    log_audit_action(current_user_id, 'create', 'billing_period', billing_period.id, f'Billing created for tenant #{tenant.id}')
    db.session.commit()

    return jsonify({
        "message": "Billing period created successfully",
        "billing_period": _serialize_billing_period(billing_period),
    }), 201


@blueprint.route('/billing_period/bulk-generate', methods=['POST'])
@jwt_required()
@require_roles('owner', 'admin')
def bulk_generate_billing_periods():
    data = request.get_json() or {}
    current_user_id = get_jwt_identity()["id"]

    from_date = _parse_date(data.get('from_date'))
    end_date = _parse_date(data.get('end_date'))
    notes = data.get('notes')

    if not from_date or not end_date:
        return {"error": "from_date and end_date are required"}, 400

    if from_date > end_date:
        return {"error": "from_date must be on or before end_date"}, 400

    current_readings = data.get('current_readings') or {}

    tenants = Tenant.query.filter_by(user_id=current_user_id, status='active').all()
    created = []
    skipped = []

    for tenant in tenants:
        duplicate = BillingPeriod.query.filter_by(
            user_id=current_user_id,
            tenant_id=tenant.id,
            from_date=from_date,
            end_date=end_date,
        ).first()
        if duplicate:
            skipped.append({'tenant_id': tenant.id, 'reason': 'Billing period already exists for range'})
            continue

        reading_payload = current_readings.get(str(tenant.id), {}) if isinstance(current_readings, dict) else {}
        payload = {
            'current_electric_sub_meter_reading': reading_payload.get('current_electric_sub_meter_reading'),
            'current_water_sub_meter_reading': reading_payload.get('current_water_sub_meter_reading'),
        }

        # Reuse existing create logic requirements per tenant
        request_data = {
            'tenant_id': tenant.id,
            'from_date': from_date.isoformat(),
            'end_date': end_date.isoformat(),
            'current_electric_sub_meter_reading': payload['current_electric_sub_meter_reading'],
            'current_water_sub_meter_reading': payload['current_water_sub_meter_reading'],
            'notes': notes,
        }

        tenant_create_response = _create_billing_period_for_bulk(current_user_id, tenant, request_data)
        if tenant_create_response.get('error'):
            skipped.append({'tenant_id': tenant.id, 'reason': tenant_create_response['error']})
            continue

        created.append({'tenant_id': tenant.id, 'billing_period_id': tenant_create_response['billing_period_id']})

    db.session.commit()

    log_audit_action(current_user_id, 'bulk_generate', 'billing_period', details=f'Created={len(created)} Skipped={len(skipped)}')
    db.session.commit()

    return jsonify({
        'message': 'Bulk billing generation completed',
        'created_count': len(created),
        'skipped_count': len(skipped),
        'created': created,
        'skipped': skipped,
    }), 200


def _create_billing_period_for_bulk(current_user_id, tenant, data):
    from_date = _parse_date(data.get('from_date'))
    end_date = _parse_date(data.get('end_date'))

    monthly_rent_amount = float(tenant.unit_rent_amount or 0)

    electric_charge_amount = None
    water_charge_amount = None
    previous_electric_sub_meter_reading = None
    previous_water_sub_meter_reading = None
    used_electric_kwh = None
    used_water_cubic_meter = None
    electric_rate_per_kwh = None
    water_rate_per_cubic_meter = None

    current_electric_sub_meter_reading = _parse_non_negative_float(data.get('current_electric_sub_meter_reading'))
    current_water_sub_meter_reading = _parse_non_negative_float(data.get('current_water_sub_meter_reading'))

    if tenant.is_fixed_power_rate:
        if tenant.monthly_fixed_power_rate is None:
            return {'error': 'Tenant fixed electric rate is not configured'}
        electric_charge_amount = float(tenant.monthly_fixed_power_rate)
        current_electric_sub_meter_reading = None
    else:
        if current_electric_sub_meter_reading is None:
            return {'error': 'Missing current electric sub meter reading'}

        previous_electric_sub_meter_reading = _get_latest_reading(tenant.id, current_user_id, 'electric')
        if previous_electric_sub_meter_reading is None:
            previous_electric_sub_meter_reading = tenant.initial_electric_sub_meter_reading
        if previous_electric_sub_meter_reading is None:
            return {'error': 'Previous electric sub meter reading is not configured'}
        if current_electric_sub_meter_reading < float(previous_electric_sub_meter_reading):
            return {'error': 'Current electric sub meter reading cannot be less than previous reading'}

        used_electric_kwh = float(current_electric_sub_meter_reading) - float(previous_electric_sub_meter_reading)
        electric_rate_per_kwh = _get_effective_rate(PowerRate, current_user_id, end_date)
        if electric_rate_per_kwh is None:
            return {'error': 'Power rate is not configured'}
        electric_charge_amount = used_electric_kwh * electric_rate_per_kwh

    if tenant.is_fixed_water_rate:
        if tenant.monthly_fixed_water_rate is None:
            return {'error': 'Tenant fixed water rate is not configured'}
        water_charge_amount = float(tenant.monthly_fixed_water_rate)
        current_water_sub_meter_reading = None
    else:
        if current_water_sub_meter_reading is None:
            return {'error': 'Missing current water sub meter reading'}

        previous_water_sub_meter_reading = _get_latest_reading(tenant.id, current_user_id, 'water')
        if previous_water_sub_meter_reading is None:
            previous_water_sub_meter_reading = tenant.initial_water_sub_meter_reading
        if previous_water_sub_meter_reading is None:
            return {'error': 'Previous water sub meter reading is not configured'}
        if current_water_sub_meter_reading < float(previous_water_sub_meter_reading):
            return {'error': 'Current water sub meter reading cannot be less than previous reading'}

        used_water_cubic_meter = float(current_water_sub_meter_reading) - float(previous_water_sub_meter_reading)
        water_rate_per_cubic_meter = _get_effective_rate(WaterRate, current_user_id, end_date)
        if water_rate_per_cubic_meter is None:
            return {'error': 'Water rate is not configured'}
        water_charge_amount = used_water_cubic_meter * water_rate_per_cubic_meter

    total_amount = monthly_rent_amount + float(electric_charge_amount or 0) + float(water_charge_amount or 0)
    computed_due_date = _compute_due_date(end_date, tenant.due_date)

    billing_period = BillingPeriod(
        user_id=current_user_id,
        tenant_id=tenant.id,
        from_date=from_date,
        end_date=end_date,
        monthly_rent_amount=monthly_rent_amount,
        electric_charge_amount=electric_charge_amount,
        previous_electric_sub_meter_reading=previous_electric_sub_meter_reading,
        water_charge_amount=water_charge_amount,
        previous_water_sub_meter_reading=previous_water_sub_meter_reading,
        current_electric_sub_meter_reading=current_electric_sub_meter_reading,
        current_water_sub_meter_reading=current_water_sub_meter_reading,
        used_electric_kwh=used_electric_kwh,
        used_water_cubic_meter=used_water_cubic_meter,
        electric_rate_per_kwh=electric_rate_per_kwh,
        water_rate_per_cubic_meter=water_rate_per_cubic_meter,
        due_date=computed_due_date,
        late_fee_amount=0,
        total_amount=total_amount,
        paid_amount=0,
        status='issued',
        notes=data.get('notes'),
    )

    _sync_billing_status(billing_period)
    db.session.add(billing_period)
    db.session.flush()

    return {'billing_period_id': billing_period.id}


@blueprint.route('/billing_period/refresh-overdue', methods=['POST'])
@jwt_required()
@require_roles('owner', 'admin')
def refresh_overdue_billing_periods():
    data = request.get_json() or {}
    current_user_id = get_jwt_identity()["id"]
    late_fee_rate = _parse_non_negative_float(data.get('late_fee_rate'))
    late_fee_rate = late_fee_rate if late_fee_rate is not None else 0

    billing_periods = BillingPeriod.query.filter_by(user_id=current_user_id).all()

    updated_count = 0
    for billing_period in billing_periods:
        previous_status = billing_period.status
        _sync_billing_status(billing_period)

        outstanding = float(billing_period.total_amount or 0) - float(billing_period.paid_amount or 0)
        if (
            billing_period.status == 'overdue'
            and late_fee_rate > 0
            and float(billing_period.late_fee_amount or 0) <= 0
            and outstanding > 0
        ):
            late_fee = round(outstanding * late_fee_rate, 2)
            billing_period.late_fee_amount = late_fee
            billing_period.total_amount = float(billing_period.total_amount or 0) + late_fee

        if billing_period.status == 'overdue':
            _create_overdue_notification(
                current_user_id,
                billing_period.tenant_id,
                billing_period.id,
                billing_period.outstanding_amount,
            )

        if billing_period.status != previous_status:
            updated_count += 1

    db.session.commit()

    log_audit_action(current_user_id, 'refresh_overdue', 'billing_period', details=f'Updated={updated_count}')
    db.session.commit()

    return jsonify({
        'message': 'Overdue statuses refreshed',
        'updated_count': updated_count,
    }), 200


@blueprint.route('/billing_period/<int:tenant_id>/previous-reading', methods=['GET'])
@jwt_required()
def get_previous_reading(tenant_id):
    current_user_id = get_jwt_identity()["id"]

    tenant = Tenant.query.filter_by(id=tenant_id, user_id=current_user_id).first()
    if not tenant:
        return {"error": "Tenant not found"}, 404

    latest_billing = (
        BillingPeriod.query
        .filter_by(tenant_id=tenant_id, user_id=current_user_id)
        .order_by(BillingPeriod.end_date.desc(), BillingPeriod.id.desc())
        .first()
    )

    previous_electric_sub_meter_reading = None
    previous_water_sub_meter_reading = None

    if latest_billing:
        previous_electric_sub_meter_reading = latest_billing.current_electric_sub_meter_reading
        previous_water_sub_meter_reading = latest_billing.current_water_sub_meter_reading

    if previous_electric_sub_meter_reading is None:
        previous_electric_sub_meter_reading = tenant.initial_electric_sub_meter_reading

    if previous_water_sub_meter_reading is None:
        previous_water_sub_meter_reading = tenant.initial_water_sub_meter_reading

    return jsonify({
        "previous_electric_sub_meter_reading": previous_electric_sub_meter_reading,
        "previous_water_sub_meter_reading": previous_water_sub_meter_reading,
    }), 200


@blueprint.route('/billing_period/<int:tenant_id>/history', methods=['GET'])
@jwt_required()
def get_billing_history(tenant_id):
    current_user_id = get_jwt_identity()["id"]

    tenant = Tenant.query.filter_by(id=tenant_id, user_id=current_user_id).first()
    if not tenant:
        return {"error": "Tenant not found"}, 404

    billing_periods = (
        BillingPeriod.query
        .filter_by(tenant_id=tenant_id, user_id=current_user_id)
        .order_by(BillingPeriod.end_date.desc(), BillingPeriod.id.desc())
        .all()
    )

    return jsonify({
        "tenant": {
            "id": tenant.id,
            "name": tenant.name,
            "address": tenant.address,
            "contact_no": tenant.contact_no,
            "unit_rent_amount": tenant.unit_rent_amount,
            "due_date": tenant.due_date,
        },
        "billing_periods": [_serialize_billing_period(period) for period in billing_periods],
    }), 200
