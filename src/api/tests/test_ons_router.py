# src/api/tests/test_ons_router.py (CORRIGIDO E COM NOVOS TESTES)

import os
from typing import Any, Generator, List
import pytest
from fastapi.testclient import TestClient
import httpx
from models.ons_dto import DateFilterDTO
from services.ons_service import ProcessResponse, OnsService


# ===================================================================
# region: Fixtures e Helpers
# ===================================================================

@pytest.fixture(autouse=True)
def mock_gcs_before_app_import(monkeypatch: Any) -> None:
    class FakeGCS:
        def __init__(self) -> None: self.bucket_name = "fake-bucket"
        def save(self, file: Any, filename: str, **kwargs: Any) -> str: return f"gs://{self.bucket_name}/{filename}"
        def exists(self) -> bool: return True
        def bucket(self, name: str) -> Any: return self
        def blob(self, name: str) -> Any: return self
        def upload_from_string(self, *args: Any, **kwargs: Any) -> None: return None
        @property
        def public_url(self) -> str: return "gs://fake-bucket/fake-file"

    import services.ons_service as service_module
    monkeypatch.setattr(service_module, "GCSFileRepository", FakeGCS)

@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    from main import app
    with TestClient(app) as test_client:
        yield test_client

def _payload() -> dict[str, Any]:
    return {"start_year": 2022, "end_year": 2023, "package": "test-package", "bucket": "test-bucket"}

# ===================================================================
# region: Testes para o Endpoint /ons/filter-parquet-files (Single DTO)
# ===================================================================

def test_filter_parquet_files_endpoint_all_success(monkeypatch: Any, client: TestClient) -> None:
    os.environ["ONS_API_URL"] = "https://example.com/api"
    async def fake_process(_self: Any, filters: Any) -> ProcessResponse:
        return ProcessResponse(success_downloads=[{"url": "u", "gcs_path": "p", "bucket": "b"}], failed_downloads=[], total_processed=1, success_count=1, failure_count=0)
    monkeypatch.setattr(OnsService, "process_reservoir_data", fake_process)

    r = client.post("/ons/filter-parquet-files", json=_payload())
    
    assert r.status_code == 200
    response_data = r.json()
    assert response_data["status"] == "success"

# --- NOVOS TESTES PARA AUMENTAR COBERTURA ---

def test_filter_parquet_files_endpoint_all_failed(monkeypatch: Any, client: TestClient) -> None:
    """Testa o cenário onde todos os downloads falham, esperando um status 422."""
    os.environ["ONS_API_URL"] = "https://example.com/api"
    async def fake_process(_self: Any, filters: Any) -> ProcessResponse:
        return ProcessResponse(success_downloads=[], failed_downloads=[{"url": "u", "error_message": "e"}], total_processed=1, success_count=0, failure_count=1)
    monkeypatch.setattr(OnsService, "process_reservoir_data", fake_process)

    r = client.post("/ons/filter-parquet-files", json=_payload())
    
    assert r.status_code == 422
    response_data = r.json()
    assert response_data["status"] == "failed"

def test_filter_parquet_files_endpoint_partial_success(monkeypatch: Any, client: TestClient) -> None:
    """Testa o cenário de sucesso parcial, esperando um status 200."""
    os.environ["ONS_API_URL"] = "https://example.com/api"
    async def fake_process(_self: Any, filters: Any) -> ProcessResponse:
        return ProcessResponse(success_downloads=[{"url": "u1"}], failed_downloads=[{"url": "u2"}], total_processed=2, success_count=1, failure_count=1)
    monkeypatch.setattr(OnsService, "process_reservoir_data", fake_process)

    r = client.post("/ons/filter-parquet-files", json=_payload())
    
    assert r.status_code == 200
    response_data = r.json()
    assert response_data["status"] == "partial_success"

# --- TESTES DE ERRO CORRIGIDOS ---

def test_service_raises_exception_returns_500(monkeypatch: Any, client: TestClient) -> None:
    """Testa se uma exceção genérica no serviço resulta em um HTTP 500."""
    async def fake_process(_self: Any, filters: Any) -> Any:
        raise ValueError("Erro de propósito no serviço")
    monkeypatch.setattr(OnsService, "process_reservoir_data", fake_process)
    
    r = client.post("/ons/filter-parquet-files", json=_payload())

    assert r.status_code == 500
    assert "Erro de propósito no serviço" in r.json()["detail"]

# ===================================================================
# region: Testes para o Endpoint /ons/bulk-ingest-parquet-files (Bulk DTO)
# ===================================================================

def test_bulk_ingest_endpoint_success(monkeypatch: Any, client: TestClient) -> None:
    """Testa o caminho de sucesso para o endpoint de processamento em lote."""
    async def fake_bulk_process(_self: Any, filters_list: List[DateFilterDTO]) -> List[ProcessResponse]:
        return [
            ProcessResponse(success_downloads=[{"url": "u1"}], failed_downloads=[], total_processed=1, success_count=1, failure_count=0),
            ProcessResponse(success_downloads=[{"url": "u2"}], failed_downloads=[], total_processed=1, success_count=1, failure_count=0)
        ]
    monkeypatch.setattr(OnsService, "process_reservoir_data_bulk", fake_bulk_process)

    r = client.post("/ons/bulk-ingest-parquet-files", json=[_payload(), _payload()])
    
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "success"
    assert len(data["data"]) == 2
    assert data["data"][0]["success_count"] == 1

def test_bulk_ingest_endpoint_exception_returns_500(monkeypatch: Any, client: TestClient) -> None:
    """Testa se uma exceção no serviço bulk resulta em um HTTP 500."""
    async def fake_bulk_process(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("Erro no processamento em lote")
    monkeypatch.setattr(OnsService, "process_reservoir_data_bulk", fake_bulk_process)

    r = client.post("/ons/bulk-ingest-parquet-files", json=[_payload()])
    
    assert r.status_code == 500
    assert "Erro no processamento em lote" in r.json()["detail"]