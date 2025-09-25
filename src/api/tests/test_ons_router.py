# src/api/tests/test_ons_router.py

import os
from typing import Any, Generator
import pytest
from fastapi.testclient import TestClient


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


def test_root_and_health_endpoints(client: TestClient) -> None:
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["message"] == "Hello World"

    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


def test_filter_parquet_files_endpoint_success(
    monkeypatch: Any, client: TestClient
) -> None:
    from services.ons_service import OnsService

    os.environ["ONS_API_URL"] = "https://example.com/api"

    async def fake_process(_self: Any, filters: Any) -> Any:
        from services.ons_service import ProcessResponse
        return ProcessResponse(
            success_downloads=[{"url": "u", "gcs_path": "p", "bucket": "b"}],
            failed_downloads=[],
            total_processed=1,
            success_count=1,
            failure_count=0
        )

    monkeypatch.setattr(OnsService, "process_reservoir_data", fake_process)

    payload = {
        "start_year": 2022,
        "end_year": 2023,
        "package": "ear-diario-por-reservatorio",
    }
    r = client.post("/ons/filter-parquet-files", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list) and data
    assert {"url", "gcs_path", "bucket"}.issubset(data[0].keys())
