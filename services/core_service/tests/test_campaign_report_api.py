from tests.conftest import CAMPAIGN_ID, MISSING_ID, REPORT_ID


def assert_error_response(response, expected_status: int | tuple[int, ...]):
    if isinstance(expected_status, int):
        expected_status = (expected_status,)

    assert response.status_code in expected_status

    body = response.json()
    assert isinstance(body, dict)
    assert "detail" in body or "message" in body or "errors" in body


def valid_report_payload(**overrides):
    payload = {
        "title": "گزارش پیشرفت تست",
        "content": "این متن کامل گزارش پیشرفت پویش است و برای تست API گزارش استفاده می‌شود.",
        "report_type": "progress",
        "image_file_ids": [1, 2],
        "attachment_file_ids": [3],
        "is_public": True,
    }

    payload.update(overrides)
    return payload


def valid_report_update_payload(**overrides):
    payload = {
        "title": "عنوان ویرایش شده گزارش",
        "content": "این متن ویرایش شده گزارش پیشرفت پویش است.",
        "report_type": "progress",
        "image_file_ids": [4, 5],
        "attachment_file_ids": [6],
        "is_public": True,
    }

    payload.update(overrides)
    return payload


# ============================================================
# Create Campaign Report
# POST /api/v1/campaigns/{campaign_id}/reports
# ============================================================

def test_create_campaign_report_success(client, owner_headers):
    response = client.post(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports",
        headers=owner_headers,
        json=valid_report_payload(),
    )

    assert response.status_code in (200, 201)

    body = response.json()
    assert body["campaign_id"] == str(CAMPAIGN_ID)
    assert body["title"] == "گزارش پیشرفت تست"
    assert body["report_type"] == "progress"
    assert body["image_file_ids"] == [1, 2]
    assert body["attachment_file_ids"] == [3]
    assert body["is_public"] is True


def test_create_campaign_report_requires_authentication(client):
    response = client.post(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports",
        json=valid_report_payload(),
    )

    assert response.status_code in (401, 403)


def test_create_campaign_report_rejects_invalid_token(
    client,
    invalid_auth_headers,
):
    response = client.post(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports",
        headers=invalid_auth_headers,
        json=valid_report_payload(),
    )

    assert response.status_code in (401, 403)


def test_create_campaign_report_returns_403_when_service_forbids_user(
    client,
    owner_headers,
):
    response = client.post(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports",
        headers=owner_headers,
        json=valid_report_payload(
            title="forbidden",
        ),
    )

    assert_error_response(response, 403)


def test_create_campaign_report_rejects_invalid_campaign_uuid(
    client,
    owner_headers,
):
    response = client.post(
        "/api/v1/campaigns/not-a-uuid/reports",
        headers=owner_headers,
        json=valid_report_payload(),
    )

    assert_error_response(response, 422)


def test_create_campaign_report_rejects_missing_title(client, owner_headers):
    payload = valid_report_payload()
    payload.pop("title")

    response = client.post(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports",
        headers=owner_headers,
        json=payload,
    )

    assert_error_response(response, 422)


def test_create_campaign_report_accepts_short_title_current_contract(
    client,
    owner_headers,
):
    response = client.post(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports",
        headers=owner_headers,
        json=valid_report_payload(
            title="کم",
        ),
    )

    assert response.status_code in (200, 201)
    assert response.json()["title"] == "کم"


def test_create_campaign_report_rejects_missing_content(client, owner_headers):
    payload = valid_report_payload()
    payload.pop("content")

    response = client.post(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports",
        headers=owner_headers,
        json=payload,
    )

    assert_error_response(response, 422)


def test_create_campaign_report_accepts_short_content_current_contract(
    client,
    owner_headers,
):
    response = client.post(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports",
        headers=owner_headers,
        json=valid_report_payload(
            content="کوتاه",
        ),
    )

    assert response.status_code in (200, 201)
    assert response.json()["content"] == "کوتاه"


def test_create_campaign_report_accepts_missing_report_type_current_contract(
    client,
    owner_headers,
):
    payload = valid_report_payload()
    payload.pop("report_type")

    response = client.post(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports",
        headers=owner_headers,
        json=payload,
    )

    assert response.status_code in (200, 201)
    assert response.json()["report_type"] == "general"


def test_create_campaign_report_rejects_invalid_report_type(
    client,
    owner_headers,
):
    response = client.post(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports",
        headers=owner_headers,
        json=valid_report_payload(
            report_type=123,
        ),
    )

    assert_error_response(response, 422)


