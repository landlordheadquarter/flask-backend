from landlordhq.extensions import db


class WaterRate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rate = db.Column(db.Float, nullable=False)
    rate_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    user = db.relationship('User', back_populates='water_rates')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'rate': self.rate,
            'rate_date': self.rate_date.strftime('%Y-%m-%d') if self.rate_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
