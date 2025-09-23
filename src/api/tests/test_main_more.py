from main import app
from fastapi.testclient import TestClient


def test_openapi_and_docs() -> None:
    client = TestClient(app)
    r = client.get("/openapi.json")
    assert r.status_code == 200
    r = client.get("/docs")
    assert r.status_code == 200