def test_create_campaign_report_accepts_private_report(client, owner_headers):
    response = client.post(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports",
        headers=owner_headers,
        json=valid_report_payload(
            is_public=False,
        ),
    )

    assert response.status_code in (200, 201)
    assert response.json()["is_public"] is False


def test_create_campaign_report_accepts_empty_media_lists(
    client,
    owner_headers,
):
    response = client.post(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports",
        headers=owner_headers,
        json=valid_report_payload(
            image_file_ids=[],
            attachment_file_ids=[],
        ),
    )

    assert response.status_code in (200, 201)


def test_create_campaign_report_rejects_invalid_image_file_ids_type(
    client,
    owner_headers,
):
    response = client.post(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports",
        headers=owner_headers,
        json=valid_report_payload(
            image_file_ids="not-list",
        ),
    )

    assert_error_response(response, 422)


def test_create_campaign_report_rejects_invalid_image_file_id_item(
    client,
    owner_headers,
):
    response = client.post(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports",
        headers=owner_headers,
        json=valid_report_payload(
            image_file_ids=[1, "bad"],
        ),
    )

    assert_error_response(response, 422)


def test_create_campaign_report_rejects_negative_image_file_id(
    client,
    owner_headers,
):
    response = client.post(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports",
        headers=owner_headers,
        json=valid_report_payload(
            image_file_ids=[-1],
        ),
    )

    assert_error_response(response, 422)


def test_create_campaign_report_rejects_invalid_attachment_file_ids_type(
    client,
    owner_headers,
):
    response = client.post(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports",
        headers=owner_headers,
        json=valid_report_payload(
            attachment_file_ids="not-list",
        ),
    )

    assert_error_response(response, 422)


def test_create_campaign_report_rejects_invalid_attachment_file_id_item(
    client,
    owner_headers,
):
    response = client.post(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports",
        headers=owner_headers,
        json=valid_report_payload(
            attachment_file_ids=[3, "bad"],
        ),
    )

    assert_error_response(response, 422)


def test_create_campaign_report_rejects_invalid_is_public_type(
    client,
    owner_headers,
):
    response = client.post(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports",
        headers=owner_headers,
        json=valid_report_payload(
            is_public="not-bool",
        ),
    )

    assert_error_response(response, 422)


def test_create_campaign_report_ignores_extra_fields_current_contract(
    client,
    owner_headers,
):
    response = client.post(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports",
        headers=owner_headers,
        json=valid_report_payload(
            author_id="11111111-1111-1111-1111-111111111111",
            created_at="2026-01-01T12:00:00Z",
        ),
    )

    assert response.status_code in (200, 201)
    assert response.json()["title"] == "گزارش پیشرفت تست"


# ============================================================
# List Campaign Reports
# GET /api/v1/campaigns/{campaign_id}/reports
# ============================================================

def test_list_campaign_reports_success_for_donor(client, auth_headers):
    response = client.get(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports",
        headers=auth_headers,
    )

    assert response.status_code == 200

    body = response.json()
    assert isinstance(body, list)
    assert len(body) == 1
    assert body[0]["campaign_id"] == str(CAMPAIGN_ID)
    assert body[0]["title"] == "گزارش پیشرفت تست"


def test_list_campaign_reports_success_for_charity_owner(client, owner_headers):
    response = client.get(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports",
        headers=owner_headers,
    )

    assert response.status_code == 200


def test_list_campaign_reports_success_for_verifier(client, verifier_headers):
    response = client.get(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports",
        headers=verifier_headers,
    )

    assert response.status_code == 200


def test_list_campaign_reports_success_for_admin(client, admin_headers):
    response = client.get(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports",
        headers=admin_headers,
    )

    assert response.status_code == 200


def test_list_campaign_reports_requires_authentication(client):
    response = client.get(f"/api/v1/campaigns/{CAMPAIGN_ID}/reports")

    assert response.status_code in (401, 403)


def test_list_campaign_reports_rejects_invalid_token(
    client,
    invalid_auth_headers,
):
    response = client.get(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports",
        headers=invalid_auth_headers,
    )

    assert response.status_code in (401, 403)


def test_list_campaign_reports_returns_404_for_missing_campaign(
    client,
    auth_headers,
):
    response = client.get(
        f"/api/v1/campaigns/{MISSING_ID}/reports",
        headers=auth_headers,
    )

    assert_error_response(response, 404)


