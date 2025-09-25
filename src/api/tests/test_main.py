# src/api/tests/test_main.py

import pytest
from fastapi.testclient import TestClient
from typing import Any, Generator


# Fixture única para mockar o GCS, aplicada a todos os testes neste arquivo.
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


# Fixture única para fornecer o cliente de teste.
@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Fornece um TestClient com as dependências já mockadas."""
    from main import app

    with TestClient(app) as test_client:
        yield test_client


# --- Testes combinados de ambos os arquivos ---

def test_read_main(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Hello World"
    assert "endpoints" in body  



def test_openapi_and_docs(client: TestClient) -> None:
    """Testa os endpoints de documentação gerados automaticamente pela FastAPI."""
    response = client.get("/openapi.json")
    assert response.status_code == 200

    response = client.get("/docs")
    assert response.status_code == 200
