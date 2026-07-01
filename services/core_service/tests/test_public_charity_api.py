def assert_error_response(response, expected_status: int | tuple[int, ...]):
    if isinstance(expected_status, int):
        expected_status = (expected_status,)

    assert response.status_code in expected_status

    body = response.json()
    assert isinstance(body, dict)
    assert "detail" in body or "message" in body or "errors" in body


# ============================================================
# Public Charities List
# GET /api/v1/charities
# ============================================================

def test_list_public_charities_success(client):
    response = client.get("/api/v1/charities")

    assert response.status_code == 200

    body = response.json()
    assert isinstance(body, list)
    assert len(body) == 1

    charity = body[0]
    assert charity["charity_name"] == "موسسه تست نیکوکاری"
    assert charity["slug"] == "test-charity"
    assert charity["activity_field"] == "آموزش"
    assert charity["province"] == "تهران"
    assert charity["city"] == "تهران"
    assert "short_description" in charity


def test_list_public_charities_does_not_require_authentication(client):
    response = client.get("/api/v1/charities")

    assert response.status_code == 200


def test_list_public_charities_ignores_invalid_token_because_it_is_public(
    client,
    invalid_auth_headers,
):
    response = client.get(
        "/api/v1/charities",
        headers=invalid_auth_headers,
    )

    assert response.status_code == 200


def test_list_public_charities_with_search_filter(client):
    response = client.get(
        "/api/v1/charities",
        params={
            "search": "نیکوکاری",
        },
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_public_charities_with_province_filter(client):
    response = client.get(
        "/api/v1/charities",
        params={
            "province": "تهران",
        },
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_public_charities_with_city_filter(client):
    response = client.get(
        "/api/v1/charities",
        params={
            "city": "تهران",
        },
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_public_charities_with_activity_field_filter(client):
    response = client.get(
        "/api/v1/charities",
        params={
            "activity_field": "آموزش",
        },
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_public_charities_with_pagination(client):
    response = client.get(
        "/api/v1/charities",
        params={
            "limit": 20,
            "offset": 0,
        },
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_public_charities_returns_empty_list_when_no_result(client):
    response = client.get(
        "/api/v1/charities",
        params={
            "search": "empty",
        },
    )

    assert response.status_code == 200
    assert response.json() == []


def test_list_public_charities_rejects_limit_less_than_one(client):
    response = client.get(
        "/api/v1/charities",
        params={
            "limit": 0,
        },
    )

    assert_error_response(response, 422)


def test_list_public_charities_rejects_limit_too_large(client):
    response = client.get(
        "/api/v1/charities",
        params={
            "limit": 101,
        },
    )

    assert_error_response(response, 422)


def test_list_public_charities_rejects_negative_offset(client):
    response = client.get(
        "/api/v1/charities",
        params={
            "offset": -1,
        },
    )

    assert_error_response(response, 422)


def test_list_public_charities_rejects_non_integer_limit(client):
    response = client.get(
        "/api/v1/charities",
        params={
            "limit": "not-number",
        },
    )

    assert_error_response(response, 422)


def test_list_public_charities_rejects_non_integer_offset(client):
    response = client.get(
        "/api/v1/charities",
        params={
            "offset": "not-number",
        },
    )

    assert_error_response(response, 422)


# ============================================================
# Public Charity Detail
# GET /api/v1/charities/{slug}
# ============================================================

def test_get_public_charity_detail_success(client):
    response = client.get("/api/v1/charities/test-charity")

    assert response.status_code == 200

    body = response.json()

    assert body["charity_name"] == "موسسه تست نیکوکاری"
    assert body["slug"] == "test-charity"
    assert body["registration_number"] == "REG-1001"
    assert body["activity_field"] == "آموزش"
    assert body["province"] == "تهران"
    assert body["city"] == "تهران"
    assert body["email"] == "charity@gmail.com"
    assert body["website"] == "https://example.org"
    assert "about_text" in body
    assert "vision_text" in body
    assert "social_links" in body


def test_get_public_charity_detail_does_not_require_authentication(client):
    response = client.get("/api/v1/charities/test-charity")

    assert response.status_code == 200


def test_get_public_charity_detail_ignores_invalid_token_because_it_is_public(
    client,
    invalid_auth_headers,
):
    response = client.get(
        "/api/v1/charities/test-charity",
        headers=invalid_auth_headers,
    )

    assert response.status_code == 200


def test_get_public_charity_detail_returns_404_for_missing_slug(client):
    response = client.get("/api/v1/charities/missing-charity")

    assert_error_response(response, 404)


def test_get_public_charity_detail_accepts_slug_with_dash(client):
    response = client.get("/api/v1/charities/test-charity")

    assert response.status_code == 200
    assert response.json()["slug"] == "test-charity"


def test_get_public_charity_detail_returns_json(client):
    response = client.get("/api/v1/charities/test-charity")

    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]