def test_list_campaign_reports_rejects_invalid_campaign_uuid(
    client,
    auth_headers,
):
    response = client.get(
        "/api/v1/campaigns/not-a-uuid/reports",
        headers=auth_headers,
    )

    assert_error_response(response, 422)


# ============================================================
# Get Campaign Report Detail
# GET /api/v1/campaigns/{campaign_id}/reports/{report_id}
# ============================================================

def test_get_campaign_report_detail_success_for_donor(client, auth_headers):
    response = client.get(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports/{REPORT_ID}",
        headers=auth_headers,
    )

    assert response.status_code == 200

    body = response.json()
    assert body["id"] == str(REPORT_ID)
    assert body["campaign_id"] == str(CAMPAIGN_ID)
    assert body["title"] == "گزارش پیشرفت تست"
    assert body["is_public"] is True


def test_get_campaign_report_detail_success_for_charity_owner(
    client,
    owner_headers,
):
    response = client.get(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports/{REPORT_ID}",
        headers=owner_headers,
    )

    assert response.status_code == 200


def test_get_campaign_report_detail_success_for_verifier(
    client,
    verifier_headers,
):
    response = client.get(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports/{REPORT_ID}",
        headers=verifier_headers,
    )

    assert response.status_code == 200


def test_get_campaign_report_detail_success_for_admin(client, admin_headers):
    response = client.get(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports/{REPORT_ID}",
        headers=admin_headers,
    )

    assert response.status_code == 200


def test_get_campaign_report_detail_requires_authentication(client):
    response = client.get(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports/{REPORT_ID}",
    )

    assert response.status_code in (401, 403)


def test_get_campaign_report_detail_rejects_invalid_token(
    client,
    invalid_auth_headers,
):
    response = client.get(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports/{REPORT_ID}",
        headers=invalid_auth_headers,
    )

    assert response.status_code in (401, 403)


def test_get_campaign_report_detail_returns_404_for_missing_report(
    client,
    auth_headers,
):
    response = client.get(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports/{MISSING_ID}",
        headers=auth_headers,
    )

    assert_error_response(response, 404)


def test_get_campaign_report_detail_rejects_invalid_campaign_uuid(
    client,
    auth_headers,
):
    response = client.get(
        f"/api/v1/campaigns/not-a-uuid/reports/{REPORT_ID}",
        headers=auth_headers,
    )

    assert_error_response(response, 422)


def test_get_campaign_report_detail_rejects_invalid_report_uuid(
    client,
    auth_headers,
):
    response = client.get(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports/not-a-uuid",
        headers=auth_headers,
    )

    assert_error_response(response, 422)


def test_get_campaign_report_detail_returns_json(client, auth_headers):
    response = client.get(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports/{REPORT_ID}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]


# ============================================================
# Update Campaign Report
# PATCH /api/v1/campaigns/{campaign_id}/reports/{report_id}
# ============================================================

def test_update_campaign_report_success(client, owner_headers):
    response = client.patch(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports/{REPORT_ID}",
        headers=owner_headers,
        json=valid_report_update_payload(),
    )

    assert response.status_code == 200

    body = response.json()
    assert body["id"] == str(REPORT_ID)
    assert body["campaign_id"] == str(CAMPAIGN_ID)
    assert body["title"] == "عنوان ویرایش شده گزارش"


def test_update_campaign_report_requires_authentication(client):
    response = client.patch(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports/{REPORT_ID}",
        json=valid_report_update_payload(),
    )

    assert response.status_code in (401, 403)


def test_update_campaign_report_rejects_invalid_token(
    client,
    invalid_auth_headers,
):
    response = client.patch(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports/{REPORT_ID}",
        headers=invalid_auth_headers,
        json=valid_report_update_payload(),
    )

    assert response.status_code in (401, 403)


def test_update_campaign_report_returns_404_for_missing_report(
    client,
    owner_headers,
):
    response = client.patch(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports/{MISSING_ID}",
        headers=owner_headers,
        json=valid_report_update_payload(),
    )

    assert_error_response(response, 404)


def test_update_campaign_report_rejects_invalid_campaign_uuid(
    client,
    owner_headers,
):
    response = client.patch(
        f"/api/v1/campaigns/not-a-uuid/reports/{REPORT_ID}",
        headers=owner_headers,
        json=valid_report_update_payload(),
    )

    assert_error_response(response, 422)


