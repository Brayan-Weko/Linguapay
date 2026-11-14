"""Tests for FastAPI OpenAPI/Swagger specification compliance and interactive documentation."""

from __future__ import annotations

import sys
from pathlib import Path
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[2]
for p in (str(BACKEND_DIR), str(REPO_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

from app.main import app  # noqa: E402

client = TestClient(app)


def test_openapi_schema_metadata_and_structure():
    """Validates that OpenAPI schema contains all metadata, tags and valid 3.x structure."""
    schema = app.openapi()
    assert schema is not None
    assert schema.get("openapi", "").startswith("3.")
    
    info = schema.get("info", {})
    assert "LinguaPay" in info.get("title", "")
    assert info.get("version") == "1.0.0"
    assert "SAFINUM" in info.get("description", "")
    assert info.get("contact", {}).get("email") is not None
    assert info.get("license", {}).get("name") is not None

    # Tags metadata
    tags = [t.get("name") for t in schema.get("tags", [])]
    for required_tag in ("health", "translate", "glossary", "tts"):
        assert required_tag in tags, f"Missing OpenAPI tag '{required_tag}'"


def test_openapi_all_routes_documented_with_examples():
    """Ensures every single public endpoint is documented in Swagger with summary, description and responses."""
    schema = app.openapi()
    paths = schema.get("paths", {})

    expected_routes = [
        "/api/v1/health",
        "/api/v1/translate",
        "/api/v1/translate/batch",
        "/api/v1/glossary/{lang}",
        "/api/v1/audit/recent",
        "/api/v1/tts/sequence",
        "/api/v1/tts/capsule/{lang}/{clip_name}",
    ]

    for route in expected_routes:
        assert route in paths, f"Route '{route}' missing from OpenAPI specification!"
        methods = paths[route]
        for method_name, op in methods.items():
            assert "summary" in op and op["summary"], f"Route {method_name.upper()} {route} missing summary"
            assert "description" in op and op["description"], f"Route {method_name.upper()} {route} missing description"
            assert "responses" in op and "200" in op["responses"], f"Route {method_name.upper()} {route} missing 200 response"


def test_swagger_ui_and_openapi_json_endpoints():
    """Ensures /docs (Swagger UI), /redoc (ReDoc) and /openapi.json serve 200 OK with correct content types."""
    # 1. /openapi.json
    resp_json = client.get("/openapi.json")
    assert resp_json.status_code == 200
    json_data = resp_json.json()
    assert "paths" in json_data
    assert len(json_data["paths"]) >= 7

    # 2. /docs (Swagger UI HTML)
    resp_docs = client.get("/docs")
    assert resp_docs.status_code == 200
    assert "text/html" in resp_docs.headers.get("content-type", "")
    assert "swagger-ui" in resp_docs.text.lower()

    # 3. /redoc (ReDoc HTML)
    resp_redoc = client.get("/redoc")
    assert resp_redoc.status_code == 200
    assert "text/html" in resp_redoc.headers.get("content-type", "")
    assert "redoc" in resp_redoc.text.lower()

