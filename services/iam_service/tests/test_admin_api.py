from tests.conftest import (
    ADMIN_ID,
    MISSING_USER_ID,
    TARGET_USER_ID,
    set_current_user,
)


def assert_error_response(response, expected_status: int | tuple[int, ...]):
    if isinstance(expected_status, int):
        expected_status = (expected_status,)

    assert response.status_code in expected_status

    body = response.json()
    assert isinstance(body, dict)
    assert "message" in body or "detail" in body or "errors" in body


# ============================================================
# Admin: List Users
# GET /api/v1/admin/users
# ============================================================

def test_admin_list_users_success(client, auth_headers):
    set_current_user(role="admin", user_id=ADMIN_ID)

    response = client.get(
        "/api/v1/admin/users",
        headers=auth_headers,
    )

    assert response.status_code == 200

    body = response.json()
    assert isinstance(body, list)
    assert len(body) >= 1
    assert body[0]["email"] == "donor@gmail.com"


def test_admin_list_users_rejects_non_admin(client, auth_headers):
    set_current_user(role="donor")

    response = client.get(
        "/api/v1/admin/users",
        headers=auth_headers,
    )

    assert_error_response(response, 403)


# ============================================================
# Admin: Get User Detail
# GET /api/v1/admin/users/{user_id}
# ============================================================

def test_admin_get_user_detail_success(client, auth_headers):
    set_current_user(role="admin", user_id=ADMIN_ID)

    response = client.get(
        f"/api/v1/admin/users/{TARGET_USER_ID}",
        headers=auth_headers,
    )

    assert response.status_code == 200

    body = response.json()
    assert body["user_id"] == str(TARGET_USER_ID)
    assert body["email"] == "target@gmail.com"
    assert body["role"] == "donor"


def test_admin_get_user_detail_rejects_non_admin(client, auth_headers):
    set_current_user(role="donor")

    response = client.get(
        f"/api/v1/admin/users/{TARGET_USER_ID}",
        headers=auth_headers,
    )

    assert_error_response(response, 403)


def test_admin_get_user_detail_returns_404_for_missing_user(
    client,
    auth_headers,
):
    set_current_user(role="admin", user_id=ADMIN_ID)

    response = client.get(
        f"/api/v1/admin/users/{MISSING_USER_ID}",
        headers=auth_headers,
    )

    assert_error_response(response, 404)


def test_admin_get_user_detail_rejects_invalid_uuid(client, auth_headers):
    set_current_user(role="admin", user_id=ADMIN_ID)

    response = client.get(
        "/api/v1/admin/users/not-a-uuid",
        headers=auth_headers,
    )

    assert_error_response(response, 422)


# ============================================================
# Admin: Suspend User
# PATCH /api/v1/admin/users/{user_id}/suspend
# ============================================================

def test_admin_suspend_user_success(client, auth_headers):
    set_current_user(role="admin", user_id=ADMIN_ID)

    response = client.patch(
        f"/api/v1/admin/users/{TARGET_USER_ID}/suspend",
        headers=auth_headers,
    )

    assert response.status_code == 200

    body = response.json()
    assert body["user_id"] == str(TARGET_USER_ID)
    assert body["status"] == "suspended"


def test_admin_suspend_user_rejects_non_admin(client, auth_headers):
    set_current_user(role="donor")

    response = client.patch(
        f"/api/v1/admin/users/{TARGET_USER_ID}/suspend",
        headers=auth_headers,
    )

    assert_error_response(response, 403)


def test_admin_suspend_user_rejects_self_suspend(client, auth_headers):
    set_current_user(role="admin", user_id=ADMIN_ID)

    response = client.patch(
        f"/api/v1/admin/users/{ADMIN_ID}/suspend",
        headers=auth_headers,
    )

    assert_error_response(response, 400)


def test_admin_suspend_user_rejects_missing_user(client, auth_headers):
    set_current_user(role="admin", user_id=ADMIN_ID)

    response = client.patch(
        f"/api/v1/admin/users/{MISSING_USER_ID}/suspend",
        headers=auth_headers,
    )

    assert_error_response(response, 400)


# ============================================================
# Admin: Activate User
# PATCH /api/v1/admin/users/{user_id}/activate
# ============================================================

def test_admin_activate_user_success(client, auth_headers):
    set_current_user(role="admin", user_id=ADMIN_ID)

    response = client.patch(
        f"/api/v1/admin/users/{TARGET_USER_ID}/activate",
        headers=auth_headers,
    )

    assert response.status_code == 200

    body = response.json()
    assert body["user_id"] == str(TARGET_USER_ID)
    assert body["status"] == "active"


def test_admin_activate_user_rejects_non_admin(client, auth_headers):
    set_current_user(role="donor")

    response = client.patch(
        f"/api/v1/admin/users/{TARGET_USER_ID}/activate",
        headers=auth_headers,
    )

    assert_error_response(response, 403)


def test_admin_activate_user_rejects_missing_user(client, auth_headers):
    set_current_user(role="admin", user_id=ADMIN_ID)

    response = client.patch(
        f"/api/v1/admin/users/{MISSING_USER_ID}/activate",
        headers=auth_headers,
    )

    assert_error_response(response, 400)


# ============================================================
# Admin: List Roles
# GET /api/v1/admin/roles
# ============================================================

def test_admin_list_roles_success(client, auth_headers):
    set_current_user(role="admin", user_id=ADMIN_ID)

    response = client.get(
        "/api/v1/admin/roles",
        headers=auth_headers,
    )

    assert response.status_code == 200

    body = response.json()
    assert body["roles"] == ["donor", "charity", "verifier", "admin"]


