from landlordhq.extensions import db
from landlordhq.constants import UTILITY_TYPES
from landlordhq.tenant.model import Tenant
from landlordhq.user.model import User
from landlordhq.bill_type.model import BillType
from landlordhq.meter_reading.model import MeterReading

class PeriodicBill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    utility_type = db.Column(db.String(50), nullable=False)  # Must match a value from UTILITY_TYPES
    amount = db.Column(db.Float, nullable=False)
    bill_date = db.Column(db.DateTime, nullable=False)
    bill_due_date = db.Column(db.DateTime, nullable=False)
    bill_status = db.Column(db.String(50), nullable=False)  # e.g., 'paid', 'unpaid'
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    # Relationships
    user = db.relationship('User', back_populates='periodic_bills')
    tenant = db.relationship('Tenant', back_populates='periodic_bills')
    bill_type = db.relationship('BillType', back_populates='periodic_bills')
    meter_reading = db.relationship('MeterReading', back_populates='periodic_bills')
    def __repr__(self):
        return f"<PeriodicBill id={self.id}, amount={self.amount}, tenant_id={self.tenant_id}>" 
    def __init__(self, user_id, tenant_id, utility_type, amount, bill_date, bill_due_date, bill_status):
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.utility_type = utility_type
        self.amount = amount
        self.bill_date = bill_date
        self.bill_due_date = bill_due_date
        self.bill_status = bill_status
    def __str__(self):
        return f"PeriodicBill(user_id={self.user_id}, tenant_id={self.tenant_id}, utility_type={self.utility_type}, amount={self.amount}, bill_date={self.bill_date}, bill_due_date={self.bill_due_date}, bill_status={self.bill_status})"
    def __init__(self, user_id, tenant_id, utility_type, amount, bill_date, bill_due_date, bill_status):
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.utility_type = utility_type
        self.amount = amount
        self.bill_date = bill_date
        self.bill_due_date = bill_due_date
        self.bill_status = bill_status