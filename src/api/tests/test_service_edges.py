import os
import asyncio
import httpx
from typing import Any

from services.ons_service import OnsService, DownloadInfo
from models.ons_dto import DateFilterDTO


def test_build_gcs_path_future_year(monkeypatch) -> None:
    class FakeRepo:
        def __init__(self) -> None:
            self.bucket_name = "b"

        def save(self, file: Any, filename: str) -> str:
            return f"gs://b/{filename}"

    import services.ons_service as mod

    monkeypatch.setattr(mod, "GCSFileRepository", FakeRepo, raising=True)

    s = OnsService()
    p = s._build_gcs_path("file_9999.csv", resource_year=9999, package_name="pkg")
    # future year goes to dated partition
    assert p.startswith("pkg/") and p.endswith(".parquet")


def test_read_to_dataframe_unsupported(monkeypatch) -> None:
    class FakeRepo:
        def __init__(self) -> None:
            self.bucket_name = "b"

        def save(self, file: Any, filename: str) -> str:
            return "gs://b/x"

    import services.ons_service as mod

    monkeypatch.setattr(mod, "GCSFileRepository", FakeRepo, raising=True)

    s = OnsService()
    try:
        s._read_to_dataframe(b"x", "unknown")
        assert False, "should raise"
    except ValueError:
        assert True


def test_download_parquet_handles_read_error(monkeypatch) -> None:
    class FakeRepo:
        def __init__(self) -> None:
            self.bucket_name = "b"

        def save(self, file: Any, filename: str) -> str:
            return "gs://b/x"

    import services.ons_service as mod

    monkeypatch.setattr(mod, "GCSFileRepository", FakeRepo, raising=True)

    s = OnsService()

    async def fake_get(url: str, *args: Any, **kwargs: Any):  # type: ignore[no-untyped-def]
        class R:
            content = b"data"

            def raise_for_status(self) -> None:
                return None

        return R()

    async def fake_read(*args: Any, **kwargs: Any):  # type: ignore[no-untyped-def]
        raise ValueError("bad")

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get, raising=True)
    monkeypatch.setattr(
        OnsService,
        "_read_to_dataframe",
        lambda *a, **k: (_ for _ in ()).throw(ValueError("x")),
    )

    info = DownloadInfo(
        url="http://u/f.parquet", year=2023, package="p", data_type="parquet"
    )
    out = asyncio.run(s._download_parquet(httpx.AsyncClient(), info))
    assert out == ""


def test_process_reservoir_data_missing_env(monkeypatch) -> None:
    if "ONS_API_URL" in os.environ:
        del os.environ["ONS_API_URL"]

    class FakeRepo:
        def __init__(self) -> None:
            self.bucket_name = "b"

        def save(self, file: Any, filename: str) -> str:
            return "gs://b/x"

    import services.ons_service as mod

    monkeypatch.setattr(mod, "GCSFileRepository", FakeRepo, raising=True)

    s = OnsService()
    df = DateFilterDTO(start_year=2020, end_year=2020, package="p", data_type="parquet")
    try:
        asyncio.run(s.process_reservoir_data(df))
        assert False, "should raise"
    except ValueError:
        assert True
