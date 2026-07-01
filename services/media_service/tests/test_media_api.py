from tests.conftest import (
    CAMPAIGN_REPORT_FILE_ID,
    CHARITY_VERIFICATION_FILE_ID,
    MISSING_FILE_ID,
    OTHER_PRIVATE_FILE_ID,
    OWNER_PRIVATE_FILE_ID,
    PUBLIC_FILE_ID,
)


def assert_error_response(response, expected_status: int | tuple[int, ...]):
    if isinstance(expected_status, int):
        expected_status = (expected_status,)

    assert response.status_code in expected_status

    body = response.json()
    assert isinstance(body, dict)
    assert "detail" in body or "message" in body or "errors" in body


def valid_upload_data(**overrides):
    data = {
        "source_service": "core_service",
        "file_usage": "campaign_report_image",
        "is_public": "true",
    }

    data.update(overrides)
    return data


def valid_upload_files(
    *,
    filename: str = "test.pdf",
    content: bytes = b"test file content",
    content_type: str = "application/pdf",
):
    return {
        "file": (filename, content, content_type),
    }


# ============================================================
# Upload File
# POST /api/v1/media/upload
# ============================================================

def test_upload_file_success_pdf(client, auth_headers):
    response = client.post(
        "/api/v1/media/upload",
        headers=auth_headers,
        data=valid_upload_data(),
        files=valid_upload_files(),
    )

    assert response.status_code == 201

    body = response.json()
    assert body["id"] == 100
    assert body["source_service"] == "core_service"
    assert body["file_usage"] == "campaign_report_image"
    assert body["original_filename"] == "test.pdf"
    assert body["mime_type"] == "application/pdf"
    assert body["size_bytes"] > 0
    assert body["is_public"] is True


def test_upload_file_success_jpeg(client, auth_headers):
    response = client.post(
        "/api/v1/media/upload",
        headers=auth_headers,
        data=valid_upload_data(is_public="false"),
        files=valid_upload_files(
            filename="image.jpg",
            content=b"fake jpeg bytes",
            content_type="image/jpeg",
        ),
    )

    assert response.status_code == 201

    body = response.json()
    assert body["original_filename"] == "image.jpg"
    assert body["mime_type"] == "image/jpeg"
    assert body["is_public"] is False


def test_upload_file_success_png(client, auth_headers):
    response = client.post(
        "/api/v1/media/upload",
        headers=auth_headers,
        data=valid_upload_data(),
        files=valid_upload_files(
            filename="image.png",
            content=b"fake png bytes",
            content_type="image/png",
        ),
    )

    assert response.status_code == 201
    assert response.json()["mime_type"] == "image/png"


def test_upload_file_success_webp(client, auth_headers):
    response = client.post(
        "/api/v1/media/upload",
        headers=auth_headers,
        data=valid_upload_data(),
        files=valid_upload_files(
            filename="image.webp",
            content=b"fake webp bytes",
            content_type="image/webp",
        ),
    )

    assert response.status_code == 201
    assert response.json()["mime_type"] == "image/webp"


def test_upload_file_requires_authentication(client):
    response = client.post(
        "/api/v1/media/upload",
        data=valid_upload_data(),
        files=valid_upload_files(),
    )

    assert response.status_code in (401, 403)


def test_upload_file_rejects_invalid_token(client, invalid_auth_headers):
    response = client.post(
        "/api/v1/media/upload",
        headers=invalid_auth_headers,
        data=valid_upload_data(),
        files=valid_upload_files(),
    )

    assert response.status_code in (401, 403)


def test_upload_file_rejects_expired_token(client, expired_auth_headers):
    response = client.post(
        "/api/v1/media/upload",
        headers=expired_auth_headers,
        data=valid_upload_data(),
        files=valid_upload_files(),
    )

    assert response.status_code in (401, 403)


def test_upload_file_rejects_refresh_token(client, refresh_token_headers):
    response = client.post(
        "/api/v1/media/upload",
        headers=refresh_token_headers,
        data=valid_upload_data(),
        files=valid_upload_files(),
    )

    assert response.status_code in (401, 403)


