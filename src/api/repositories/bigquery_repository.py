import os
import json
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple
from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError
from google.oauth2 import service_account  # type: ignore[import-untyped]
from utils.logger import LogLevel, log
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))


class BigQueryRepository(ABC):
    @abstractmethod
    def execute_paginated_query(
        self, query: str, count_query: str, page: int, page_size: int
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Executa query paginada no BigQuery"""
        raise NotImplementedError


class GCPBigQueryRepository(BigQueryRepository):
    def __init__(self) -> None:
        self.project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
        self.location = os.environ.get("BIGQUERY_LOCATION", "southamerica-east1")
        log(
            f"GCPBigQueryRepository init - project={self.project_id}, location={self.location}",
            LogLevel.DEBUG,
        )
        self._client: bigquery.Client | None = None  # lazy init

    @property
    def client(self) -> bigquery.Client:
        if self._client is None:
            self._client = self._create_bigquery_client()
        return self._client

    @client.setter
    def client(self, value: bigquery.Client) -> None:  # 👈 setter só pra testes
        self._client = value

    
    

    def _create_bigquery_client(self) -> bigquery.Client:
        log("Creating BigQuery client", LogLevel.DEBUG)

        credentials_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
        if credentials_json:
            try:
                credentials_info = json.loads(credentials_json.strip())
                credentials = service_account.Credentials.from_service_account_info(credentials_info)
                log("Successfully created BigQuery client with JSON credentials", LogLevel.INFO)
                return bigquery.Client(
                    credentials=credentials,
                    project=self.project_id or credentials_info.get("project_id"),
                    location=self.location,
                )
            except Exception as e:
                log(f"Could not create credentials from JSON: {e}", LogLevel.ERROR)

        credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if credentials_path and os.path.exists(credentials_path):
            try:
                credentials = service_account.Credentials.from_service_account_file(credentials_path)
                log("Successfully created BigQuery client with service account file", LogLevel.INFO)
                return bigquery.Client(
                    credentials=credentials,
                    project=self.project_id or credentials.project_id,
                    location=self.location,
                )
            except Exception as e:
                log(f"Could not create credentials from file: {e}", LogLevel.ERROR)

        try:
            client = bigquery.Client(project=self.project_id, location=self.location)
            log("Successfully created BigQuery client with default credentials", LogLevel.INFO)
            return client
        except Exception as e:
            log(f"All authentication methods failed: {e}", LogLevel.ERROR)
            raise Exception(f"Could not authenticate with BigQuery: {e}")

    def execute_paginated_query(
        self, query: str, count_query: str, page: int, page_size: int
    ) -> Tuple[List[Dict[str, Any]], int]:
        try:
            log(
                f"Executing count query (project={self.project_id} | location={self.location}): {count_query}",
                LogLevel.DEBUG,
            )
            count_job = self.client.query(count_query)  # 🔑 usa o property → cria só se precisar
            count_result = list(count_job.result())
            total_records = count_result[0]["total"] if count_result else 0

            offset = (page - 1) * page_size
            paginated_query = f"{query} LIMIT {page_size} OFFSET {offset}"

            log(f"Executing paginated query - Page: {page}, Size: {page_size}", LogLevel.DEBUG)
            log(f"Running query: {paginated_query}", LogLevel.DEBUG)

            query_job = self.client.query(paginated_query)
            results = query_job.result()
            data = [dict(row) for row in results]

            log(f"Query executed successfully: {len(data)} rows of {total_records} total", LogLevel.INFO)
            return data, total_records

        except GoogleCloudError as e:
            log(f"BigQuery error: {e}", LogLevel.ERROR)
            raise
        except Exception as e:
            log(f"Unexpected error in paginated query: {e}", LogLevel.ERROR)
            raise
