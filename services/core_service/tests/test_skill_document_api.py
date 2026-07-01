from tests.conftest import MISSING_ID


DOCUMENT_ID = "34343434-3434-4343-8343-343434343434"
SKILL_CONTRIBUTION_ID = "12121212-1212-4121-8121-121212121212"


def assert_error_response(response, expected_status: int | tuple[int, ...]):
    if isinstance(expected_status, int):
        expected_status = (expected_status,)

    assert response.status_code in expected_status

    body = response.json()
    assert isinstance(body, dict)
    assert "detail" in body or "message" in body or "errors" in body


def valid_skill_document_payload(**overrides):
    payload = {
        "skill_contribution_id": SKILL_CONTRIBUTION_ID,
        "title": "مدرک مهارت",
        "description": "توضیح مدرک مهارت برای تست",
        "document_type": "certificate",
        "file_id": 10,
        "is_public": True,
    }

    payload.update(overrides)
    return payload


def valid_skill_document_update_payload(**overrides):
    payload = {
        "title": "مدرک مهارت ویرایش شده",
        "description": "توضیح ویرایش شده مدرک مهارت",
        "document_type": "portfolio",
        "file_id": 11,
        "is_public": True,
    }

    payload.update(overrides)
    return payload


def valid_review_payload(**overrides):
    payload = {
        "status": "verified",
        "review_note": "مدرک بررسی و تایید شد",
    }

    payload.update(overrides)
    return payload


# ============================================================
# Create My Skill Document
# POST /api/v1/me/skill-documents
# ============================================================

def test_create_skill_document_success(client, auth_headers):
    response = client.post(
        "/api/v1/me/skill-documents",
        headers=auth_headers,
        json=valid_skill_document_payload(),
    )

    assert response.status_code in (200, 201)

    body = response.json()
    assert "id" in body
    assert "user_id" in body
    assert "title" in body
    assert "description" in body
    assert "document_type" in body
    assert "file_id" in body
    assert "is_public" in body
    assert "status" in body


def test_create_skill_document_requires_authentication(client):
    response = client.post(
        "/api/v1/me/skill-documents",
        json=valid_skill_document_payload(),
    )

    assert response.status_code in (401, 403)


def test_create_skill_document_rejects_invalid_token(client, invalid_auth_headers):
    response = client.post(
        "/api/v1/me/skill-documents",
        headers=invalid_auth_headers,
        json=valid_skill_document_payload(),
    )

    assert response.status_code in (401, 403)


def test_create_skill_document_accepts_missing_skill_contribution_id_current_contract(
    client,
    auth_headers,
):
    payload = valid_skill_document_payload()
    payload.pop("skill_contribution_id")

    response = client.post(
        "/api/v1/me/skill-documents",
        headers=auth_headers,
        json=payload,
    )

    assert response.status_code in (200, 201)
    assert "skill_contribution_id" in response.json()


def test_create_skill_document_rejects_invalid_skill_contribution_id(
    client,
    auth_headers,
):
    response = client.post(
        "/api/v1/me/skill-documents",
        headers=auth_headers,
        json=valid_skill_document_payload(
            skill_contribution_id="not-a-uuid",
        ),
    )

    assert_error_response(response, 422)


def test_create_skill_document_rejects_missing_title(client, auth_headers):
    payload = valid_skill_document_payload()
    payload.pop("title")

    response = client.post(
        "/api/v1/me/skill-documents",
        headers=auth_headers,
        json=payload,
    )

    assert_error_response(response, 422)


def test_create_skill_document_accepts_short_title_current_contract(
    client,
    auth_headers,
):
    response = client.post(
        "/api/v1/me/skill-documents",
        headers=auth_headers,
        json=valid_skill_document_payload(
            title="کم",
        ),
    )

    assert response.status_code in (200, 201)


def test_create_skill_document_rejects_too_long_title(client, auth_headers):
    response = client.post(
        "/api/v1/me/skill-documents",
        headers=auth_headers,
        json=valid_skill_document_payload(
            title="الف" * 256,
        ),
    )

    assert_error_response(response, 422)


def test_create_skill_document_accepts_missing_description_current_contract(
    client,
    auth_headers,
):
    payload = valid_skill_document_payload()
    payload.pop("description")

    response = client.post(
        "/api/v1/me/skill-documents",
        headers=auth_headers,
        json=payload,
    )

    assert response.status_code in (200, 201)
    assert "description" in response.json()


