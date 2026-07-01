from tests.conftest import CAMPAIGN_ID


SKILL_CONTRIBUTION_ID = "12121212-1212-4121-8121-121212121212"


def assert_error_response(response, expected_status: int | tuple[int, ...]):
    if isinstance(expected_status, int):
        expected_status = (expected_status,)

    assert response.status_code in expected_status

    body = response.json()
    assert isinstance(body, dict)
    assert "detail" in body or "message" in body or "errors" in body


def valid_donation_payload(**overrides):
    payload = {
        "amount": 50000,
    }
    payload.update(overrides)
    return payload


def valid_skill_contribution_payload(**overrides):
    payload = {
        "skill_category": "education",
        "skill_title": "تدریس ریاضی",
        "description": "این توضیح برای تست مشارکت مهارتی است و بیشتر از حداقل طول لازم نوشته شده است.",
        "availability": "هفته‌ای دو روز",
        "collaboration_type": "online",
        "contact_phone": "09123456789",
        "document_file_id": "10",
    }
    payload.update(overrides)
    return payload


def valid_skill_decision_payload(**overrides):
    payload = {
        "note": "درخواست بررسی شد.",
    }
    payload.update(overrides)
    return payload


# ============================================================
# Start Donation
# POST /api/v1/campaigns/{campaign_id}/donations
# ============================================================

def test_start_donation_success(client, auth_headers):
    response = client.post(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/donations",
        headers=auth_headers,
        json=valid_donation_payload(),
    )

    assert response.status_code in (200, 201)

    body = response.json()
    assert body["campaign_id"] == str(CAMPAIGN_ID)
    assert str(body["amount"]) in ("50000", "50000.00")
    assert body["provider"] == "zarinpal"
    assert body["payment_status"] == "pending"
    assert "payment_url" in body
    assert "authority" in body


def test_start_donation_requires_authentication(client):
    response = client.post(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/donations",
        json=valid_donation_payload(),
    )

    assert response.status_code in (401, 403)


def test_start_donation_rejects_invalid_token(client, invalid_auth_headers):
    response = client.post(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/donations",
        headers=invalid_auth_headers,
        json=valid_donation_payload(),
    )

    assert response.status_code in (401, 403)


def test_start_donation_rejects_invalid_campaign_uuid(client, auth_headers):
    response = client.post(
        "/api/v1/campaigns/not-a-uuid/donations",
        headers=auth_headers,
        json=valid_donation_payload(),
    )

    assert_error_response(response, 422)


def test_start_donation_rejects_missing_amount(client, auth_headers):
    response = client.post(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/donations",
        headers=auth_headers,
        json={},
    )

    assert_error_response(response, 422)


def test_start_donation_rejects_amount_less_than_minimum(client, auth_headers):
    response = client.post(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/donations",
        headers=auth_headers,
        json=valid_donation_payload(amount=9999),
    )

    assert_error_response(response, 422)


def test_start_donation_rejects_zero_amount(client, auth_headers):
    response = client.post(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/donations",
        headers=auth_headers,
        json=valid_donation_payload(amount=0),
    )

    assert_error_response(response, 422)


def test_start_donation_rejects_negative_amount(client, auth_headers):
    response = client.post(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/donations",
        headers=auth_headers,
        json=valid_donation_payload(amount=-1000),
    )

    assert_error_response(response, 422)


def test_start_donation_rejects_too_large_amount(client, auth_headers):
    response = client.post(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/donations",
        headers=auth_headers,
        json=valid_donation_payload(amount=100000001),
    )

    assert_error_response(response, 422)


def test_start_donation_rejects_non_numeric_amount(client, auth_headers):
    response = client.post(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/donations",
        headers=auth_headers,
        json=valid_donation_payload(amount="not-number"),
    )

    assert_error_response(response, 422)


def test_start_donation_ignores_extra_fields_current_contract(
    client,
    auth_headers,
):
    response = client.post(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/donations",
        headers=auth_headers,
        json=valid_donation_payload(
            status="paid",
            donor_id="11111111-1111-1111-1111-111111111111",
        ),
    )

    assert response.status_code in (200, 201)
    assert response.json()["campaign_id"] == str(CAMPAIGN_ID)


# ============================================================
# Payment Callback
# GET /api/v1/payments/callback
# ============================================================

def test_payment_callback_success(client):
    response = client.get(
        "/api/v1/payments/callback",
        params={
            "Authority": "A000000000000000000000000000001",
            "Status": "OK",
        },
    )

    assert response.status_code == 200

    body = response.json()
    assert body["campaign_id"] == str(CAMPAIGN_ID)
    assert body["status"] in ("success", "failed", "canceled", "pending")
    assert "message" in body


