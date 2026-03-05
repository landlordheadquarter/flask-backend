"""Payment Controller."""
from datetime import date, datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from landlordhq.billing_period.model import BillingPeriod
from landlordhq.extensions import db
from landlordhq.payment.model import Payment
from landlordhq.tenant.model import Tenant
from landlordhq.utils import log_audit_action


blueprint = Blueprint('payment', __name__)


def _parse_non_negative_float(value):
    if value in (None, ''):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number < 0:
        return None
    return number


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except (TypeError, ValueError):
        return None


def _sync_billing_status(billing_period):
    total_amount = float(billing_period.total_amount or 0)
    paid_amount = float(billing_period.paid_amount or 0)
    outstanding = total_amount - paid_amount

    if outstanding <= 0:
        billing_period.status = 'paid'
        return

    if paid_amount > 0:
        billing_period.status = 'partially_paid'
        return

    if billing_period.due_date and billing_period.due_date < date.today():
        billing_period.status = 'overdue'
    else:
        billing_period.status = 'issued'


@blueprint.route('/payment', methods=['POST'])
@jwt_required()
def create_payment():
    data = request.get_json() or {}
    current_user_id = get_jwt_identity()['id']

    billing_period_id = data.get('billing_period_id')
    amount = _parse_non_negative_float(data.get('amount'))
    payment_date = _parse_date(data.get('payment_date'))

    if not billing_period_id:
        return {'error': 'billing_period_id is required'}, 400

    if amount is None or amount <= 0:
        return {'error': 'Valid payment amount is required'}, 400

    if payment_date is None:
        return {'error': 'Valid payment_date is required (YYYY-MM-DD)'}, 400

    billing_period = BillingPeriod.query.filter_by(
        id=billing_period_id,
        user_id=current_user_id,
    ).first()
    if not billing_period:
        return {'error': 'Billing period not found'}, 404

    outstanding_amount = float(billing_period.total_amount or 0) - float(billing_period.paid_amount or 0)
    if amount > outstanding_amount:
        return {'error': 'Payment amount cannot exceed outstanding amount'}, 400

    payment = Payment(
        user_id=current_user_id,
        tenant_id=billing_period.tenant_id,
        billing_period_id=billing_period.id,
        amount=amount,
        payment_date=payment_date,
        payment_method=data.get('payment_method'),
        reference_no=data.get('reference_no'),
        notes=data.get('notes'),
    )

    billing_period.paid_amount = float(billing_period.paid_amount or 0) + amount
    _sync_billing_status(billing_period)

    db.session.add(payment)
    db.session.commit()

    log_audit_action(current_user_id, 'create', 'payment', payment.id, f'Payment created for bill #{billing_period.id}')
    db.session.commit()

    return jsonify({
        'message': 'Payment recorded successfully',
        'payment': payment.to_dict(),
        'billing_period': {
            'id': billing_period.id,
            'status': billing_period.status,
            'paid_amount': billing_period.paid_amount,
            'outstanding_amount': billing_period.outstanding_amount,
        },
    }), 201


@blueprint.route('/payments', methods=['GET'])
@jwt_required()
def get_payments():
    current_user_id = get_jwt_identity()['id']
    tenant_id = request.args.get('tenant_id', type=int)
    billing_period_id = request.args.get('billing_period_id', type=int)

    query = Payment.query.filter_by(user_id=current_user_id)

    if tenant_id:
        query = query.filter_by(tenant_id=tenant_id)

    if billing_period_id:
        query = query.filter_by(billing_period_id=billing_period_id)

    payments = query.order_by(Payment.payment_date.desc(), Payment.id.desc()).all()
    return jsonify({'payments': [payment.to_dict() for payment in payments]}), 200


@blueprint.route('/tenant/<int:tenant_id>/ledger', methods=['GET'])
@jwt_required()
def get_tenant_ledger(tenant_id):
    current_user_id = get_jwt_identity()['id']

    tenant = Tenant.query.filter_by(id=tenant_id, user_id=current_user_id).first()
    if not tenant:
        return {'error': 'Tenant not found'}, 404

    billing_periods = (
        BillingPeriod.query
        .filter_by(user_id=current_user_id, tenant_id=tenant_id)
        .order_by(BillingPeriod.end_date.desc(), BillingPeriod.id.desc())
        .all()
    )

    payments = (
        Payment.query
        .filter_by(user_id=current_user_id, tenant_id=tenant_id)
        .order_by(Payment.payment_date.desc(), Payment.id.desc())
        .all()
    )

    total_billed = sum(float(period.total_amount or 0) for period in billing_periods)
    total_paid = sum(float(payment.amount or 0) for payment in payments)

    return jsonify({
        'tenant': {
            'id': tenant.id,
            'name': tenant.name,
            'address': tenant.address,
            'contact_no': tenant.contact_no,
        },
        'summary': {
            'total_billed': total_billed,
            'total_paid': total_paid,
            'outstanding_balance': total_billed - total_paid,
        },
        'billing_periods': [
            {
                'id': period.id,
                'from_date': period.from_date.isoformat() if period.from_date else None,
                'end_date': period.end_date.isoformat() if period.end_date else None,
                'status': period.status,
                'total_amount': period.total_amount,
                'paid_amount': period.paid_amount,
                'outstanding_amount': period.outstanding_amount,
            }
            for period in billing_periods
        ],
        'payments': [payment.to_dict() for payment in payments],
    }), 200
