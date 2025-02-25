import unittest
import os
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models import Task, User, get_db, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.message_service.gmail_service import GmailService
from app.api.routes.tasks import router
from fastapi.testclient import TestClient
from fastapi import FastAPI
import datetime

class TestTaskRoutes(unittest.TestCase):
    def setUp(self):
        # Create test database
        self.engine = create_engine("sqlite:///test.db")
        Base.metadata.create_all(self.engine)
        self.TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db = self.TestingSessionLocal()
        
        # Override get_db dependency
        def override_get_db():
            try:
                yield self.db
            finally:
                self.db.close()
                
        self.app = FastAPI()
        self.app.include_router(router)
        self.app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(self.app)
        
    def tearDown(self):
        # Clean up test database
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)
    
    def test_get_tasks(self):
        test_user = User(id=1, email="test@test.com")
        self.db.add(test_user)
        self.db.commit()    

        response = self.client.get("/tasks", headers={"user-id": "1"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

    def test_get_tasks_invalid_user(self):
        response = self.client.get("/tasks", headers={"user-id": "2"})
        self.assertEqual(response.status_code, 404)

    def test_get_tasks_no_user_id(self):
        response = self.client.get("/tasks")
        self.assertEqual(response.status_code, 422)

    def test_update_task(self):
        task = Task(title="Test Task", description="Test Description", due_date=datetime.date(2025, 1, 1))
        task.user_id = 1
        self.db.add(task)
        self.db.commit()

        response = self.client.put("/tasks/1", json={"title": "Updated Task", "description": "Updated Description", "due_date": "2025-01-02"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['title'], "Updated Task")
        self.assertEqual(response.json()['description'], "Updated Description")
        self.assertEqual(response.json()['due_date'], "2025-01-02") 
    
    def test_update_task_invalid_task(self):
        response = self.client.put("/tasks/2", json={"title": "Updated Task", "description": "Updated Description", "due_date": "2025-01-02"})
        self.assertEqual(response.status_code, 404)

