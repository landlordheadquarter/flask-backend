from landlordhq.extensions import db
from landlordhq.constants import UTILITY_TYPES

class DueDate(db.Model):
    __tablename__ = 'due_dates'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # Relationships
    user = db.relationship('User', back_populates='due_dates')
    tenant = db.relationship('Tenant', back_populates='due_dates')

    def __repr__(self):
        return f"<DueDate id={self.id}, due_date={self.due_date}, tenant_id={self.tenant_id}>"
    def __init__(self, user_id, tenant_id, due_date):
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.due_date = due_date