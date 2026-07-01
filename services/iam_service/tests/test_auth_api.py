import pytest

from tests.conftest import VALID_PASSWORD


def assert_error_response(response, expected_status: int | tuple[int, ...]):
    if isinstance(expected_status, int):
        expected_status = (expected_status,)

    assert response.status_code in expected_status

    body = response.json()
    assert isinstance(body, dict)
    assert "message" in body or "detail" in body or "errors" in body


# ============================================================
# Register API
# POST /api/v1/auth/register
# ============================================================

def test_register_success(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Test User",
            "email": "newuser@gmail.com",
            "password": VALID_PASSWORD,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "message" in body


def test_register_rejects_invalid_email_format(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Test User",
            "email": "not-an-email",
            "password": VALID_PASSWORD,
        },
    )

    assert_error_response(response, 422)


@pytest.mark.parametrize(
    "email",
    [
        "user@example.com",
        "user@test.com",
        "user@fake.com",
        "user@mailinator.com",
    ],
)
def test_register_rejects_blocked_email_domains(client, email):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Test User",
            "email": email,
            "password": VALID_PASSWORD,
        },
    )

    assert_error_response(response, (400, 422))


def test_register_rejects_unknown_email_domain(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Test User",
            "email": "user@unknown-domain.dev",
            "password": VALID_PASSWORD,
        },
    )

    assert_error_response(response, (400, 422))


@pytest.mark.parametrize(
    "password",
    [
        "short",
        "lowercase123!",
        "UPPERCASE123!",
        "NoNumber!",
        "NoSpecial123",
    ],
)
def test_register_rejects_weak_passwords(client, password):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Test User",
            "email": "weakpass@gmail.com",
            "password": password,
        },
    )

    assert_error_response(response, (400, 422))


def test_register_rejects_missing_full_name(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "missingname@gmail.com",
            "password": VALID_PASSWORD,
        },
    )

    assert_error_response(response, 422)


def test_register_rejects_duplicate_user(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Existing User",
            "email": "exists@gmail.com",
            "password": VALID_PASSWORD,
        },
    )

    assert_error_response(response, 400)


def test_register_rate_limit(client):
    payload = {
        "full_name": "Rate Limit User",
        "email": "ratelimit-register@gmail.com",
        "password": VALID_PASSWORD,
    }

    for _ in range(5):
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 200

    response = client.post("/api/v1/auth/register", json=payload)

    assert_error_response(response, 429)


# ============================================================
# Verify OTP API
# POST /api/v1/auth/verify-otp
# ============================================================

def test_verify_otp_success(client):
    response = client.post(
        "/api/v1/auth/verify-otp",
        json={
            "email": "newuser@gmail.com",
            "otp": "123456",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["verified"] is True
    assert body["user"]["email"] == "newuser@gmail.com"


def test_verify_otp_rejects_invalid_email(client):
    response = client.post(
        "/api/v1/auth/verify-otp",
        json={
            "email": "bad-email",
            "otp": "123456",
        },
    )

    assert_error_response(response, 422)


@pytest.mark.parametrize("otp", ["0000", "bad", "999999"])
def test_verify_otp_rejects_invalid_or_expired_otp(client, otp):
    response = client.post(
        "/api/v1/auth/verify-otp",
        json={
            "email": "newuser@gmail.com",
            "otp": otp,
        },
    )

    assert_error_response(response, 400)


def test_verify_otp_rejects_expired_registration(client):
    response = client.post(
        "/api/v1/auth/verify-otp",
        json={
            "email": "expired@gmail.com",
            "otp": "123456",
        },
    )

    assert_error_response(response, 400)


def test_verify_otp_rejects_missing_otp(client):
    response = client.post(
        "/api/v1/auth/verify-otp",
        json={
            "email": "newuser@gmail.com",
        },
    )

    assert_error_response(response, 422)


def test_verify_otp_rate_limit(client):
    payload = {
        "email": "ratelimit-verify@gmail.com",
        "otp": "123456",
    }

    for _ in range(5):
        response = client.post("/api/v1/auth/verify-otp", json=payload)
        assert response.status_code == 201

    response = client.post("/api/v1/auth/verify-otp", json=payload)

    assert_error_response(response, 429)


# ============================================================
# Login API
# POST /api/v1/auth/login
# ============================================================

def test_login_success(client):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "donor@gmail.com",
            "password": VALID_PASSWORD,
        },
    )

    assert response.status_code == 200

    body = response.json()
    assert body["access_token"] == "access-token"
    assert body["refresh_token"] == "refresh-token"
    assert body["token_type"] == "bearer"
    assert body["role"] == "donor"


