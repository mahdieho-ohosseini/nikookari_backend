def test_root_endpoint_success(client):
    response = client.get("/")

    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "media_service"
    assert "version" in body


def test_health_endpoint_success(client):
    response = client.get("/health")

    assert response.status_code in (200, 503)

    body = response.json()
    assert "status" in body
    assert "database" in body


def test_health_details_endpoint_success(client):
    response = client.get("/health/details")

    assert response.status_code in (200, 503)

    body = response.json()
    assert "status" in body
    assert body["service"] == "media-service"
    assert "version" in body
    assert "database" in body
    assert "storage" in body
    assert "backend" in body["storage"]
    assert "upload_dir" in body["storage"]


def test_metrics_endpoint_success(client):
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]

    text = response.text

    assert "media_service_uptime_seconds" in text
    assert "media_http_requests_total" in text
    assert "media_http_errors_total" in text
    assert "media_http_request_duration_seconds_average" in text


def test_metrics_records_requests(client):
    client.get("/")
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "media_http_requests_total" in response.text


def test_openapi_endpoint_success(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200

    body = response.json()
    assert "openapi" in body
    assert "paths" in body


def test_docs_endpoint_success(client):
    response = client.get("/docs")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_upload_requires_authentication(client):
    response = client.post(
        "/api/v1/media/upload",
        data={
            "source_service": "core_service",
            "file_usage": "campaign_report_image",
            "is_public": "true",
        },
        files={
            "file": ("test.pdf", b"test content", "application/pdf"),
        },
    )

    assert response.status_code in (401, 403)


def test_file_metadata_requires_authentication(client):
    response = client.get("/api/v1/media/files/1")

    assert response.status_code in (401, 403)


def test_file_download_requires_authentication(client):
    response = client.get("/api/v1/media/files/1/download")

    assert response.status_code in (401, 403)


def test_file_delete_requires_authentication(client):
    response = client.delete("/api/v1/media/files/1")

    assert response.status_code in (401, 403)