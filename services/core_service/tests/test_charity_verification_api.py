from tests.conftest import REQUEST_ID


def assert_error_response(response, expected_status: int | tuple[int, ...]):
    if isinstance(expected_status, int):
        expected_status = (expected_status,)

    assert response.status_code in expected_status

    body = response.json()
    assert isinstance(body, dict)
    assert "detail" in body or "message" in body or "errors" in body


def valid_charity_verification_payload(**overrides):
    payload = {
        "charity_name": "موسسه تست نیکوکاری",
        "registration_number": "REG-1001",
        "establishment_date": "2020-01-01",
        "activity_field": "آموزش",
        "short_description": "این یک توضیح تستی برای احراز موسسه است.",
        "phone": "09123456789",
        "email": "charity@gmail.com",
        "website": "https://example.org",
        "province": "تهران",
        "city": "تهران",
        "full_address": "تهران، خیابان تست، پلاک ۱",
        "bank_name": "بانک تست",
        "shaba_number": "IR123456789012345678901234",
        "account_owner": "موسسه تست نیکوکاری",
        "articles_of_association_file_id": 1,
        "activity_license_file_id": 2,
        "national_card_file_id": 3,
    }

    payload.update(overrides)
    return payload


# ============================================================
# Create Charity Verification Request
# POST /api/v1/charity-verification-requests
# ============================================================

def test_create_charity_verification_request_success(client, auth_headers):
    response = client.post(
        "/api/v1/charity-verification-requests",
        headers=auth_headers,
        json=valid_charity_verification_payload(),
    )

    assert response.status_code in (200, 201)

    body = response.json()
    assert body["charity_name"] == "موسسه تست نیکوکاری"
    assert body["registration_number"] == "REG-1001"
    assert body["status"] == "pending"
    assert body["articles_of_association_file_id"] == 1
    assert body["activity_license_file_id"] == 2
    assert body["national_card_file_id"] == 3
    assert "documents" in body


def test_create_charity_verification_request_requires_authentication(client):
    response = client.post(
        "/api/v1/charity-verification-requests",
        json=valid_charity_verification_payload(),
    )

    assert response.status_code in (401, 403)


def test_create_charity_verification_request_rejects_invalid_token(
    client,
    invalid_auth_headers,
):
    response = client.post(
        "/api/v1/charity-verification-requests",
        headers=invalid_auth_headers,
        json=valid_charity_verification_payload(),
    )

    assert response.status_code in (401, 403)


def test_create_charity_verification_request_rejects_duplicate_pending_request(
    client,
    auth_headers,
):
    response = client.post(
        "/api/v1/charity-verification-requests",
        headers=auth_headers,
        json=valid_charity_verification_payload(
            charity_name="duplicate",
        ),
    )

    assert_error_response(response, 400)


def test_create_charity_verification_request_rejects_missing_charity_name(
    client,
    auth_headers,
):
    payload = valid_charity_verification_payload()
    payload.pop("charity_name")

    response = client.post(
        "/api/v1/charity-verification-requests",
        headers=auth_headers,
        json=payload,
    )

    assert_error_response(response, 422)


def test_create_charity_verification_request_rejects_missing_registration_number(
    client,
    auth_headers,
):
    payload = valid_charity_verification_payload()
    payload.pop("registration_number")

    response = client.post(
        "/api/v1/charity-verification-requests",
        headers=auth_headers,
        json=payload,
    )

    assert_error_response(response, 422)


def test_create_charity_verification_request_rejects_missing_establishment_date(
    client,
    auth_headers,
):
    payload = valid_charity_verification_payload()
    payload.pop("establishment_date")

    response = client.post(
        "/api/v1/charity-verification-requests",
        headers=auth_headers,
        json=payload,
    )

    assert_error_response(response, 422)


