"""Sprint 1 foundation tests: FastAPI health & linguistics pack validation."""

from pathlib import Path
import sys
from fastapi.testclient import TestClient

# Allow importing linguistics/validate_packs.py and backend/app
BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[2]
for p in (str(BACKEND_DIR), str(REPO_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

from app.main import app  # noqa: E402
from linguistics.validate_packs import main as validate_packs_main  # noqa: E402


client = TestClient(app)


def test_health_endpoint():
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["status"] == "ok"
    assert payload["strict_verifier"] is True
    assert payload["zero_pii_logging"] is True
    langs = {item["language"] for item in payload["languages"]}
    assert {"ewondo", "duala", "fulfulde"}.issubset(langs)


def test_language_packs_valid():
    assert validate_packs_main() == 0

