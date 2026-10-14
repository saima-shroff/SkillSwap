from flask_security import hash_password, verify_password

from app import create_app, db
from app.models import Role, User
from .conftest import AutoInitTestConfig, auth_headers, create_user


def test_sqlite_startup_initializes_tables_and_roles(monkeypatch):
    monkeypatch.setenv("ADMIN_EMAIL", "seed-admin@example.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "seed-admin-password-long")
    app = create_app(AutoInitTestConfig)
    with app.app_context():
        assert Role.query.filter_by(name="User").one()
        assert Role.query.filter_by(name="Admin").one()
        admin = User.query.filter_by(email="seed-admin@example.com").one()
        assert "Admin" in [role.name for role in admin.roles]


def register(client, email, name, **extra):
    return client.post(
        "/api/auth/register",
        json={"email": email, "name": name, "password": "correct horse battery", **extra},
    )


def make_listing(client, headers, listing_type, name, category="Design"):
    response = client.post(
        "/api/listings",
        headers=headers,
        json={
            "listing_type": listing_type,
            "skill_name": name,
            "category": category,
            "description": "A thoughtful skill listing.",
            "proficiency_level": "Advanced",
        },
    )
    assert response.status_code == 201, response.get_json()
    return response.get_json()["listing"]


def test_registration_assigns_only_user_role_and_login_returns_token(app, client):
    response = register(client, "ada@example.com", "Ada", roles=["Admin"])
    assert response.status_code == 201
    assert response.get_json()["user"]["roles"] == ["User"]
    login = client.post(
        "/api/auth/login", json={"email": "ada@example.com", "password": "correct horse battery"}
    )
    assert login.status_code == 200
    assert login.get_json()["token"]


def test_existing_account_can_login_with_password_shorter_than_registration_minimum(app, client):
    create_user(app, "legacy@example.com")
    with app.app_context():
        user = User.query.filter_by(email="legacy@example.com").one()
        user.password = hash_password("short-pass")
        db.session.commit()
    response = client.post(
        "/api/auth/login",
        json={"email": "legacy@example.com", "password": "short-pass"},
    )
    assert response.status_code == 200
    assert response.get_json()["token"]


def test_login_migrates_hashes_from_the_old_development_password_salt(app, client):
    create_user(app, "old-salt@example.com")
    with app.app_context():
        user = User.query.filter_by(email="old-salt@example.com").one()
        app.config["SECURITY_PASSWORD_SALT"] = "development-only-change-me-too"
        user.password = hash_password("correct horse battery")
        old_hash = user.password
        app.config["SECURITY_PASSWORD_SALT"] = "test-password-salt"
        db.session.commit()

    response = client.post(
        "/api/auth/login",
        json={"email": "old-salt@example.com", "password": "correct horse battery"},
    )
    assert response.status_code == 200
    with app.app_context():
        user = User.query.filter_by(email="old-salt@example.com").one()
        assert user.password != old_hash
        assert verify_password("correct horse battery", user.password)


def test_listing_defaults_visibility_and_owner_isolation(app, client):
    register(client, "owner@example.com", "Owner")
    owner_headers = auth_headers(client, "owner@example.com")
    offer = make_listing(client, owner_headers, "Offer", "Illustration")
    want = make_listing(client, owner_headers, "Want", "Python")
    assert offer["is_approved"] is False
    assert offer["moderation_status"] == "pending"
    assert want["is_approved"] is True

    public = client.get("/api/listings").get_json()["listings"]
    assert [item["skill"]["name"] for item in public] == ["Python"]
    assert client.get(f"/api/listings/{offer['id']}").status_code == 404

    other_id = register(client, "other@example.com", "Other").get_json()["user"]["id"]
    other_headers = auth_headers(client, "other@example.com")
    assert client.put(
        f"/api/listings/{want['id']}", headers=other_headers, json={"description": "Changed"}
    ).status_code == 403
    assert client.delete(f"/api/listings/{want['id']}", headers=other_headers).status_code == 403
    assert other_id != offer["user_id"]
    assert client.get(f"/api/listings/{offer['id']}", headers=owner_headers).status_code == 200


def test_admin_moderation_and_protected_metrics(app, client):
    register(client, "member@example.com", "Member")
    member_headers = auth_headers(client, "member@example.com")
    offer = make_listing(client, member_headers, "Offer", "Ceramics")
    assert client.get("/api/admin/stats", headers=member_headers).status_code == 403

    create_user(app, "admin@example.com", role="Admin", name="Admin")
    admin_headers = auth_headers(client, "admin@example.com")
    assert client.get("/api/admin/stats").status_code == 401
    queue = client.get("/api/admin/listings/pending", headers=admin_headers).get_json()["listings"]
    assert [item["id"] for item in queue] == [offer["id"]]
    result = client.put(
        f"/api/admin/listings/{offer['id']}/approve",
        headers=admin_headers,
        json={"approved": True},
    )
    assert result.status_code == 200
    assert result.get_json()["listing"]["is_approved"] is True


def test_rejected_offer_stays_hidden_until_owner_resubmits(app, client):
    register(client, "member@example.com", "Member")
    member_headers = auth_headers(client, "member@example.com")
    offer = make_listing(client, member_headers, "Offer", "Woodworking")
    create_user(app, "admin@example.com", role="Admin")
    admin_headers = auth_headers(client, "admin@example.com")

    rejected = client.put(
        f"/api/admin/listings/{offer['id']}/approve",
        headers=admin_headers,
        json={"approved": False},
    )
    assert rejected.status_code == 200
    assert rejected.get_json()["listing"]["moderation_status"] == "rejected"
    assert client.get(f"/api/listings/{offer['id']}").status_code == 404
    assert client.put(
        f"/api/admin/listings/{offer['id']}/approve",
        headers=admin_headers,
        json={"approved": True},
    ).status_code == 409

    edited = client.put(
        f"/api/listings/{offer['id']}",
        headers=member_headers,
        json={"description": "Updated description."},
    )
    assert edited.status_code == 200
    assert edited.get_json()["listing"]["moderation_status"] == "rejected"

    resubmitted = client.put(
        f"/api/listings/{offer['id']}",
        headers=member_headers,
        json={"description": "Updated description.", "resubmit": True},
    )
    assert resubmitted.status_code == 200
    assert resubmitted.get_json()["listing"]["moderation_status"] == "pending"
    assert resubmitted.get_json()["listing"]["is_approved"] is False


def test_exchange_requires_both_completion_confirmations_and_allows_one_review(app, client):
    register(client, "sender@example.com", "Sender")
    register(client, "receiver@example.com", "Receiver")
    sender = auth_headers(client, "sender@example.com")
    receiver = auth_headers(client, "receiver@example.com")
    offered = make_listing(client, sender, "Offer", "Photography")
    wanted = make_listing(client, receiver, "Want", "Writing")

    create_user(app, "admin@example.com", role="Admin")
    admin = auth_headers(client, "admin@example.com")
    assert client.put(
        f"/api/admin/listings/{offered['id']}/approve", headers=admin, json={"approved": True}
    ).status_code == 200

    created = client.post(
        "/api/requests",
        headers=sender,
        json={"offered_listing_id": offered["id"], "requested_listing_id": wanted["id"]},
    )
    assert created.status_code == 201, created.get_json()
    exchange_id = created.get_json()["request"]["id"]
    assert client.put(
        f"/api/requests/{exchange_id}", headers=sender, json={"action": "accept"}
    ).status_code == 403
    assert client.put(
        f"/api/requests/{exchange_id}", headers=receiver, json={"action": "accept"}
    ).status_code == 200

    first = client.put(
        f"/api/requests/{exchange_id}", headers=sender, json={"action": "complete"}
    ).get_json()["request"]
    assert first["status"] == "Accepted"
    assert first["sender_completed"] is True
    assert client.post(
        "/api/reviews", headers=sender, json={"exchange_id": exchange_id, "rating": 5}
    ).status_code == 409

    complete = client.put(
        f"/api/requests/{exchange_id}", headers=receiver, json={"action": "complete"}
    ).get_json()["request"]
    assert complete["status"] == "Completed"
    review = client.post(
        "/api/reviews",
        headers=sender,
        json={"exchange_id": exchange_id, "rating": 5, "comment": "A lovely exchange."},
    )
    assert review.status_code == 201
    duplicate = client.post(
        "/api/reviews", headers=sender, json={"exchange_id": exchange_id, "rating": 4}
    )
    assert duplicate.status_code == 409
    assert client.get(f"/api/reviews?reviewee_id={created.get_json()['request']['receiver_id']}").status_code == 200


def test_non_object_json_is_rejected_with_explicit_client_error(client):
    assert client.post("/api/auth/register", json=["unexpected"]).status_code == 400
    assert client.post("/api/auth/login", json=["unexpected"]).status_code == 400


def test_cli_bootstrap_creates_admin_with_hashed_password(app, client):
    result = app.test_cli_runner().invoke(
        args=["bootstrap-admin"],
        env={
            "ADMIN_EMAIL": "root@example.com",
            "ADMIN_PASSWORD": "a-long-admin-password",
        },
    )
    assert result.exit_code == 0, result.output
    with app.app_context():
        user = User.query.filter_by(email="root@example.com").one()
        assert "Admin" in [role.name for role in user.roles]
        assert user.password != "a-long-admin-password"
    assert client.post(
        "/api/auth/login",
        json={"email": "root@example.com", "password": "a-long-admin-password"},
    ).status_code == 200