def test_login_rejects_invalid_email_format(client):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "bad-email",
            "password": VALID_PASSWORD,
        },
    )

    assert_error_response(response, 422)


def test_login_rejects_wrong_password(client):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "donor@gmail.com",
            "password": "Wrong@123",
        },
    )

    assert_error_response(response, 401)


def test_login_rejects_missing_user(client):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "missing@gmail.com",
            "password": VALID_PASSWORD,
        },
    )

    assert_error_response(response, 400)


def test_login_rejects_unverified_user(client):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "unverified@gmail.com",
            "password": VALID_PASSWORD,
        },
    )

    assert_error_response(response, 400)


def test_login_rejects_suspended_user(client):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "suspended@gmail.com",
            "password": VALID_PASSWORD,
        },
    )

    assert_error_response(response, 403)


def test_login_rejects_missing_password(client):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "donor@gmail.com",
        },
    )

    assert_error_response(response, 422)


def test_login_rate_limit(client):
    payload = {
        "email": "ratelimit-login@gmail.com",
        "password": VALID_PASSWORD,
    }

    for _ in range(5):
        response = client.post("/api/v1/auth/login", json=payload)
        assert response.status_code == 200

    response = client.post("/api/v1/auth/login", json=payload)

    assert_error_response(response, 429)


# ============================================================
# Resend OTP API
# POST /api/v1/auth/resend-otp
# ============================================================

def test_resend_otp_success(client):
    response = client.post(
        "/api/v1/auth/resend-otp",
        json={
            "email": "newuser@gmail.com",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "message" in body


def test_resend_otp_rejects_invalid_email(client):
    response = client.post(
        "/api/v1/auth/resend-otp",
        json={
            "email": "bad-email",
        },
    )

    assert_error_response(response, 422)


def test_resend_otp_rejects_missing_pending_registration(client):
    response = client.post(
        "/api/v1/auth/resend-otp",
        json={
            "email": "nopending@gmail.com",
        },
    )

    assert_error_response(response, 400)


def test_resend_otp_rejects_service_cooldown(client):
    response = client.post(
        "/api/v1/auth/resend-otp",
        json={
            "email": "cooldown@gmail.com",
        },
    )

    assert_error_response(response, 429)


def test_resend_otp_rate_limit(client):
    payload = {
        "email": "ratelimit-resend@gmail.com",
    }

    for _ in range(3):
        response = client.post("/api/v1/auth/resend-otp", json=payload)
        assert response.status_code == 200

    response = client.post("/api/v1/auth/resend-otp", json=payload)

    assert_error_response(response, 429)


# ============================================================
# Refresh Token API
# POST /api/v1/auth/refresh
# ============================================================

def test_refresh_token_success(client):
    response = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": "valid-refresh",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"] == "new-access-token"
    assert body["refresh_token"] == "new-refresh-token"
    assert body["token_type"] == "bearer"


def test_refresh_token_rejects_invalid_token(client):
    response = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": "invalid-refresh",
        },
    )

    assert_error_response(response, 401)


def test_refresh_token_rejects_revoked_token(client):
    response = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": "revoked-refresh",
        },
    )

    assert_error_response(response, 401)


def test_refresh_token_rejects_access_token_instead_of_refresh_token(client):
    response = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": "access-token",
        },
    )

    assert_error_response(response, 401)


def test_refresh_token_rejects_missing_refresh_token(client):
    response = client.post(
        "/api/v1/auth/refresh",
        json={},
    )

    assert_error_response(response, 422)


# ============================================================
# Complete Verifier Onboarding API
# POST /api/v1/auth/verifier/complete-onboarding
# ============================================================

def test_complete_verifier_onboarding_success(client):
    response = client.post(
        "/api/v1/auth/verifier/complete-onboarding",
        json={
            "token": "valid-token",
            "new_password": VALID_PASSWORD,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Account activated successfully. You can now login."


def test_complete_verifier_onboarding_rejects_invalid_token(client):
    response = client.post(
        "/api/v1/auth/verifier/complete-onboarding",
        json={
            "token": "bad-token",
            "new_password": VALID_PASSWORD,
        },
    )

    assert_error_response(response, 400)


def test_complete_verifier_onboarding_rejects_missing_token(client):
    response = client.post(
        "/api/v1/auth/verifier/complete-onboarding",
        json={
            "new_password": VALID_PASSWORD,
        },
    )

    assert_error_response(response, 422)


# ============================================================
# Me Token API
# GET /api/v1/auth/me-token
# ============================================================

def test_me_token_without_token_is_rejected(client):
    response = client.get("/api/v1/auth/me-token")

    assert response.status_code in (401, 403)