import pytest
from fastapi.testclient import TestClient
from typing import Any, Generator


@pytest.fixture(autouse=True)
def mock_gcs_repository(monkeypatch: Any) -> None:
    """Simula o GCSFileRepository para evitar autenticação real durante os testes."""

    class FakeGCSFileRepository:
        def __init__(self) -> None:
            self.bucket_name = "fake-bucket"

        def save(self, file: Any, filename: str) -> str:
            return f"gs://{self.bucket_name}/{filename}"

    import services.ons_service as ons_service_module

    monkeypatch.setattr(ons_service_module, "GCSFileRepository", FakeGCSFileRepository)


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Fornece um TestClient com as dependências já mockadas."""
    from main import app

    with TestClient(app) as test_client:
        yield test_client


def test_read_main(client: TestClient) -> None:
    """
    Testa o endpoint principal usando um cliente com dependências simuladas.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}
