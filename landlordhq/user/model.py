from landlordhq.extensions import db
from landlordhq.extensions import migrate
from landlordhq.extensions import bcrypt

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    password = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
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