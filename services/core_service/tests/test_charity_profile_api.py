from tests.conftest import MISSING_ID, PROFILE_ID


def assert_error_response(response, expected_status: int | tuple[int, ...]):
    if isinstance(expected_status, int):
        expected_status = (expected_status,)

    assert response.status_code in expected_status

    body = response.json()
    assert isinstance(body, dict)
    assert "detail" in body or "message" in body or "errors" in body


def valid_profile_update_payload(**overrides):
    payload = {
        "logo_file_id": 10,
        "cover_file_id": 11,
        "short_description": "توضیح کوتاه موسسه برای تست پروفایل خیریه",
        "about_text": "این متن درباره موسسه تستی است و برای تست API پروفایل استفاده می‌شود.",
        "vision_text": "چشم‌انداز این موسسه تستی کمک به آموزش و توانمندسازی است.",
        "social_links": {
            "instagram": "https://instagram.com/test_charity",
            "website": "https://example.org",
        },
    }

    payload.update(overrides)
    return payload


# ============================================================
# Get My Charity Profile
# GET /api/v1/charity/profile/me
# ============================================================

def test_get_my_charity_profile_success(client, owner_headers):
    response = client.get(
        "/api/v1/charity/profile/me",
        headers=owner_headers,
    )

    assert response.status_code == 200

    body = response.json()
    assert body["has_profile"] is True
    assert body["profile"]["id"] == str(PROFILE_ID)
    assert body["profile"]["charity_name"] == "موسسه تست نیکوکاری"
    assert body["profile"]["slug"] == "test-charity"


def test_get_my_charity_profile_requires_authentication(client):
    response = client.get("/api/v1/charity/profile/me")

    assert response.status_code in (401, 403)


def test_get_my_charity_profile_rejects_invalid_token(
    client,
    invalid_auth_headers,
):
    response = client.get(
        "/api/v1/charity/profile/me",
        headers=invalid_auth_headers,
    )

    assert response.status_code in (401, 403)


def test_get_my_charity_profile_allows_charity_owner(client, owner_headers):
    response = client.get(
        "/api/v1/charity/profile/me",
        headers=owner_headers,
    )

    assert response.status_code == 200


def test_get_my_charity_profile_returns_json(client, owner_headers):
    response = client.get(
        "/api/v1/charity/profile/me",
        headers=owner_headers,
    )

    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]


# ============================================================
# Update My Charity Profile
# PATCH /api/v1/charity/profile/{profile_id}
# ============================================================

def test_update_my_charity_profile_success(client, owner_headers):
    response = client.patch(
        f"/api/v1/charity/profile/{PROFILE_ID}",
        headers=owner_headers,
        json=valid_profile_update_payload(),
    )

    assert response.status_code == 200

    body = response.json()
    assert body["id"] == str(PROFILE_ID)
    assert body["status"] == "incomplete"
    assert body["is_published"] is False
    assert body["logo_file_id"] == 10
    assert body["cover_file_id"] == 11


def test_update_my_charity_profile_requires_authentication(client):
    response = client.patch(
        f"/api/v1/charity/profile/{PROFILE_ID}",
        json=valid_profile_update_payload(),
    )

    assert response.status_code in (401, 403)


def test_update_my_charity_profile_rejects_invalid_token(
    client,
    invalid_auth_headers,
):
    response = client.patch(
        f"/api/v1/charity/profile/{PROFILE_ID}",
        headers=invalid_auth_headers,
        json=valid_profile_update_payload(),
    )

    assert response.status_code in (401, 403)


def test_update_my_charity_profile_returns_404_for_missing_profile(
    client,
    owner_headers,
):
    response = client.patch(
        f"/api/v1/charity/profile/{MISSING_ID}",
        headers=owner_headers,
        json=valid_profile_update_payload(),
    )

    assert_error_response(response, 404)


def test_update_my_charity_profile_rejects_invalid_profile_uuid(
    client,
    owner_headers,
):
    response = client.patch(
        "/api/v1/charity/profile/not-a-uuid",
        headers=owner_headers,
        json=valid_profile_update_payload(),
    )

    assert_error_response(response, 422)


