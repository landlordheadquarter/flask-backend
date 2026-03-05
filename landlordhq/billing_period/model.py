from landlordhq.extensions import db


class BillingPeriod(db.Model):
    __tablename__ = 'billing_periods'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    from_date = db.Column(db.Date(), nullable=False)
    end_date = db.Column(db.Date(), nullable=False)
    monthly_rent_amount = db.Column(db.Float, nullable=False, default=0)
    electric_charge_amount = db.Column(db.Float, nullable=True)
    water_charge_amount = db.Column(db.Float, nullable=True)
    previous_electric_sub_meter_reading = db.Column(db.Float, nullable=True)
    current_electric_sub_meter_reading = db.Column(db.Float, nullable=True)
    used_electric_kwh = db.Column(db.Float, nullable=True)
    electric_rate_per_kwh = db.Column(db.Float, nullable=True)
    previous_water_sub_meter_reading = db.Column(db.Float, nullable=True)
    current_water_sub_meter_reading = db.Column(db.Float, nullable=True)
    used_water_cubic_meter = db.Column(db.Float, nullable=True)
    water_rate_per_cubic_meter = db.Column(db.Float, nullable=True)
    due_date = db.Column(db.Date(), nullable=True)
    late_fee_amount = db.Column(db.Float, nullable=False, default=0)
    total_amount = db.Column(db.Float, nullable=False, default=0)
    paid_amount = db.Column(db.Float, nullable=False, default=0)
    status = db.Column(db.String(30), nullable=False, default='issued')
    notes = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    user = db.relationship('User')
    tenant = db.relationship('Tenant')
    payments = db.relationship('Payment', back_populates='billing_period', cascade='all, delete-orphan')

    @property
    def outstanding_amount(self):
        return float(self.total_amount or 0) - float(self.paid_amount or 0)
