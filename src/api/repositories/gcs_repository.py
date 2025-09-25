import os
import json
from typing import IO, Tuple
from google.cloud import storage, bigquery  # type: ignore[import-untyped]
from google.oauth2 import service_account  # type: ignore[import-untyped]
from google.api_core.exceptions import NotFound  # type: ignore[import-untyped]
from repositories.base_repository import FileRepository
from utils.logger import LogLevel, log
from dotenv import load_dotenv


load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))


class GCSFileRepository(FileRepository):
    def __init__(self) -> None:
        self.client, self.bq_client = self._create_storage_client()
        self.bucket_name = os.environ.get("GCS_BUCKET_NAME", "default-bucket")
        self.bucket = self.client.bucket(self.bucket_name)

    def _create_storage_client(self) -> Tuple[storage.Client, bigquery.Client]:
        """Create Google Cloud Storage and BigQuery clients with proper authentication"""

        log("Checking environment variables for GCS authentication", LogLevel.DEBUG)
        log(
            f"GOOGLE_CREDENTIALS_JSON exists: {'GOOGLE_CREDENTIALS_JSON' in os.environ}",
            LogLevel.DEBUG,
        )
        log(
            f"GOOGLE_APPLICATION_CREDENTIALS exists: {'GOOGLE_APPLICATION_CREDENTIALS' in os.environ}",
            LogLevel.DEBUG,
        )
        log(
            f"GOOGLE_CLOUD_PROJECT exists: {'GOOGLE_CLOUD_PROJECT' in os.environ}",
            LogLevel.DEBUG,
        )

        credentials_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
        if credentials_json:
            log(
                "Found GOOGLE_CREDENTIALS_JSON, attempting to parse JSON credentials",
                LogLevel.DEBUG,
            )
            try:
                credentials_json = credentials_json.strip()
                credentials_info = json.loads(credentials_json)
                credentials = service_account.Credentials.from_service_account_info(
                    credentials_info
                )
                log(
                    "Successfully created GCS and BigQuery clients with JSON credentials",
                    LogLevel.INFO,
                )
                storage_client = storage.Client(credentials=credentials)
                bq_client = bigquery.Client(
                    credentials=credentials, 
                    project="sauter-university-challenger"
                )
                return storage_client, bq_client
            except json.JSONDecodeError as e:
                log(f"GOOGLE_CREDENTIALS_JSON is not valid JSON: {e}", LogLevel.ERROR)
            except Exception as e:
                log(f"Could not create credentials from JSON: {e}", LogLevel.ERROR)

        credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if credentials_path:
            log(
                f"Found GOOGLE_APPLICATION_CREDENTIALS: {credentials_path}",
                LogLevel.DEBUG,
            )
            if os.path.exists(credentials_path):
                try:
                    credentials = service_account.Credentials.from_service_account_file(
                        credentials_path
                    )
                    log(
                        "Successfully created GCS and BigQuery clients with service account file",
                        LogLevel.INFO,
                    )
                    storage_client = storage.Client(credentials=credentials)
                    bq_client = bigquery.Client(
                        credentials=credentials, 
                        project="sauter-university-challenger"
                    )
                    return storage_client, bq_client
                except Exception as e:
                    log(f"Could not create credentials from file: {e}", LogLevel.ERROR)
            else:
                log(
                    f"Credentials file does not exist: {credentials_path}",
                    LogLevel.ERROR,
                )

        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "sauter-university-challenger")
        log(f"Using project ID: {project_id}", LogLevel.DEBUG)
        try:
            storage_client = storage.Client(project=project_id)
            bq_client = bigquery.Client(project=project_id)
            log("Successfully created clients with project ID", LogLevel.INFO)
            return storage_client, bq_client
        except Exception as e:
            log(f"Could not create clients with project ID: {e}", LogLevel.ERROR)

        log("Trying default credentials as last resort", LogLevel.DEBUG)
        try:
            storage_client = storage.Client()
            bq_client = bigquery.Client(project="sauter-university-challenger")
            log(
                "Successfully created clients with default credentials",
                LogLevel.INFO,
            )
            return storage_client, bq_client
        except Exception as e:
            log(
                f"All authentication methods failed. Original error: {e}",
                LogLevel.ERROR,
            )
            raise Exception(
                f"Could not authenticate with Google Cloud Storage. "
                f"Please ensure one of the following environment variables is set:\n"
                f"- GOOGLE_CREDENTIALS_JSON: JSON string with service account credentials\n"
                f"- GOOGLE_APPLICATION_CREDENTIALS: Path to service account key file\n"
                f"- GOOGLE_CLOUD_PROJECT: Your GCP project ID\n"
                f"Original error: {e}"
            )

    def upload(self, file: IO[bytes], filename: str, content_type: str) -> str:
        blob = self.bucket.blob(filename)
        blob.upload_from_string(file.read(), content_type=content_type)
        return blob.public_url

    def save(self, file: IO[bytes], filename: str) -> str:
        return self.upload(file, filename, "application/octet-stream")

    def _table_exists(self, dataset_id: str, table_id: str) -> bool:
        """Check if a BigQuery table exists"""
        try:
            table_ref = self.bq_client.dataset(dataset_id).table(table_id)
            self.bq_client.get_table(table_ref)
            log(f"Table {dataset_id}.{table_id} exists", LogLevel.DEBUG)
            return True
        except NotFound:
            log(f"Table {dataset_id}.{table_id} does not exist", LogLevel.DEBUG)
            return False
        except Exception as e:
            log(f"Error checking if table exists: {e}", LogLevel.ERROR)
            return False

    def raw_table_has_value(self, package_name: str, column_name: str, last_day: str) -> bool:
        """Check if a value exists in the raw table. Returns False if table doesn't exist."""
        table_id = f"raw_{package_name}"
        dataset_id = "bronze"
        
        # First check if the table exists
        if not self._table_exists(dataset_id, table_id):
            log(f"Table {dataset_id}.{table_id} doesn't exist, returning False", LogLevel.INFO)
            return False
        
        # Table exists, now check for the value
        try:
            query = f"""
                SELECT 1
                FROM `sauter-university-challenger.{dataset_id}.{table_id}`
                WHERE {column_name} = @last_day
                LIMIT 1
            """

            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("last_day", "STRING", last_day)
                ]
            )

            log(f"Querying table {dataset_id}.{table_id} for value {last_day} in column {column_name}", LogLevel.DEBUG)
            results = self.bq_client.query(query, job_config=job_config).result()
            has_value = results.total_rows > 0
            
            if has_value:
                log(f"Found value {last_day} in table {dataset_id}.{table_id}", LogLevel.INFO)
            else:
                log(f"Value {last_day} not found in table {dataset_id}.{table_id}", LogLevel.INFO)
                
            return has_value
            
        except Exception as e:
            log(f"Error querying table {dataset_id}.{table_id}: {e}", LogLevel.ERROR)
            return False