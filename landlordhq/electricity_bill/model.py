from landlordhq.extensions import db
from landlordhq.constants import UTILITY_TYPES

class ElectricityBill(db.Model):
    __tablename__ = 'electricity_bills'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    previous_reading_id = db.Column(db.Integer, db.ForeignKey('meter_readings.id'), nullable=False)
    current_reading_id = db.Column(db.Integer, db.ForeignKey('meter_readings.id'), nullable=False)
    consumed_kilowatt = db.Column(db.Float, nullable=False)
    kilowatt_price = db.Column(db.Float, nullable=False)
    bill_date = db.Column(db.DateTime, nullable=False)
    bill_amount = db.Column(db.Float, nullable=False)
    bill_status = db.Column(db.String(50), nullable=False)  # e.g., 'paid', 'unpaid'
    bill_due_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    # Relationships
    user = db.relationship('User', back_populates='electricity_bills')
    tenant = db.relationship('Tenant', back_populates='electricity_bills')
    previous_reading = db.relationship('MeterReading', foreign_keys=[previous_reading_id])
    current_reading = db.relationship('MeterReading', foreign_keys=[current_reading_id])
    