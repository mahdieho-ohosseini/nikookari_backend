import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


# ==========================================================
# Fix Python import path for local project
# ==========================================================
CURRENT_FILE = Path(__file__).resolve()

possible_roots = [
    CURRENT_FILE.parents[1],              # core_service/
    CURRENT_FILE.parents[1] / "src",      # core_service/src/
    CURRENT_FILE.parents[1] / "app",      # core_service/app/
]

for root in possible_roots:
    if root.exists():
        root_str = str(root)
        if root_str not in sys.path:
            sys.path.insert(0, root_str)


@pytest.fixture()
def client(monkeypatch):
    async def fake_create_db_and_tables():
        return None

    import app.main as main

    monkeypatch.setattr(main, "create_db_and_tables", fake_create_db_and_tables, raising=False)

    if hasattr(main.app, "openapi_schema"):
        main.app.openapi_schema = None

    with TestClient(main.app) as test_client:
        yield test_client