def test_payment_callback_rejects_missing_authority(client):
    response = client.get(
        "/api/v1/payments/callback",
        params={
            "Status": "OK",
        },
    )

    assert_error_response(response, 422)


def test_payment_callback_rejects_missing_status(client):
    response = client.get(
        "/api/v1/payments/callback",
        params={
            "Authority": "A000000000000000000000000000001",
        },
    )

    assert_error_response(response, 422)


def test_payment_callback_accepts_failed_status(client):
    response = client.get(
        "/api/v1/payments/callback",
        params={
            "Authority": "A000000000000000000000000000001",
            "Status": "NOK",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] in ("success", "failed", "canceled", "pending")


# ============================================================
# My Donations
# GET /api/v1/me/donations
# ============================================================

def test_list_my_donations_success(client, auth_headers):
    response = client.get(
        "/api/v1/me/donations",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_my_donations_requires_authentication(client):
    response = client.get("/api/v1/me/donations")

    assert response.status_code in (401, 403)


def test_list_my_donations_rejects_invalid_token(client, invalid_auth_headers):
    response = client.get(
        "/api/v1/me/donations",
        headers=invalid_auth_headers,
    )

    assert response.status_code in (401, 403)


def test_list_my_donations_returns_json(client, auth_headers):
    response = client.get(
        "/api/v1/me/donations",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]


# ============================================================
# Campaign Donations
# GET /api/v1/campaigns/{campaign_id}/donations
# ============================================================

def test_list_campaign_donations_rejects_donor_current_contract(
    client,
    auth_headers,
):
    response = client.get(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/donations",
        headers=auth_headers,
    )

    assert_error_response(response, 403)


def test_list_campaign_donations_success_for_owner(client, owner_headers):
    response = client.get(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/donations",
        headers=owner_headers,
    )

    assert response.status_code == 200


def test_list_campaign_donations_success_for_admin(client, admin_headers):
    response = client.get(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/donations",
        headers=admin_headers,
    )

    assert response.status_code == 200


def test_list_campaign_donations_requires_authentication(client):
    response = client.get(f"/api/v1/campaigns/{CAMPAIGN_ID}/donations")

    assert response.status_code in (401, 403)


def test_list_campaign_donations_rejects_invalid_campaign_uuid(
    client,
    auth_headers,
):
    response = client.get(
        "/api/v1/campaigns/not-a-uuid/donations",
        headers=auth_headers,
    )

    assert_error_response(response, 422)


# ============================================================
# Create Skill Contribution
# POST /api/v1/campaigns/{campaign_id}/skill-contributions
# ============================================================

def test_create_skill_contribution_success(client, auth_headers):
    response = client.post(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/skill-contributions",
        headers=auth_headers,
        json=valid_skill_contribution_payload(),
    )

    assert response.status_code in (200, 201)

    body = response.json()
    assert body["campaign_id"] == str(CAMPAIGN_ID)
    assert body["skill_category"] == "education"
    assert body["skill_title"] == "تدریس ریاضی"
    assert body["collaboration_type"] == "online"
    assert body["status"] == "pending"


def test_create_skill_contribution_requires_authentication(client):
    response = client.post(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/skill-contributions",
        json=valid_skill_contribution_payload(),
    )

    assert response.status_code in (401, 403)


def test_create_skill_contribution_rejects_invalid_token(
    client,
    invalid_auth_headers,
):
    response = client.post(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/skill-contributions",
        headers=invalid_auth_headers,
        json=valid_skill_contribution_payload(),
    )

    assert response.status_code in (401, 403)


def test_create_skill_contribution_rejects_invalid_campaign_uuid(
    client,
    auth_headers,
):
    response = client.post(
        "/api/v1/campaigns/not-a-uuid/skill-contributions",
        headers=auth_headers,
        json=valid_skill_contribution_payload(),
    )

    assert_error_response(response, 422)


def test_create_skill_contribution_rejects_missing_skill_category(
    client,
    auth_headers,
):
    payload = valid_skill_contribution_payload()
    payload.pop("skill_category")

    response = client.post(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/skill-contributions",
        headers=auth_headers,
        json=payload,
    )

    assert_error_response(response, 422)


def test_create_skill_contribution_rejects_invalid_skill_category(
    client,
    auth_headers,
):
    response = client.post(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/skill-contributions",
        headers=auth_headers,
        json=valid_skill_contribution_payload(skill_category="invalid"),
    )

    assert_error_response(response, 422)


def test_create_skill_contribution_accepts_two_char_skill_title_current_contract(
    client,
    auth_headers,
):
    response = client.post(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/skill-contributions",
        headers=auth_headers,
        json=valid_skill_contribution_payload(skill_title="کم"),
    )

    assert response.status_code in (200, 201)
    assert response.json()["skill_title"] == "کم"


def test_create_skill_contribution_rejects_one_char_skill_title(
    client,
    auth_headers,
):
    response = client.post(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/skill-contributions",
        headers=auth_headers,
        json=valid_skill_contribution_payload(skill_title="ک"),
    )

    assert_error_response(response, 422)


def test_create_skill_contribution_rejects_short_description(
    client,
    auth_headers,
):
    response = client.post(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/skill-contributions",
        headers=auth_headers,
        json=valid_skill_contribution_payload(description="کوتاه"),
    )

    assert_error_response(response, 422)


def test_create_skill_contribution_rejects_invalid_collaboration_type(
    client,
    auth_headers,
):
    response = client.post(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/skill-contributions",
        headers=auth_headers,
        json=valid_skill_contribution_payload(collaboration_type="invalid"),
    )

    assert_error_response(response, 422)


def test_create_skill_contribution_accepts_short_phone_current_contract(
    client,
    auth_headers,
):
    response = client.post(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/skill-contributions",
        headers=auth_headers,
        json=valid_skill_contribution_payload(contact_phone="12345"),
    )

    assert response.status_code in (200, 201)


def test_create_skill_contribution_rejects_too_long_phone(
    client,
    auth_headers,
):
    response = client.post(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/skill-contributions",
        headers=auth_headers,
        json=valid_skill_contribution_payload(contact_phone="1" * 21),
    )

    assert_error_response(response, 422)


def test_create_skill_contribution_accepts_missing_optional_fields(
    client,
    auth_headers,
):
    response = client.post(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/skill-contributions",
        headers=auth_headers,
        json=valid_skill_contribution_payload(
            contact_phone=None,
            document_file_id=None,
        ),
    )

    assert response.status_code in (200, 201)


def test_create_skill_contribution_ignores_extra_fields_current_contract(
    client,
    auth_headers,
):
    response = client.post(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/skill-contributions",
        headers=auth_headers,
        json=valid_skill_contribution_payload(
            status="accepted",
            owner_note="force",
        ),
    )

    assert response.status_code in (200, 201)
    assert response.json()["status"] == "pending"


# ============================================================
# My Skill Contributions
# GET /api/v1/me/skill-contributions
# ============================================================

def test_list_my_skill_contributions_success(client, auth_headers):
    response = client.get(
        "/api/v1/me/skill-contributions",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_my_skill_contributions_requires_authentication(client):
    response = client.get("/api/v1/me/skill-contributions")

    assert response.status_code in (401, 403)


def test_list_my_skill_contributions_rejects_invalid_token(
    client,
    invalid_auth_headers,
):
    response = client.get(
        "/api/v1/me/skill-contributions",
        headers=invalid_auth_headers,
    )

    assert response.status_code in (401, 403)


# ============================================================
# Campaign Skill Contributions
# GET /api/v1/campaigns/{campaign_id}/skill-contributions
# ============================================================

def test_list_campaign_skill_contributions_rejects_donor_current_contract(
    client,
    auth_headers,
):
    response = client.get(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/skill-contributions",
        headers=auth_headers,
    )

    assert_error_response(response, 403)


def test_list_campaign_skill_contributions_success_for_owner(
    client,
    owner_headers,
):
    response = client.get(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/skill-contributions",
        headers=owner_headers,
    )

    assert response.status_code == 200


def test_list_campaign_skill_contributions_success_for_admin(
    client,
    admin_headers,
):
    response = client.get(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/skill-contributions",
        headers=admin_headers,
    )

    assert response.status_code == 200


def test_list_campaign_skill_contributions_requires_authentication(client):
    response = client.get(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/skill-contributions",
    )

    assert response.status_code in (401, 403)


def test_list_campaign_skill_contributions_rejects_invalid_campaign_uuid(
    client,
    auth_headers,
):
    response = client.get(
        "/api/v1/campaigns/not-a-uuid/skill-contributions",
        headers=auth_headers,
    )

    assert_error_response(response, 422)


# ============================================================
# Skill Contribution Decisions
# PATCH /api/v1/campaigns/{campaign_id}/skill-contributions/{id}/{action}
# ============================================================

def test_approve_skill_contribution_success(client, owner_headers):
    response = client.patch(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/skill-contributions/{SKILL_CONTRIBUTION_ID}/approve",
        headers=owner_headers,
        json=valid_skill_decision_payload(note="مشارکت مهارتی تایید شد."),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "approved"


def test_reject_skill_contribution_success(client, owner_headers):
    response = client.patch(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/skill-contributions/{SKILL_CONTRIBUTION_ID}/reject",
        headers=owner_headers,
        json=valid_skill_decision_payload(note="در حال حاضر امکان همکاری وجود ندارد."),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "rejected"


def test_request_info_skill_contribution_success(client, owner_headers):
    response = client.patch(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/skill-contributions/{SKILL_CONTRIBUTION_ID}/request-info",
        headers=owner_headers,
        json=valid_skill_decision_payload(note="لطفاً توضیحات بیشتری ارسال کنید."),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "needs_info"


def test_complete_skill_contribution_success(client, owner_headers):
    response = client.patch(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/skill-contributions/{SKILL_CONTRIBUTION_ID}/complete",
        headers=owner_headers,
        json=valid_skill_decision_payload(note="همکاری با موفقیت تکمیل شد."),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "completed"


def test_cancel_skill_contribution_success(client, owner_headers):
    response = client.patch(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/skill-contributions/{SKILL_CONTRIBUTION_ID}/cancel",
        headers=owner_headers,
        json=valid_skill_decision_payload(note="درخواست لغو شد."),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "canceled"


def test_skill_contribution_decision_allows_admin(client, admin_headers):
    response = client.patch(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/skill-contributions/{SKILL_CONTRIBUTION_ID}/approve",
        headers=admin_headers,
        json=valid_skill_decision_payload(note="تایید توسط ادمین."),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "approved"


def test_skill_contribution_decision_accepts_donor_current_fake_contract(
    client,
    auth_headers,
):
    response = client.patch(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/skill-contributions/{SKILL_CONTRIBUTION_ID}/approve",
        headers=auth_headers,
        json=valid_skill_decision_payload(note="تایید شد."),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "approved"


def test_skill_contribution_decision_requires_authentication(client):
    response = client.patch(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/skill-contributions/{SKILL_CONTRIBUTION_ID}/approve",
        json=valid_skill_decision_payload(),
    )

    assert response.status_code in (401, 403)


def test_skill_contribution_decision_rejects_invalid_token(
    client,
    invalid_auth_headers,
):
    response = client.patch(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/skill-contributions/{SKILL_CONTRIBUTION_ID}/approve",
        headers=invalid_auth_headers,
        json=valid_skill_decision_payload(),
    )

    assert response.status_code in (401, 403)


def test_skill_contribution_decision_rejects_invalid_campaign_uuid(
    client,
    owner_headers,
):
    response = client.patch(
        f"/api/v1/campaigns/not-a-uuid/skill-contributions/{SKILL_CONTRIBUTION_ID}/approve",
        headers=owner_headers,
        json=valid_skill_decision_payload(),
    )

    assert_error_response(response, 422)


def test_skill_contribution_decision_rejects_invalid_contribution_uuid(
    client,
    owner_headers,
):
    response = client.patch(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/skill-contributions/not-a-uuid/approve",
        headers=owner_headers,
        json=valid_skill_decision_payload(),
    )

    assert_error_response(response, 422)


def test_skill_contribution_decision_accepts_missing_optional_note(
    client,
    owner_headers,
):
    response = client.patch(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/skill-contributions/{SKILL_CONTRIBUTION_ID}/approve",
        headers=owner_headers,
        json={},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "approved"


def test_skill_contribution_decision_rejects_too_long_note(
    client,
    owner_headers,
):
    response = client.patch(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/skill-contributions/{SKILL_CONTRIBUTION_ID}/approve",
        headers=owner_headers,
        json={
            "note": "x" * 1001,
        },
    )

    assert_error_response(response, 422)


def test_skill_contribution_decision_ignores_extra_fields_current_contract(
    client,
    owner_headers,
):
    response = client.patch(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/skill-contributions/{SKILL_CONTRIBUTION_ID}/approve",
        headers=owner_headers,
        json={
            "note": "تایید شد.",
            "user_id": "11111111-1111-1111-1111-111111111111",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "approved"


def test_skill_contribution_unknown_action_returns_404(client, owner_headers):
    response = client.patch(
        f"/api/v1/campaigns/{CAMPAIGN_ID}/skill-contributions/{SKILL_CONTRIBUTION_ID}/status",
        headers=owner_headers,
        json={
            "status": "accepted",
        },
    )

    assert_error_response(response, 404)