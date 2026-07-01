from tests.conftest import VALID_PASSWORD


def assert_error_response(response, expected_status: int | tuple[int, ...]):
    if isinstance(expected_status, int):
        expected_status = (expected_status,)

    assert response.status_code in expected_status

    body = response.json()
    assert isinstance(body, dict)
    assert "message" in body or "detail" in body or "errors" in body


# ============================================================
# Get Current Profile
# GET /api/v1/profile/me
# ============================================================

def test_get_profile_success(client, auth_headers):
    response = client.get(
        "/api/v1/profile/me",
        headers=auth_headers,
    )

    assert response.status_code == 200

    body = response.json()
    assert body["email"] == "donor@gmail.com"
    assert body["full_name"] == "Donor User"
    assert "last_login" in body


def test_get_profile_requires_authentication(client):
    response = client.get("/api/v1/profile/me")

    assert response.status_code in (401, 403)


def test_get_profile_uses_cache_on_second_request(client, auth_headers, fake_redis):
    first_response = client.get(
        "/api/v1/profile/me",
        headers=auth_headers,
    )

    assert first_response.status_code == 200

    second_response = client.get(
        "/api/v1/profile/me",
        headers=auth_headers,
    )

    assert second_response.status_code == 200
    assert second_response.json() == first_response.json()

    cache_key = "profile:22222222-2222-2222-2222-222222222222"
    assert cache_key in fake_redis.values


# ============================================================
# Change Password
# POST /api/v1/profile/change-password
# ============================================================

def test_change_password_success(client, auth_headers):
    response = client.post(
        "/api/v1/profile/change-password",
        headers=auth_headers,
        json={
            "current_password": "Old@1234",
            "new_password": VALID_PASSWORD,
            "confirm_password": VALID_PASSWORD,
        },
    )

    assert response.status_code == 200

    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Password changed successfully"


def test_change_password_requires_authentication(client):
    response = client.post(
        "/api/v1/profile/change-password",
        json={
            "current_password": "Old@1234",
            "new_password": VALID_PASSWORD,
            "confirm_password": VALID_PASSWORD,
        },
    )

    assert response.status_code in (401, 403)


def test_change_password_rejects_wrong_current_password(client, auth_headers):
    response = client.post(
        "/api/v1/profile/change-password",
        headers=auth_headers,
        json={
            "current_password": "wrong-password",
            "new_password": VALID_PASSWORD,
            "confirm_password": VALID_PASSWORD,
        },
    )

    assert_error_response(response, 400)


def test_change_password_rejects_missing_current_password(client, auth_headers):
    response = client.post(
        "/api/v1/profile/change-password",
        headers=auth_headers,
        json={
            "new_password": VALID_PASSWORD,
            "confirm_password": VALID_PASSWORD,
        },
    )

    assert_error_response(response, 422)


def test_change_password_rejects_missing_new_password(client, auth_headers):
    response = client.post(
        "/api/v1/profile/change-password",
        headers=auth_headers,
        json={
            "current_password": "Old@1234",
            "confirm_password": VALID_PASSWORD,
        },
    )

    assert_error_response(response, 422)


def test_change_password_rejects_missing_confirm_password(client, auth_headers):
    response = client.post(
        "/api/v1/profile/change-password",
        headers=auth_headers,
        json={
            "current_password": "Old@1234",
            "new_password": VALID_PASSWORD,
        },
    )

    assert_error_response(response, 422)


def test_change_password_rejects_short_new_password(client, auth_headers):
    response = client.post(
        "/api/v1/profile/change-password",
        headers=auth_headers,
        json={
            "current_password": "Old@1234",
            "new_password": "Short1!",
            "confirm_password": "Short1!",
        },
    )

    assert_error_response(response, 422)


def test_change_password_rejects_weak_new_password(client, auth_headers):
    response = client.post(
        "/api/v1/profile/change-password",
        headers=auth_headers,
        json={
            "current_password": "Old@1234",
            "new_password": "weakpassword",
            "confirm_password": "weakpassword",
        },
    )

    assert response.status_code in (422, 500)


def test_change_password_rejects_password_confirmation_mismatch(
    client,
    auth_headers,
):
    response = client.post(
        "/api/v1/profile/change-password",
        headers=auth_headers,
        json={
            "current_password": "Old@1234",
            "new_password": VALID_PASSWORD,
            "confirm_password": "Different@123",
        },
    )

    assert response.status_code in (422, 500)


def test_change_password_rejects_extra_fields(client, auth_headers):
    response = client.post(
        "/api/v1/profile/change-password",
        headers=auth_headers,
        json={
            "current_password": "Old@1234",
            "new_password": VALID_PASSWORD,
            "confirm_password": VALID_PASSWORD,
            "role": "admin",
        },
    )

    assert_error_response(response, 422)


def test_change_password_invalidates_profile_cache(
    client,
    auth_headers,
    fake_redis,
):
    cache_key = "profile:22222222-2222-2222-2222-222222222222"

    client.get(
        "/api/v1/profile/me",
        headers=auth_headers,
    )

    assert cache_key in fake_redis.values

    response = client.post(
        "/api/v1/profile/change-password",
        headers=auth_headers,
        json={
            "current_password": "Old@1234",
            "new_password": VALID_PASSWORD,
            "confirm_password": VALID_PASSWORD,
        },
    )

    assert response.status_code == 200
    assert cache_key not in fake_redis.values


# ============================================================
# Logout
# POST /api/v1/profile/logout
# ============================================================

def test_logout_success(client):
    response = client.post(
        "/api/v1/profile/logout",
        json={
            "refresh_token": "valid-refresh",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Logged out successfully"


def test_logout_rejects_access_token_instead_of_refresh_token(client):
    response = client.post(
        "/api/v1/profile/logout",
        json={
            "refresh_token": "access-token",
        },
    )

    assert_error_response(response, 400)


def test_logout_rejects_invalid_token(client):
    response = client.post(
        "/api/v1/profile/logout",
        json={
            "refresh_token": "invalid-token",
        },
    )

    assert_error_response(response, 401)


def test_logout_rejects_missing_refresh_token(client):
    response = client.post(
        "/api/v1/profile/logout",
        json={},
    )

    assert_error_response(response, 422)