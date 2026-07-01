from tests.conftest import CAMPAIGN_ID, MISSING_ID, PROFILE_ID


def assert_error_response(response, expected_status: int | tuple[int, ...]):
    if isinstance(expected_status, int):
        expected_status = (expected_status,)

    assert response.status_code in expected_status

    body = response.json()
    assert isinstance(body, dict)
    assert "detail" in body or "message" in body or "errors" in body


def valid_campaign_payload(**overrides):
    payload = {
        "title": "پویش تست",
        "description": "این توضیح کامل پویش تست است و برای بررسی ساخت پویش استفاده می‌شود.",
        "short_description": "توضیح کوتاه پویش تست",
        "category": "education",
        "target_amount": 1000000,
        "start_date": None,
        "end_date": None,
        "cover_image_file_id": 1,
        "gallery_file_ids": [2, 3],
        "attachment_file_ids": [4],
    }

    payload.update(overrides)
    return payload


def valid_campaign_update_payload(**overrides):
    payload = {
        "title": "عنوان ویرایش شده پویش",
        "description": "این توضیح کامل ویرایش شده برای پویش تست است.",
        "short_description": "توضیح کوتاه ویرایش شده",
        "category": "education",
        "target_amount": 2000000,
        "start_date": None,
        "end_date": None,
        "cover_image_file_id": 5,
        "gallery_file_ids": [6, 7],
        "attachment_file_ids": [8],
    }

    payload.update(overrides)
    return payload


# ============================================================
# Create Campaign
# POST /api/v1/campaigns/
# ============================================================

def test_create_campaign_success(client, owner_headers):
    response = client.post(
        "/api/v1/campaigns/",
        headers=owner_headers,
        json=valid_campaign_payload(),
    )

    assert response.status_code in (200, 201)

    body = response.json()
    assert body["title"] == "پویش تست"
    assert body["status"] == "pending_review"
    assert body["charity_id"] == str(PROFILE_ID)
    assert int(body["target_amount"]) == 1000000
    assert body["cover_image_file_id"] == 1
    assert body["gallery_file_ids"] == [2, 3]
    assert body["attachment_file_ids"] == [4]


def test_create_campaign_requires_authentication(client):
    response = client.post(
        "/api/v1/campaigns/",
        json=valid_campaign_payload(),
    )

    assert response.status_code in (401, 403)


def test_create_campaign_rejects_invalid_token(client, invalid_auth_headers):
    response = client.post(
        "/api/v1/campaigns/",
        headers=invalid_auth_headers,
        json=valid_campaign_payload(),
    )

    assert response.status_code in (401, 403)


def test_create_campaign_accepts_donor_role_current_contract(
    client,
    auth_headers,
):
    response = client.post(
        "/api/v1/campaigns/",
        headers=auth_headers,
        json=valid_campaign_payload(),
    )

    assert response.status_code in (200, 201)


def test_create_campaign_allows_charity_owner(client, owner_headers):
    response = client.post(
        "/api/v1/campaigns/",
        headers=owner_headers,
        json=valid_campaign_payload(),
    )

    assert response.status_code in (200, 201)


def test_create_campaign_rejects_duplicate_or_invalid_business_case(
    client,
    owner_headers,
):
    response = client.post(
        "/api/v1/campaigns/",
        headers=owner_headers,
        json=valid_campaign_payload(
            title="duplicate",
        ),
    )

    assert_error_response(response, 400)


def test_create_campaign_rejects_missing_title(client, owner_headers):
    payload = valid_campaign_payload()
    payload.pop("title")

    response = client.post(
        "/api/v1/campaigns/",
        headers=owner_headers,
        json=payload,
    )

    assert_error_response(response, 422)


def test_create_campaign_accepts_short_title(client, owner_headers):
    response = client.post(
        "/api/v1/campaigns/",
        headers=owner_headers,
        json=valid_campaign_payload(
            title="کم",
        ),
    )

    assert response.status_code in (200, 201)


def test_create_campaign_rejects_missing_description(client, owner_headers):
    payload = valid_campaign_payload()
    payload.pop("description")

    response = client.post(
        "/api/v1/campaigns/",
        headers=owner_headers,
        json=payload,
    )

    assert_error_response(response, 422)


def test_create_campaign_accepts_short_description(client, owner_headers):
    response = client.post(
        "/api/v1/campaigns/",
        headers=owner_headers,
        json=valid_campaign_payload(
            description="کوتاه",
        ),
    )

    assert response.status_code in (200, 201)


