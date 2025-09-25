from typing import Any, Generator
import pytest
from fastapi.testclient import TestClient
import httpx


@pytest.fixture(autouse=True)
def mock_gcs_before_app_import(monkeypatch: Any) -> None:
    class FakeGCS:
        def __init__(self) -> None:
            self.bucket_name = "fake-bucket"

        def save(self, file: Any, filename: str) -> str:
            return f"gs://{self.bucket_name}/{filename}"

    import services.ons_service as service_module

    monkeypatch.setattr(service_module, "GCSFileRepository", FakeGCS)


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    from main import app

    with TestClient(app) as test_client:
        yield test_client


def _payload() -> dict:
    return {
        "start_year": 2022,
        "end_year": 2023,
        "package": "ear-diario-por-reservatorio",
    }


def test_value_error_is_handled(monkeypatch: Any, client: TestClient) -> None:
    from services.ons_service import OnsService

    async def fake(_self: Any, filters: Any) -> Any:
        raise ValueError("bad config")

    monkeypatch.setattr(OnsService, "process_reservoir_data", fake)
    r = client.post("/ons/filter-parquet-files", json=_payload())

    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "error"
    assert data["message"] == "bad config"
    assert data["data"]["error_type"] == "configuration_error"


def test_request_error_is_handled(monkeypatch: Any, client: TestClient) -> None:
    from services.ons_service import OnsService

    async def fake(_self: Any, filters: Any) -> Any:
        raise httpx.RequestError("network issue")

    monkeypatch.setattr(OnsService, "process_reservoir_data", fake)
    r = client.post("/ons/filter-parquet-files", json=_payload())

    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "error"
    assert "network issue" in data["message"]
    assert data["data"]["error_type"] == "network_error"


def test_http_status_error_is_handled(
    monkeypatch: Any, client: TestClient
) -> None:
    from services.ons_service import OnsService

    mock_response = httpx.Response(status_code=418, request=httpx.Request("GET", "http://test"))

    async def fake(_self: Any, filters: Any) -> Any:
        raise httpx.HTTPStatusError("I'm a teapot", request=mock_response.request, response=mock_response)

    monkeypatch.setattr(OnsService, "process_reservoir_data", fake)
    r = client.post("/ons/filter-parquet-files", json=_payload())

    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "error"
    assert "I'm a teapot" in data["message"]
    assert data["data"]["error_type"] == "api_error"
    assert data["data"]["api_status_code"] == 418


def test_generic_error_is_handled(monkeypatch: Any, client: TestClient) -> None:
    from services.ons_service import OnsService

    async def fake(_self: Any, filters: Any) -> Any:
        raise RuntimeError("boom")

    monkeypatch.setattr(OnsService, "process_reservoir_data", fake)
    r = client.post("/ons/filter-parquet-files", json=_payload())

    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "error"
    assert "boom" in data["message"]
    assert data["data"]["error_type"] == "internal_error"