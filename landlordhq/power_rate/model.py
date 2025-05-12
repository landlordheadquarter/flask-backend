from landlordhq.extensions import db
from landlordhq.constants import UTILITY_TYPES
from landlordhq.tenant.model import Tenant
from landlordhq.user.model import User

class PowerRate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rate = db.Column(db.Float, nullable=False)
    rate_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    # Relationships
    user = db.relationship('User', back_populates='power_rates')
    