def test_create_campaign_rejects_missing_short_description(
    client,
    owner_headers,
):
    payload = valid_campaign_payload()
    payload.pop("short_description")

    response = client.post(
        "/api/v1/campaigns/",
        headers=owner_headers,
        json=payload,
    )

    assert_error_response(response, 422)


def test_create_campaign_accepts_short_short_description(
    client,
    owner_headers,
):
    response = client.post(
        "/api/v1/campaigns/",
        headers=owner_headers,
        json=valid_campaign_payload(
            short_description="کم",
        ),
    )

    assert response.status_code in (200, 201)


def test_create_campaign_rejects_missing_category(client, owner_headers):
    payload = valid_campaign_payload()
    payload.pop("category")

    response = client.post(
        "/api/v1/campaigns/",
        headers=owner_headers,
        json=payload,
    )

    assert_error_response(response, 422)


def test_create_campaign_rejects_invalid_category_type(client, owner_headers):
    response = client.post(
        "/api/v1/campaigns/",
        headers=owner_headers,
        json=valid_campaign_payload(
            category=123,
        ),
    )

    assert_error_response(response, 422)


def test_create_campaign_rejects_missing_target_amount(client, owner_headers):
    payload = valid_campaign_payload()
    payload.pop("target_amount")

    response = client.post(
        "/api/v1/campaigns/",
        headers=owner_headers,
        json=payload,
    )

    assert_error_response(response, 422)


def test_create_campaign_rejects_zero_target_amount(client, owner_headers):
    response = client.post(
        "/api/v1/campaigns/",
        headers=owner_headers,
        json=valid_campaign_payload(
            target_amount=0,
        ),
    )

    assert_error_response(response, 422)


def test_create_campaign_rejects_negative_target_amount(client, owner_headers):
    response = client.post(
        "/api/v1/campaigns/",
        headers=owner_headers,
        json=valid_campaign_payload(
            target_amount=-1000,
        ),
    )

    assert_error_response(response, 422)


def test_create_campaign_rejects_non_numeric_target_amount(
    client,
    owner_headers,
):
    response = client.post(
        "/api/v1/campaigns/",
        headers=owner_headers,
        json=valid_campaign_payload(
            target_amount="not-number",
        ),
    )

    assert_error_response(response, 422)


def test_create_campaign_accepts_missing_optional_dates(client, owner_headers):
    response = client.post(
        "/api/v1/campaigns/",
        headers=owner_headers,
        json=valid_campaign_payload(
            start_date=None,
            end_date=None,
        ),
    )

    assert response.status_code in (200, 201)


def test_create_campaign_rejects_invalid_start_date(client, owner_headers):
    response = client.post(
        "/api/v1/campaigns/",
        headers=owner_headers,
        json=valid_campaign_payload(
            start_date="not-a-date",
        ),
    )

    assert_error_response(response, 422)


def test_create_campaign_rejects_invalid_end_date(client, owner_headers):
    response = client.post(
        "/api/v1/campaigns/",
        headers=owner_headers,
        json=valid_campaign_payload(
            end_date="not-a-date",
        ),
    )

    assert_error_response(response, 422)


def test_create_campaign_accepts_negative_cover_file_id(client, owner_headers):
    response = client.post(
        "/api/v1/campaigns/",
        headers=owner_headers,
        json=valid_campaign_payload(
            cover_image_file_id=-1,
        ),
    )

    assert response.status_code in (200, 201)


def test_create_campaign_rejects_non_integer_cover_file_id(
    client,
    owner_headers,
):
    response = client.post(
        "/api/v1/campaigns/",
        headers=owner_headers,
        json=valid_campaign_payload(
            cover_image_file_id="not-number",
        ),
    )

    assert_error_response(response, 422)


def test_create_campaign_accepts_empty_gallery_and_attachments(
    client,
    owner_headers,
):
    response = client.post(
        "/api/v1/campaigns/",
        headers=owner_headers,
        json=valid_campaign_payload(
            gallery_file_ids=[],
            attachment_file_ids=[],
        ),
    )

    assert response.status_code in (200, 201)


def test_create_campaign_rejects_invalid_gallery_type(client, owner_headers):
    response = client.post(
        "/api/v1/campaigns/",
        headers=owner_headers,
        json=valid_campaign_payload(
            gallery_file_ids="not-list",
        ),
    )

    assert_error_response(response, 422)


