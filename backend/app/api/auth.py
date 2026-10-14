import base64
import hashlib
import hmac

from email_validator import EmailNotValidError, validate_email
from flask import Blueprint, current_app, jsonify
from flask_security import current_user, hash_password, verify_password

from app import db
from app.api import error, json_object, protected
from app.models import User

auth_bp = Blueprint("auth", __name__)


def verify_user_password(user, password):
    if verify_password(password, user.password):
        return True

    security_extension = current_app.extensions["security"]
    for legacy_salt in current_app.config.get("LEGACY_SECURITY_PASSWORD_SALTS", ()):
        legacy_hmac = hmac.new(
            legacy_salt.encode("utf-8"),
            password.encode("utf-8"),
            hashlib.sha512,
        ).digest()
        legacy_hash_input = base64.b64encode(legacy_hmac).decode("ascii")
        if security_extension.pwd_context.verify(legacy_hash_input, user.password):
            user.password = hash_password(password)
            db.session.commit()
            return True
    return False


def user_json(user):
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "bio": user.bio,
        "location": user.location,
        "roles": [role.name for role in user.roles],
    }


@auth_bp.post("/register")
def register():
    data = json_object()
    if data is None:
        return error("Request body must be a JSON object.", 400)
    raw_email = data.get("email", "")
    raw_name = data.get("name", "")
    try:
        email = validate_email(raw_email.strip(), check_deliverability=False).normalized.lower()
    except (EmailNotValidError, AttributeError):
        email = ""
    password = data.get("password", "")
    name = raw_name.strip() if isinstance(raw_name, str) else ""
    if not email or len(email) > 255:
        return error("Enter a valid email address.", 400)
    if not isinstance(password, str) or len(password) < 12 or len(password) > 256:
        return error("Password must contain between 12 and 256 characters.", 400)
    if len(name) < 2 or len(name) > 100:
        return error("Name must be between 2 and 100 characters.", 400)
    if User.query.filter_by(email=email).first():
        return error("An account with that email already exists.", 409)

    user = User(email=email, password=hash_password(password), name=name, active=True)
    from app.models import Role

    user_role = Role.query.filter_by(name="User").first()
    if user_role is None:
        return error("User role is not initialized. Run flask init-db.", 500)
    user.roles.append(user_role)
    db.session.add(user)
    db.session.commit()
    return jsonify({"user": user_json(user)}), 201


@auth_bp.post("/login")
def login():
    data = json_object()
    if data is None:
        return error("Request body must be a JSON object.", 400)
    raw_email = data.get("email", "")
    try:
        email = validate_email(raw_email.strip(), check_deliverability=False).normalized.lower()
    except (EmailNotValidError, AttributeError):
        email = ""
    password = data.get("password", "")
    user = User.query.filter_by(email=email).first()
    if (
        user is None
        or not user.active
        or not isinstance(password, str)
        or not verify_user_password(user, password)
    ):
        return error("Email or password is incorrect.", 401)
    return jsonify({"token": user.get_auth_token(), "user": user_json(user)})


@auth_bp.get("/me")
@protected
def me():
    return jsonify({"user": user_json(current_user)})
