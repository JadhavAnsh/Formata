import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.services.appwrite_storage import AppwriteStorageService
from app.services.appwrite_db import AppwriteDBService

class TestAppwriteIntegration(unittest.TestCase):
    @patch('app.services.appwrite_storage.Storage')
    @patch('app.services.appwrite_storage.Client')
    def test_storage_upload(self, mock_client, mock_storage):
        service = AppwriteStorageService()
        mock_storage_instance = mock_storage.return_value
        mock_storage_instance.create_file.return_value = {'$id': 'test_file_id'}
        
        # Create a dummy file
        with open("test_upload.txt", "w") as f:
            f.write("test content")
        
        file_id = service.upload_file("test_upload.txt", "test_file_id")
        
        self.assertEqual(file_id, 'test_file_id')
        mock_storage_instance.create_file.assert_called_once()
        
        # Cleanup
        os.remove("test_upload.txt")

    @patch('app.services.appwrite_db.Databases')
    @patch('app.services.appwrite_db.Client')
    def test_db_create_job(self, mock_client, mock_db):
        service = AppwriteDBService()
        mock_db_instance = mock_db.return_value
        mock_db_instance.create_document.return_value = {'$id': 'test_job_id'}
        
        job_data = {"user_id": "user123", "status": "pending"}
        job_id = service.create_job_document("test_job_id", job_data)
        
        self.assertEqual(job_id, 'test_job_id')
        mock_db_instance.create_document.assert_called_once()

if __name__ == '__main__':
    unittest.main()
