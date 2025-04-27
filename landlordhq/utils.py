"""Helper utilities and decorators for the LandlordHQ package."""
from datetime import datetime
    
def jwt_identity(jwt):
    """Extract the identity from a JWT token."""
    return jwt['sub'] if 'sub' in jwt else None

def identity_loader(identity):
    """Load the identity from the database."""
    return identity

def date_to_str(date):
    """Convert a date to a string in the format YYYY-MM-DD."""
    return date.strftime('%Y-%m-%d') if date else None

def str_to_date(date_str):
    """Convert a string in the format YYYY-MM-DD to a date."""

    return datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None