def test_upload_file_rejects_missing_source_service(client, auth_headers):
    data = valid_upload_data()
    data.pop("source_service")

    response = client.post(
        "/api/v1/media/upload",
        headers=auth_headers,
        data=data,
        files=valid_upload_files(),
    )

    assert_error_response(response, 422)


def test_upload_file_rejects_missing_file_usage(client, auth_headers):
    data = valid_upload_data()
    data.pop("file_usage")

    response = client.post(
        "/api/v1/media/upload",
        headers=auth_headers,
        data=data,
        files=valid_upload_files(),
    )

    assert_error_response(response, 422)


def test_upload_file_rejects_missing_file(client, auth_headers):
    response = client.post(
        "/api/v1/media/upload",
        headers=auth_headers,
        data=valid_upload_data(),
    )

    assert_error_response(response, 422)


def test_upload_file_rejects_empty_file(client, auth_headers):
    response = client.post(
        "/api/v1/media/upload",
        headers=auth_headers,
        data=valid_upload_data(),
        files=valid_upload_files(content=b""),
    )

    assert_error_response(response, 400)


def test_upload_file_rejects_disallowed_text_file(client, auth_headers):
    response = client.post(
        "/api/v1/media/upload",
        headers=auth_headers,
        data=valid_upload_data(),
        files=valid_upload_files(
            filename="test.txt",
            content=b"hello",
            content_type="text/plain",
        ),
    )

    assert_error_response(response, 400)


def test_upload_file_rejects_disallowed_json_file(client, auth_headers):
    response = client.post(
        "/api/v1/media/upload",
        headers=auth_headers,
        data=valid_upload_data(),
        files=valid_upload_files(
            filename="test.json",
            content=b'{"x": 1}',
            content_type="application/json",
        ),
    )

    assert_error_response(response, 400)


def test_upload_file_rejects_large_file(client, auth_headers):
    large_content = b"x" * (10 * 1024 * 1024 + 1)

    response = client.post(
        "/api/v1/media/upload",
        headers=auth_headers,
        data=valid_upload_data(),
        files=valid_upload_files(
            filename="large.pdf",
            content=large_content,
            content_type="application/pdf",
        ),
    )

    assert_error_response(response, 413)


def test_upload_file_accepts_false_is_public(client, auth_headers):
    response = client.post(
        "/api/v1/media/upload",
        headers=auth_headers,
        data=valid_upload_data(is_public="false"),
        files=valid_upload_files(),
    )

    assert response.status_code == 201
    assert response.json()["is_public"] is False


def test_upload_file_accepts_missing_is_public_default_false_current_contract(
    client,
    auth_headers,
):
    data = valid_upload_data()
    data.pop("is_public")

    response = client.post(
        "/api/v1/media/upload",
        headers=auth_headers,
        data=data,
        files=valid_upload_files(),
    )

    assert response.status_code == 201
    assert response.json()["is_public"] is False


def test_upload_file_rejects_invalid_is_public_type(client, auth_headers):
    response = client.post(
        "/api/v1/media/upload",
        headers=auth_headers,
        data=valid_upload_data(is_public="not-bool"),
        files=valid_upload_files(),
    )

    assert_error_response(response, 422)


# ============================================================
# Get File Metadata
# GET /api/v1/media/files/{file_id}
# ============================================================

def test_get_public_file_metadata_success(client, auth_headers):
    response = client.get(
        f"/api/v1/media/files/{PUBLIC_FILE_ID}",
        headers=auth_headers,
    )

    assert response.status_code == 200

    body = response.json()
    assert body["id"] == PUBLIC_FILE_ID
    assert body["is_public"] is True
    assert body["original_filename"] == "public.png"


