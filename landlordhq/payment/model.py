from landlordhq.extensions import db


class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    billing_period_id = db.Column(db.Integer, db.ForeignKey('billing_periods.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.Date(), nullable=False)
    payment_method = db.Column(db.String(50), nullable=True)
    reference_no = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    user = db.relationship('User', back_populates='payments')
    tenant = db.relationship('Tenant')
    billing_period = db.relationship('BillingPeriod', back_populates='payments')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'tenant_id': self.tenant_id,
            'billing_period_id': self.billing_period_id,
            'amount': self.amount,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'payment_method': self.payment_method,
            'reference_no': self.reference_no,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