def test_create_campaign_rejects_invalid_gallery_item(client, owner_headers):
    response = client.post(
        "/api/v1/campaigns/",
        headers=owner_headers,
        json=valid_campaign_payload(
            gallery_file_ids=[1, "bad"],
        ),
    )

    assert_error_response(response, 422)


def test_create_campaign_rejects_invalid_attachment_type(client, owner_headers):
    response = client.post(
        "/api/v1/campaigns/",
        headers=owner_headers,
        json=valid_campaign_payload(
            attachment_file_ids="not-list",
        ),
    )

    assert_error_response(response, 422)


def test_create_campaign_ignores_extra_fields(client, owner_headers):
    response = client.post(
        "/api/v1/campaigns/",
        headers=owner_headers,
        json=valid_campaign_payload(
            status="active",
            collected_amount=999999999,
        ),
    )

    assert response.status_code in (200, 201)


# ============================================================
# List Campaigns
# GET /api/v1/campaigns/
# ============================================================

def test_list_campaigns_success(client, auth_headers):
    response = client.get(
        "/api/v1/campaigns/",
        headers=auth_headers,
    )

    assert response.status_code == 200

    body = response.json()
    assert isinstance(body, list)
    assert len(body) == 1
    assert body[0]["id"] == str(CAMPAIGN_ID)
    assert body[0]["title"] == "پویش تست"


def test_list_campaigns_requires_authentication(client):
    response = client.get("/api/v1/campaigns/")

    assert response.status_code in (401, 403)


def test_list_campaigns_rejects_invalid_token(client, invalid_auth_headers):
    response = client.get(
        "/api/v1/campaigns/",
        headers=invalid_auth_headers,
    )

    assert response.status_code in (401, 403)


def test_list_campaigns_accepts_valid_auth_token(client, auth_headers):
    response = client.get(
        "/api/v1/campaigns/",
        headers=auth_headers,
    )

    assert response.status_code == 200


