import os
import asyncio
import pytest
from typing import Any

from services.ons_service import OnsService


def test_process_reservoir_data_success_filters_and_downloads(monkeypatch: Any) -> None:
    # Arrange
    os.environ["ONS_API_URL"] = "https://example.com/api"

    # Fake repository to avoid real GCS client
    class FakeRepo:
        def __init__(self) -> None:
            self.bucket_name = "test-bucket"
        def save(self, file: Any, filename: str) -> str:
            return f"gs://{self.bucket_name}/{filename}"

    import services.ons_service as mod
    monkeypatch.setattr(mod, "GCSFileRepository", FakeRepo, raising=True)

    # Fake package_show response
    resources = [
        {"format": "PARQUET", "url": "https://cdn/ear_2022.parquet", "name": "ear 2022"},
        {"format": "PARQUET", "url": "https://cdn/ear_2023.parquet", "name": "ear 2023"},
        {"format": "CSV", "url": "https://cdn/ear_2024.csv", "name": "ear 2024"},
        {"format": "PARQUET", "url": "https://cdn/ear_2021.parquet", "name": "ear 2021"},
    ]

    class _Resp:
        def __init__(self, json_obj: dict[str, Any]) -> None:
            self._json = json_obj
        def raise_for_status(self) -> None:
            return None
        def json(self) -> dict[str, Any]:
            return self._json

    async def fake_get(self: Any, url: str, *args: Any, **kwargs: Any) -> _Resp:
        return _Resp({"result": {"resources": resources}})

    # Patch httpx.AsyncClient.get
    import httpx
    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get, raising=True)

    service = OnsService()

    # Short-circuit the heavy download path
    async def fake_download_parquet(client: Any, download_info: Any) -> str:
        return f"{download_info.package}/{download_info.year}/file.parquet"

    monkeypatch.setattr(service, "_download_parquet", fake_download_parquet)

    # Act
    from models.ons_dto import DateFilterDTO
    filters = DateFilterDTO(start_year=2022, end_year=2023, package="ear-diario-por-reservatorio", data_type="parquet")
    result = asyncio.run(service.process_reservoir_data(filters))

    # Assert: should include only 2022 and 2023 parquet resources
    assert isinstance(result, list)
    assert len(result) == 2
    urls = [r["url"] for r in result]
    assert "https://cdn/ear_2022.parquet" in urls
    assert "https://cdn/ear_2023.parquet" in urls
    for item in result:
        assert item["bucket"] == "test-bucket"
        assert item["gcs_path"].endswith("/file.parquet")


def test_process_reservoir_data_no_resources(monkeypatch: Any) -> None:
    os.environ["ONS_API_URL"] = "https://example.com/api"

    # Fake repository
    class FakeRepo:
        def __init__(self) -> None:
            self.bucket_name = "test-bucket"
        def save(self, file: Any, filename: str) -> str:
            return f"gs://{self.bucket_name}/{filename}"

    import services.ons_service as mod
    monkeypatch.setattr(mod, "GCSFileRepository", FakeRepo, raising=True)

    class _Resp:
        def __init__(self, json_obj: dict[str, Any]):
            self._json = json_obj
        def raise_for_status(self) -> None:
            return None
        def json(self) -> dict[str, Any]:
            return self._json

    async def fake_get(self: Any, url: str, *args: Any, **kwargs: Any) -> _Resp:
        return _Resp({"result": {"resources": []}})

    import httpx
    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get, raising=True)

    service = OnsService()
    from models.ons_dto import DateFilterDTO
    filters = DateFilterDTO(start_year=2022, end_year=2023, package="ear-diario-por-reservatorio", data_type="parquet")

    result = asyncio.run(service.process_reservoir_data(filters))
    assert result == []


def test_build_gcs_path_uses_year_partition(monkeypatch: Any) -> None:
    # Fake repository to bypass real GCS init
    class FakeRepo:
        def __init__(self) -> None:
            self.bucket_name = "test-bucket"
        def save(self, file: Any, filename: str) -> str:
            return f"gs://{self.bucket_name}/{filename}"

    import services.ons_service as mod
    monkeypatch.setattr(mod, "GCSFileRepository", FakeRepo, raising=True)

    service = OnsService()
    p = service._build_gcs_path("file_2020.parquet", resource_year=2020, package_name="pkg")
    assert p.startswith("pkg/2020/")
    assert p.endswith(".parquet")


def test_missing_env_raises_value_error(monkeypatch: Any) -> None:
    if "ONS_API_URL" in os.environ:
        del os.environ["ONS_API_URL"]
    # Fake repository
    class FakeRepo:
        def __init__(self) -> None:
            self.bucket_name = "test-bucket"
        def save(self, file: Any, filename: str) -> str:
            return f"gs://{self.bucket_name}/{filename}"

    import services.ons_service as mod
    monkeypatch.setattr(mod, "GCSFileRepository", FakeRepo, raising=True)

    service = OnsService()
    from models.ons_dto import DateFilterDTO
    filters = DateFilterDTO(start_year=2022, end_year=2022, package="ear-diario-por-reservatorio", data_type="parquet")
    with pytest.raises(ValueError):
        # Run in event loop because it's async
        asyncio.run(service.process_reservoir_data(filters))


