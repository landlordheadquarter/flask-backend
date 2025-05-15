from landlordhq.extensions import db

class Tenant(db.Model):
    __tablename__ = 'tenants'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    contact_no = db.Column(db.String(15), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)
    billing_day = db.Column(db.Integer, nullable=True)
    advance_payment = db.Column(db.Float, nullable=True)
    deposit_amount = db.Column(db.Float, nullable=True)
    terms = db.Column(db.String(255), nullable=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    user = db.relationship('User', back_populates='users')
    units = db.relationship('Unit', back_populates='units')
     # Relationship with MeterReading
    meter_readings = db.relationship('MeterReading', back_populates='tenants')