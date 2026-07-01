from tests.conftest import CAMPAIGN_ID, MISSING_ID, PROFILE_ID, REQUEST_ID


def assert_error_response(response, expected_status: int | tuple[int, ...]):
    if isinstance(expected_status, int):
        expected_status = (expected_status,)

    assert response.status_code in expected_status

    body = response.json()
    assert isinstance(body, dict)
    assert "detail" in body or "message" in body or "errors" in body


# ============================================================
# Verifier Dashboard
# GET /api/v1/verifier/dashboard
# ============================================================

def test_verifier_dashboard_success(client, verifier_headers):
    response = client.get(
        "/api/v1/verifier/dashboard",
        headers=verifier_headers,
    )

    assert response.status_code == 200

    body = response.json()
    assert "stats" in body
    assert "items" in body
    assert body["stats"]["total"] == 1
    assert body["stats"]["pending"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["charity_name"] == "موسسه تست نیکوکاری"


def test_verifier_dashboard_allows_admin(client, admin_headers):
    response = client.get(
        "/api/v1/verifier/dashboard",
        headers=admin_headers,
    )

    assert response.status_code == 200


def test_verifier_dashboard_rejects_donor(client, auth_headers):
    response = client.get(
        "/api/v1/verifier/dashboard",
        headers=auth_headers,
    )

    assert_error_response(response, 403)


def test_verifier_dashboard_requires_authentication(client):
    response = client.get("/api/v1/verifier/dashboard")

    assert response.status_code in (401, 403)


def test_verifier_dashboard_rejects_invalid_token(client, invalid_auth_headers):
    response = client.get(
        "/api/v1/verifier/dashboard",
        headers=invalid_auth_headers,
    )

    assert response.status_code in (401, 403)


def test_verifier_dashboard_accepts_filters(client, verifier_headers):
    response = client.get(
        "/api/v1/verifier/dashboard",
        headers=verifier_headers,
        params={
            "status": "pending",
            "activity_field": "آموزش",
            "search": "تست",
            "limit": 20,
            "offset": 0,
        },
    )

    assert response.status_code == 200


def test_verifier_dashboard_rejects_invalid_status(client, verifier_headers):
    response = client.get(
        "/api/v1/verifier/dashboard",
        headers=verifier_headers,
        params={
            "status": "invalid-status",
        },
    )

    assert_error_response(response, 422)


def test_verifier_dashboard_rejects_limit_less_than_one(
    client,
    verifier_headers,
):
    response = client.get(
        "/api/v1/verifier/dashboard",
        headers=verifier_headers,
        params={
            "limit": 0,
        },
    )

    assert_error_response(response, 422)


def test_verifier_dashboard_rejects_limit_too_large(client, verifier_headers):
    response = client.get(
        "/api/v1/verifier/dashboard",
        headers=verifier_headers,
        params={
            "limit": 101,
        },
    )

    assert_error_response(response, 422)


def test_verifier_dashboard_rejects_negative_offset(client, verifier_headers):
    response = client.get(
        "/api/v1/verifier/dashboard",
        headers=verifier_headers,
        params={
            "offset": -1,
        },
    )

    assert_error_response(response, 422)


# ============================================================
# Verification Request Detail
# GET /api/v1/verifier/requests/{request_id}
# ============================================================

def test_verifier_get_request_detail_success(client, verifier_headers):
    response = client.get(
        f"/api/v1/verifier/requests/{REQUEST_ID}",
        headers=verifier_headers,
    )

    assert response.status_code == 200

    body = response.json()
    assert body["id"] == str(REQUEST_ID)
    assert body["charity_name"] == "موسسه تست نیکوکاری"
    assert body["status"] == "pending"
    assert "documents" in body


def test_verifier_get_request_detail_allows_admin(client, admin_headers):
    response = client.get(
        f"/api/v1/verifier/requests/{REQUEST_ID}",
        headers=admin_headers,
    )

    assert response.status_code == 200


def test_verifier_get_request_detail_rejects_donor(client, auth_headers):
    response = client.get(
        f"/api/v1/verifier/requests/{REQUEST_ID}",
        headers=auth_headers,
    )

    assert_error_response(response, 403)


def test_verifier_get_request_detail_requires_authentication(client):
    response = client.get(f"/api/v1/verifier/requests/{REQUEST_ID}")

    assert response.status_code in (401, 403)


def test_verifier_get_request_detail_returns_404_for_missing_request(
    client,
    verifier_headers,
):
    response = client.get(
        f"/api/v1/verifier/requests/{MISSING_ID}",
        headers=verifier_headers,
    )

    assert_error_response(response, 404)


def test_verifier_get_request_detail_rejects_invalid_uuid(
    client,
    verifier_headers,
):
    response = client.get(
        "/api/v1/verifier/requests/not-a-uuid",
        headers=verifier_headers,
    )

    assert_error_response(response, 422)


# ============================================================
# Approve Verification Request
# POST /api/v1/verifier/requests/{request_id}/approve
# ============================================================

def test_verifier_approve_request_success(client, verifier_headers):
    response = client.post(
        f"/api/v1/verifier/requests/{REQUEST_ID}/approve",
        headers=verifier_headers,
    )

    assert response.status_code == 200

    body = response.json()
    assert body["id"] == str(REQUEST_ID)
    assert body["status"] == "approved"
    assert body["rejection_reason"] is None


def test_verifier_approve_request_allows_admin(client, admin_headers):
    response = client.post(
        f"/api/v1/verifier/requests/{REQUEST_ID}/approve",
        headers=admin_headers,
    )

    assert response.status_code == 200


def test_verifier_approve_request_rejects_donor(client, auth_headers):
    response = client.post(
        f"/api/v1/verifier/requests/{REQUEST_ID}/approve",
        headers=auth_headers,
    )

    assert_error_response(response, 403)


def test_verifier_approve_request_requires_authentication(client):
    response = client.post(f"/api/v1/verifier/requests/{REQUEST_ID}/approve")

    assert response.status_code in (401, 403)


def test_verifier_approve_request_returns_404_for_missing_request(
    client,
    verifier_headers,
):
    response = client.post(
        f"/api/v1/verifier/requests/{MISSING_ID}/approve",
        headers=verifier_headers,
    )

    assert_error_response(response, 404)


def test_verifier_approve_request_rejects_invalid_uuid(
    client,
    verifier_headers,
):
    response = client.post(
        "/api/v1/verifier/requests/not-a-uuid/approve",
        headers=verifier_headers,
    )

    assert_error_response(response, 422)


# ============================================================
# Reject Verification Request
# POST /api/v1/verifier/requests/{request_id}/reject
# ============================================================

def test_verifier_reject_request_success(client, verifier_headers):
    response = client.post(
        f"/api/v1/verifier/requests/{REQUEST_ID}/reject",
        headers=verifier_headers,
        json={
            "reason": "مدارک ارسالی ناقص هستند.",
        },
    )

    assert response.status_code == 200

    body = response.json()
    assert body["id"] == str(REQUEST_ID)
    assert body["status"] == "rejected"
    assert body["rejection_reason"] == "مدارک ارسالی ناقص هستند."


def test_verifier_reject_request_allows_admin(client, admin_headers):
    response = client.post(
        f"/api/v1/verifier/requests/{REQUEST_ID}/reject",
        headers=admin_headers,
        json={
            "reason": "مدارک ارسالی ناقص هستند.",
        },
    )

    assert response.status_code == 200


def test_verifier_reject_request_rejects_donor(client, auth_headers):
    response = client.post(
        f"/api/v1/verifier/requests/{REQUEST_ID}/reject",
        headers=auth_headers,
        json={
            "reason": "مدارک ارسالی ناقص هستند.",
        },
    )

    assert_error_response(response, 403)


def test_verifier_reject_request_requires_authentication(client):
    response = client.post(
        f"/api/v1/verifier/requests/{REQUEST_ID}/reject",
        json={
            "reason": "مدارک ارسالی ناقص هستند.",
        },
    )

    assert response.status_code in (401, 403)


def test_verifier_reject_request_rejects_missing_reason(
    client,
    verifier_headers,
):
    response = client.post(
        f"/api/v1/verifier/requests/{REQUEST_ID}/reject",
        headers=verifier_headers,
        json={},
    )

    assert_error_response(response, 422)


def test_verifier_reject_request_rejects_short_reason(
    client,
    verifier_headers,
):
    response = client.post(
        f"/api/v1/verifier/requests/{REQUEST_ID}/reject",
        headers=verifier_headers,
        json={
            "reason": "نه",
        },
    )

    assert_error_response(response, 422)


def test_verifier_reject_request_rejects_too_long_reason(
    client,
    verifier_headers,
):
    response = client.post(
        f"/api/v1/verifier/requests/{REQUEST_ID}/reject",
        headers=verifier_headers,
        json={
            "reason": "x" * 1001,
        },
    )

    assert_error_response(response, 422)


def test_verifier_reject_request_returns_404_for_missing_request(
    client,
    verifier_headers,
):
    response = client.post(
        f"/api/v1/verifier/requests/{MISSING_ID}/reject",
        headers=verifier_headers,
        json={
            "reason": "مدارک ارسالی ناقص هستند.",
        },
    )

    assert_error_response(response, 404)


# ============================================================
# Pending Charity Profiles
# GET /api/v1/verifier/charity-profiles/pending
# ============================================================

def test_verifier_get_pending_charity_profiles_success(client, verifier_headers):
    response = client.get(
        "/api/v1/verifier/charity-profiles/pending",
        headers=verifier_headers,
    )

    assert response.status_code == 200

    body = response.json()
    assert isinstance(body, list)
    assert len(body) == 1
    assert body[0]["status"] == "pending_review"


def test_verifier_get_pending_charity_profiles_allows_admin(
    client,
    admin_headers,
):
    response = client.get(
        "/api/v1/verifier/charity-profiles/pending",
        headers=admin_headers,
    )

    assert response.status_code == 200


def test_verifier_get_pending_charity_profiles_rejects_donor(
    client,
    auth_headers,
):
    response = client.get(
        "/api/v1/verifier/charity-profiles/pending",
        headers=auth_headers,
    )

    assert_error_response(response, 403)


def test_verifier_get_pending_charity_profiles_requires_authentication(client):
    response = client.get("/api/v1/verifier/charity-profiles/pending")

    assert response.status_code in (401, 403)


# ============================================================
# Approve Charity Profile
# POST /api/v1/verifier/charity-profiles/{profile_id}/approve
# ============================================================

def test_verifier_approve_charity_profile_success(client, verifier_headers):
    response = client.post(
        f"/api/v1/verifier/charity-profiles/{PROFILE_ID}/approve",
        headers=verifier_headers,
    )

    assert response.status_code == 200

    body = response.json()
    assert body["id"] == str(PROFILE_ID)
    assert body["status"] == "active"
    assert body["is_published"] is True
    assert body["message"] == "Charity profile approved successfully"


def test_verifier_approve_charity_profile_allows_admin(client, admin_headers):
    response = client.post(
        f"/api/v1/verifier/charity-profiles/{PROFILE_ID}/approve",
        headers=admin_headers,
    )

    assert response.status_code == 200


def test_verifier_approve_charity_profile_rejects_donor(client, auth_headers):
    response = client.post(
        f"/api/v1/verifier/charity-profiles/{PROFILE_ID}/approve",
        headers=auth_headers,
    )

    assert_error_response(response, 403)


def test_verifier_approve_charity_profile_requires_authentication(client):
    response = client.post(
        f"/api/v1/verifier/charity-profiles/{PROFILE_ID}/approve",
    )

    assert response.status_code in (401, 403)


def test_verifier_approve_charity_profile_returns_404_for_missing_profile(
    client,
    verifier_headers,
):
    response = client.post(
        f"/api/v1/verifier/charity-profiles/{MISSING_ID}/approve",
        headers=verifier_headers,
    )

    assert_error_response(response, 404)


def test_verifier_approve_charity_profile_rejects_invalid_uuid(
    client,
    verifier_headers,
):
    response = client.post(
        "/api/v1/verifier/charity-profiles/not-a-uuid/approve",
        headers=verifier_headers,
    )

    assert_error_response(response, 422)


# ============================================================
# Reject Charity Profile
# POST /api/v1/verifier/charity-profiles/{profile_id}/reject
# ============================================================

def test_verifier_reject_charity_profile_success(client, verifier_headers):
    response = client.post(
        f"/api/v1/verifier/charity-profiles/{PROFILE_ID}/reject",
        headers=verifier_headers,
    )

    assert response.status_code == 200

    body = response.json()
    assert body["id"] == str(PROFILE_ID)
    assert body["status"] == "rejected"
    assert body["is_published"] is False
    assert body["message"] == "Charity profile rejected successfully"


def test_verifier_reject_charity_profile_allows_admin(client, admin_headers):
    response = client.post(
        f"/api/v1/verifier/charity-profiles/{PROFILE_ID}/reject",
        headers=admin_headers,
    )

    assert response.status_code == 200


def test_verifier_reject_charity_profile_rejects_donor(client, auth_headers):
    response = client.post(
        f"/api/v1/verifier/charity-profiles/{PROFILE_ID}/reject",
        headers=auth_headers,
    )

    assert_error_response(response, 403)


def test_verifier_reject_charity_profile_requires_authentication(client):
    response = client.post(
        f"/api/v1/verifier/charity-profiles/{PROFILE_ID}/reject",
    )

    assert response.status_code in (401, 403)


def test_verifier_reject_charity_profile_returns_404_for_missing_profile(
    client,
    verifier_headers,
):
    response = client.post(
        f"/api/v1/verifier/charity-profiles/{MISSING_ID}/reject",
        headers=verifier_headers,
    )

    assert_error_response(response, 404)


# ============================================================
# Campaign Management by Verifier/Admin
# PATCH /api/v1/verifier/{campaign_id}/approve|reject|suspend|resume
# ============================================================

def test_verifier_approve_campaign_success(client, verifier_headers):
    response = client.patch(
        f"/api/v1/verifier/{CAMPAIGN_ID}/approve",
        headers=verifier_headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "active"


def test_verifier_reject_campaign_success(client, verifier_headers):
    response = client.patch(
        f"/api/v1/verifier/{CAMPAIGN_ID}/reject",
        headers=verifier_headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "rejected"


def test_verifier_suspend_campaign_success(client, verifier_headers):
    response = client.patch(
        f"/api/v1/verifier/{CAMPAIGN_ID}/suspend",
        headers=verifier_headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "suspended"


def test_verifier_resume_campaign_success(client, verifier_headers):
    response = client.patch(
        f"/api/v1/verifier/{CAMPAIGN_ID}/resume",
        headers=verifier_headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "active"


def test_campaign_management_allows_admin(client, admin_headers):
    response = client.patch(
        f"/api/v1/verifier/{CAMPAIGN_ID}/approve",
        headers=admin_headers,
    )

    assert response.status_code == 200


def test_campaign_management_rejects_donor(client, auth_headers):
    response = client.patch(
        f"/api/v1/verifier/{CAMPAIGN_ID}/approve",
        headers=auth_headers,
    )

    assert_error_response(response, 403)


def test_campaign_management_requires_authentication(client):
    response = client.patch(f"/api/v1/verifier/{CAMPAIGN_ID}/approve")

    assert response.status_code in (401, 403)


def test_campaign_management_returns_404_for_missing_campaign(
    client,
    verifier_headers,
):
    response = client.patch(
        f"/api/v1/verifier/{MISSING_ID}/approve",
        headers=verifier_headers,
    )

    assert_error_response(response, 404)


def test_campaign_management_rejects_invalid_campaign_uuid(
    client,
    verifier_headers,
):
    response = client.patch(
        "/api/v1/verifier/not-a-uuid/approve",
        headers=verifier_headers,
    )

    assert_error_response(response, 422)