import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "development-only-change-me")
    SECURITY_PASSWORD_SALT = os.environ.get(
        "SECURITY_PASSWORD_SALT", "development-only-change-me-too"
    )
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///skillswap.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECURITY_TOKEN_AUTHENTICATION_HEADER = "Authorization"
    SECURITY_TOKEN_AUTHENTICATION_KEY = "auth_token"
    SECURITY_PASSWORD_HASH = "pbkdf2_sha512"
    LEGACY_SECURITY_PASSWORD_SALTS = tuple(
        salt
        for salt in os.environ.get(
            "LEGACY_SECURITY_PASSWORD_SALTS", "development-only-change-me-too"
        ).split(",")
        if salt
    )
    SECURITY_REGISTERABLE = False
    SECURITY_SEND_REGISTER_EMAIL = False
    SECURITY_TOKEN_MAX_AGE = 60 * 60 * 24 * 7
    JSON_SORT_KEYS = False
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    AUTO_CREATE_DB = os.environ.get("AUTO_CREATE_DB", "true").lower() in {"1", "true", "yes"}
