"""Unit view."""

from flask import Blueprint
from flask import request


blueprint = Blueprint("unit", __name__)

@blueprint.route("/unit", methods=["GET"])
def unit():
    """Unit view."""
    return "Unit view"

@blueprint.route("/unit/<string:unit_id>", methods=["GET"])
def unit_id(unit_id):
    """Unit view with unit_id."""
    return f"Unit view with unit_id: {unit_id}"