def test_create_skill_document_accepts_short_description_current_contract(
    client,
    auth_headers,
):
    response = client.post(
        "/api/v1/me/skill-documents",
        headers=auth_headers,
        json=valid_skill_document_payload(
            description="کوتاه",
        ),
    )

    assert response.status_code in (200, 201)
    assert "description" in response.json()


def test_create_skill_document_accepts_missing_document_type_current_contract(
    client,
    auth_headers,
):
    payload = valid_skill_document_payload()
    payload.pop("document_type")

    response = client.post(
        "/api/v1/me/skill-documents",
        headers=auth_headers,
        json=payload,
    )

    assert response.status_code in (200, 201)
    assert isinstance(response.json()["document_type"], str)


def test_create_skill_document_accepts_certificate_type(client, auth_headers):
    response = client.post(
        "/api/v1/me/skill-documents",
        headers=auth_headers,
        json=valid_skill_document_payload(document_type="certificate"),
    )

    assert response.status_code in (200, 201)


def test_create_skill_document_accepts_resume_type(client, auth_headers):
    response = client.post(
        "/api/v1/me/skill-documents",
        headers=auth_headers,
        json=valid_skill_document_payload(document_type="resume"),
    )

    assert response.status_code in (200, 201)


def test_create_skill_document_accepts_portfolio_type(client, auth_headers):
    response = client.post(
        "/api/v1/me/skill-documents",
        headers=auth_headers,
        json=valid_skill_document_payload(document_type="portfolio"),
    )

    assert response.status_code in (200, 201)


def test_create_skill_document_accepts_license_type(client, auth_headers):
    response = client.post(
        "/api/v1/me/skill-documents",
        headers=auth_headers,
        json=valid_skill_document_payload(document_type="license"),
    )

    assert response.status_code in (200, 201)


def test_create_skill_document_accepts_identity_type(client, auth_headers):
    response = client.post(
        "/api/v1/me/skill-documents",
        headers=auth_headers,
        json=valid_skill_document_payload(document_type="identity"),
    )

    assert response.status_code in (200, 201)


def test_create_skill_document_accepts_other_type(client, auth_headers):
    response = client.post(
        "/api/v1/me/skill-documents",
        headers=auth_headers,
        json=valid_skill_document_payload(document_type="other"),
    )

    assert response.status_code in (200, 201)


def test_create_skill_document_rejects_invalid_document_type(client, auth_headers):
    response = client.post(
        "/api/v1/me/skill-documents",
        headers=auth_headers,
        json=valid_skill_document_payload(document_type="invalid-type"),
    )

    assert_error_response(response, 422)


def test_create_skill_document_rejects_missing_file_id(client, auth_headers):
    payload = valid_skill_document_payload()
    payload.pop("file_id")

    response = client.post(
        "/api/v1/me/skill-documents",
        headers=auth_headers,
        json=payload,
    )

    assert_error_response(response, 422)


def test_create_skill_document_rejects_zero_file_id(client, auth_headers):
    response = client.post(
        "/api/v1/me/skill-documents",
        headers=auth_headers,
        json=valid_skill_document_payload(file_id=0),
    )

    assert_error_response(response, 422)


def test_create_skill_document_rejects_negative_file_id(client, auth_headers):
    response = client.post(
        "/api/v1/me/skill-documents",
        headers=auth_headers,
        json=valid_skill_document_payload(file_id=-1),
    )

    assert_error_response(response, 422)


def test_create_skill_document_rejects_non_integer_file_id(client, auth_headers):
    response = client.post(
        "/api/v1/me/skill-documents",
        headers=auth_headers,
        json=valid_skill_document_payload(file_id="not-number"),
    )

    assert_error_response(response, 422)


def test_create_skill_document_accepts_missing_is_public_current_contract(
    client,
    auth_headers,
):
    payload = valid_skill_document_payload()
    payload.pop("is_public")

    response = client.post(
        "/api/v1/me/skill-documents",
        headers=auth_headers,
        json=payload,
    )

    assert response.status_code in (200, 201)
    assert isinstance(response.json()["is_public"], bool)


def test_create_skill_document_rejects_invalid_is_public_type(client, auth_headers):
    response = client.post(
        "/api/v1/me/skill-documents",
        headers=auth_headers,
        json=valid_skill_document_payload(is_public="not-bool"),
    )

    assert_error_response(response, 422)


