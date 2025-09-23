import os
from google.cloud import storage
from repositories.base_repository import FileRepository

class GCSFileRepository(FileRepository):
    def __init__(self):
        self.client = storage.Client()
        self.bucket_name = os.environ["BUCKET_NAME"]
        self.bucket = self.client.bucket(self.bucket_name)

    def upload(self, file, filename: str, content_type: str) -> str:
        blob = self.bucket.blob(filename)
        blob.upload_from_file(file, content_type=content_type)
        blob.make_public()
        return blob.public_url

