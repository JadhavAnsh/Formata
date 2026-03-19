from appwrite.client import Client
from appwrite.services.storage import Storage
from appwrite.input_file import InputFile
from app.config.settings import settings
from app.utils.logger import logger
import os

class AppwriteStorageService:
    def __init__(self):
        self.client = Client()
        self.client.set_endpoint(settings.appwrite_endpoint)
        self.client.set_project(settings.appwrite_project_id)
        self.client.set_key(settings.appwrite_api_key)
        self.storage = Storage(self.client)
        self.bucket_id = settings.appwrite_storage_bucket_id

    def upload_file(self, file_path: str, file_id: str = None) -> str:
        """Upload a local file to Appwrite storage."""
        try:
            if not file_id:
                import uuid
                file_id = str(uuid.uuid4())
            
            result = self.storage.create_file(
                bucket_id=self.bucket_id,
                file_id=file_id,
                file=InputFile.from_path(file_path)
            )
            return result['$id']
        except Exception as e:
            logger.error(f"Appwrite Storage Upload Error: {str(e)}")
            raise

    def download_file(self, file_id: str, local_path: str):
        """Download a file from Appwrite storage to a local path."""
        try:
            result = self.storage.get_file_download(
                bucket_id=self.bucket_id,
                file_id=file_id
            )
            with open(local_path, "wb") as f:
                f.write(result)
            return local_path
        except Exception as e:
            logger.error(f"Appwrite Storage Download Error: {str(e)}")
            raise

    def delete_file(self, file_id: str):
        """Delete a file from Appwrite storage."""
        try:
            self.storage.delete_file(
                bucket_id=self.bucket_id,
                file_id=file_id
            )
        except Exception as e:
            logger.error(f"Appwrite Storage Delete Error: {str(e)}")

appwrite_storage = AppwriteStorageService()