def test_create_skill_document_ignores_extra_fields_current_contract(
    client,
    auth_headers,
):
    response = client.post(
        "/api/v1/me/skill-documents",
        headers=auth_headers,
        json=valid_skill_document_payload(
            status="verified",
            review_note="نباید از body ساخت قبول شود",
        ),
    )

    assert response.status_code in (200, 201)
    assert "status" in response.json()


# ============================================================
# List My Skill Documents
# GET /api/v1/me/skill-documents
# ============================================================

def test_list_my_skill_documents_success(client, auth_headers):
    response = client.get(
        "/api/v1/me/skill-documents",
        headers=auth_headers,
    )

    assert response.status_code == 200

    body = response.json()
    assert isinstance(body, list)
    assert len(body) >= 1
    assert "id" in body[0]
    assert "title" in body[0]


def test_list_my_skill_documents_requires_authentication(client):
    response = client.get("/api/v1/me/skill-documents")

    assert response.status_code in (401, 403)


def test_list_my_skill_documents_rejects_invalid_token(
    client,
    invalid_auth_headers,
):
    response = client.get(
        "/api/v1/me/skill-documents",
        headers=invalid_auth_headers,
    )

    assert response.status_code in (401, 403)


def test_list_my_skill_documents_returns_json(client, auth_headers):
    response = client.get(
        "/api/v1/me/skill-documents",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]


# ============================================================
# Get Skill Document
# GET /api/v1/skill-documents/{document_id}
# ============================================================

def test_get_skill_document_success(client, auth_headers):
    response = client.get(
        f"/api/v1/skill-documents/{DOCUMENT_ID}",
        headers=auth_headers,
    )

    assert response.status_code == 200

    body = response.json()
    assert body["id"] == DOCUMENT_ID
    assert body["title"] == "مدرک تست"
    assert "description" in body
    assert "document_type" in body
    assert "file_id" in body
    assert "status" in body


def test_get_skill_document_requires_authentication(client):
    response = client.get(f"/api/v1/skill-documents/{DOCUMENT_ID}")

    assert response.status_code in (401, 403)


def test_get_skill_document_rejects_invalid_token(client, invalid_auth_headers):
    response = client.get(
        f"/api/v1/skill-documents/{DOCUMENT_ID}",
        headers=invalid_auth_headers,
    )

    assert response.status_code in (401, 403)


def test_get_skill_document_returns_404_for_missing_document(
    client,
    auth_headers,
):
    response = client.get(
        f"/api/v1/skill-documents/{MISSING_ID}",
        headers=auth_headers,
    )

    assert_error_response(response, 404)


def test_get_skill_document_rejects_invalid_document_uuid(client, auth_headers):
    response = client.get(
        "/api/v1/skill-documents/not-a-uuid",
        headers=auth_headers,
    )

    assert_error_response(response, 422)


