from landlordhq.extensions import db
from landlordhq.unit.tenant_unit_association import tenant_unit_association

class Unit(db.Model):
    __tablename__ = 'units'

    id = db.Column(db.Integer, primary_key=True)
    unit_no = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    billing_day = db.Column(db.Integer, nullable=False)  # Stores the day of the month (1-31)
    unit_type = db.Column(db.String(50), nullable=True)  # e.g., 'apartment', 'house'
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    user = db.relationship('User', back_populates='users')
    tenants = db.relationship('Tenant', secondary=tenant_unit_association, back_populates='units')
