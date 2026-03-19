import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from app.guards.appwrite_auth import verify_appwrite_session
from app.jobs.store import JobStore

@pytest.mark.asyncio
async def test_verify_appwrite_session_valid():
    # Mock Appwrite Account and Client
    mock_user = {"$id": "user_123", "name": "Test User"}
    
    with patch("app.guards.appwrite_auth.Client") as MockClient:
        with patch("app.guards.appwrite_auth.Account") as MockAccount:
            mock_account_instance = MockAccount.return_value
            mock_account_instance.get.return_value = mock_user
            
            # Call guard
            user = await verify_appwrite_session(x_appwrite_jwt="valid_jwt")
            
            assert user["$id"] == "user_123"
            assert user["name"] == "Test User"

@pytest.mark.asyncio
async def test_verify_appwrite_session_invalid():
    with patch("app.guards.appwrite_auth.Client") as MockClient:
        with patch("app.guards.appwrite_auth.Account") as MockAccount:
            mock_account_instance = MockAccount.return_value
            mock_account_instance.get.side_effect = Exception("Invalid JWT")
            
            with pytest.raises(HTTPException) as excinfo:
                await verify_appwrite_session(x_appwrite_jwt="invalid_jwt")
            
            assert excinfo.value.status_code == 401

def test_job_store_multi_tenancy():
    store = JobStore()
    
    # Create jobs for different users
    job1_id = store.create_job("file1.csv", "/path/1", user_id="user_A")
    job2_id = store.create_job("file2.csv", "/path/2", user_id="user_B")
    job3_id = store.create_job("file3.csv", "/path/3", user_id="user_A")
    
    # Check filtering
    user_a_jobs = store.get_jobs_by_user("user_A")
    user_b_jobs = store.get_jobs_by_user("user_B")
    
    assert len(user_a_jobs) == 2
    assert len(user_b_jobs) == 1
    
    # Check to_dict contains user_id
    assert user_a_jobs[0]["user_id"] == "user_A"
