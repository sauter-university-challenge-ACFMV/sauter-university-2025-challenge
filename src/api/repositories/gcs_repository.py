import os
import json
from typing import IO
from google.cloud import storage  # type: ignore[import-not-found]
from google.oauth2 import service_account  # type: ignore[import-not-found]
from repositories.base_repository import FileRepository
from utils.logger import LogLevel, log
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

class GCSFileRepository(FileRepository):
    def __init__(self) -> None:
        self.client = self._create_storage_client()
        self.bucket_name = os.environ.get("GCS_BUCKET_NAME", "default-bucket")
        self.bucket = self.client.bucket(self.bucket_name)
    
    def _create_storage_client(self) -> storage.Client:  # type: ignore[name-defined]
        """Create Google Cloud Storage client with proper authentication"""
        
        log("Checking environment variables for GCS authentication", LogLevel.DEBUG)
        log(f"GOOGLE_CREDENTIALS_JSON exists: {'GOOGLE_CREDENTIALS_JSON' in os.environ}", LogLevel.DEBUG)
        log(f"GOOGLE_APPLICATION_CREDENTIALS exists: {'GOOGLE_APPLICATION_CREDENTIALS' in os.environ}", LogLevel.DEBUG)
        log(f"GOOGLE_CLOUD_PROJECT exists: {'GOOGLE_CLOUD_PROJECT' in os.environ}", LogLevel.DEBUG)
        
        credentials_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
        if credentials_json:
            log("Found GOOGLE_CREDENTIALS_JSON, attempting to parse JSON credentials", LogLevel.DEBUG)
            try:
                credentials_json = credentials_json.strip()
                credentials_info = json.loads(credentials_json)
                credentials = service_account.Credentials.from_service_account_info(credentials_info)
                log("Successfully created GCS client with JSON credentials", LogLevel.INFO)
                return storage.Client(credentials=credentials)
            except json.JSONDecodeError as e:
                log(f"GOOGLE_CREDENTIALS_JSON is not valid JSON: {e}", LogLevel.ERROR)
            except Exception as e:
                log(f"Could not create credentials from JSON: {e}", LogLevel.ERROR)
        
        credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if credentials_path:
            log(f"Found GOOGLE_APPLICATION_CREDENTIALS: {credentials_path}", LogLevel.DEBUG)
            if os.path.exists(credentials_path):
                try:
                    credentials = service_account.Credentials.from_service_account_file(credentials_path)
                    log("Successfully created GCS client with service account file", LogLevel.INFO)
                    return storage.Client(credentials=credentials)
                except Exception as e:
                    log(f"Could not create credentials from file: {e}", LogLevel.ERROR)
            else:
                log(f"Credentials file does not exist: {credentials_path}", LogLevel.ERROR)
        
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
        if project_id:
            log(f"Found GOOGLE_CLOUD_PROJECT: {project_id}", LogLevel.DEBUG)
            try:
                client = storage.Client(project=project_id)
                log("Successfully created GCS client with project ID", LogLevel.INFO)
                return client
            except Exception as e:
                log(f"Could not create client with project ID: {e}", LogLevel.ERROR)
        
        log("Trying default credentials as last resort", LogLevel.DEBUG)
        try:
            client = storage.Client()
            log("Successfully created GCS client with default credentials", LogLevel.INFO)
            return client
        except Exception as e:
            log(f"All authentication methods failed. Original error: {e}", LogLevel.ERROR)
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
        # blob.upload_from_file(file, content_type=content_type)
        # blob.make_public()
        return blob.public_url

    def save(self, file: IO[bytes], filename: str) -> str:
        return self.upload(file, filename, "application/octet-stream")