def test_admin_list_roles_rejects_non_admin(client, auth_headers):
    set_current_user(role="donor")

    response = client.get(
        "/api/v1/admin/roles",
        headers=auth_headers,
    )

    assert_error_response(response, 403)


def test_admin_list_roles_uses_cache_on_second_request(
    client,
    auth_headers,
    fake_redis,
):
    set_current_user(role="admin", user_id=ADMIN_ID)

    first_response = client.get(
        "/api/v1/admin/roles",
        headers=auth_headers,
    )

    assert first_response.status_code == 200
    assert "admin:roles" in fake_redis.values

    second_response = client.get(
        "/api/v1/admin/roles",
        headers=auth_headers,
    )

    assert second_response.status_code == 200
    assert second_response.json() == first_response.json()


# ============================================================
# Admin: Update User Role
# PATCH /api/v1/admin/users/{user_id}/role
# ============================================================

def test_admin_update_user_role_success(client, auth_headers):
    set_current_user(role="admin", user_id=ADMIN_ID)

    response = client.patch(
        f"/api/v1/admin/users/{TARGET_USER_ID}/role",
        headers=auth_headers,
        json={
            "role": "verifier",
        },
    )

    assert response.status_code == 200

    body = response.json()
    assert body["user_id"] == str(TARGET_USER_ID)
    assert body["role"] == "verifier"


def test_admin_update_user_role_rejects_non_admin(client, auth_headers):
    set_current_user(role="donor")

    response = client.patch(
        f"/api/v1/admin/users/{TARGET_USER_ID}/role",
        headers=auth_headers,
        json={
            "role": "verifier",
        },
    )

    assert_error_response(response, 403)


def test_admin_update_user_role_rejects_invalid_role(client, auth_headers):
    set_current_user(role="admin", user_id=ADMIN_ID)

    response = client.patch(
        f"/api/v1/admin/users/{TARGET_USER_ID}/role",
        headers=auth_headers,
        json={
            "role": "super_admin",
        },
    )

    assert_error_response(response, 422)


def test_admin_update_user_role_rejects_missing_role(client, auth_headers):
    set_current_user(role="admin", user_id=ADMIN_ID)

    response = client.patch(
        f"/api/v1/admin/users/{TARGET_USER_ID}/role",
        headers=auth_headers,
        json={},
    )

    assert_error_response(response, 422)


def test_admin_update_user_role_rejects_self_role_change(
    client,
    auth_headers,
):
    set_current_user(role="admin", user_id=ADMIN_ID)

    response = client.patch(
        f"/api/v1/admin/users/{ADMIN_ID}/role",
        headers=auth_headers,
        json={
            "role": "donor",
        },
    )

    assert_error_response(response, 400)


def test_admin_update_user_role_rejects_missing_user(client, auth_headers):
    set_current_user(role="admin", user_id=ADMIN_ID)

    response = client.patch(
        f"/api/v1/admin/users/{MISSING_USER_ID}/role",
        headers=auth_headers,
        json={
            "role": "verifier",
        },
    )

    assert_error_response(response, 400)


# ============================================================
# Admin: Create Verifier
# POST /api/v1/admin/verifiers
# ============================================================

def test_admin_create_verifier_success(client, auth_headers):
    set_current_user(role="admin", user_id=ADMIN_ID)

    response = client.post(
        "/api/v1/admin/verifiers",
        headers=auth_headers,
        json={
            "full_name": "Verifier User",
            "email": "new.verifier@gmail.com",
        },
    )

    assert response.status_code == 201

    body = response.json()
    assert body["email"] == "new.verifier@gmail.com"
    assert body["full_name"] == "Verifier User"
    assert body["role"] == "verifier"
    assert body["is_verified"] is True


def test_admin_create_verifier_rejects_non_admin(client, auth_headers):
    set_current_user(role="donor")

    response = client.post(
        "/api/v1/admin/verifiers",
        headers=auth_headers,
        json={
            "full_name": "Verifier User",
            "email": "new.verifier@gmail.com",
        },
    )

    assert_error_response(response, 403)


def test_admin_create_verifier_rejects_duplicate_email(client, auth_headers):
    set_current_user(role="admin", user_id=ADMIN_ID)

    response = client.post(
        "/api/v1/admin/verifiers",
        headers=auth_headers,
        json={
            "full_name": "Existing Verifier",
            "email": "exists@gmail.com",
        },
    )

    assert_error_response(response, 400)


def test_admin_create_verifier_rejects_invalid_email(client, auth_headers):
    set_current_user(role="admin", user_id=ADMIN_ID)

    response = client.post(
        "/api/v1/admin/verifiers",
        headers=auth_headers,
        json={
            "full_name": "Verifier User",
            "email": "bad-email",
        },
    )

    assert_error_response(response, 422)


def test_admin_create_verifier_rejects_missing_full_name(
    client,
    auth_headers,
):
    set_current_user(role="admin", user_id=ADMIN_ID)

    response = client.post(
        "/api/v1/admin/verifiers",
        headers=auth_headers,
        json={
            "email": "new.verifier@gmail.com",
        },
    )

    assert_error_response(response, 422)


def test_admin_create_verifier_rejects_missing_email(client, auth_headers):
    set_current_user(role="admin", user_id=ADMIN_ID)

    response = client.post(
        "/api/v1/admin/verifiers",
        headers=auth_headers,
        json={
            "full_name": "Verifier User",
        },
    )

    assert_error_response(response, 422)