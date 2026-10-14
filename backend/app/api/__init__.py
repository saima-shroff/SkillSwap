from functools import wraps

from flask import jsonify, request
from flask_security import auth_token_required, current_user


def protected(view):
    return auth_token_required(view)


def admin_required(view):
    @protected
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.has_role("Admin"):
            return jsonify({"error": "Admin access required."}), 403
        return view(*args, **kwargs)

    return wrapped


def error(message, status):
    return jsonify({"error": message}), status


def json_object():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None
