import os
import asyncio
import httpx
from typing import Any

from services.ons_service import OnsService, DownloadInfo, DownloadResult
from models.ons_dto import DateFilterDTO


def test_download_parquet_save_failure(monkeypatch: Any) -> None:
    class FakeRepo:
        def __init__(self) -> None:
            self.bucket_name = "b"

        def save(self, file: Any, filename: str) -> str:
            raise RuntimeError("save failed")

        def raw_table_has_value(self, package_name: str, column_name: str, last_day: str) -> bool:
            return False

    import services.ons_service as mod

    monkeypatch.setattr(mod, "GCSFileRepository", FakeRepo, raising=True)

    s = OnsService()

    async def fake_get(url: str, *args: Any, **kwargs: Any):  # type: ignore[no-untyped-def]
        class R:
            content = b"data"

            def raise_for_status(self) -> None:
                return None

        return R()

    # Make reading work and saving fail
    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get, raising=True)
    monkeypatch.setattr(
        OnsService,
        "_read_to_dataframe",
        lambda *a, **k: __import__("pandas").DataFrame({"date_column": ["2023-01-01", "2023-01-02"]}),
    )

    info = DownloadInfo(
        url="http://u/f.parquet", year=2023, package="p", data_type="parquet"
    )
    out = asyncio.run(s._download_parquet(httpx.AsyncClient(), info))
    
    # Now returns DownloadResult instead of string
    assert isinstance(out, DownloadResult)
    assert out.success == False
    assert "Failed to save to GCS bucket" in out.error_message
    assert out.url == "http://u/f.parquet"
    assert out.package == "p"


def test_download_parquet_success(monkeypatch: Any) -> None:
    class FakeRepo:
        def __init__(self) -> None:
            self.bucket_name = "b"

        def save(self, file: Any, filename: str) -> str:
            return f"gs://b/{filename}"

        def raw_table_has_value(self, package_name: str, column_name: str, last_day: str) -> bool:
            return False

    import services.ons_service as mod

    monkeypatch.setattr(mod, "GCSFileRepository", FakeRepo, raising=True)

    s = OnsService()

    async def fake_get(url: str, *args: Any, **kwargs: Any):  # type: ignore[no-untyped-def]
        class R:
            content = b"data"

            def raise_for_status(self) -> None:
                return None

        return R()

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get, raising=True)
    monkeypatch.setattr(
        OnsService,
        "_read_to_dataframe",
        lambda *a, **k: __import__("pandas").DataFrame({"date_column": ["2023-01-01", "2023-01-02"]}),
    )

    info = DownloadInfo(
        url="http://u/f.parquet", year=2023, package="p", data_type="parquet"
    )
    out = asyncio.run(s._download_parquet(httpx.AsyncClient(), info))
    
    assert isinstance(out, DownloadResult)
    assert out.success == True
    assert out.gcs_path == "p/2023/01/24/f.parquet"  # Uses current date for current year
    assert out.error_message == ""


def test_download_parquet_data_already_exists(monkeypatch: Any) -> None:
    class FakeRepo:
        def __init__(self) -> None:
            self.bucket_name = "b"

        def save(self, file: Any, filename: str) -> str:
            return f"gs://b/{filename}"

        def raw_table_has_value(self, package_name: str, column_name: str, last_day: str) -> bool:
            return True  # Data already exists

    import services.ons_service as mod

    monkeypatch.setattr(mod, "GCSFileRepository", FakeRepo, raising=True)

    s = OnsService()

    async def fake_get(url: str, *args: Any, **kwargs: Any):  # type: ignore[no-untyped-def]
        class R:
            content = b"data"

            def raise_for_status(self) -> None:
                return None

        return R()

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get, raising=True)
    monkeypatch.setattr(
        OnsService,
        "_read_to_dataframe",
        lambda *a, **k: __import__("pandas").DataFrame({"date_column": ["2023-01-01", "2023-01-02"]}),
    )

    info = DownloadInfo(
        url="http://u/f.parquet", year=2023, package="p", data_type="parquet"
    )
    out = asyncio.run(s._download_parquet(httpx.AsyncClient(), info))
    
    assert isinstance(out, DownloadResult)
    assert out.success == False
    assert out.error_message == "Data already exists in the raw table"


def test_process_reservoir_data_partial_success(monkeypatch: Any) -> None:
    os.environ["ONS_API_URL"] = "https://example.com/api"

    class FakeRepo:
        def __init__(self) -> None:
            self.bucket_name = "b"

        def save(self, file: Any, filename: str) -> str:
            return f"gs://b/{filename}"

        def raw_table_has_value(self, package_name: str, column_name: str, last_day: str) -> bool:
            return False

    import services.ons_service as mod

    monkeypatch.setattr(mod, "GCSFileRepository", FakeRepo, raising=True)

    # Two parquet resources in range
    resources = [
        {"format": "PARQUET", "url": "http://u/2022.parquet", "name": "n 2022"},
        {"format": "PARQUET", "url": "http://u/2023.parquet", "name": "n 2023"},
    ]

    class Resp:
        def __init__(self, obj: dict[str, Any]):
            self._obj = obj

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, Any]:
            return self._obj

    async def fake_get(self, url: str, *a: Any, **k: Any):  # type: ignore[no-untyped-def]
        return Resp({"result": {"resources": resources}})

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get, raising=True)

    s = OnsService()

    async def fake_download(client: Any, info: DownloadInfo) -> DownloadResult:
        if info.year == 2022:
            return DownloadResult(
                url=info.url,
                year=info.year,
                package=info.package,
                data_type=info.data_type,
                success=True,
                gcs_path="p/2022/x.parquet",
                bucket="b"
            )
        else:
            return DownloadResult(
                url=info.url,
                year=info.year,
                package=info.package,
                data_type=info.data_type,
                success=False,
                error_message="boom",
                bucket="b"
            )

    monkeypatch.setattr(s, "_download_parquet", fake_download)

    filters = DateFilterDTO(start_year=2022, end_year=2023, package="pkg")
    result = asyncio.run(s.process_reservoir_data(filters))
    
    # Now returns ProcessResponse instead of list
    assert result.total_processed == 2
    assert result.success_count == 1
    assert result.failure_count == 1
    assert len(result.success_downloads) == 1
    assert len(result.failed_downloads) == 1
    assert result.success_downloads[0]["url"].endswith("2022.parquet")
    assert result.failed_downloads[0]["url"].endswith("2023.parquet")