def test_update_my_charity_profile_accepts_partial_update(
    client,
    owner_headers,
):
    response = client.patch(
        f"/api/v1/charity/profile/{PROFILE_ID}",
        headers=owner_headers,
        json={
            "short_description": "توضیح کوتاه جدید برای تست",
        },
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(PROFILE_ID)


def test_update_my_charity_profile_accepts_short_description(
    client,
    owner_headers,
):
    response = client.patch(
        f"/api/v1/charity/profile/{PROFILE_ID}",
        headers=owner_headers,
        json=valid_profile_update_payload(
            short_description="کوتاه",
        ),
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(PROFILE_ID)


def test_update_my_charity_profile_accepts_short_about_text(
    client,
    owner_headers,
):
    response = client.patch(
        f"/api/v1/charity/profile/{PROFILE_ID}",
        headers=owner_headers,
        json=valid_profile_update_payload(
            about_text="کوتاه",
        ),
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(PROFILE_ID)


def test_update_my_charity_profile_accepts_negative_logo_file_id(
    client,
    owner_headers,
):
    response = client.patch(
        f"/api/v1/charity/profile/{PROFILE_ID}",
        headers=owner_headers,
        json=valid_profile_update_payload(
            logo_file_id=-1,
        ),
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(PROFILE_ID)


def test_update_my_charity_profile_accepts_negative_cover_file_id(
    client,
    owner_headers,
):
    response = client.patch(
        f"/api/v1/charity/profile/{PROFILE_ID}",
        headers=owner_headers,
        json=valid_profile_update_payload(
            cover_file_id=-1,
        ),
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(PROFILE_ID)


def test_update_my_charity_profile_rejects_non_integer_logo_file_id(
    client,
    owner_headers,
):
    response = client.patch(
        f"/api/v1/charity/profile/{PROFILE_ID}",
        headers=owner_headers,
        json=valid_profile_update_payload(
            logo_file_id="not-number",
        ),
    )

    assert_error_response(response, 422)


def test_update_my_charity_profile_rejects_invalid_social_links_type(
    client,
    owner_headers,
):
    response = client.patch(
        f"/api/v1/charity/profile/{PROFILE_ID}",
        headers=owner_headers,
        json=valid_profile_update_payload(
            social_links="not-object",
        ),
    )

    assert_error_response(response, 422)


def test_update_my_charity_profile_ignores_extra_fields(
    client,
    owner_headers,
):
    response = client.patch(
        f"/api/v1/charity/profile/{PROFILE_ID}",
        headers=owner_headers,
        json=valid_profile_update_payload(
            role="admin",
        ),
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(PROFILE_ID)


# ============================================================
# Submit Charity Profile
# POST /api/v1/charity/profile/{profile_id}/submit
# ============================================================

def test_submit_charity_profile_success(client, owner_headers):
    response = client.post(
        f"/api/v1/charity/profile/{PROFILE_ID}/submit",
        headers=owner_headers,
    )

    assert response.status_code == 200

    body = response.json()
    assert body["id"] == str(PROFILE_ID)
    assert body["status"] == "pending_review"
    assert "message" in body


def test_submit_charity_profile_requires_authentication(client):
    response = client.post(
        f"/api/v1/charity/profile/{PROFILE_ID}/submit",
    )

    assert response.status_code in (401, 403)


def test_submit_charity_profile_rejects_invalid_token(
    client,
    invalid_auth_headers,
):
    response = client.post(
        f"/api/v1/charity/profile/{PROFILE_ID}/submit",
        headers=invalid_auth_headers,
    )

    assert response.status_code in (401, 403)


def test_submit_charity_profile_returns_404_for_missing_profile(
    client,
    owner_headers,
):
    response = client.post(
        f"/api/v1/charity/profile/{MISSING_ID}/submit",
        headers=owner_headers,
    )

    assert_error_response(response, 404)


def test_submit_charity_profile_rejects_invalid_profile_uuid(
    client,
    owner_headers,
):
    response = client.post(
        "/api/v1/charity/profile/not-a-uuid/submit",
        headers=owner_headers,
    )

    assert_error_response(response, 422)