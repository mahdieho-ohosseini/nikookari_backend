from tests.conftest import VALID_PASSWORD


def assert_error_response(response, expected_status: int | tuple[int, ...]):
    if isinstance(expected_status, int):
        expected_status = (expected_status,)

    assert response.status_code in expected_status

    body = response.json()
    assert isinstance(body, dict)
    assert "message" in body or "detail" in body or "errors" in body


# ============================================================
# Start Password Reset
# POST /api/v1/auth/password-reset/start
# ============================================================

def test_password_reset_start_success(client):
    response = client.post(
        "/api/v1/auth/password-reset/start",
        json={
            "email": "donor@gmail.com",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "message" in body


def test_password_reset_start_rejects_invalid_email(client):
    response = client.post(
        "/api/v1/auth/password-reset/start",
        json={
            "email": "bad-email",
        },
    )

    assert_error_response(response, 422)


def test_password_reset_start_rejects_missing_email(client):
    response = client.post(
        "/api/v1/auth/password-reset/start",
        json={},
    )

    assert_error_response(response, 422)


def test_password_reset_start_rate_limit(client):
    payload = {
        "email": "ratelimit-start@gmail.com",
    }

    for _ in range(3):
        response = client.post("/api/v1/auth/password-reset/start", json=payload)
        assert response.status_code == 200

    response = client.post("/api/v1/auth/password-reset/start", json=payload)

    assert_error_response(response, 429)


# ============================================================
# Verify Password Reset OTP
# POST /api/v1/auth/password-reset/verify
# ============================================================

def test_password_reset_verify_success(client):
    response = client.post(
        "/api/v1/auth/password-reset/verify",
        json={
            "email": "donor@gmail.com",
            "otp": "123456",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "message" in body


def test_password_reset_verify_rejects_invalid_email(client):
    response = client.post(
        "/api/v1/auth/password-reset/verify",
        json={
            "email": "bad-email",
            "otp": "123456",
        },
    )

    assert_error_response(response, 422)


def test_password_reset_verify_rejects_invalid_otp(client):
    response = client.post(
        "/api/v1/auth/password-reset/verify",
        json={
            "email": "donor@gmail.com",
            "otp": "0000",
        },
    )

    assert_error_response(response, 400)


def test_password_reset_verify_rejects_missing_otp(client):
    response = client.post(
        "/api/v1/auth/password-reset/verify",
        json={
            "email": "donor@gmail.com",
        },
    )

    assert_error_response(response, 422)


def test_password_reset_verify_rejects_too_short_otp(client):
    response = client.post(
        "/api/v1/auth/password-reset/verify",
        json={
            "email": "donor@gmail.com",
            "otp": "123",
        },
    )

    assert_error_response(response, 422)


def test_password_reset_verify_rate_limit(client):
    payload = {
        "email": "ratelimit-verify-reset@gmail.com",
        "otp": "123456",
    }

    for _ in range(5):
        response = client.post("/api/v1/auth/password-reset/verify", json=payload)
        assert response.status_code == 200

    response = client.post("/api/v1/auth/password-reset/verify", json=payload)

    assert_error_response(response, 429)


# ============================================================
# Complete Password Reset
# POST /api/v1/auth/password-reset/complete
# ============================================================

def test_password_reset_complete_success(client):
    response = client.post(
        "/api/v1/auth/password-reset/complete",
        json={
            "email": "donor@gmail.com",
            "new_password": VALID_PASSWORD,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "message" in body


def test_password_reset_complete_rejects_invalid_email(client):
    response = client.post(
        "/api/v1/auth/password-reset/complete",
        json={
            "email": "bad-email",
            "new_password": VALID_PASSWORD,
        },
    )

    assert_error_response(response, 422)


def test_password_reset_complete_rejects_short_password(client):
    response = client.post(
        "/api/v1/auth/password-reset/complete",
        json={
            "email": "donor@gmail.com",
            "new_password": "short",
        },
    )

    assert_error_response(response, 422)


def test_password_reset_complete_rejects_expired_session(client):
    response = client.post(
        "/api/v1/auth/password-reset/complete",
        json={
            "email": "expired@gmail.com",
            "new_password": VALID_PASSWORD,
        },
    )

    assert_error_response(response, 403)


def test_password_reset_complete_rejects_missing_user(client):
    response = client.post(
        "/api/v1/auth/password-reset/complete",
        json={
            "email": "missing@gmail.com",
            "new_password": VALID_PASSWORD,
        },
    )

    assert_error_response(response, 400)


def test_password_reset_complete_rejects_missing_password(client):
    response = client.post(
        "/api/v1/auth/password-reset/complete",
        json={
            "email": "donor@gmail.com",
        },
    )

    assert_error_response(response, 422)


def test_password_reset_complete_rate_limit(client):
    payload = {
        "email": "ratelimit-complete@gmail.com",
        "new_password": VALID_PASSWORD,
    }

    for _ in range(5):
        response = client.post("/api/v1/auth/password-reset/complete", json=payload)
        assert response.status_code == 200

    response = client.post("/api/v1/auth/password-reset/complete", json=payload)

    assert_error_response(response, 429)


# ============================================================
# Resend Password Reset OTP
# POST /api/v1/auth/password-reset/resend_otp
# ============================================================

def test_password_reset_resend_otp_success(client):
    response = client.post(
        "/api/v1/auth/password-reset/resend_otp",
        json={
            "email": "donor@gmail.com",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "message" in body


def test_password_reset_resend_otp_rejects_invalid_email(client):
    response = client.post(
        "/api/v1/auth/password-reset/resend_otp",
        json={
            "email": "bad-email",
        },
    )

    assert_error_response(response, 422)


def test_password_reset_resend_otp_rejects_service_cooldown(client):
    response = client.post(
        "/api/v1/auth/password-reset/resend_otp",
        json={
            "email": "wait@gmail.com",
        },
    )

    assert_error_response(response, 429)


def test_password_reset_resend_otp_rate_limit(client):
    payload = {
        "email": "ratelimit-resend-reset@gmail.com",
    }

    for _ in range(3):
        response = client.post("/api/v1/auth/password-reset/resend_otp", json=payload)
        assert response.status_code == 200

    response = client.post("/api/v1/auth/password-reset/resend_otp", json=payload)

    assert_error_response(response, 429)