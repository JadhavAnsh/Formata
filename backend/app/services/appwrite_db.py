from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.id import ID
from app.config.settings import settings
from app.utils.logger import logger
from typing import Dict, Any, Optional, List

class AppwriteDBService:
    def __init__(self):
        self.client = Client()
        self.client.set_endpoint(settings.appwrite_endpoint)
        self.client.set_project(settings.appwrite_project_id)
        self.client.set_key(settings.appwrite_api_key)
        self.databases = Databases(self.client)
        self.database_id = settings.appwrite_database_id
        self.collection_id = settings.appwrite_jobs_collection_id

    def create_job_document(self, job_id: str, data: Dict[str, Any]) -> str:
        """Create a new job document in Appwrite database."""
        try:
            result = self.databases.create_document(
                database_id=self.database_id,
                collection_id=self.collection_id,
                document_id=job_id,
                data=data
            )
            return result['$id']
        except Exception as e:
            logger.error(f"Appwrite DB Create Error: {str(e)}")
            raise

    def get_job_document(self, job_id: str) -> Dict[str, Any]:
        """Get a job document from Appwrite database."""
        try:
            return self.databases.get_document(
                database_id=self.database_id,
                collection_id=self.collection_id,
                document_id=job_id
            )
        except Exception as e:
            logger.error(f"Appwrite DB Get Error: {str(e)}")
            raise

    def update_job_document(self, job_id: str, data: Dict[str, Any]) -> bool:
        """Update a job document in Appwrite database."""
        try:
            self.databases.update_document(
                database_id=self.database_id,
                collection_id=self.collection_id,
                document_id=job_id,
                data=data
            )
            return True
        except Exception as e:
            logger.error(f"Appwrite DB Update Error: {str(e)}")
            return False

    def list_user_jobs(self, user_id: str) -> List[Dict[str, Any]]:
        """List all jobs for a specific user."""
        try:
            # Note: Requires an index on user_id in Appwrite
            from appwrite.query import Query
            result = self.databases.list_documents(
                database_id=self.database_id,
                collection_id=self.collection_id,
                queries=[Query.equal("user_id", user_id)]
            )
            return result['documents']
        except Exception as e:
            logger.error(f"Appwrite DB List Error: {str(e)}")
            return []

    def delete_job_document(self, job_id: str) -> bool:
        """Delete a job document from Appwrite database."""
        try:
            self.databases.delete_document(
                database_id=self.database_id,
                collection_id=self.collection_id,
                document_id=job_id
            )
            return True
        except Exception as e:
            logger.error(f"Appwrite DB Delete Error: {str(e)}")
            return False

appwrite_db = AppwriteDBService()
