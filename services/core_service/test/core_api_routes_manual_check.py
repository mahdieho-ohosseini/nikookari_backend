import pytest


PUBLIC_PATHS = {
    "/",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/verify-otp",
    "/api/v1/auth/refresh",
    "/api/v1/charities",
}


def is_public_path(path: str) -> bool:
    return any(path == public_path or path.startswith(f"{public_path}/") for public_path in PUBLIC_PATHS)


def test_root_health_check(client):
    response = client.get("/")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "service" in body
    assert "version" in body


def test_openapi_schema_is_available(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()

    assert schema["openapi"]
    assert "paths" in schema
    assert "components" in schema


def test_openapi_has_bearer_auth_security_scheme(client):
    schema = client.get("/openapi.json").json()

    security_schemes = schema["components"].get("securitySchemes", {})

    assert "BearerAuth" in security_schemes
    assert security_schemes["BearerAuth"]["type"] == "http"
    assert security_schemes["BearerAuth"]["scheme"] == "bearer"


def test_protected_routes_show_swagger_lock(client):
    schema = client.get("/openapi.json").json()

    global_security = schema.get("security", [])
    protected_operations = []

    for path, path_config in schema["paths"].items():
        if is_public_path(path):
            continue

        for method, operation in path_config.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                continue

            protected_operations.append((method, path, operation))

    assert protected_operations, "No protected routes found in OpenAPI schema"

    for method, path, operation in protected_operations:
        operation_security = operation.get("security")

        assert (
            operation_security == [{"BearerAuth": []}]
            or (
                operation_security is None
                and global_security == [{"BearerAuth": []}]
            )
        ), f"{method.upper()} {path} should require BearerAuth in Swagger"


def test_protected_routes_show_swagger_lock(client):
    schema = client.get("/openapi.json").json()

    protected_operations = []

    for path, path_config in schema["paths"].items():
        if is_public_path(path):
            continue

        for method, operation in path_config.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                continue

            protected_operations.append((method, path, operation))

    assert protected_operations, "No protected routes found in OpenAPI schema"

    for method, path, operation in protected_operations:
        assert operation.get("security") == [{"BearerAuth": []}], (
            f"{method.upper()} {path} should require BearerAuth in Swagger"
        )


def test_no_duplicate_registered_routes(client):
    routes = []

    for route in client.app.routes:
        path = getattr(route, "path", None)
        methods = getattr(route, "methods", None)

        if not path or not methods:
            continue

        for method in methods:
            if method in {"HEAD", "OPTIONS"}:
                continue
            routes.append((method, path))

    duplicates = sorted({route for route in routes if routes.count(route) > 1})

    assert duplicates == [], f"Duplicate routes found: {duplicates}"


def test_all_openapi_operations_have_tags_and_operation_ids(client):
    schema = client.get("/openapi.json").json()

    missing_tags = []
    missing_operation_ids = []

    for path, path_config in schema["paths"].items():
        for method, operation in path_config.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                continue

            if not operation.get("tags"):
                missing_tags.append(f"{method.upper()} {path}")

            if not operation.get("operationId"):
                missing_operation_ids.append(f"{method.upper()} {path}")

    assert missing_tags == [], f"Routes without tags: {missing_tags}"
    assert missing_operation_ids == [], f"Routes without operationId: {missing_operation_ids}"


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/charities",
    ],
)
def test_public_get_routes_are_accessible_without_token(client, path):
    response = client.get(path)

    assert response.status_code not in {401, 403}, (
        f"Public route {path} should not require authentication"
    )


def test_protected_routes_do_not_return_200_without_token(client):
    schema = client.get("/openapi.json").json()

    checked = []

    for path, path_config in schema["paths"].items():
        if is_public_path(path):
            continue

        if "{" in path:
            continue

        if "get" not in path_config:
            continue

        response = client.get(path)
        checked.append((path, response.status_code))

        assert response.status_code != 200, (
            f"Protected route GET {path} returned 200 without token"
        )

    assert checked, "No protected GET routes were checked"