def test_create_charity_verification_request_rejects_invalid_establishment_date(
    client,
    auth_headers,
):
    response = client.post(
        "/api/v1/charity-verification-requests",
        headers=auth_headers,
        json=valid_charity_verification_payload(
            establishment_date="not-a-date",
        ),
    )

    assert_error_response(response, 422)


def test_create_charity_verification_request_rejects_missing_activity_field(
    client,
    auth_headers,
):
    payload = valid_charity_verification_payload()
    payload.pop("activity_field")

    response = client.post(
        "/api/v1/charity-verification-requests",
        headers=auth_headers,
        json=payload,
    )

    assert_error_response(response, 422)


def test_create_charity_verification_request_rejects_short_description(
    client,
    auth_headers,
):
    response = client.post(
        "/api/v1/charity-verification-requests",
        headers=auth_headers,
        json=valid_charity_verification_payload(
            short_description="کوتاه",
        ),
    )

    assert_error_response(response, 422)


def test_create_charity_verification_request_rejects_invalid_phone_length(
    client,
    auth_headers,
):
    response = client.post(
        "/api/v1/charity-verification-requests",
        headers=auth_headers,
        json=valid_charity_verification_payload(
            phone="12345",
        ),
    )

    assert_error_response(response, 422)


def test_create_charity_verification_request_accepts_phone_not_starting_with_09(
    client,
    auth_headers,
):
    response = client.post(
        "/api/v1/charity-verification-requests",
        headers=auth_headers,
        json=valid_charity_verification_payload(
            phone="02112345678",
        ),
    )

    assert response.status_code in (200, 201)


def test_create_charity_verification_request_rejects_invalid_email(
    client,
    auth_headers,
):
    response = client.post(
        "/api/v1/charity-verification-requests",
        headers=auth_headers,
        json=valid_charity_verification_payload(
            email="bad-email",
        ),
    )

    assert_error_response(response, 422)


def test_create_charity_verification_request_accepts_website_as_plain_text(
    client,
    auth_headers,
):
    response = client.post(
        "/api/v1/charity-verification-requests",
        headers=auth_headers,
        json=valid_charity_verification_payload(
            website="not-a-url",
        ),
    )

    assert response.status_code in (200, 201)


def test_create_charity_verification_request_accepts_missing_optional_website(
    client,
    auth_headers,
):
    payload = valid_charity_verification_payload()
    payload["website"] = None

    response = client.post(
        "/api/v1/charity-verification-requests",
        headers=auth_headers,
        json=payload,
    )

    assert response.status_code in (200, 201)


def test_create_charity_verification_request_rejects_missing_address(
    client,
    auth_headers,
):
    payload = valid_charity_verification_payload()
    payload.pop("full_address")

    response = client.post(
        "/api/v1/charity-verification-requests",
        headers=auth_headers,
        json=payload,
    )

    assert_error_response(response, 422)


def test_create_charity_verification_request_rejects_invalid_shaba(
    client,
    auth_headers,
):
    response = client.post(
        "/api/v1/charity-verification-requests",
        headers=auth_headers,
        json=valid_charity_verification_payload(
            shaba_number="123",
        ),
    )

    assert_error_response(response, 422)


def test_create_charity_verification_request_rejects_missing_account_owner(
    client,
    auth_headers,
):
    payload = valid_charity_verification_payload()
    payload.pop("account_owner")

    response = client.post(
        "/api/v1/charity-verification-requests",
        headers=auth_headers,
        json=payload,
    )

    assert_error_response(response, 422)


def test_create_charity_verification_request_accepts_missing_articles_file(
    client,
    auth_headers,
):
    payload = valid_charity_verification_payload()
    payload.pop("articles_of_association_file_id")

    response = client.post(
        "/api/v1/charity-verification-requests",
        headers=auth_headers,
        json=payload,
    )

    assert response.status_code in (200, 201)


def test_create_charity_verification_request_accepts_missing_license_file(
    client,
    auth_headers,
):
    payload = valid_charity_verification_payload()
    payload.pop("activity_license_file_id")

    response = client.post(
        "/api/v1/charity-verification-requests",
        headers=auth_headers,
        json=payload,
    )

    assert response.status_code in (200, 201)


