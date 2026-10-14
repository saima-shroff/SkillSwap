import pytest
from flask_security import SQLAlchemyUserDatastore, hash_password

from app import create_app, db
from app.models import Role, User


class TestConfig:
    TESTING = True
    SECRET_KEY = "test-secret"
    SECURITY_PASSWORD_SALT = "test-password-salt"
    LEGACY_SECURITY_PASSWORD_SALTS = ("development-only-change-me-too",)
    SECURITY_PASSWORD_HASH = "pbkdf2_sha512"
    SECURITY_TOKEN_AUTHENTICATION_HEADER = "Authorization"
    SECURITY_TOKEN_AUTHENTICATION_KEY = "auth_token"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_ORIGINS = "http://localhost:5173"
    AUTO_CREATE_DB = False


class AutoInitTestConfig(TestConfig):
    AUTO_CREATE_DB = True


@pytest.fixture()
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        datastore = SQLAlchemyUserDatastore(db, User, Role)
        datastore.create_role(name="User")
        datastore.create_role(name="Admin")
        db.session.commit()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def create_user(app, email, role="User", name=None):
    with app.app_context():
        user = User(email=email, password=hash_password("correct horse battery"), name=name or email.split("@")[0])
        user.roles.append(Role.query.filter_by(name=role).one())
        db.session.add(user)
        db.session.commit()
        return user.id


def auth_headers(client, email, password="correct horse battery"):
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.get_json()
    headers = {"Authorization": response.get_json()["token"]}
    assert client.get("/api/auth/me", headers=headers).status_code == 200
    return headers