def test_get_skill_document_returns_json(client, auth_headers):
    response = client.get(
        f"/api/v1/skill-documents/{DOCUMENT_ID}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]


# ============================================================
# Update My Skill Document
# PATCH /api/v1/me/skill-documents/{document_id}
# ============================================================

def test_update_skill_document_success(client, auth_headers):
    response = client.patch(
        f"/api/v1/me/skill-documents/{DOCUMENT_ID}",
        headers=auth_headers,
        json=valid_skill_document_update_payload(),
    )

    assert response.status_code == 200

    body = response.json()
    assert body["id"] == DOCUMENT_ID
    assert "title" in body
    assert "description" in body
    assert "document_type" in body
    assert "file_id" in body
    assert isinstance(body["is_public"], bool)


def test_update_skill_document_requires_authentication(client):
    response = client.patch(
        f"/api/v1/me/skill-documents/{DOCUMENT_ID}",
        json=valid_skill_document_update_payload(),
    )

    assert response.status_code in (401, 403)


def test_update_skill_document_rejects_invalid_token(
    client,
    invalid_auth_headers,
):
    response = client.patch(
        f"/api/v1/me/skill-documents/{DOCUMENT_ID}",
        headers=invalid_auth_headers,
        json=valid_skill_document_update_payload(),
    )

    assert response.status_code in (401, 403)


def test_update_skill_document_returns_404_for_missing_document(
    client,
    auth_headers,
):
    response = client.patch(
        f"/api/v1/me/skill-documents/{MISSING_ID}",
        headers=auth_headers,
        json=valid_skill_document_update_payload(),
    )

    assert_error_response(response, 404)


def test_update_skill_document_rejects_invalid_document_uuid(
    client,
    auth_headers,
):
    response = client.patch(
        "/api/v1/me/skill-documents/not-a-uuid",
        headers=auth_headers,
        json=valid_skill_document_update_payload(),
    )

    assert_error_response(response, 422)


def test_update_skill_document_accepts_partial_title_update(
    client,
    auth_headers,
):
    response = client.patch(
        f"/api/v1/me/skill-documents/{DOCUMENT_ID}",
        headers=auth_headers,
        json={
            "title": "عنوان جدید مدرک",
        },
    )

    assert response.status_code == 200
    assert "title" in response.json()


def test_update_skill_document_accepts_short_title_current_contract(
    client,
    auth_headers,
):
    response = client.patch(
        f"/api/v1/me/skill-documents/{DOCUMENT_ID}",
        headers=auth_headers,
        json={
            "title": "کم",
        },
    )

    assert response.status_code == 200
    assert "title" in response.json()


def test_update_skill_document_rejects_too_long_title(client, auth_headers):
    response = client.patch(
        f"/api/v1/me/skill-documents/{DOCUMENT_ID}",
        headers=auth_headers,
        json={
            "title": "الف" * 256,
        },
    )

    assert_error_response(response, 422)


def test_update_skill_document_accepts_description_update_current_contract(
    client,
    auth_headers,
):
    response = client.patch(
        f"/api/v1/me/skill-documents/{DOCUMENT_ID}",
        headers=auth_headers,
        json={
            "description": "توضیح جدید مدرک",
        },
    )

    assert response.status_code == 200
    assert "description" in response.json()


def test_update_skill_document_accepts_short_description_current_contract(
    client,
    auth_headers,
):
    response = client.patch(
        f"/api/v1/me/skill-documents/{DOCUMENT_ID}",
        headers=auth_headers,
        json={
            "description": "کوتاه",
        },
    )

    assert response.status_code == 200
    assert "description" in response.json()


def test_update_skill_document_accepts_null_description_current_contract(
    client,
    auth_headers,
):
    response = client.patch(
        f"/api/v1/me/skill-documents/{DOCUMENT_ID}",
        headers=auth_headers,
        json={
            "description": None,
        },
    )

    assert response.status_code == 200
    assert "description" in response.json()


def test_update_skill_document_accepts_document_type_update(
    client,
    auth_headers,
):
    response = client.patch(
        f"/api/v1/me/skill-documents/{DOCUMENT_ID}",
        headers=auth_headers,
        json={
            "document_type": "resume",
        },
    )

    assert response.status_code == 200
    assert "document_type" in response.json()


def test_update_skill_document_rejects_invalid_document_type(
    client,
    auth_headers,
):
    response = client.patch(
        f"/api/v1/me/skill-documents/{DOCUMENT_ID}",
        headers=auth_headers,
        json={
            "document_type": "invalid-type",
        },
    )

    assert_error_response(response, 422)


def test_update_skill_document_accepts_file_id_update(client, auth_headers):
    response = client.patch(
        f"/api/v1/me/skill-documents/{DOCUMENT_ID}",
        headers=auth_headers,
        json={
            "file_id": 22,
        },
    )

    assert response.status_code == 200
    assert "file_id" in response.json()


def test_update_skill_document_rejects_zero_file_id(client, auth_headers):
    response = client.patch(
        f"/api/v1/me/skill-documents/{DOCUMENT_ID}",
        headers=auth_headers,
        json={
            "file_id": 0,
        },
    )

    assert_error_response(response, 422)


def test_update_skill_document_rejects_negative_file_id(client, auth_headers):
    response = client.patch(
        f"/api/v1/me/skill-documents/{DOCUMENT_ID}",
        headers=auth_headers,
        json={
            "file_id": -1,
        },
    )

    assert_error_response(response, 422)


def test_update_skill_document_rejects_non_integer_file_id(client, auth_headers):
    response = client.patch(
        f"/api/v1/me/skill-documents/{DOCUMENT_ID}",
        headers=auth_headers,
        json={
            "file_id": "not-number",
        },
    )

    assert_error_response(response, 422)


def test_update_skill_document_accepts_is_public_update_current_contract(
    client,
    auth_headers,
):
    response = client.patch(
        f"/api/v1/me/skill-documents/{DOCUMENT_ID}",
        headers=auth_headers,
        json={
            "is_public": True,
        },
    )

    assert response.status_code == 200
    assert isinstance(response.json()["is_public"], bool)


def test_update_skill_document_rejects_invalid_is_public_type(
    client,
    auth_headers,
):
    response = client.patch(
        f"/api/v1/me/skill-documents/{DOCUMENT_ID}",
        headers=auth_headers,
        json={
            "is_public": "not-bool",
        },
    )

    assert_error_response(response, 422)


def test_update_skill_document_ignores_extra_fields_current_contract(
    client,
    auth_headers,
):
    response = client.patch(
        f"/api/v1/me/skill-documents/{DOCUMENT_ID}",
        headers=auth_headers,
        json={
            "status": "verified",
            "review_note": "نباید از update عادی اعمال شود",
        },
    )

    assert response.status_code == 200
    assert "status" in response.json()


def test_put_skill_document_is_not_allowed(client, auth_headers):
    response = client.put(
        f"/api/v1/me/skill-documents/{DOCUMENT_ID}",
        headers=auth_headers,
        json=valid_skill_document_update_payload(),
    )

    assert_error_response(response, 405)


# ============================================================
# Delete My Skill Document
# DELETE /api/v1/me/skill-documents/{document_id}
# ============================================================

def test_delete_skill_document_success(client, auth_headers):
    response = client.delete(
        f"/api/v1/me/skill-documents/{DOCUMENT_ID}",
        headers=auth_headers,
    )

    assert response.status_code in (200, 204)

    if response.status_code != 204:
        assert isinstance(response.json(), dict)


def test_delete_skill_document_requires_authentication(client):
    response = client.delete(f"/api/v1/me/skill-documents/{DOCUMENT_ID}")

    assert response.status_code in (401, 403)


def test_delete_skill_document_rejects_invalid_token(client, invalid_auth_headers):
    response = client.delete(
        f"/api/v1/me/skill-documents/{DOCUMENT_ID}",
        headers=invalid_auth_headers,
    )

    assert response.status_code in (401, 403)


def test_delete_skill_document_returns_404_for_missing_document(
    client,
    auth_headers,
):
    response = client.delete(
        f"/api/v1/me/skill-documents/{MISSING_ID}",
        headers=auth_headers,
    )

    assert_error_response(response, 404)


def test_delete_skill_document_rejects_invalid_document_uuid(
    client,
    auth_headers,
):
    response = client.delete(
        "/api/v1/me/skill-documents/not-a-uuid",
        headers=auth_headers,
    )

    assert_error_response(response, 422)


# ============================================================
# List Documents By Skill Contribution
# GET /api/v1/skill-contributions/{skill_contribution_id}/documents
# ============================================================

def test_list_documents_by_skill_contribution_success_for_donor_current_contract(
    client,
    auth_headers,
):
    response = client.get(
        f"/api/v1/skill-contributions/{SKILL_CONTRIBUTION_ID}/documents",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_documents_by_skill_contribution_success_for_owner(
    client,
    owner_headers,
):
    response = client.get(
        f"/api/v1/skill-contributions/{SKILL_CONTRIBUTION_ID}/documents",
        headers=owner_headers,
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_documents_by_skill_contribution_success_for_verifier(
    client,
    verifier_headers,
):
    response = client.get(
        f"/api/v1/skill-contributions/{SKILL_CONTRIBUTION_ID}/documents",
        headers=verifier_headers,
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_documents_by_skill_contribution_success_for_admin(
    client,
    admin_headers,
):
    response = client.get(
        f"/api/v1/skill-contributions/{SKILL_CONTRIBUTION_ID}/documents",
        headers=admin_headers,
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_documents_by_skill_contribution_requires_authentication(client):
    response = client.get(
        f"/api/v1/skill-contributions/{SKILL_CONTRIBUTION_ID}/documents",
    )

    assert response.status_code in (401, 403)


def test_list_documents_by_skill_contribution_rejects_invalid_token(
    client,
    invalid_auth_headers,
):
    response = client.get(
        f"/api/v1/skill-contributions/{SKILL_CONTRIBUTION_ID}/documents",
        headers=invalid_auth_headers,
    )

    assert response.status_code in (401, 403)


def test_list_documents_by_skill_contribution_accepts_missing_contribution_current_contract(
    client,
    auth_headers,
):
    response = client.get(
        f"/api/v1/skill-contributions/{MISSING_ID}/documents",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_documents_by_skill_contribution_rejects_invalid_uuid(
    client,
    auth_headers,
):
    response = client.get(
        "/api/v1/skill-contributions/not-a-uuid/documents",
        headers=auth_headers,
    )

    assert_error_response(response, 422)


# ============================================================
# Review Skill Document
# PATCH /api/v1/skill-documents/{document_id}/review
# ============================================================

def test_review_skill_document_success_for_verifier(client, verifier_headers):
    response = client.patch(
        f"/api/v1/skill-documents/{DOCUMENT_ID}/review",
        headers=verifier_headers,
        json=valid_review_payload(status="verified"),
    )

    assert response.status_code == 200

    body = response.json()
    assert body["id"] == DOCUMENT_ID
    assert body["status"] == "verified"


def test_review_skill_document_success_for_admin(client, admin_headers):
    response = client.patch(
        f"/api/v1/skill-documents/{DOCUMENT_ID}/review",
        headers=admin_headers,
        json=valid_review_payload(status="verified"),
    )

    assert response.status_code == 200


def test_review_skill_document_accepts_donor_current_contract(
    client,
    auth_headers,
):
    response = client.patch(
        f"/api/v1/skill-documents/{DOCUMENT_ID}/review",
        headers=auth_headers,
        json=valid_review_payload(status="verified"),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "verified"


def test_review_skill_document_requires_authentication(client):
    response = client.patch(
        f"/api/v1/skill-documents/{DOCUMENT_ID}/review",
        json=valid_review_payload(status="verified"),
    )

    assert response.status_code in (401, 403)


def test_review_skill_document_rejects_invalid_token(client, invalid_auth_headers):
    response = client.patch(
        f"/api/v1/skill-documents/{DOCUMENT_ID}/review",
        headers=invalid_auth_headers,
        json=valid_review_payload(status="verified"),
    )

    assert response.status_code in (401, 403)


def test_review_skill_document_accepts_rejected_status(client, verifier_headers):
    response = client.patch(
        f"/api/v1/skill-documents/{DOCUMENT_ID}/review",
        headers=verifier_headers,
        json=valid_review_payload(
            status="rejected",
            review_note="مدرک رد شد",
        ),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "rejected"


def test_review_skill_document_rejects_approved_status(client, verifier_headers):
    response = client.patch(
        f"/api/v1/skill-documents/{DOCUMENT_ID}/review",
        headers=verifier_headers,
        json=valid_review_payload(status="approved"),
    )

    assert_error_response(response, 422)


def test_review_skill_document_rejects_pending_status(client, verifier_headers):
    response = client.patch(
        f"/api/v1/skill-documents/{DOCUMENT_ID}/review",
        headers=verifier_headers,
        json=valid_review_payload(status="pending"),
    )

    assert_error_response(response, 422)


def test_review_skill_document_rejects_missing_status(client, verifier_headers):
    payload = valid_review_payload()
    payload.pop("status")

    response = client.patch(
        f"/api/v1/skill-documents/{DOCUMENT_ID}/review",
        headers=verifier_headers,
        json=payload,
    )

    assert_error_response(response, 422)


def test_review_skill_document_accepts_missing_review_note_current_contract(
    client,
    verifier_headers,
):
    payload = valid_review_payload()
    payload.pop("review_note")

    response = client.patch(
        f"/api/v1/skill-documents/{DOCUMENT_ID}/review",
        headers=verifier_headers,
        json=payload,
    )

    assert response.status_code == 200
    assert "review_note" in response.json()


def test_review_skill_document_returns_404_for_missing_document(
    client,
    verifier_headers,
):
    response = client.patch(
        f"/api/v1/skill-documents/{MISSING_ID}/review",
        headers=verifier_headers,
        json=valid_review_payload(status="verified"),
    )

    assert_error_response(response, 404)


def test_review_skill_document_rejects_invalid_document_uuid(
    client,
    verifier_headers,
):
    response = client.patch(
        "/api/v1/skill-documents/not-a-uuid/review",
        headers=verifier_headers,
        json=valid_review_payload(status="verified"),
    )

    assert_error_response(response, 422)


def test_review_skill_document_ignores_extra_fields_current_contract(
    client,
    verifier_headers,
):
    response = client.patch(
        f"/api/v1/skill-documents/{DOCUMENT_ID}/review",
        headers=verifier_headers,
        json=valid_review_payload(
            status="verified",
            user_id="11111111-1111-1111-1111-111111111111",
            file_id=999,
        ),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "verified"