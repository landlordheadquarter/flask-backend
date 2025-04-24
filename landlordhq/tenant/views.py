"""Renter views."""

from flask import Blueprint
from flask import request

blueprint = Blueprint("tenant", __name__)

@blueprint.route("/tenant", methods=["GET"])
def tenant():
    """tenant view."""
    return "tenant view"

@blueprint.route("/tenant/<string:tenant_id>", methods=["GET"])
def tenant_id(tenant_id):
    """tenant view with tenant_id."""
    return f"tenant view with tenant_id: {tenant_id}"