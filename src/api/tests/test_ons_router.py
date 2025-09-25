# src/api/tests/test_ons_router.py

import os
from typing import Any, Generator
import pytest
from fastapi.testclient import TestClient
import httpx


# ===================================================================
# region: Fixtures e Helpers
# ===================================================================

@pytest.fixture(autouse=True)
def mock_gcs_before_app_import(monkeypatch: Any) -> None:
    """Mocka o GCSFileRepository antes que a aplicação FastAPI seja importada."""
    class FakeGCS:
        def __init__(self) -> None:
            self.bucket_name = "fake-bucket"

        def save(self, file: Any, filename: str) -> str:
            return f"gs://{self.bucket_name}/{filename}"

    import services.ons_service as service_module

    monkeypatch.setattr(service_module, "GCSFileRepository", FakeGCS)


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Fornece um TestClient para a aplicação FastAPI."""
    from main import app

    with TestClient(app) as test_client:
        yield test_client


def _payload() -> dict[str, Any]:
    """Retorna um payload padrão para os testes do endpoint de filtro."""
    return {
        "start_year": 2022,
        "end_year": 2023,
        "package": "ear-diario-por-reservatorio",
    }


# ===================================================================
# region: Testes para Endpoints Básicos
# ===================================================================

def test_root_and_health_endpoints(client: TestClient) -> None:
    """Testa os endpoints / e /health para garantir que a API está de pé."""
    r_root = client.get("/")
    assert r_root.status_code == 200
    assert r_root.json()["message"] == "Hello World"

    r_health = client.get("/health")
    assert r_health.status_code == 200
    assert r_health.json()["status"] == "healthy"


# ===================================================================
# region: Testes para o Endpoint /ons/filter-parquet-files
# ===================================================================

def test_filter_parquet_files_endpoint_success(
    monkeypatch: Any, client: TestClient
) -> None:
    """Testa o caminho de sucesso para o endpoint de filtro."""
    from services.ons_service import OnsService, ProcessResponse

    os.environ["ONS_API_URL"] = "https://example.com/api"

    async def fake_process(_self: Any, filters: Any) -> ProcessResponse:
        return ProcessResponse(
            success_downloads=[{"url": "u", "gcs_path": "p", "bucket": "b"}],
            failed_downloads=[],
            total_processed=1,
            success_count=1,
            failure_count=0,
        )

    monkeypatch.setattr(OnsService, "process_reservoir_data", fake_process)

    r = client.post("/ons/filter-parquet-files", json=_payload())
    
    assert r.status_code == 200
    response_data = r.json()
    assert response_data["status"] == "success"
    assert "data" in response_data
    
    success_list = response_data["data"]["success_downloads"]
    assert isinstance(success_list, list) and success_list
    assert {"url", "gcs_path", "bucket"}.issubset(success_list[0].keys())


def test_value_error_is_handled(monkeypatch: Any, client: TestClient) -> None:
    """Testa o tratamento de ValueError (ex: erro de configuração)."""
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
    """Testa o tratamento de httpx.RequestError (ex: erro de rede)."""
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
    """Testa o tratamento de httpx.HTTPStatusError (ex: API da ONS fora do ar)."""
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
    """Testa o tratamento de uma exceção genérica e inesperada."""
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