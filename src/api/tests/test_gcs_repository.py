# src/api/tests/test_gcs_repository.py (CORRIGIDO)

import io
from typing import Any
import pytest
import os

def test_gcs_repository_env_paths(monkeypatch: Any) -> None:
    class FakeClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def bucket(self, name: str) -> Any:
            class B:
                # ADICIONADO: Método para simular a verificação de existência do bucket.
                def exists(self) -> bool:
                    return True

                def blob(self, filename: str) -> Any:
                    class BL:
                        public_url = f"gs://{name}/{filename}"
                        def upload_from_string(self, *_: Any, **__: Any) -> None:
                            return None
                    return BL()
            return B()

    class FakeSA:
        @classmethod
        def from_service_account_info(cls, info: dict[str, Any]) -> Any:
            return object()
        @classmethod
        def from_service_account_file(cls, path: str) -> Any:
            return object()

    import repositories.gcs_repository as g
    monkeypatch.setenv("GCS_BUCKET_NAME", "test-bucket")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "pid")
    monkeypatch.delenv("GOOGLE_CREDENTIALS_JSON", raising=False)
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    monkeypatch.setattr(g, "storage", type("S", (), {"Client": FakeClient}))
    monkeypatch.setattr(
        g, "service_account", type("SA", (), {"Credentials": FakeSA})
    )
    
    import google.auth # type: ignore[import-untyped]
    def fake_default(*args: Any, **kwargs: Any) -> Any:
        return object(), "test-project"
    monkeypatch.setattr(google.auth, "default", fake_default)

    repo = g.GCSFileRepository()
    
    url = repo.save(io.BytesIO(b"x"), "path/file.bin", _bucket_name="test-bucket")
    assert url.startswith("gs://test-bucket/")


def test_gcs_repository_json_credentials(monkeypatch: Any) -> None:
    class FakeClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass
        def bucket(self, name: str) -> Any:
            class B:
                # ADICIONADO: Método para simular a verificação de existência do bucket.
                def exists(self) -> bool:
                    return True
                def blob(self, filename: str) -> Any:
                    class BL:
                        public_url = f"gs://{name}/{filename}"
                        def upload_from_string(self, *_: Any, **__: Any) -> None:
                            return None
                    return BL()
            return B()

    class FakeCred:
        @staticmethod
        def from_service_account_info(info: dict[str, Any]) -> Any:
            return object()

    import repositories.gcs_repository as g
    monkeypatch.setenv("GCS_BUCKET_NAME", "test-bucket")
    monkeypatch.setenv("GOOGLE_CREDENTIALS_JSON", '{"type": "service_account"}')
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    monkeypatch.setattr(g, "storage", type("S", (), {"Client": FakeClient}))
    monkeypatch.setattr(g, "service_account", type("SA", (), {"Credentials": FakeCred}))
    
    import google.auth # type: ignore[import-untyped]
    def fake_default(*args: Any, **kwargs: Any) -> Any:
        return object(), "test-project"
    monkeypatch.setattr(google.auth, "default", fake_default)

    repo = g.GCSFileRepository()
    url = repo.save(io.BytesIO(b"x"), "a.bin", _bucket_name="test-bucket")
    assert url.startswith("gs://test-bucket/")


def test_gcs_repository_file_credentials(monkeypatch: Any, tmp_path: Any) -> None:
    class FakeClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass
        def bucket(self, name: str) -> Any:
            class B:
                # ADICIONADO: Método para simular a verificação de existência do bucket.
                def exists(self) -> bool:
                    return True
                def blob(self, filename: str) -> Any:
                    class BL:
                        public_url = f"gs://{name}/{filename}"
                        def upload_from_string(self, *_: Any, **__: Any) -> None:
                            return None
                    return BL()
            return B()

    class FakeCred:
        @staticmethod
        def from_service_account_file(path: str) -> Any:
            return object()

    cred_path = tmp_path / "sa.json"
    cred_path.write_text('{"type": "service_account"}')

    import repositories.gcs_repository as g
    monkeypatch.setenv("GCS_BUCKET_NAME", "test-bucket")
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", str(cred_path))
    monkeypatch.delenv("GOOGLE_CREDENTIALS_JSON", raising=False)
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    monkeypatch.setattr(g, "storage", type("S", (), {"Client": FakeClient}))
    monkeypatch.setattr(g, "service_account", type("SA", (), {"Credentials": FakeCred}))
    
    import google.auth # type: ignore[import-untyped]
    def fake_default(*args: Any, **kwargs: Any) -> Any:
        return object(), "test-project"
    monkeypatch.setattr(google.auth, "default", fake_default)

    repo = g.GCSFileRepository()
    url = repo.save(io.BytesIO(b"x"), "b.bin", _bucket_name="test-bucket")
    assert url.startswith("gs://test-bucket/")