import os

import click
from email_validator import EmailNotValidError, validate_email
from flask import Flask, jsonify
from flask_cors import CORS
from flask_security import Security, SQLAlchemyUserDatastore, hash_password
from flask_sqlalchemy import SQLAlchemy

from config import Config

db = SQLAlchemy()
security = Security()


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)
    db.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"].split(",")}})

    from app.models import Role, User

    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    security.init_app(app, user_datastore)
    security.unauthn_handler(
        lambda mechanisms=None, headers=None: (
            jsonify({"error": "Authentication required."}),
            401,
            headers or {},
        )
    )

    from app.api.admin import admin_bp
    from app.api.auth import auth_bp
    from app.api.listings import listings_bp
    from app.api.profile import profile_bp
    from app.api.requests import requests_bp
    from app.api.reviews import reviews_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(profile_bp, url_prefix="/api/profile")
    app.register_blueprint(listings_bp, url_prefix="/api/listings")
    app.register_blueprint(requests_bp, url_prefix="/api/requests")
    app.register_blueprint(reviews_bp, url_prefix="/api/reviews")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")

    def initialize_database():
        db.create_all()
        for name, description in (("User", "Standard member"), ("Admin", "Platform administrator")):
            if not user_datastore.find_role(name):
                user_datastore.create_role(name=name, description=description)
        db.session.commit()

    def seed_admin(reset_password=False):
        email = os.environ.get("ADMIN_EMAIL", "").strip()
        password = os.environ.get("ADMIN_PASSWORD", "")
        if not email and not password:
            return None
        if not email or not password:
            raise click.ClickException("Set both ADMIN_EMAIL and ADMIN_PASSWORD.")
        try:
            email = validate_email(email, check_deliverability=False).normalized.lower()
        except EmailNotValidError as exc:
            raise click.ClickException("ADMIN_EMAIL must be a valid email address.") from exc
        if len(password) < 12 or len(password) > 256:
            raise click.ClickException("ADMIN_PASSWORD must contain between 12 and 256 characters.")

        user = user_datastore.find_user(email=email)
        if user is None:
            user = user_datastore.create_user(
                email=email,
                password=hash_password(password),
                name="Admin",
                active=True,
            )
        elif reset_password:
            user.password = hash_password(password)
            user.active = True
        user_datastore.add_role_to_user(user, user_datastore.find_role("Admin"))
        db.session.commit()
        return user

    if app.config.get("AUTO_CREATE_DB") and app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite"):
        with app.app_context():
            initialize_database()
            seed_admin()

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    @app.cli.command("init-db")
    def init_db():
        """Create tables, standard roles, and the configured Admin account."""
        initialize_database()
        admin = seed_admin()
        click.echo("Database initialized.")
        if admin:
            click.echo(f"Admin account ready for {admin.email}.")

    @app.cli.command("bootstrap-admin")
    def bootstrap_admin():
        """Create or promote the Admin specified by ADMIN_EMAIL and ADMIN_PASSWORD."""
        import os

        email = os.environ.get("ADMIN_EMAIL", "").strip().lower()
        password = os.environ.get("ADMIN_PASSWORD", "")
        if not email or not password:
            raise click.ClickException("Set ADMIN_EMAIL and ADMIN_PASSWORD.")
        if len(password) < 12:
            raise click.ClickException("ADMIN_PASSWORD must contain at least 12 characters.")
        initialize_database()
        user = user_datastore.find_user(email=email)
        if user is None:
            user = user_datastore.create_user(email=email, password=hash_password(password), active=True)
        else:
            user.password = hash_password(password)
            user.active = True
        user_datastore.add_role_to_user(user, user_datastore.find_role("Admin"))
        db.session.commit()
        click.echo(f"Admin account ready for {email}.")

    return app