def test_update_campaign_report_rejects_invalid_report_uuid(
    client,
    owner_headers,
):
    response = client.patch(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports/not-a-uuid",
        headers=owner_headers,
        json=valid_report_update_payload(),
    )

    assert_error_response(response, 422)


def test_update_campaign_report_accepts_partial_update(
    client,
    owner_headers,
):
    response = client.patch(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports/{REPORT_ID}",
        headers=owner_headers,
        json={
            "title": "عنوان جدید گزارش",
        },
    )

    assert response.status_code == 200
    assert response.json()["title"] == "عنوان جدید گزارش"


def test_update_campaign_report_accepts_short_title_current_contract(
    client,
    owner_headers,
):
    response = client.patch(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports/{REPORT_ID}",
        headers=owner_headers,
        json={
            "title": "کم",
        },
    )

    assert response.status_code == 200
    assert response.json()["title"] == "کم"


def test_update_campaign_report_accepts_short_content_current_contract(
    client,
    owner_headers,
):
    response = client.patch(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports/{REPORT_ID}",
        headers=owner_headers,
        json={
            "content": "کوتاه",
        },
    )

    assert response.status_code == 200
    assert response.json()["content"] == "کوتاه"


def test_update_campaign_report_rejects_invalid_report_type(
    client,
    owner_headers,
):
    response = client.patch(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports/{REPORT_ID}",
        headers=owner_headers,
        json={
            "report_type": 123,
        },
    )

    assert_error_response(response, 422)


def test_update_campaign_report_rejects_invalid_image_file_ids_type(
    client,
    owner_headers,
):
    response = client.patch(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports/{REPORT_ID}",
        headers=owner_headers,
        json={
            "image_file_ids": "not-list",
        },
    )

    assert_error_response(response, 422)


def test_update_campaign_report_rejects_invalid_image_file_id_item(
    client,
    owner_headers,
):
    response = client.patch(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports/{REPORT_ID}",
        headers=owner_headers,
        json={
            "image_file_ids": [1, "bad"],
        },
    )

    assert_error_response(response, 422)


def test_update_campaign_report_rejects_negative_attachment_file_id(
    client,
    owner_headers,
):
    response = client.patch(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports/{REPORT_ID}",
        headers=owner_headers,
        json={
            "attachment_file_ids": [-1],
        },
    )

    assert_error_response(response, 422)


def test_update_campaign_report_rejects_invalid_is_public_type(
    client,
    owner_headers,
):
    response = client.patch(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports/{REPORT_ID}",
        headers=owner_headers,
        json={
            "is_public": "not-bool",
        },
    )

    assert_error_response(response, 422)


def test_update_campaign_report_ignores_extra_fields_current_contract(
    client,
    owner_headers,
):
    response = client.patch(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports/{REPORT_ID}",
        headers=owner_headers,
        json={
            "author_id": "11111111-1111-1111-1111-111111111111",
            "created_at": "2026-01-01T12:00:00Z",
        },
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(REPORT_ID)


# ============================================================
# Delete Campaign Report
# DELETE /api/v1/campaigns/{campaign_id}/reports/{report_id}
# ============================================================

def test_delete_campaign_report_success(client, owner_headers):
    response = client.delete(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports/{REPORT_ID}",
        headers=owner_headers,
    )

    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "success"
    assert "message" in body


def test_delete_campaign_report_requires_authentication(client):
    response = client.delete(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports/{REPORT_ID}",
    )

    assert response.status_code in (401, 403)


def test_delete_campaign_report_rejects_invalid_token(
    client,
    invalid_auth_headers,
):
    response = client.delete(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports/{REPORT_ID}",
        headers=invalid_auth_headers,
    )

    assert response.status_code in (401, 403)


def test_delete_campaign_report_returns_404_for_missing_report(
    client,
    owner_headers,
):
    response = client.delete(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports/{MISSING_ID}",
        headers=owner_headers,
    )

    assert_error_response(response, 404)


def test_delete_campaign_report_rejects_invalid_campaign_uuid(
    client,
    owner_headers,
):
    response = client.delete(
        f"/api/v1/campaigns/not-a-uuid/reports/{REPORT_ID}",
        headers=owner_headers,
    )

    assert_error_response(response, 422)


def test_delete_campaign_report_rejects_invalid_report_uuid(
    client,
    owner_headers,
):
    response = client.delete(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/reports/not-a-uuid",
        headers=owner_headers,
    )

    assert_error_response(response, 422)