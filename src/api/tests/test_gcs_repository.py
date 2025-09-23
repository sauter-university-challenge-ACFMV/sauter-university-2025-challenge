import os
from typing import Any


def test_gcs_repository_env_paths(monkeypatch) -> None:
    # Avoid hitting real GCS by monkeypatching storage and service_account
    class FakeClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def bucket(self, name: str):  # type: ignore[no-untyped-def]
            class B:
                def blob(self, filename: str):  # type: ignore[no-untyped-def]
                    class BL:
                        public_url = f"gs://{name}/{filename}"

                        def upload_from_string(self, *_: Any, **__: Any) -> None:
                            return None

                    return BL()

            return B()

    class FakeSA:
        @classmethod
        def from_service_account_info(cls, info: dict[str, Any]):  # type: ignore[no-untyped-def]
            return object()

        @classmethod
        def from_service_account_file(cls, path: str):  # type: ignore[no-untyped-def]
            return object()

    import repositories.gcs_repository as g

    monkeypatch.setenv("GCS_BUCKET_NAME", "test-bucket")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "pid")
    monkeypatch.delenv("GOOGLE_CREDENTIALS_JSON", raising=False)
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)

    monkeypatch.setattr(g, "storage", type("S", (), {"Client": FakeClient}))
    monkeypatch.setattr(
        g,
        "service_account",
        type(
            "SA",
            (),
            {
                "Credentials": type(
                    "C",
                    (),
                    {
                        "from_service_account_info": staticmethod(
                            FakeSA.from_service_account_info
                        ),
                        "from_service_account_file": staticmethod(
                            FakeSA.from_service_account_file
                        ),
                    },
                )
            },
        ),
    )

    repo = g.GCSFileRepository()

    # upload/save path flow
    class F:
        def __init__(self) -> None:
            self._b = b"x"

        def read(self) -> bytes:
            return self._b

    url = repo.save(F(), "path/file.bin")
    assert url.startswith("gs://test-bucket/")


def test_gcs_repository_json_credentials(monkeypatch) -> None:
    class FakeClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def bucket(self, name: str):  # type: ignore[no-untyped-def]
            class B:
                def blob(self, filename: str):  # type: ignore[no-untyped-def]
                    class BL:
                        public_url = f"gs://{name}/{filename}"

                        def upload_from_string(self, *_: Any, **__: Any) -> None:
                            return None

                    return BL()

            return B()

    class FakeCred:
        @staticmethod
        def from_service_account_info(info: dict[str, Any]):  # type: ignore[no-untyped-def]
            return object()

    import repositories.gcs_repository as g

    monkeypatch.setenv("GCS_BUCKET_NAME", "test-bucket")
    monkeypatch.setenv("GOOGLE_CREDENTIALS_JSON", '{"type": "service_account"}')
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)

    monkeypatch.setattr(g, "storage", type("S", (), {"Client": FakeClient}))
    monkeypatch.setattr(g, "service_account", type("SA", (), {"Credentials": FakeCred}))

    repo = g.GCSFileRepository()
    url = repo.save(type("F", (), {"read": lambda self: b"x"})(), "a.bin")
    assert url.startswith("gs://test-bucket/")


def test_gcs_repository_file_credentials(monkeypatch, tmp_path) -> None:
    class FakeClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def bucket(self, name: str):  # type: ignore[no-untyped-def]
            class B:
                def blob(self, filename: str):  # type: ignore[no-untyped-def]
                    class BL:
                        public_url = f"gs://{name}/{filename}"

                        def upload_from_string(self, *_: Any, **__: Any) -> None:
                            return None

                    return BL()

            return B()

    class FakeCred:
        @staticmethod
        def from_service_account_file(path: str):  # type: ignore[no-untyped-def]
            return object()

    cred_path = tmp_path / "sa.json"
    cred_path.write_text("{}")

    import repositories.gcs_repository as g

    monkeypatch.setenv("GCS_BUCKET_NAME", "test-bucket")
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", str(cred_path))
    monkeypatch.delenv("GOOGLE_CREDENTIALS_JSON", raising=False)
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)

    monkeypatch.setattr(g, "storage", type("S", (), {"Client": FakeClient}))
    monkeypatch.setattr(g, "service_account", type("SA", (), {"Credentials": FakeCred}))

    repo = g.GCSFileRepository()
    url = repo.save(type("F", (), {"read": lambda self: b"x"})(), "b.bin")
    assert url.startswith("gs://test-bucket/")
