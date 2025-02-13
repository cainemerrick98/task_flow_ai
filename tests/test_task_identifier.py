from ai_agents.task_identifier import TaskIdentifier
from message_service.models import Message
from ai_agents.models import Task
import unittest
import json
from unittest.mock import patch

class TestTaskIdentifier(unittest.TestCase):
    
    @patch('ai_agent.task_identifier.Mistral')
    def setUp(self, mock_mistral):
        self.task_identifier = TaskIdentifier()
        # Create a mock instance that will be returned by Mistral()
        self.mock_mistral_instance = mock_mistral.return_value
        # Create a mock for the chat attribute
        self.mock_chat = self.mock_mistral_instance.chat
        
    def test_identify_task_with_due_date(self):
        # Mock the API response
        mock_response = {
            "task": "Update Website Pricing Page",
            "due_date": "2024-01-19",
            "description": "Update pricing page to include new enterprise tier pricing"
        }
        
        # Create a complete mock response chain
        mock_completion = unittest.mock.MagicMock()
        mock_completion.choices = [
            unittest.mock.MagicMock(
                message=unittest.mock.MagicMock(
                    content=json.dumps(mock_response)
                )
            )
        ]
        self.mock_chat.complete.return_value = mock_completion

        message = Message(
            id="123",
            subject="Website Update",
            sender="manager@company.com",
            body="I need to update the pricing page on our website by next Friday.",
            attachments=[]
        )
        task = self.task_identifier.get_task(message)
        
        self.assertIsInstance(task, Task)
        self.assertEqual(task.task, "Update Website Pricing Page")
        self.assertEqual(task.due_date, "2024-01-19")
        self.assertEqual(task.description, "Update pricing page to include new enterprise tier pricing")

    def test_identify_task_without_task(self):
        # Create a complete mock response chain
        mock_completion = unittest.mock.MagicMock()
        mock_completion.choices = [
            unittest.mock.MagicMock(
                message=unittest.mock.MagicMock(
                    content="None"
                )
            )
        ]
        self.mock_chat.complete.return_value = mock_completion
        
        message = Message(
            id="456", 
            subject="Hello",
            sender="colleague@company.com",
            body="Just wanted to say hello!",
            attachments=[]
        )
        task = self.task_identifier.get_task(message)
        
        self.assertIsNone(task)

    def test_parse_response_with_invalid_json(self):
        invalid_response = "not a json string"
        result = self.task_identifier.parse_response(invalid_response)
        self.assertIsNone(result)

    def test_parse_response_with_none(self):
        response = "None"
        result = self.task_identifier.parse_response(response)
        self.assertIsNone(result)

    def test_parse_response_with_valid_json(self):
        valid_response = {
            "task": "Update Website Pricing Page",
            "due_date": "2024-01-19",
            "description": "Update pricing page to include new enterprise tier pricing"
        }
        result = self.task_identifier.parse_response(json.dumps(valid_response))
        self.assertIsInstance(result, Task)
        self.assertEqual(result.task, "Update Website Pricing Page")
        self.assertEqual(result.due_date, "2024-01-19")
        self.assertEqual(result.description, "Update pricing page to include new enterprise tier pricing")  





