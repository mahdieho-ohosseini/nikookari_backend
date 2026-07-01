import requests


BASE_URL = "http://127.0.0.1:8000"


def test_root_endpoint():
    response = requests.get(f"{BASE_URL}/", timeout=5)

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert "message" in data


def test_openapi_endpoint():
    response = requests.get(f"{BASE_URL}/openapi.json", timeout=5)

    assert response.status_code == 200

    data = response.json()

    assert "openapi" in data
    assert "paths" in data


def test_health_endpoint():
    response = requests.get(f"{BASE_URL}/health", timeout=5)

    assert response.status_code in [200, 503]

    data = response.json()

    assert data["service"] == "iam-service"
    assert "status" in data
    assert "database" in data
    assert "redis" in data
    assert "email_circuit_breaker" in data


def test_metrics_endpoint():
    response = requests.get(f"{BASE_URL}/metrics", timeout=5)

    assert response.status_code == 200

    text = response.text

    assert "iam_service_uptime_seconds" in text
    assert "iam_http_requests_total" in text
    assert "iam_http_errors_total" in text
    assert "iam_http_request_duration_seconds_average" in text


def test_profile_me_requires_authentication():
    response = requests.get(f"{BASE_URL}/api/v1/profile/me", timeout=5)

    assert response.status_code == 401


def test_admin_users_requires_authentication():
    response = requests.get(f"{BASE_URL}/api/v1/admin/users", timeout=5)

    assert response.status_code == 401


def test_admin_roles_requires_authentication():
    response = requests.get(f"{BASE_URL}/api/v1/admin/roles", timeout=5)

    assert response.status_code == 401