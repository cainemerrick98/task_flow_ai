import unittest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
from app.models import Base, User, Task, GmailCredentials
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError

class TestModels(unittest.TestCase):
    def setUp(self):
        # Create in-memory SQLite database for testing
        self.engine = create_engine('sqlite:///:memory:')
        # Enable foreign key support
        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
            
        Base.metadata.create_all(self.engine)
        TestingSessionLocal = sessionmaker(bind=self.engine)
        self.db = TestingSessionLocal()

    def tearDown(self):
        self.db.close()

    def test_create_user(self):
        user = User(
            email="test@example.com",
            password="test_password"
        )
        self.db.add(user)
        self.db.commit()
        
        saved_user = self.db.query(User).first()
        self.assertEqual(saved_user.email, "test@example.com")
        self.assertTrue(saved_user.is_active)
        self.assertFalse(saved_user.is_google_authenticated)
        self.assertFalse(saved_user.is_outlook_authenticated)
        self.assertFalse(saved_user.is_slack_authenticated)

    def test_create_task(self):
        # First create a user
        user = User(email="test@example.com", password="test_password")
        self.db.add(user)
        self.db.commit()
        
        # Create task for user
        task = Task(
            user_id=user.id,
            title="Test Task",
            description="Test Description",
            due_date=datetime(2024, 12, 31, tzinfo=timezone.utc)
        )
        self.db.add(task)
        self.db.commit()
        
        saved_task = self.db.query(Task).first()
        self.assertEqual(saved_task.title, "Test Task")
        self.assertEqual(saved_task.description, "Test Description")
        self.assertFalse(saved_task.completed)
        self.assertEqual(saved_task.user_id, user.id)
        self.assertEqual(saved_task.due_date, datetime(2024, 12, 31))
        self.assertIsInstance(saved_task.created_at, datetime)
        self.assertIsInstance(saved_task.updated_at, datetime)

    def test_task_user_relationship(self):
        user = User(email="test@example.com", password="test_password")
        self.db.add(user)
        self.db.commit()
        
        task = Task(
            user_id=user.id,
            title="Test Task"
        )
        self.db.add(task)
        self.db.commit()
        
        # Test foreign key constraint
        invalid_task = Task(
            user_id=999,  # Non-existent user_id
            title="Invalid Task"
        )
        self.db.add(invalid_task)
        
        with self.assertRaises(IntegrityError):
            self.db.commit()

    def test_gmail_credentials(self):
        # Create a user first
        user = User(email="test@example.com", password="test_password")
        self.db.add(user)
        self.db.commit()

        # Test creating Gmail credentials
        credentials = GmailCredentials(
            user_id=user.id,
            token="test_token",
            refresh_token="test_refresh_token"
        )
        self.db.add(credentials)
        self.db.commit()

        # Test token encryption/decryption
        saved_credentials = self.db.query(GmailCredentials).first()
        self.assertNotEqual(saved_credentials.encrypted_token, "test_token")  # Should be encrypted
        self.assertEqual(saved_credentials.token, "test_token")  # Should be decrypted
        self.assertEqual(saved_credentials.refresh_token, "test_refresh_token")

        # Test foreign key constraint
        invalid_credentials = GmailCredentials(
            user_id=999,  # Non-existent user_id
            token="test_token"
        )
        self.db.add(invalid_credentials)
        
        with self.assertRaises(IntegrityError):
            self.db.commit()