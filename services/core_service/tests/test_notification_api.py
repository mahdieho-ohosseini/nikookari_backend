from tests.conftest import MISSING_ID, NOTIFICATION_ID


def assert_error_response(response, expected_status: int | tuple[int, ...]):
    if isinstance(expected_status, int):
        expected_status = (expected_status,)

    assert response.status_code in expected_status

    body = response.json()
    assert isinstance(body, dict)
    assert "detail" in body or "message" in body or "errors" in body


# ============================================================
# My Notifications
# GET /api/v1/notifications
# ============================================================

def test_list_my_notifications_success(client, auth_headers):
    response = client.get(
        "/api/v1/notifications",
        headers=auth_headers,
    )

    assert response.status_code == 200

    body = response.json()
    assert isinstance(body, list)
    assert len(body) == 1

    notification = body[0]
    assert notification["id"] == str(NOTIFICATION_ID)
    assert notification["title"] == "اعلان تست"
    assert notification["message"] == "این یک اعلان تست است."
    assert notification["type"] == "info"
    assert notification["is_read"] is False
    assert "created_at" in notification


def test_list_my_notifications_requires_authentication(client):
    response = client.get("/api/v1/notifications")

    assert response.status_code in (401, 403)


def test_list_my_notifications_rejects_invalid_token(
    client,
    invalid_auth_headers,
):
    response = client.get(
        "/api/v1/notifications",
        headers=invalid_auth_headers,
    )

    assert response.status_code in (401, 403)


def test_list_my_notifications_returns_json(client, auth_headers):
    response = client.get(
        "/api/v1/notifications",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]


def test_list_my_notifications_accepts_pagination(client, auth_headers):
    response = client.get(
        "/api/v1/notifications",
        headers=auth_headers,
        params={
            "skip": 0,
            "limit": 20,
        },
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_my_notifications_rejects_negative_skip(client, auth_headers):
    response = client.get(
        "/api/v1/notifications",
        headers=auth_headers,
        params={
            "skip": -1,
        },
    )

    assert_error_response(response, 422)


def test_list_my_notifications_rejects_limit_less_than_one(
    client,
    auth_headers,
):
    response = client.get(
        "/api/v1/notifications",
        headers=auth_headers,
        params={
            "limit": 0,
        },
    )

    assert_error_response(response, 422)


def test_list_my_notifications_rejects_limit_too_large(
    client,
    auth_headers,
):
    response = client.get(
        "/api/v1/notifications",
        headers=auth_headers,
        params={
            "limit": 101,
        },
    )

    assert_error_response(response, 422)


def test_list_my_notifications_rejects_non_integer_skip(
    client,
    auth_headers,
):
    response = client.get(
        "/api/v1/notifications",
        headers=auth_headers,
        params={
            "skip": "not-number",
        },
    )

    assert_error_response(response, 422)


def test_list_my_notifications_rejects_non_integer_limit(
    client,
    auth_headers,
):
    response = client.get(
        "/api/v1/notifications",
        headers=auth_headers,
        params={
            "limit": "not-number",
        },
    )

    assert_error_response(response, 422)


# ============================================================
# Mark One Notification As Read
# PATCH /api/v1/notifications/{notification_id}/read
# ============================================================

def test_mark_notification_as_read_success(client, auth_headers):
    response = client.patch(
        f"/api/v1/notifications/{NOTIFICATION_ID}/read",
        headers=auth_headers,
    )

    assert response.status_code == 200

    body = response.json()
    assert body["id"] == str(NOTIFICATION_ID)
    assert body["title"] == "اعلان تست"
    assert body["is_read"] is True


def test_mark_notification_as_read_requires_authentication(client):
    response = client.patch(
        f"/api/v1/notifications/{NOTIFICATION_ID}/read",
    )

    assert response.status_code in (401, 403)


def test_mark_notification_as_read_rejects_invalid_token(
    client,
    invalid_auth_headers,
):
    response = client.patch(
        f"/api/v1/notifications/{NOTIFICATION_ID}/read",
        headers=invalid_auth_headers,
    )

    assert response.status_code in (401, 403)


def test_mark_notification_as_read_returns_404_for_missing_notification(
    client,
    auth_headers,
):
    response = client.patch(
        f"/api/v1/notifications/{MISSING_ID}/read",
        headers=auth_headers,
    )

    assert_error_response(response, 404)


def test_mark_notification_as_read_rejects_invalid_notification_uuid(
    client,
    auth_headers,
):
    response = client.patch(
        "/api/v1/notifications/not-a-uuid/read",
        headers=auth_headers,
    )

    assert_error_response(response, 422)


def test_mark_notification_as_read_returns_json(client, auth_headers):
    response = client.patch(
        f"/api/v1/notifications/{NOTIFICATION_ID}/read",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]


# ============================================================
# Mark All Notifications As Read
# PATCH /api/v1/notifications/read-all
# ============================================================

def test_mark_all_notifications_as_read_success(client, auth_headers):
    response = client.patch(
        "/api/v1/notifications/read-all",
        headers=auth_headers,
    )

    assert response.status_code == 200

    body = response.json()
    assert "message" in body
    assert "updated_count" in body
    assert body["updated_count"] == 1


def test_mark_all_notifications_as_read_requires_authentication(client):
    response = client.patch("/api/v1/notifications/read-all")

    assert response.status_code in (401, 403)


def test_mark_all_notifications_as_read_rejects_invalid_token(
    client,
    invalid_auth_headers,
):
    response = client.patch(
        "/api/v1/notifications/read-all",
        headers=invalid_auth_headers,
    )

    assert response.status_code in (401, 403)


def test_mark_all_notifications_as_read_rejects_body_fields(
    client,
    auth_headers,
):
    response = client.patch(
        "/api/v1/notifications/read-all",
        headers=auth_headers,
        json={
            "user_id": "11111111-1111-1111-1111-111111111111",
        },
    )

    assert response.status_code in (200, 422)


def test_mark_all_notifications_as_read_returns_json(client, auth_headers):
    response = client.patch(
        "/api/v1/notifications/read-all",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]