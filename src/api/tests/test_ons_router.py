import os
from typing import Any
from fastapi.testclient import TestClient
from main import app


def test_root_and_health_endpoints() -> None:
    client = TestClient(app)
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["message"] == "Hello World"

    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


def test_filter_parquet_files_endpoint_success(monkeypatch: Any) -> None:
    from services.ons_service import OnsService

    os.environ["ONS_API_URL"] = "https://example.com/api"

    async def fake_process(_self: Any, filters: Any) -> list[dict]:
        return [{"url": "u", "gcs_path": "p", "bucket": "b"}]

    monkeypatch.setattr(OnsService, "process_reservoir_data", fake_process)

    client = TestClient(app)
    payload = {
        "start_year": 2022,
        "end_year": 2023,
        "package": "ear-diario-por-reservatorio",
        "data_type": "parquet",
    }
    r = client.post("/ons/filter-parquet-files", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list) and data
    assert {"url", "gcs_path", "bucket"}.issubset(data[0].keys())
