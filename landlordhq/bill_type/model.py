from landlordhq.extensions import db
from landlordhq.constants import UTILITY_TYPES

class BillType(db.Model):
    __tablename__ = 'bill_types'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    utility_type = db.Column(db.String(50), nullable=False)  # Must match a value from UTILITY_TYPES
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    def __repr__(self):
        return f"<BillType id={self.id}, name={self.name}, utility_type={self.utility_type}>"
    def __init__(self, name, utility_type):
        self.name = name
        self.utility_type = utility_type
    def __str__(self):
        return f"BillType(name={self.name}, utility_type={self.utility_type})"
    def __eq__(self, other):
        if not isinstance(other, BillType):
            return False
        return self.name == other.name and self.utility_type == other.utility_type
    def __ne__(self, other):
        return not self.__eq__(other)