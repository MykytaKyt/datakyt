from datetime import UTC, datetime, timedelta

import jwt
import pytest

from datakyt.models import Role
from datakyt.services import users
from datakyt.services.errors import AuthError
from datakyt.settings import get_settings
from tests.conftest import ADMIN_PASSWORD


def login(client, email, password):
    return client.post("/auth/login", data={"username": email, "password": password})


def test_login_returns_working_token(anon_client, admin):
    response = login(anon_client, "ADMIN@example.com", ADMIN_PASSWORD)
    assert response.status_code == 200
    token = response.json()["access_token"]
    me = anon_client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "admin@example.com"
    assert me.json()["role"] == "admin"
    assert "password_hash" not in me.json()


@pytest.mark.parametrize(
    ("email", "password"),
    [("admin@example.com", "wrong-password"), ("nobody@example.com", ADMIN_PASSWORD)],
)
def test_login_rejects_bad_credentials(anon_client, admin, email, password):
    response = login(anon_client, email, password)
    assert response.status_code == 401
    assert response.json()["detail"] == "incorrect e-mail or password"
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_inactive_user_cannot_log_in_or_use_token(client, anon_client, viewer, session):
    token = users.create_access_token(viewer)
    client.patch(f"/users/{viewer.id}", json={"is_active": False})
    assert login(anon_client, "viewer@example.com", "viewer-password").status_code == 401
    response = anon_client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_anonymous_requests_are_rejected(anon_client):
    assert anon_client.get("/employees").status_code == 401
    assert anon_client.post("/offices", json={"city": "X"}).status_code == 401


@pytest.mark.parametrize(
    "token",
    [
        "garbage",
        jwt.encode(
            {"sub": "1", "exp": datetime.now(UTC) + timedelta(hours=1)},
            "other-key-other-key-other-key-other-key",
        ),
        jwt.encode({"sub": "1"}, "test-secret-test-secret-test-secret"),
        jwt.encode(
            {"sub": "abc", "exp": datetime.now(UTC) + timedelta(hours=1)},
            "test-secret-test-secret-test-secret",
        ),
        jwt.encode(
            {"sub": "999999", "exp": datetime.now(UTC) + timedelta(hours=1)},
            "test-secret-test-secret-test-secret",
        ),
    ],
    ids=["malformed", "wrong-key", "no-exp", "bad-sub", "unknown-user"],
)
def test_invalid_tokens_are_rejected(anon_client, token):
    response = anon_client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_expired_token_is_rejected(anon_client, admin):
    token = users.create_access_token(admin, now=datetime.now(UTC) - timedelta(days=2))
    response = anon_client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_token_in_cookie_is_accepted(anon_client, admin):
    anon_client.cookies.set("datakyt_token", users.create_access_token(admin))
    assert anon_client.get("/auth/me").status_code == 200


def test_viewer_can_read_but_not_write(viewer_client, factory):
    office = factory.office()
    assert viewer_client.get("/offices").status_code == 200
    assert viewer_client.get(f"/offices/{office.id}").status_code == 200
    assert viewer_client.get("/reports/inventory").status_code == 200
    forbidden = [
        viewer_client.post("/offices", json={"city": "X"}),
        viewer_client.patch(f"/offices/{office.id}", json={"city": "Y"}),
        viewer_client.delete(f"/offices/{office.id}"),
        viewer_client.post("/equipment/1/issue", json={"employee_id": 1}),
        viewer_client.post("/equipment/1/return", json={}),
        viewer_client.post(
            "/assignments/licenses", json={"employee_id": 1, "software_license_id": 1}
        ),
        viewer_client.delete("/assignments/licenses/1"),
        viewer_client.post("/import/offices", files={"file": ("o.csv", b"city\nX\n")}),
        viewer_client.get("/users"),
        viewer_client.get("/audit-log"),
    ]
    for response in forbidden:
        assert response.status_code == 403, response.request.url
        assert response.json()["detail"] == "admin role required"


def test_every_mutating_route_requires_admin(app):
    """Guard against new routes that forget the admin dependency."""
    from fastapi.routing import APIRoute

    from datakyt.api.deps import require_role

    def dependency_names(route):
        stack = list(route.dependant.dependencies)
        while stack:
            dep = stack.pop()
            yield getattr(dep.call, "__qualname__", "")
            stack.extend(dep.dependencies)

    admin_check = require_role(Role.ADMIN).__qualname__
    for route in app.routes:
        if not isinstance(route, APIRoute) or route.path == "/auth/login":
            continue
        if route.methods & {"POST", "PATCH", "PUT", "DELETE"}:
            assert admin_check in set(dependency_names(route)), route.path


def test_user_management(client):
    created = client.post(
        "/users", json={"email": "New@Example.com", "password": "long-enough", "role": "viewer"}
    )
    assert created.status_code == 201
    user = created.json()
    assert user["email"] == "new@example.com"
    assert (
        client.post("/users", json={"email": "x@example.com", "password": "short"}).status_code
        == 422
    )
    assert (
        client.post(
            "/users", json={"email": "new@example.com", "password": "long-enough"}
        ).status_code
        == 409
    )
    promoted = client.patch(
        f"/users/{user['id']}", json={"role": "admin", "password": "new-password"}
    )
    assert promoted.json()["role"] == "admin"
    assert login(client, "new@example.com", "new-password").status_code == 200
    assert client.get("/users", params={"role": "admin"}).json()["total"] == 2


def test_password_helpers():
    hashed = users.hash_password("secret-password")
    assert users.verify_password("secret-password", hashed)
    assert not users.verify_password("other", hashed)
    assert not users.verify_password("x" * 100, hashed)
    assert not users.verify_password("secret-password", "not-a-bcrypt-hash")


def test_ensure_admin_only_runs_on_empty_table(session):
    created = users.ensure_admin(session, "Boss@Example.com", "password123")
    assert created is not None and created.role == Role.ADMIN
    assert created.email == "boss@example.com"
    assert users.ensure_admin(session, "other@example.com", "password123") is None
    assert users.authenticate(session, "boss@example.com", "password123").id == created.id
    with pytest.raises(AuthError):
        users.authenticate(session, "boss@example.com", "nope")


def test_token_contains_role_and_expiry(admin):
    payload = jwt.decode(
        users.create_access_token(admin),
        get_settings().resolved_jwt_secret(),
        algorithms=["HS256"],
    )
    assert payload["sub"] == str(admin.id)
    assert payload["role"] == "admin"
    assert payload["exp"] > payload["iat"]
