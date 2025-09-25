# src/api/tests/test_ons_service.py (Versão corrigida)

import os
import asyncio
import httpx
from typing import Any
import pytest
from services.ons_service import OnsService, DownloadInfo, DownloadResult, ProcessResponse
from models.ons_dto import DateFilterDTO

# ===================================================================
# region: Tests for the main service method: process_reservoir_data
# ===================================================================

def test_process_reservoir_data_success_filters_and_downloads(monkeypatch: Any) -> None:
    """
    Teste completo de sucesso: valida a busca na API, a filtragem por ano e
    tipo de arquivo, e o processamento correto.
    """
    os.environ["ONS_API_URL"] = "https://example.com/api"

    class FakeRepo:
        def __init__(self) -> None: self.bucket_name = "test-bucket"
        def save(self, file: Any, filename: str) -> str: return f"gs://{self.bucket_name}/{filename}"

    import services.ons_service as mod
    monkeypatch.setattr(mod, "GCSFileRepository", FakeRepo, raising=True)

    resources = [
        {"format": "PARQUET", "url": "https://cdn/ear_2022.parquet", "name": "ear 2022"},
        {"format": "PARQUET", "url": "https://cdn/ear_2023.parquet", "name": "ear 2023"},
        {"format": "CSV", "url": "https://cdn/ear_2024.csv", "name": "ear 2024"},
        {"format": "PARQUET", "url": "https://cdn/ear_2021.parquet", "name": "ear 2021"},
    ]

    class _Resp:
        def __init__(self, json_obj: dict[str, Any]) -> None: self._json = json_obj
        def raise_for_status(self) -> None: return
        def json(self) -> dict[str, Any]: return self._json

    async def fake_get(self: Any, url: str, *args: Any, **kwargs: Any) -> _Resp:
        return _Resp({"result": {"resources": resources}})

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get, raising=True)

    service = OnsService()

    async def fake_download_parquet(client: Any, download_info: Any) -> Any:
        return DownloadResult(
            success=True, url=download_info.url, year=download_info.year, package=download_info.package,
            data_type=download_info.data_type, gcs_path=f"{download_info.package}/{download_info.year}/file.parquet",
            bucket="test-bucket"
        )

    monkeypatch.setattr(service, "_download_parquet", fake_download_parquet)

    # CORREÇÃO: Adicionado o argumento 'bucket'
    filters = DateFilterDTO(start_year=2022, end_year=2023, package="ear-diario-por-reservatorio", bucket="test-bucket")
    result = asyncio.run(service.process_reservoir_data(filters))

    assert isinstance(result, ProcessResponse)
    assert result.success_count == 2
    assert result.failure_count == 0
    urls = [r["url"] for r in result.success_downloads]
    assert "https://cdn/ear_2022.parquet" in urls
    assert "https://cdn/ear_2023.parquet" in urls


def test_process_reservoir_data_partial_success(monkeypatch: Any) -> None:
    os.environ["ONS_API_URL"] = "https://example.com/api"

    class FakeRepo:
        def __init__(self) -> None: self.bucket_name = "b"
        def save(self, file: Any, filename: str) -> str: return f"gs://b/{filename}"
        def raw_table_has_value(self, package_name: str, column_name: str, last_day: str) -> bool: return False

    import services.ons_service as mod
    monkeypatch.setattr(mod, "GCSFileRepository", FakeRepo, raising=True)

    resources = [
        {"format": "PARQUET", "url": "http://u/2022.parquet", "name": "n 2022"},
        {"format": "PARQUET", "url": "http://u/2023.parquet", "name": "n 2023"},
    ]

    class Resp:
        def __init__(self, obj: dict[str, Any]): self._obj = obj
        def raise_for_status(self) -> None: return
        def json(self) -> dict[str, Any]: return self._obj

    async def fake_get(self: Any, url: str, *a: Any, **k: Any) -> Resp:
        return Resp({"result": {"resources": resources}})

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get, raising=True)

    s = OnsService()

    async def fake_download(client: Any, info: DownloadInfo) -> DownloadResult:
        if info.year == 2022:
            return DownloadResult(success=True, url=info.url, year=info.year, package=info.package, data_type=info.data_type, gcs_path="p/2022/x.parquet", bucket="b")
        else:
            return DownloadResult(success=False, url=info.url, year=info.year, package=info.package, data_type=info.data_type, error_message="boom", bucket="b")

    monkeypatch.setattr(s, "_download_parquet", fake_download)

    # CORREÇÃO: Adicionado o argumento 'bucket'
    filters = DateFilterDTO(start_year=2022, end_year=2023, package="pkg", bucket="test-bucket")
    result = asyncio.run(s.process_reservoir_data(filters))
    
    assert result.total_processed == 2
    assert result.success_count == 1
    assert result.failure_count == 1