def test_list_campaigns_accepts_pagination(client, auth_headers):
    response = client.get(
        "/api/v1/campaigns/",
        headers=auth_headers,
        params={
            "skip": 0,
            "limit": 20,
        },
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_campaigns_accepts_charity_id_filter(client, auth_headers):
    response = client.get(
        "/api/v1/campaigns/",
        headers=auth_headers,
        params={
            "charity_id": str(PROFILE_ID),
        },
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_campaigns_rejects_invalid_charity_id(client, auth_headers):
    response = client.get(
        "/api/v1/campaigns/",
        headers=auth_headers,
        params={
            "charity_id": "not-a-uuid",
        },
    )

    assert_error_response(response, 422)


def test_list_campaigns_accepts_negative_skip_current_contract(
    client,
    auth_headers,
):
    response = client.get(
        "/api/v1/campaigns/",
        headers=auth_headers,
        params={
            "skip": -1,
        },
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_campaigns_accepts_limit_less_than_one_current_contract(
    client,
    auth_headers,
):
    response = client.get(
        "/api/v1/campaigns/",
        headers=auth_headers,
        params={
            "limit": 0,
        },
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_campaigns_rejects_non_integer_skip(client, auth_headers):
    response = client.get(
        "/api/v1/campaigns/",
        headers=auth_headers,
        params={
            "skip": "not-number",
        },
    )

    assert_error_response(response, 422)


def test_list_campaigns_rejects_non_integer_limit(client, auth_headers):
    response = client.get(
        "/api/v1/campaigns/",
        headers=auth_headers,
        params={
            "limit": "not-number",
        },
    )

    assert_error_response(response, 422)


# ============================================================
# Get Campaign Detail
# GET /api/v1/campaigns/{campaign_id}
# ============================================================

def test_get_campaign_detail_success(client, auth_headers):
    response = client.get(
        f"/api/v1/campaigns/{CAMPAIGN_ID}",
        headers=auth_headers,
    )

    assert response.status_code == 200

    body = response.json()
    assert body["id"] == str(CAMPAIGN_ID)
    assert body["title"] == "پویش تست"
    assert body["status"] == "active"
    assert body["charity_id"] == str(PROFILE_ID)


def test_get_campaign_detail_requires_authentication(client):
    response = client.get(f"/api/v1/campaigns/{CAMPAIGN_ID}")

    assert response.status_code in (401, 403)


def test_get_campaign_detail_rejects_invalid_token(
    client,
    invalid_auth_headers,
):
    response = client.get(
        f"/api/v1/campaigns/{CAMPAIGN_ID}",
        headers=invalid_auth_headers,
    )

    assert response.status_code in (401, 403)


def test_get_campaign_detail_accepts_authenticated_user(client, auth_headers):
    response = client.get(
        f"/api/v1/campaigns/{CAMPAIGN_ID}",
        headers=auth_headers,
    )

    assert response.status_code == 200


def test_get_campaign_detail_returns_404_for_missing_campaign(
    client,
    auth_headers,
):
    response = client.get(
        f"/api/v1/campaigns/{MISSING_ID}",
        headers=auth_headers,
    )

    assert_error_response(response, 404)


def test_get_campaign_detail_rejects_invalid_campaign_uuid(
    client,
    auth_headers,
):
    response = client.get(
        "/api/v1/campaigns/not-a-uuid",
        headers=auth_headers,
    )

    assert_error_response(response, 422)


def test_get_campaign_detail_returns_json(client, auth_headers):
    response = client.get(
        f"/api/v1/campaigns/{CAMPAIGN_ID}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]


# ============================================================
# Update Campaign
# PUT /api/v1/campaigns/{campaign_id}
# ============================================================

def test_update_campaign_success(client, owner_headers):
    response = client.put(
        f"/api/v1/campaigns/{CAMPAIGN_ID}",
        headers=owner_headers,
        json=valid_campaign_update_payload(),
    )

    assert response.status_code == 200

    body = response.json()
    assert body["id"] == str(CAMPAIGN_ID)
    assert body["title"] == "عنوان ویرایش شده پویش"
    assert body["status"] == "draft"


def test_update_campaign_requires_authentication(client):
    response = client.put(
        f"/api/v1/campaigns/{CAMPAIGN_ID}",
        json=valid_campaign_update_payload(),
    )

    assert response.status_code in (401, 403)


def test_update_campaign_rejects_invalid_token(client, invalid_auth_headers):
    response = client.put(
        f"/api/v1/campaigns/{CAMPAIGN_ID}",
        headers=invalid_auth_headers,
        json=valid_campaign_update_payload(),
    )

    assert response.status_code in (401, 403)


def test_update_campaign_accepts_donor_role_current_contract(
    client,
    auth_headers,
):
    response = client.put(
        f"/api/v1/campaigns/{CAMPAIGN_ID}",
        headers=auth_headers,
        json=valid_campaign_update_payload(),
    )

    assert response.status_code == 200


def test_update_campaign_returns_404_for_missing_campaign(
    client,
    owner_headers,
):
    response = client.put(
        f"/api/v1/campaigns/{MISSING_ID}",
        headers=owner_headers,
        json=valid_campaign_update_payload(),
    )

    assert_error_response(response, 404)


def test_update_campaign_rejects_invalid_campaign_uuid(client, owner_headers):
    response = client.put(
        "/api/v1/campaigns/not-a-uuid",
        headers=owner_headers,
        json=valid_campaign_update_payload(),
    )

    assert_error_response(response, 422)


def test_update_campaign_accepts_partial_update(client, owner_headers):
    response = client.put(
        f"/api/v1/campaigns/{CAMPAIGN_ID}",
        headers=owner_headers,
        json={
            "title": "عنوان جدید پویش",
        },
    )

    assert response.status_code == 200
    assert response.json()["title"] == "عنوان جدید پویش"


def test_update_campaign_accepts_short_title(client, owner_headers):
    response = client.put(
        f"/api/v1/campaigns/{CAMPAIGN_ID}",
        headers=owner_headers,
        json={
            "title": "کم",
        },
    )

    assert response.status_code == 200


def test_update_campaign_accepts_short_description(client, owner_headers):
    response = client.put(
        f"/api/v1/campaigns/{CAMPAIGN_ID}",
        headers=owner_headers,
        json={
            "description": "کوتاه",
        },
    )

    assert response.status_code == 200


def test_update_campaign_rejects_zero_target_amount(client, owner_headers):
    response = client.put(
        f"/api/v1/campaigns/{CAMPAIGN_ID}",
        headers=owner_headers,
        json={
            "target_amount": 0,
        },
    )

    assert_error_response(response, 422)


def test_update_campaign_rejects_negative_target_amount(client, owner_headers):
    response = client.put(
        f"/api/v1/campaigns/{CAMPAIGN_ID}",
        headers=owner_headers,
        json={
            "target_amount": -1000,
        },
    )

    assert_error_response(response, 422)


def test_update_campaign_rejects_non_numeric_target_amount(
    client,
    owner_headers,
):
    response = client.put(
        f"/api/v1/campaigns/{CAMPAIGN_ID}",
        headers=owner_headers,
        json={
            "target_amount": "not-number",
        },
    )

    assert_error_response(response, 422)


def test_update_campaign_rejects_invalid_start_date(client, owner_headers):
    response = client.put(
        f"/api/v1/campaigns/{CAMPAIGN_ID}",
        headers=owner_headers,
        json={
            "start_date": "not-a-date",
        },
    )

    assert_error_response(response, 422)


def test_update_campaign_rejects_invalid_end_date(client, owner_headers):
    response = client.put(
        f"/api/v1/campaigns/{CAMPAIGN_ID}",
        headers=owner_headers,
        json={
            "end_date": "not-a-date",
        },
    )

    assert_error_response(response, 422)


def test_update_campaign_accepts_negative_cover_file_id(
    client,
    owner_headers,
):
    response = client.put(
        f"/api/v1/campaigns/{CAMPAIGN_ID}",
        headers=owner_headers,
        json={
            "cover_image_file_id": -1,
        },
    )

    assert response.status_code == 200


def test_update_campaign_rejects_invalid_gallery_type(client, owner_headers):
    response = client.put(
        f"/api/v1/campaigns/{CAMPAIGN_ID}",
        headers=owner_headers,
        json={
            "gallery_file_ids": "not-list",
        },
    )

    assert_error_response(response, 422)


def test_update_campaign_rejects_invalid_attachment_item(
    client,
    owner_headers,
):
    response = client.put(
        f"/api/v1/campaigns/{CAMPAIGN_ID}",
        headers=owner_headers,
        json={
            "attachment_file_ids": [1, "bad"],
        },
    )

    assert_error_response(response, 422)


def test_update_campaign_ignores_extra_fields(client, owner_headers):
    response = client.put(
        f"/api/v1/campaigns/{CAMPAIGN_ID}",
        headers=owner_headers,
        json={
            "status": "active",
            "collected_amount": 999999999,
        },
    )

    assert response.status_code == 200


def test_patch_campaign_is_not_allowed(client, owner_headers):
    response = client.patch(
        f"/api/v1/campaigns/{CAMPAIGN_ID}",
        headers=owner_headers,
        json=valid_campaign_update_payload(),
    )

    assert_error_response(response, 405)


# ============================================================
# Delete Campaign
# DELETE /api/v1/campaigns/{campaign_id}
# ============================================================

def test_delete_campaign_success(client, owner_headers):
    response = client.delete(
        f"/api/v1/campaigns/{CAMPAIGN_ID}",
        headers=owner_headers,
    )

    assert response.status_code in (200, 204)

    if response.status_code != 204:
        body = response.json()
        assert isinstance(body, dict)


def test_delete_campaign_requires_authentication(client):
    response = client.delete(f"/api/v1/campaigns/{CAMPAIGN_ID}")

    assert response.status_code in (401, 403)


def test_delete_campaign_rejects_invalid_token(client, invalid_auth_headers):
    response = client.delete(
        f"/api/v1/campaigns/{CAMPAIGN_ID}",
        headers=invalid_auth_headers,
    )

    assert response.status_code in (401, 403)


def test_delete_campaign_accepts_donor_role_current_contract(
    client,
    auth_headers,
):
    response = client.delete(
        f"/api/v1/campaigns/{CAMPAIGN_ID}",
        headers=auth_headers,
    )

    assert response.status_code in (200, 204)


def test_delete_campaign_returns_404_for_missing_campaign(
    client,
    owner_headers,
):
    response = client.delete(
        f"/api/v1/campaigns/{MISSING_ID}",
        headers=owner_headers,
    )

    assert_error_response(response, 404)


def test_delete_campaign_rejects_invalid_campaign_uuid(client, owner_headers):
    response = client.delete(
        "/api/v1/campaigns/not-a-uuid",
        headers=owner_headers,
    )

    assert_error_response(response, 422)