def test_get_owner_private_file_metadata_success(client, auth_headers):
    response = client.get(
        f"/api/v1/media/files/{OWNER_PRIVATE_FILE_ID}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert body_has_media_fields(response.json())


def test_get_campaign_report_file_metadata_success_for_authenticated_user(
    client,
    auth_headers,
):
    response = client.get(
        f"/api/v1/media/files/{CAMPAIGN_REPORT_FILE_ID}",
        headers=auth_headers,
    )

    assert response.status_code == 200


def test_get_charity_verification_file_metadata_success_for_verifier(
    client,
    verifier_headers,
):
    response = client.get(
        f"/api/v1/media/files/{CHARITY_VERIFICATION_FILE_ID}",
        headers=verifier_headers,
    )

    assert response.status_code == 200


def test_get_private_file_metadata_success_for_admin(client, admin_headers):
    response = client.get(
        f"/api/v1/media/files/{OTHER_PRIVATE_FILE_ID}",
        headers=admin_headers,
    )

    assert response.status_code == 200


def test_get_private_file_metadata_rejects_other_user(client, auth_headers):
    response = client.get(
        f"/api/v1/media/files/{OTHER_PRIVATE_FILE_ID}",
        headers=auth_headers,
    )

    assert_error_response(response, 403)


def test_get_private_file_metadata_rejects_verifier_for_non_verification_file(
    client,
    verifier_headers,
):
    response = client.get(
        f"/api/v1/media/files/{OTHER_PRIVATE_FILE_ID}",
        headers=verifier_headers,
    )

    assert_error_response(response, 403)


def test_get_file_metadata_requires_authentication(client):
    response = client.get(f"/api/v1/media/files/{PUBLIC_FILE_ID}")

    assert response.status_code in (401, 403)


def test_get_file_metadata_rejects_invalid_token(client, invalid_auth_headers):
    response = client.get(
        f"/api/v1/media/files/{PUBLIC_FILE_ID}",
        headers=invalid_auth_headers,
    )

    assert response.status_code in (401, 403)


def test_get_file_metadata_returns_404_for_missing_file(client, auth_headers):
    response = client.get(
        f"/api/v1/media/files/{MISSING_FILE_ID}",
        headers=auth_headers,
    )

    assert_error_response(response, 404)


def test_get_file_metadata_rejects_invalid_file_id(client, auth_headers):
    response = client.get(
        "/api/v1/media/files/not-an-int",
        headers=auth_headers,
    )

    assert_error_response(response, 422)


def test_get_file_metadata_rejects_negative_file_id_current_contract(
    client,
    auth_headers,
):
    response = client.get(
        "/api/v1/media/files/-1",
        headers=auth_headers,
    )

    assert response.status_code in (200, 404)


# ============================================================
# Download File
# GET /api/v1/media/files/{file_id}/download
# ============================================================

def test_download_public_file_success(client, auth_headers):
    response = client.get(
        f"/api/v1/media/files/{PUBLIC_FILE_ID}/download",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.content == b"test file content"


def test_download_owner_private_file_success(client, auth_headers):
    response = client.get(
        f"/api/v1/media/files/{OWNER_PRIVATE_FILE_ID}/download",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.content == b"test file content"


def test_download_campaign_report_file_success_for_authenticated_user(
    client,
    auth_headers,
):
    response = client.get(
        f"/api/v1/media/files/{CAMPAIGN_REPORT_FILE_ID}/download",
        headers=auth_headers,
    )

    assert response.status_code == 200


def test_download_charity_verification_file_success_for_verifier(
    client,
    verifier_headers,
):
    response = client.get(
        f"/api/v1/media/files/{CHARITY_VERIFICATION_FILE_ID}/download",
        headers=verifier_headers,
    )

    assert response.status_code == 200


def test_download_private_file_success_for_admin(client, admin_headers):
    response = client.get(
        f"/api/v1/media/files/{OTHER_PRIVATE_FILE_ID}/download",
        headers=admin_headers,
    )

    assert response.status_code == 200


def test_download_private_file_rejects_other_user(client, auth_headers):
    response = client.get(
        f"/api/v1/media/files/{OTHER_PRIVATE_FILE_ID}/download",
        headers=auth_headers,
    )

    assert_error_response(response, 403)


def test_download_private_file_rejects_verifier_for_non_verification_file(
    client,
    verifier_headers,
):
    response = client.get(
        f"/api/v1/media/files/{OTHER_PRIVATE_FILE_ID}/download",
        headers=verifier_headers,
    )

    assert_error_response(response, 403)


def test_download_file_requires_authentication(client):
    response = client.get(f"/api/v1/media/files/{PUBLIC_FILE_ID}/download")

    assert response.status_code in (401, 403)


def test_download_file_rejects_invalid_token(client, invalid_auth_headers):
    response = client.get(
        f"/api/v1/media/files/{PUBLIC_FILE_ID}/download",
        headers=invalid_auth_headers,
    )

    assert response.status_code in (401, 403)


def test_download_file_returns_404_for_missing_file(client, auth_headers):
    response = client.get(
        f"/api/v1/media/files/{MISSING_FILE_ID}/download",
        headers=auth_headers,
    )

    assert_error_response(response, 404)


def test_download_file_rejects_invalid_file_id(client, auth_headers):
    response = client.get(
        "/api/v1/media/files/not-an-int/download",
        headers=auth_headers,
    )

    assert_error_response(response, 422)


# ============================================================
# Delete File
# DELETE /api/v1/media/files/{file_id}
# ============================================================

def test_delete_owner_private_file_success(client, auth_headers):
    response = client.delete(
        f"/api/v1/media/files/{OWNER_PRIVATE_FILE_ID}",
        headers=auth_headers,
    )

    assert response.status_code == 200

    body = response.json()
    assert body["message"] == "File deleted successfully."
    assert body["deleted_file_id"] == OWNER_PRIVATE_FILE_ID


def test_delete_private_file_success_for_admin(client, admin_headers):
    response = client.delete(
        f"/api/v1/media/files/{OTHER_PRIVATE_FILE_ID}",
        headers=admin_headers,
    )

    assert response.status_code == 200
    assert response.json()["deleted_file_id"] == OTHER_PRIVATE_FILE_ID


def test_delete_private_file_rejects_other_user(client, auth_headers):
    response = client.delete(
        f"/api/v1/media/files/{OTHER_PRIVATE_FILE_ID}",
        headers=auth_headers,
    )

    assert_error_response(response, 403)


def test_delete_private_file_rejects_verifier(client, verifier_headers):
    response = client.delete(
        f"/api/v1/media/files/{OTHER_PRIVATE_FILE_ID}",
        headers=verifier_headers,
    )

    assert_error_response(response, 403)


def test_delete_file_requires_authentication(client):
    response = client.delete(f"/api/v1/media/files/{OWNER_PRIVATE_FILE_ID}")

    assert response.status_code in (401, 403)


def test_delete_file_rejects_invalid_token(client, invalid_auth_headers):
    response = client.delete(
        f"/api/v1/media/files/{OWNER_PRIVATE_FILE_ID}",
        headers=invalid_auth_headers,
    )

    assert response.status_code in (401, 403)


def test_delete_file_returns_404_for_missing_file(client, auth_headers):
    response = client.delete(
        f"/api/v1/media/files/{MISSING_FILE_ID}",
        headers=auth_headers,
    )

    assert_error_response(response, 404)


def test_delete_file_rejects_invalid_file_id(client, auth_headers):
    response = client.delete(
        "/api/v1/media/files/not-an-int",
        headers=auth_headers,
    )

    assert_error_response(response, 422)


def test_patch_file_is_not_allowed(client, auth_headers):
    response = client.patch(
        f"/api/v1/media/files/{OWNER_PRIVATE_FILE_ID}",
        headers=auth_headers,
        json={
            "is_public": True,
        },
    )

    assert_error_response(response, 405)


def body_has_media_fields(body):
    required_fields = {
        "id",
        "owner_user_id",
        "source_service",
        "file_usage",
        "original_filename",
        "stored_filename",
        "mime_type",
        "extension",
        "size_bytes",
        "storage_backend",
        "storage_path",
        "public_url",
        "is_public",
        "checksum_sha256",
        "created_at",
        "updated_at",
        "deleted_at",
    }

    return required_fields.issubset(set(body.keys()))