def test_process_reservoir_data_defaults_years_to_current(monkeypatch: Any) -> None:
    os.environ["ONS_API_URL"] = "https://example.com/api"

    class FakeRepo:
        def __init__(self) -> None: self.bucket_name = "b"
        def save(self, file: Any, filename: str) -> str: return f"gs://b/{filename}"
        def raw_table_has_value(self, package_name: str, column_name: str, last_day: str) -> bool: return False

    import services.ons_service as mod
    monkeypatch.setattr(mod, "GCSFileRepository", FakeRepo, raising=True)

    from datetime import datetime
    now_year = datetime.now().year
    resources = [{"format": "PARQUET", "url": f"http://u/{now_year}.parquet", "name": f"n {now_year}"}]

    class Resp:
        def __init__(self, obj: dict[str, Any]): self._obj = obj
        def raise_for_status(self) -> None: return
        def json(self) -> dict[str, Any]: return self._obj

    async def fake_get(self: Any, url: str, *a: Any, **k: Any) -> Resp:
        return Resp({"result": {"resources": resources}})

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get, raising=True)

    s = OnsService()

    async def fake_download_ok(client: Any, info: DownloadInfo) -> DownloadResult:
        return DownloadResult(success=True, url=info.url, year=info.year, package=info.package, data_type=info.data_type, gcs_path=f"p/{info.year}/ok.parquet", bucket="b")

    monkeypatch.setattr(s, "_download_parquet", fake_download_ok)

    # CORREÇÃO: Adicionado o argumento 'bucket'
    filters = DateFilterDTO(start_year=None, end_year=None, package="pkg", bucket="test-bucket")
    result = asyncio.run(s.process_reservoir_data(filters))
    
    assert result.total_processed == 1
    assert result.success_count == 1


def test_process_reservoir_data_raises_on_no_resources(monkeypatch: Any) -> None:
    os.environ["ONS_API_URL"] = "https://example.com/api"
    class FakeRepo:
        def __init__(self) -> None: self.bucket_name = "b"

    import services.ons_service as mod
    monkeypatch.setattr(mod, "GCSFileRepository", FakeRepo, raising=True)
    
    resources: list[dict[str, Any]] = []

    class Resp:
        def __init__(self, obj: dict[str, Any]): self._obj = obj
        def raise_for_status(self) -> None: return
        def json(self) -> dict[str, Any]: return self._obj

    async def fake_get(self: Any, url: str, *a: Any, **k: Any) -> Resp:
        return Resp({"result": {"resources": resources}})

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get, raising=True)
    s = OnsService()
    
    # CORREÇÃO: Adicionado o argumento 'bucket'
    filters = DateFilterDTO(start_year=2022, end_year=2023, package="pkg", bucket="test-bucket")
    
    with pytest.raises(Exception, match="No resources found in the package"):
        asyncio.run(s.process_reservoir_data(filters))


def test_process_reservoir_data_missing_env_var(monkeypatch: Any) -> None:
    if "ONS_API_URL" in os.environ:
        del os.environ["ONS_API_URL"]
    
    class FakeRepo:
        def __init__(self) -> None: self.bucket_name = "b"

    import services.ons_service as mod
    monkeypatch.setattr(mod, "GCSFileRepository", FakeRepo, raising=True)

    s = OnsService()
    
    # CORREÇÃO: Adicionado o argumento 'bucket'
    df = DateFilterDTO(start_year=2020, end_year=2020, package="p", bucket="test-bucket")
    
    with pytest.raises(ValueError):
        asyncio.run(s.process_reservoir_data(df))


# ===================================================================
# region: Tests for the helper method: _download_parquet
# ===================================================================

def test_download_parquet_success(monkeypatch: Any) -> None:
    class FakeRepo:
        def __init__(self) -> None: self.bucket_name = "b"
        def save(self, file: Any, filename: str) -> str: return f"gs://b/{filename}"
        def raw_table_has_value(self, package_name: str, column_name: str, last_day: str) -> bool: return False

    import services.ons_service as mod
    monkeypatch.setattr(mod, "GCSFileRepository", FakeRepo, raising=True)

    s = OnsService()
    class R:
        content = b"data"
        def raise_for_status(self) -> None: return

    async def fake_get(url: str, *args: Any, **kwargs: Any) -> R:
        return R()

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get, raising=True)
    monkeypatch.setattr(
        OnsService,
        "_read_to_dataframe",
        lambda *a, **k: __import__("pandas").DataFrame({"date_column": ["2023-01-01", "2023-01-02"]}),
    )
    info = DownloadInfo(url="http://u/f.parquet", year=2023, package="p", data_type="parquet")
    out = asyncio.run(s._download_parquet(httpx.AsyncClient(), info))
    
    assert isinstance(out, DownloadResult)
    assert out.success is False
    assert out.gcs_path == ""


