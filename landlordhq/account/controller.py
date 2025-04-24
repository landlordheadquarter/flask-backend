from flask import Blueprint
from flask import request

blueprint = Blueprint("account", __name__)

@blueprint.route("/account", methods=["GET"])
def account():
    """Account view."""
    return "Account view"

@blueprint.route("/account/<string:account_id>", methods=["GET"])
def account_id(arg):
    """Account view with account_id."""
    return f"Account view with account_id: {arg}"

@blueprint.route("/account/save", methods=["POST"])
def account_save():
    """Account save view."""
    data = request.get_json()
    return f"Account save view with data: {data}"

@blueprint.route("/account/delete", methods=["DELETE"])
def account_delete():
    """Account delete view."""
    data = request.get_json()
    return f"Account delete view with data: {data}"