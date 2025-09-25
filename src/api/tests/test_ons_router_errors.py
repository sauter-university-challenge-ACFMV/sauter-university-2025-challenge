# src/api/tests/test_ons_router_errors.py

from typing import Any, Generator
import pytest
from fastapi.testclient import TestClient
import httpx


# Fixture para simular o GCS e evitar a autenticação real
@pytest.fixture(autouse=True)
def mock_gcs_before_app_import(monkeypatch: Any) -> None:
    class FakeGCS:
        def __init__(self) -> None:
            self.bucket_name = "fake-bucket"

        def save(self, file: Any, filename: str) -> str:
            return f"gs://{self.bucket_name}/{filename}"

    import services.ons_service as service_module

    monkeypatch.setattr(service_module, "GCSFileRepository", FakeGCS)


# Fixture que fornece um TestClient seguro
@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    from main import app  # Importa o app DEPOIS do mock ser aplicado

    with TestClient(app) as test_client:
        yield test_client


def _payload() -> dict:
    return {
        "start_year": 2022,
        "end_year": 2023,
        "package": "ear-diario-por-reservatorio",
    }


def test_value_error_translates_to_500(monkeypatch: Any, client: TestClient) -> None:
    from services.ons_service import OnsService

    async def fake(_self: Any, filters: Any) -> Any:
        raise ValueError("bad")

    monkeypatch.setattr(OnsService, "process_reservoir_data", fake)
    r = client.post("/ons/filter-parquet-files", json=_payload())
    assert r.status_code == 500


def test_request_error_translates_to_503(monkeypatch: Any, client: TestClient) -> None:
    from services.ons_service import OnsService

    async def fake(_self: Any, filters: Any) -> Any:
        raise httpx.RequestError("net")

    monkeypatch.setattr(OnsService, "process_reservoir_data", fake)
    r = client.post("/ons/filter-parquet-files", json=_payload())
    assert r.status_code == 503


def test_http_status_error_propagates_status(
    monkeypatch: Any, client: TestClient
) -> None:
    from services.ons_service import OnsService

    class Resp:
        status_code = 418

    async def fake(_self: Any, filters: Any) -> Any:
        raise httpx.HTTPStatusError("teapot", request=None, response=Resp())  # type: ignore

    monkeypatch.setattr(OnsService, "process_reservoir_data", fake)
    r = client.post("/ons/filter-parquet-files", json=_payload())
    assert r.status_code == 418


def test_generic_error_becomes_500(monkeypatch: Any, client: TestClient) -> None:
    from services.ons_service import OnsService

    async def fake(_self: Any, filters: Any) -> Any:
        raise RuntimeError("boom")

    monkeypatch.setattr(OnsService, "process_reservoir_data", fake)
    r = client.post("/ons/filter-parquet-files", json=_payload())
    assert r.status_code == 500
