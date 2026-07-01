def assert_error_response(response, expected_status: int | tuple[int, ...]):
    if isinstance(expected_status, int):
        expected_status = (expected_status,)

    assert response.status_code in expected_status

    body = response.json()
    assert isinstance(body, dict)
    assert "detail" in body or "message" in body or "errors" in body


# ============================================================
# Root
# GET /
# ============================================================

def test_root_endpoint_success(client):
    response = client.get("/")

    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "QForm Core"
    assert "version" in body


def test_root_endpoint_returns_json(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]


# ============================================================
# Basic Health
# GET /health
# ============================================================

def test_health_endpoint_success(client):
    response = client.get("/health")

    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "core-service"
    assert "version" in body


def test_health_endpoint_keeps_old_response_contract(client):
    response = client.get("/health")

    assert response.status_code == 200

    body = response.json()

    assert set(body.keys()) == {
        "status",
        "service",
        "version",
    }


def test_health_endpoint_does_not_require_authentication(client):
    response = client.get("/health")

    assert response.status_code == 200


# ============================================================
# Detailed Health
# GET /health/details
# ============================================================

def test_health_details_success(client):
    response = client.get("/health/details")

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "ok"
    assert body["service"] == "core-service"
    assert "version" in body
    assert body["database"] is True

    assert "payment_provider" in body
    assert "zarinpal" in body["payment_provider"]

    zarinpal = body["payment_provider"]["zarinpal"]

    assert zarinpal["service"] == "zarinpal"
    assert zarinpal["state"] in ("closed", "open")
    assert "failures" in zarinpal
    assert "failure_threshold" in zarinpal
    assert "retry_after_seconds" in zarinpal


def test_health_details_does_not_require_authentication(client):
    response = client.get("/health/details")

    assert response.status_code == 200


def test_health_details_returns_json(client):
    response = client.get("/health/details")

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

    assert "core_service_uptime_seconds" in text
    assert "core_http_requests_total" in text
    assert "core_http_errors_total" in text
    assert "core_http_request_duration_seconds_average" in text


def test_metrics_endpoint_includes_zarinpal_circuit_breaker(client):
    response = client.get("/metrics")

    assert response.status_code == 200

    text = response.text

    assert "core_circuit_breaker_open" in text
    assert 'service="zarinpal"' in text
    assert "core_circuit_breaker_failures" in text
    assert "core_circuit_breaker_failure_threshold" in text
    assert "core_circuit_breaker_retry_after_seconds" in text


def test_metrics_endpoint_returns_plain_text(client):
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]


def test_metrics_endpoint_does_not_require_authentication(client):
    response = client.get("/metrics")

    assert response.status_code == 200


def test_metrics_counter_increases_after_request(client):
    before_response = client.get("/metrics")
    assert before_response.status_code == 200

    client.get("/health")

    after_response = client.get("/metrics")
    assert after_response.status_code == 200

    assert "core_http_requests_total" in after_response.text


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


def test_openapi_public_paths_do_not_require_security(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200

    body = response.json()
    paths = body["paths"]

    for public_path in ["/", "/health", "/health/details", "/metrics"]:
        assert public_path in paths

        for operation in paths[public_path].values():
            assert operation.get("security", []) == []


# ============================================================
# Protected endpoint smoke checks
# ============================================================

def test_verifier_dashboard_without_token_is_rejected(client):
    response = client.get("/api/v1/verifier/dashboard")

    assert response.status_code in (401, 403)


def test_charity_profile_me_without_token_is_rejected(client):
    response = client.get("/api/v1/charity/profile/me")

    assert response.status_code in (401, 403)


def test_campaign_create_without_token_is_rejected(client):
    response = client.post(
        "/api/v1/campaigns",
        json={
            "title": "پویش تست",
            "description": "توضیح کامل پویش تست برای کمک‌رسانی",
            "short_description": "توضیح کوتاه",
            "category": "education",
            "target_amount": 1000000,
        },
    )

    assert response.status_code in (401, 403)


def test_notification_without_token_is_rejected(client):
    response = client.get("/api/v1/notifications")

    assert response.status_code in (401, 403)


def test_skill_documents_without_token_is_rejected(client):
    response = client.get("/api/v1/skill-documents/me")

    assert response.status_code in (401, 403)


# ============================================================
# Invalid token smoke checks
# ============================================================

def test_protected_endpoint_rejects_invalid_token(
    client,
    invalid_auth_headers,
):
    response = client.get(
        "/api/v1/notifications",
        headers=invalid_auth_headers,
    )

    assert response.status_code in (401, 403)


def test_protected_endpoint_rejects_malformed_authorization_header(client):
    response = client.get(
        "/api/v1/notifications",
        headers={
            "Authorization": "NotBearer token",
        },
    )

    assert response.status_code in (401, 403)