from typing import Any
from fastapi.testclient import TestClient
from main import app


def _payload() -> dict:
    return {
        "start_year": 2022,
        "end_year": 2023,
        "package": "ear-diario-por-reservatorio",
        "data_type": "parquet",
    }


def test_value_error_translates_to_500(monkeypatch: Any) -> None:
    from services.ons_service import OnsService

    async def fake(_self, filters):  # type: ignore[no-untyped-def]
        raise ValueError("bad")

    monkeypatch.setattr(OnsService, "process_reservoir_data", fake)
    client = TestClient(app)
    r = client.post("/ons/filter-parquet-files", json=_payload())
    assert r.status_code == 500


def test_request_error_translates_to_503(monkeypatch: Any) -> None:
    from services.ons_service import OnsService
    import httpx

    async def fake(_self, filters):  # type: ignore[no-untyped-def]
        raise httpx.RequestError("net")

    monkeypatch.setattr(OnsService, "process_reservoir_data", fake)
    client = TestClient(app)
    r = client.post("/ons/filter-parquet-files", json=_payload())
    assert r.status_code == 503


def test_http_status_error_propagates_status(monkeypatch: Any) -> None:
    from services.ons_service import OnsService
    import httpx

    class Resp:
        status_code = 418

    async def fake(_self, filters):  # type: ignore[no-untyped-def]
        raise httpx.HTTPStatusError("teapot", request=None, response=Resp())

    monkeypatch.setattr(OnsService, "process_reservoir_data", fake)
    client = TestClient(app)
    r = client.post("/ons/filter-parquet-files", json=_payload())
    assert r.status_code == 418


def test_generic_error_becomes_500(monkeypatch: Any) -> None:
    from services.ons_service import OnsService

    async def fake(_self, filters):  # type: ignore[no-untyped-def]
        raise RuntimeError("boom")

    monkeypatch.setattr(OnsService, "process_reservoir_data", fake)
    client = TestClient(app)
    r = client.post("/ons/filter-parquet-files", json=_payload())
    assert r.status_code == 500
