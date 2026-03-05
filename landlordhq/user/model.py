from landlordhq.extensions import db
from landlordhq.extensions import migrate
from landlordhq.extensions import bcrypt

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    role = db.Column(db.String(20), default='owner')
    password = db.Column(db.String(100))
    contact_no = db.Column(db.String(30), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    profile_photo_url = db.Column(db.String(255), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    # Relationship with Tenant
    tenants = db.relationship('Tenant', back_populates='user')
    units = db.relationship('Unit', back_populates='user')
    meter_readings = db.relationship('MeterReading', back_populates='user')
    power_rates = db.relationship('PowerRate', back_populates='user')
    water_rates = db.relationship('WaterRate', back_populates='user')
    payments = db.relationship('Payment', back_populates='user')
    notifications = db.relationship('Notification', back_populates='user')
    audit_logs = db.relationship('AuditLog', back_populates='user')
    
    def __init__(self, name, email, password=None, **kwargs):
        """Create a new user."""
        super().__init__(**kwargs)  # Pass any additional arguments to the parent class
        self.name = name
        self.email = email
        self.password = password
            
            
    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password)
        
        
    def check_password(self, password):
        """Check the password against the stored hash."""
        return bcrypt.check_password_hash(self.password, password)
    
    
    def __repr__(self):
        return f"<User {self.name}>".format(name = self.name)