def test_process_reservoir_data_all_success(monkeypatch: Any) -> None:
    os.environ["ONS_API_URL"] = "https://example.com/api"

    class FakeRepo:
        def __init__(self) -> None:
            self.bucket_name = "b"

        def save(self, file: Any, filename: str) -> str:
            return f"gs://b/{filename}"

        def raw_table_has_value(self, package_name: str, column_name: str, last_day: str) -> bool:
            return False

    import services.ons_service as mod

    monkeypatch.setattr(mod, "GCSFileRepository", FakeRepo, raising=True)

    resources = [
        {"format": "PARQUET", "url": "http://u/2022.parquet", "name": "n 2022"},
    ]

    class Resp:
        def __init__(self, obj: dict[str, Any]):
            self._obj = obj

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, Any]:
            return self._obj

    async def fake_get(self, url: str, *a: Any, **k: Any):  # type: ignore[no-untyped-def]
        return Resp({"result": {"resources": resources}})

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get, raising=True)

    s = OnsService()

    async def fake_download_success(client: Any, info: DownloadInfo) -> DownloadResult:
        return DownloadResult(
            url=info.url,
            year=info.year,
            package=info.package,
            data_type=info.data_type,
            success=True,
            gcs_path=f"p/{info.year}/ok.parquet",
            bucket="b"
        )

    monkeypatch.setattr(s, "_download_parquet", fake_download_success)

    filters = DateFilterDTO(start_year=2022, end_year=2022, package="pkg")
    result = asyncio.run(s.process_reservoir_data(filters))
    
    assert result.total_processed == 1
    assert result.success_count == 1
    assert result.failure_count == 0
    assert len(result.success_downloads) == 1
    assert len(result.failed_downloads) == 0


def test_process_reservoir_data_defaults_years(monkeypatch: Any) -> None:
    os.environ["ONS_API_URL"] = "https://example.com/api"

    class FakeRepo:
        def __init__(self) -> None:
            self.bucket_name = "b"

        def save(self, file: Any, filename: str) -> str:
            return f"gs://b/{filename}"

        def raw_table_has_value(self, package_name: str, column_name: str, last_day: str) -> bool:
            return False

    import services.ons_service as mod

    monkeypatch.setattr(mod, "GCSFileRepository", FakeRepo, raising=True)

    from datetime import datetime

    now_year = datetime.now().year
    resources = [
        {
            "format": "PARQUET",
            "url": f"http://u/{now_year}.parquet",
            "name": f"n {now_year}",
        },
    ]

    class Resp:
        def __init__(self, obj: dict[str, Any]):
            self._obj = obj

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, Any]:
            return self._obj

    async def fake_get(self, url: str, *a: Any, **k: Any):  # type: ignore[no-untyped-def]
        return Resp({"result": {"resources": resources}})

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get, raising=True)

    s = OnsService()

    async def fake_download_ok(client: Any, info: DownloadInfo) -> DownloadResult:
        return DownloadResult(
            url=info.url,
            year=info.year,
            package=info.package,
            data_type=info.data_type,
            success=True,
            gcs_path=f"p/{info.year}/ok.parquet",
            bucket="b"
        )

    monkeypatch.setattr(s, "_download_parquet", fake_download_ok)

    filters = DateFilterDTO(start_year=None, end_year=None, package="pkg")
    result = asyncio.run(s.process_reservoir_data(filters))
    
    assert result.total_processed == 1
    assert result.success_count == 1
    assert result.failure_count == 0
    assert len(result.success_downloads) == 1


def test_process_reservoir_data_no_resources_found(monkeypatch: Any) -> None:
    os.environ["ONS_API_URL"] = "https://example.com/api"

    class FakeRepo:
        def __init__(self) -> None:
            self.bucket_name = "b"

    import services.ons_service as mod

    monkeypatch.setattr(mod, "GCSFileRepository", FakeRepo, raising=True)

    # Empty resources
    resources: list[dict[str, Any]] = []

    class Resp:
        def __init__(self, obj: dict[str, Any]):
            self._obj = obj

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, Any]:
            return self._obj

    async def fake_get(self, url: str, *a: Any, **k: Any):  # type: ignore[no-untyped-def]
        return Resp({"result": {"resources": resources}})

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get, raising=True)

    s = OnsService()

    filters = DateFilterDTO(start_year=2022, end_year=2023, package="pkg")
    
    # Should raise an exception when no resources found
    try:
        result = asyncio.run(s.process_reservoir_data(filters))
        assert False, "Expected exception but none was raised"
    except Exception as e:
        assert "No resources found in the package" in str(e)