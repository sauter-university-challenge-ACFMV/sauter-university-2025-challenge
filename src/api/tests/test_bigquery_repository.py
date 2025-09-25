import pytest
from unittest.mock import MagicMock, patch
from google.cloud.exceptions import GoogleCloudError
from repositories.bigquery_repository import GCPBigQueryRepository


@pytest.fixture
def mock_client() -> MagicMock:
    """Cria um mock do client BigQuery"""
    client = MagicMock()
    return client


def test_execute_paginated_query_success(mock_client: MagicMock) -> None:
    repo = GCPBigQueryRepository()
    repo.client = mock_client

    query = "SELECT * FROM tabela"
    count_query = "SELECT COUNT(*) as total FROM tabela"

    def fake_query(sql: str) -> MagicMock:  # 👈 também tipado
        mock = MagicMock()
        if "COUNT" in sql:
            mock.result.return_value = [{"total": 5}]
        else:
            mock.result.return_value = [
                {"id": 1, "name": "teste"},
                {"id": 2, "name": "outro"},
            ]
        return mock

    mock_client.query.side_effect = fake_query

    data, total = repo.execute_paginated_query(query, count_query, page=1, page_size=2)

    assert total == 5
    assert len(data) == 2
    assert data[0]["id"] == 1
    mock_client.query.assert_any_call(count_query)
    mock_client.query.assert_any_call(query + " LIMIT 2 OFFSET 0")


def test_execute_paginated_query_empty_result(mock_client: MagicMock) -> None:
    repo = GCPBigQueryRepository()
    repo.client = mock_client

    # Count vazio
    mock_client.query.return_value.result.return_value = []

    query = "SELECT * FROM tabela"
    count_query = "SELECT COUNT(*) as total FROM tabela"

    data, total = repo.execute_paginated_query(query, count_query, page=1, page_size=10)

    assert total == 0
    assert data == []


def test_execute_paginated_query_raises_google_error(mock_client: MagicMock) -> None:
    repo = GCPBigQueryRepository()
    repo.client = mock_client

    # Simula erro do BigQuery
    mock_client.query.side_effect = GoogleCloudError("erro no bigquery")

    query = "SELECT * FROM tabela"
    count_query = "SELECT COUNT(*) as total FROM tabela"

    with pytest.raises(GoogleCloudError):
        repo.execute_paginated_query(query, count_query, page=1, page_size=10)


def test_create_bigquery_client_with_json_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_credentials = '{"type": "service_account", "project_id": "fake-project"}'

    monkeypatch.setenv("GOOGLE_CREDENTIALS_JSON", fake_credentials)
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "fake-project")

    with patch("repositories.bigquery_repository.bigquery.Client") as mock_client:
        repo = GCPBigQueryRepository()
        assert repo.client == mock_client.return_value
        mock_client.assert_called()
