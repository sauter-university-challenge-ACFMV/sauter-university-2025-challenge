import os
import json
from google.cloud import storage
from google.oauth2 import service_account
from repositories.base_repository import FileRepository
from utils.logger import LogLevels, log

class GCSFileRepository(FileRepository):
    def __init__(self):
        # Initialize client with proper authentication
        self.client = self._create_storage_client()
        self.bucket_name = os.environ.get("GCS_BUCKET_NAME", "default-bucket")
        self.bucket = self.client.bucket(self.bucket_name)
    
    def _create_storage_client(self):
        """Create Google Cloud Storage client with proper authentication"""
        
        # Debug: Check available environment variables
        log("Checking environment variables for GCS authentication", LogLevels.DEBUG)
        log(f"GOOGLE_CREDENTIALS_JSON exists: {'GOOGLE_CREDENTIALS_JSON' in os.environ}", LogLevels.DEBUG)
        log(f"GOOGLE_APPLICATION_CREDENTIALS exists: {'GOOGLE_APPLICATION_CREDENTIALS' in os.environ}", LogLevels.DEBUG)
        log(f"GOOGLE_CLOUD_PROJECT exists: {'GOOGLE_CLOUD_PROJECT' in os.environ}", LogLevels.DEBUG)
        
        # Method 1: Try JSON credentials from environment variable
        credentials_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
        if credentials_json:
            log("Found GOOGLE_CREDENTIALS_JSON, attempting to parse JSON credentials", LogLevels.DEBUG)
            try:
                # Remove any extra whitespace and newlines
                credentials_json = credentials_json.strip()
                credentials_info = json.loads(credentials_json)
                credentials = service_account.Credentials.from_service_account_info(credentials_info)
                log("Successfully created GCS client with JSON credentials", LogLevels.INFO)
                return storage.Client(credentials=credentials)
            except json.JSONDecodeError as e:
                log(f"GOOGLE_CREDENTIALS_JSON is not valid JSON: {e}", LogLevels.ERROR)
            except Exception as e:
                log(f"Could not create credentials from JSON: {e}", LogLevels.ERROR)
        
        # Method 2: Try service account key file path
        credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if credentials_path:
            log(f"Found GOOGLE_APPLICATION_CREDENTIALS: {credentials_path}", LogLevels.DEBUG)
            if os.path.exists(credentials_path):
                try:
                    credentials = service_account.Credentials.from_service_account_file(credentials_path)
                    log("Successfully created GCS client with service account file", LogLevels.INFO)
                    return storage.Client(credentials=credentials)
                except Exception as e:
                    log(f"Could not create credentials from file: {e}", LogLevels.ERROR)
            else:
                log(f"Credentials file does not exist: {credentials_path}", LogLevels.ERROR)
        
        # Method 3: Try using project ID with default credentials
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
        if project_id:
            log(f"Found GOOGLE_CLOUD_PROJECT: {project_id}", LogLevels.DEBUG)
            try:
                client = storage.Client(project=project_id)
                log("Successfully created GCS client with project ID", LogLevels.INFO)
                return client
            except Exception as e:
                log(f"Could not create client with project ID: {e}", LogLevels.ERROR)
        
        # Method 4: Last resort - try default credentials (works in GCP environments)
        log("Trying default credentials as last resort", LogLevels.DEBUG)
        try:
            client = storage.Client()
            log("Successfully created GCS client with default credentials", LogLevels.INFO)
            return client
        except Exception as e:
            log(f"All authentication methods failed. Original error: {e}", LogLevels.ERROR)
            raise Exception(
                f"Could not authenticate with Google Cloud Storage. "
                f"Please ensure one of the following environment variables is set:\n"
                f"- GOOGLE_CREDENTIALS_JSON: JSON string with service account credentials\n"
                f"- GOOGLE_APPLICATION_CREDENTIALS: Path to service account key file\n"
                f"- GOOGLE_CLOUD_PROJECT: Your GCP project ID\n"
                f"Original error: {e}"
            )

    def upload(self, file, filename: str, content_type: str) -> str:
        blob = self.bucket.blob(filename)
        blob.upload_from_file(file, content_type=content_type)
        # blob.make_public()
        return blob.public_url

    def save(self, file, filename: str) -> str:
        return self.upload(file, filename, "application/octet-stream")