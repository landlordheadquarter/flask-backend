from landlordhq.extensions import db
from landlordhq.unit.tenant_unit_association import tenant_unit_association

class Unit(db.Model):
    __tablename__ = 'units'

    id = db.Column(db.Integer, primary_key=True)
    unit_no = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    occupants_count = db.Column(db.Integer, nullable=True)
    description = db.Column(db.String(255), nullable=True)
    electric_meter_no = db.Column(db.String(50), nullable=True)
    water_meter_no = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    user = db.relationship('User', back_populates='units')
    tenants = db.relationship('Tenant', secondary=tenant_unit_association)
