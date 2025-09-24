import os
import asyncio
import httpx
from typing import Any

from services.ons_service import OnsService, DownloadInfo
from models.ons_dto import DateFilterDTO


def test_download_parquet_save_failure(monkeypatch: Any) -> None:
    class FakeRepo:
        def __init__(self) -> None:
            self.bucket_name = "b"

        def save(self, file: Any, filename: str) -> str:
            raise RuntimeError("save failed")

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
        lambda *a, **k: __import__("pandas").DataFrame({"a": [1]}),
    )

    info = DownloadInfo(
        url="http://u/f.parquet", year=2023, package="p", data_type="parquet"
    )
    out = asyncio.run(s._download_parquet(httpx.AsyncClient(), info))
    assert out == ""


def test_process_reservoir_data_partial_success(monkeypatch: Any) -> None:
    os.environ["ONS_API_URL"] = "https://example.com/api"

    class FakeRepo:
        def __init__(self) -> None:
            self.bucket_name = "b"

        def save(self, file: Any, filename: str) -> str:
            return f"gs://b/{filename}"

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

    async def fake_download(client: Any, info: DownloadInfo) -> str:
        if info.year == 2022:
            return "p/2022/x.parquet"
        raise RuntimeError("boom")

    monkeypatch.setattr(s, "_download_parquet", fake_download)

    filters = DateFilterDTO(start_year=2022, end_year=2023, package="pkg")
    out = asyncio.run(s.process_reservoir_data(filters))
    assert len(out) == 1
    assert out[0]["url"].endswith("2022.parquet")


def test_process_reservoir_data_defaults_years(monkeypatch: Any) -> None:
    os.environ["ONS_API_URL"] = "https://example.com/api"

    class FakeRepo:
        def __init__(self) -> None:
            self.bucket_name = "b"

        def save(self, file: Any, filename: str) -> str:
            return f"gs://b/{filename}"

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

    async def fake_download_ok(client: Any, info: DownloadInfo) -> str:
        return f"p/{info.year}/ok.parquet"

    monkeypatch.setattr(s, "_download_parquet", fake_download_ok)

    filters = DateFilterDTO(start_year=None, end_year=None, package="pkg")
    out = asyncio.run(s.process_reservoir_data(filters))
    assert len(out) == 1
