from landlordhq.extensions import db
from landlordhq.constants import UTILITY_TYPES
from landlordhq.tenant.model import Tenant
from landlordhq.user.model import User
from landlordhq.bill_type.model import BillType

class TenantBill(db.Model):
    
    __tablename__ = 'tenant_bills'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    period_type = db.Column(db.String(50), nullable=False)  # e.g., 'monthly', 'quarterly'
    bill_type_id = db.Column(db.Integer, db.ForeignKey('bill_types.id'), nullable=False)
    billing_day = db.Column(db.Integer, nullable=False)  # Stores the day of the month (1-31)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())        
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    # Relationships
    user = db.relationship('User', back_populates='tenant_bills')
    tenant = db.relationship('Tenant', back_populates='tenant_bills')
    bill_type = db.relationship('BillType', back_populates='tenant_bills')
    def __repr__(self):
        return f"<TenantBill id={self.id}, bill_amount={self.bill_amount}, tenant_id={self.tenant_id}>"
    def __init__(self, user_id, tenant_id, period_type, bill_type_id, due_date, bill_amount, bill_status):
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.period_type = period_type
        self.bill_type_id = bill_type_id
        self.due_date = due_date
        self.bill_amount = bill_amount
        self.bill_status = bill_status
    def __str__(self):
        return f"TenantBill(user_id={self.user_id}, tenant_id={self.tenant_id}, period_type={self.period_type}, bill_type_id={self.bill_type_id}, due_date={self.due_date}, bill_amount={self.bill_amount}, bill_status={self.bill_status})"