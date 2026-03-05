from landlordhq.extensions import db

class Tenant(db.Model):
    __tablename__ = 'tenants'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    contact_no = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(255), nullable=True, unique=True)
    password = db.Column(db.String(255), nullable=True)
    emergency_contact = db.Column(db.String(100), nullable=True)
    emergency_contact_no = db.Column(db.String(15), nullable=True)
    due_date = db.Column(db.Integer, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)
    billing_day = db.Column(db.Integer, nullable=True)
    advance_payment = db.Column(db.Float, nullable=True)
    deposit_amount = db.Column(db.Float, nullable=True)
    unit_rent_amount = db.Column(db.Float, nullable=True)
    is_fixed_power_rate = db.Column(db.Boolean, nullable=False, default=False)
    monthly_fixed_power_rate = db.Column(db.Float, nullable=True)
    initial_electric_sub_meter_reading = db.Column(db.Float, nullable=True)
    is_fixed_water_rate = db.Column(db.Boolean, nullable=False, default=False)
    monthly_fixed_water_rate = db.Column(db.Float, nullable=True)
    initial_water_sub_meter_reading = db.Column(db.Float, nullable=True)
    terms = db.Column(db.String(255), nullable=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=True)
    status = db.Column(db.String(50), nullable=True, default='active')  # e.g., 'active', 'inactive', archived
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    user = db.relationship('User', back_populates='tenants')
    unit = db.relationship('Unit')
     # Relationship with MeterReading
    meter_readings = db.relationship('MeterReading', back_populates='tenant')