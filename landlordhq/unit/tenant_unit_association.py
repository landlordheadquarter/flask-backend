from landlordhq.extensions import db

tenant_unit_association = db.Table(
    'tenant_unit_association',
    db.Column('tenant_id', db.Integer, db.ForeignKey('tenants.id'), primary_key=True),
    db.Column('unit_id', db.Integer, db.ForeignKey('units.id'), primary_key=True)
)