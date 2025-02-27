import unittest
from unittest.mock import patch, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import User
from app.api.routes.auth import router as login_router

class TestLoginRoutes(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(login_router)
        self.client = TestClient(self.app)
        
        # Create a serializable mock user - use a regular object instead of MagicMock
        class SerializableUser:
            def __init__(self):
                self.id = 1
                self.email = "test@example.com"
                self.password = "test_password"
        
        self.mock_user = SerializableUser()
        
        # Set up mock db 
        self.mock_db = MagicMock(spec=Session)
        
        # Set up query chain
        filter_result = MagicMock()
        filter_result.first.return_value = self.mock_user
        
        query_result = MagicMock()
        query_result.filter.return_value = filter_result
        
        self.mock_db.query.return_value = query_result
        
        # Override the dependency
        from app.models import get_db
        self.app.dependency_overrides[get_db] = lambda: self.mock_db

    def test_login_success(self):
        response = self.client.post("/login", json={
            "email": "test@example.com",
            "password": "test_password"
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('message', response.json())
        self.assertEqual(response.json()['message'], "Successfully logged in")

    def test_login_invalid_credentials(self):
        # Change mock to return None for this test
        filter_result = MagicMock()
        filter_result.first.return_value = None
        
        query_result = MagicMock()
        query_result.filter.return_value = filter_result
        
        self.mock_db.query.return_value = query_result
        
        response = self.client.post("/login", json={
            "email": "test@example.com", 
            "password": "wrong_password"
        })

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['detail'], "Invalid credentials")
            
            
