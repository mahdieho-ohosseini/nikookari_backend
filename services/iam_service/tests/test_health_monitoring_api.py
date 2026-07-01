def assert_error_response(response, expected_status: int | tuple[int, ...]):
    if isinstance(expected_status, int):
        expected_status = (expected_status,)

    assert response.status_code in expected_status

    body = response.json()
    assert isinstance(body, dict)
    assert "message" in body or "detail" in body or "errors" in body


# ============================================================
# Root
# GET /
# ============================================================

def test_root_endpoint_success(client):
    response = client.get("/")

    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "ok"
    assert "message" in body


# ============================================================
# OpenAPI
# GET /openapi.json
# ============================================================

def test_openapi_endpoint_success(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200

    body = response.json()
    assert "openapi" in body
    assert "paths" in body
    assert "components" in body


def test_openapi_has_bearer_auth_scheme(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200

    body = response.json()
    security_schemes = body["components"]["securitySchemes"]

    assert "BearerAuth" in security_schemes
    assert security_schemes["BearerAuth"]["type"] == "http"
    assert security_schemes["BearerAuth"]["scheme"] == "bearer"


# ============================================================
# Health
# GET /health
# ============================================================

def test_health_endpoint_success(client):
    response = client.get("/health")

    assert response.status_code == 200

    body = response.json()
    assert body["service"] == "iam-service"
    assert body["status"] == "ok"
    assert body["database"] == "connected"
    assert body["redis"] == "connected"
    assert "email_circuit_breaker" in body


def test_health_endpoint_returns_json(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]


# ============================================================
# Metrics
# GET /metrics
# ============================================================

def test_metrics_endpoint_success(client):
    response = client.get("/metrics")

    assert response.status_code == 200

    text = response.text

    assert "iam_service_uptime_seconds" in text
    assert "iam_http_requests_total" in text
    assert "iam_http_errors_total" in text
    assert "iam_http_request_duration_seconds" in text


def test_metrics_endpoint_returns_plain_text(client):
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]


def test_metrics_endpoint_does_not_require_authentication(client):
    response = client.get("/metrics")

    assert response.status_code == 200


# ============================================================
# Public endpoints should not require auth
# ============================================================

def test_public_root_does_not_require_authentication(client):
    response = client.get("/")

    assert response.status_code == 200


def test_public_health_does_not_require_authentication(client):
    response = client.get("/health")

    assert response.status_code == 200


def test_public_openapi_does_not_require_authentication(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200


# ============================================================
# Protected endpoint smoke checks
# ============================================================

def test_profile_me_without_authentication_is_rejected(client):
    response = client.get("/api/v1/profile/me")

    assert response.status_code in (401, 403)


def test_admin_users_without_authentication_is_rejected(client):
    response = client.get("/api/v1/admin/users")

    assert response.status_code in (401, 403)


def test_admin_roles_without_authentication_is_rejected(client):
    response = client.get("/api/v1/admin/roles")

    assert response.status_code in (401, 403)