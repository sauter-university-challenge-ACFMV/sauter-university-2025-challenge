import io
from typing import Any


def test_gcs_repository_env_paths(monkeypatch: Any) -> None:
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
    
    # Patch google.auth.default to return fake credentials
    import google.auth # type: ignore[import-untyped]
    def fake_default(*args, **kwargs): # type: ignore[no-untyped-def]
        return object(), "test-project"
    monkeypatch.setattr(google.auth, "default", fake_default)

    repo = g.GCSFileRepository()

    # upload/save path flow
    url = repo.save(io.BytesIO(b"x"), "path/file.bin")
    assert url.startswith("gs://test-bucket/")


def test_gcs_repository_json_credentials(monkeypatch: Any) -> None:
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
    monkeypatch.setenv("GOOGLE_CREDENTIALS_JSON", '{"type": "service_account", "project_id": "test-project", "client_email": "test@test.com", "token_uri": "https://oauth2.googleapis.com/token", "private_key": "-----BEGIN PRIVATE KEY-----\\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7VJTUt9Us8cKB\\n-----END PRIVATE KEY-----\\n"}')
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)

    monkeypatch.setattr(g, "storage", type("S", (), {"Client": FakeClient}))
    monkeypatch.setattr(g, "service_account", type("SA", (), {"Credentials": FakeCred}))
    
    # Patch google.auth.default to return fake credentials
    import google.auth # type: ignore[import-untyped]
    def fake_default(*args, **kwargs): # type: ignore[no-untyped-def]
        return object(), "test-project"
    monkeypatch.setattr(google.auth, "default", fake_default)

    repo = g.GCSFileRepository()
    url = repo.save(io.BytesIO(b"x"), "a.bin")
    assert url.startswith("gs://test-bucket/")


def test_gcs_repository_file_credentials(monkeypatch: Any, tmp_path: Any) -> None:
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
    cred_path.write_text('{"type": "service_account", "project_id": "test-project", "client_email": "test@test.com", "token_uri": "https://oauth2.googleapis.com/token", "private_key": "-----BEGIN PRIVATE KEY-----\\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7VJTUt9Us8cKB\\n-----END PRIVATE KEY-----\\n"}')

    import repositories.gcs_repository as g

    monkeypatch.setenv("GCS_BUCKET_NAME", "test-bucket")
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", str(cred_path))
    monkeypatch.delenv("GOOGLE_CREDENTIALS_JSON", raising=False)
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)

    monkeypatch.setattr(g, "storage", type("S", (), {"Client": FakeClient}))
    monkeypatch.setattr(g, "service_account", type("SA", (), {"Credentials": FakeCred}))
    
    # Patch google.auth.default to return fake credentials
    import google.auth # type: ignore[import-untyped]
    def fake_default(*args, **kwargs): # type: ignore[no-untyped-def]
        return object(), "test-project"
    monkeypatch.setattr(google.auth, "default", fake_default)

    repo = g.GCSFileRepository()
    url = repo.save(io.BytesIO(b"x"), "b.bin")
    assert url.startswith("gs://test-bucket/")
