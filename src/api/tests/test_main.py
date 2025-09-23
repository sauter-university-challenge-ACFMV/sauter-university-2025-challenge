from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
"""
Testes temporários para validação do pipeline CI.

Estes testes serão substituídos pelos testes reais da API.
"""


def test_read_main() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}
