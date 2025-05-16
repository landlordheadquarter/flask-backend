from landlordhq.extensions import db
from landlordhq.constants import UTILITY_TYPES

class MeterReading(db.Model):
    __tablename__ = 'meter_readings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    utility_type = db.Column(db.String(50), nullable=False)  # Must match a value from UTILITY_TYPES
    reading_date = db.Column(db.DateTime, nullable=False)
    reading = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # Relationships
    user = db.relationship('User', back_populates='meter_readings')
    tenant = db.relationship('Tenant', back_populates='meter_readings')

    def __repr__(self):
        return f"<MeterReading id={self.id}, utility_type={self.utility_type}, tenant_id={self.tenant_id}>"