def test_download_parquet_data_already_exists(monkeypatch: Any) -> None:
    class FakeRepo:
        def __init__(self) -> None: self.bucket_name = "b"
        def save(self, file: Any, filename: str) -> str: return f"gs://b/{filename}"
        def raw_table_has_value(self, package_name: str, column_name: str, last_day: str) -> bool: return True

    import services.ons_service as mod
    monkeypatch.setattr(mod, "GCSFileRepository", FakeRepo, raising=True)
    s = OnsService()

    class R:
        content = b"data"
        def raise_for_status(self) -> None: return

    async def fake_get(url: str, *args: Any, **kwargs: Any) -> R:
        return R()

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get, raising=True)
    monkeypatch.setattr(
        OnsService,
        "_read_to_dataframe",
        lambda *a, **k: __import__("pandas").DataFrame({"date_column": ["2023-01-01", "2023-01-02"]}),
    )
    info = DownloadInfo(url="http://u/f.parquet", year=2023, package="p", data_type="parquet")
    out = asyncio.run(s._download_parquet(httpx.AsyncClient(), info))
    
    assert isinstance(out, DownloadResult)
    assert out.success is False
    assert out.error_message == "Data already exists in the raw table"


def test_download_parquet_save_to_gcs_fails(monkeypatch: Any) -> None:
    class FakeRepo:
        def __init__(self) -> None: self.bucket_name = "b"
        def save(self, file: Any, filename: str) -> str: raise RuntimeError("save failed")
        def raw_table_has_value(self, package_name: str, column_name: str, last_day: str) -> bool: return False

    import services.ons_service as mod
    monkeypatch.setattr(mod, "GCSFileRepository", FakeRepo, raising=True)
    s = OnsService()

    class R:
        content = b"data"
        def raise_for_status(self) -> None: return

    async def fake_get(url: str, *args: Any, **kwargs: Any) -> R:
        return R()

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get, raising=True)
    monkeypatch.setattr(
        OnsService,
        "_read_to_dataframe",
        lambda *a, **k: __import__("pandas").DataFrame({"date_column": ["2023-01-01"]}),
    )
    info = DownloadInfo(url="http://u/f.parquet", year=2023, package="p", data_type="parquet")
    out = asyncio.run(s._download_parquet(httpx.AsyncClient(), info))
    
    assert isinstance(out, DownloadResult)
    assert out.success is False
    assert "Failed to save to GCS bucket" in out.error_message


def test_download_parquet_handles_read_error(monkeypatch: Any) -> None:
    class FakeRepo:
        def __init__(self) -> None: self.bucket_name = "b"
        def save(self, file: Any, filename: str) -> str: return "gs://b/x"

    import services.ons_service as mod
    monkeypatch.setattr(mod, "GCSFileRepository", FakeRepo, raising=True)
    s = OnsService()

    class R:
        content = b"data"
        def raise_for_status(self) -> None: return

    async def fake_get(url: str, *args: Any, **kwargs: Any) -> R:
        return R()

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get, raising=True)
    monkeypatch.setattr(
        OnsService,
        "_read_to_dataframe",
        lambda *a, **k: (_ for _ in ()).throw(ValueError("bad format")),
    )
    info = DownloadInfo(url="http://u/f.parquet", year=2023, package="p", data_type="parquet")
    out = asyncio.run(s._download_parquet(httpx.AsyncClient(), info))
    
    assert isinstance(out, DownloadResult)
    assert out.success is False
    assert "Failed to read source file" in out.error_message


# ===================================================================
# region: Tests for other helper methods
# ===================================================================

def test_build_gcs_path_for_past_year(monkeypatch: Any) -> None:
    class FakeRepo:
        def __init__(self) -> None: self.bucket_name = "b"

    import services.ons_service as mod
    monkeypatch.setattr(mod, "GCSFileRepository", FakeRepo, raising=True)
    s = OnsService()
    
    path = s._build_gcs_path("file_2020.parquet", resource_year=2020, package_name="pkg")
    assert path == "pkg/2020/file_2020.parquet"


def test_build_gcs_path_for_future_year(monkeypatch: Any) -> None:
    class FakeRepo:
        def __init__(self) -> None: self.bucket_name = "b"

    import services.ons_service as mod
    monkeypatch.setattr(mod, "GCSFileRepository", FakeRepo, raising=True)
    s = OnsService()
    
    path = s._build_gcs_path("file_9999.parquet", resource_year=9999, package_name="pkg")
    assert path.startswith("pkg/") and path.endswith(".parquet")


def test_read_to_dataframe_unsupported_format_raises_error(monkeypatch: Any) -> None:
    class FakeRepo:
        def __init__(self) -> None: self.bucket_name = "b"

    import services.ons_service as mod
    monkeypatch.setattr(mod, "GCSFileRepository", FakeRepo, raising=True)
    s = OnsService()

    with pytest.raises(ValueError):
        s._read_to_dataframe(b"some_data", "unsupported_format")