def test_create_charity_verification_request_accepts_missing_national_card_file(
    client,
    auth_headers,
):
    payload = valid_charity_verification_payload()
    payload.pop("national_card_file_id")

    response = client.post(
        "/api/v1/charity-verification-requests",
        headers=auth_headers,
        json=payload,
    )

    assert response.status_code in (200, 201)


def test_create_charity_verification_request_rejects_non_integer_file_id(
    client,
    auth_headers,
):
    response = client.post(
        "/api/v1/charity-verification-requests",
        headers=auth_headers,
        json=valid_charity_verification_payload(
            articles_of_association_file_id="not-number",
        ),
    )

    assert_error_response(response, 422)


def test_create_charity_verification_request_accepts_negative_file_id(
    client,
    auth_headers,
):
    response = client.post(
        "/api/v1/charity-verification-requests",
        headers=auth_headers,
        json=valid_charity_verification_payload(
            articles_of_association_file_id=-1,
        ),
    )

    assert response.status_code in (200, 201)


def test_create_charity_verification_request_ignores_extra_fields(
    client,
    auth_headers,
):
    response = client.post(
        "/api/v1/charity-verification-requests",
        headers=auth_headers,
        json=valid_charity_verification_payload(
            role="admin",
        ),
    )

    assert response.status_code in (200, 201)


# ============================================================
# Get My Latest Charity Verification Request
# GET /api/v1/charity-verification-requests/me/latest
# ============================================================

def test_get_my_latest_charity_verification_request_success(client, auth_headers):
    response = client.get(
        "/api/v1/charity-verification-requests/me/latest",
        headers=auth_headers,
    )

    assert response.status_code == 200

    body = response.json()
    assert body["id"] == str(REQUEST_ID)
    assert body["charity_name"] == "موسسه تست نیکوکاری"
    assert body["status"] == "pending"
    assert "documents" in body


def test_get_my_latest_charity_verification_request_requires_authentication(client):
    response = client.get("/api/v1/charity-verification-requests/me/latest")

    assert response.status_code in (401, 403)


def test_get_my_latest_charity_verification_request_rejects_invalid_token(
    client,
    invalid_auth_headers,
):
    response = client.get(
        "/api/v1/charity-verification-requests/me/latest",
        headers=invalid_auth_headers,
    )

    assert response.status_code in (401, 403)


def test_get_old_me_charity_verification_request_path_returns_404(
    client,
    auth_headers,
):
    response = client.get(
        "/api/v1/charity-verification-requests/me",
        headers=auth_headers,
    )

    assert response.status_code == 404


# ============================================================
# Delete My Pending Charity Verification Request
# DELETE /api/v1/charity-verification-requests/me/pending
# ============================================================

def test_delete_my_pending_charity_verification_request_success(
    client,
    auth_headers,
):
    response = client.delete(
        "/api/v1/charity-verification-requests/me/pending",
        headers=auth_headers,
    )

    assert response.status_code == 200

    body = response.json()
    assert "message" in body
    assert body["deleted_request_id"] == str(REQUEST_ID)


def test_delete_my_pending_charity_verification_request_requires_authentication(
    client,
):
    response = client.delete("/api/v1/charity-verification-requests/me/pending")

    assert response.status_code in (401, 403)


def test_delete_my_pending_charity_verification_request_rejects_invalid_token(
    client,
    invalid_auth_headers,
):
    response = client.delete(
        "/api/v1/charity-verification-requests/me/pending",
        headers=invalid_auth_headers,
    )

    assert response.status_code in (401, 403)


def test_delete_old_me_charity_verification_request_path_returns_404(
    client,
    auth_headers,
):
    response = client.delete(
        "/api/v1/charity-verification-requests/me",
        headers=auth_headers,
    )

    assert response.status_code == 404