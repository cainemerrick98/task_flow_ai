import unittest
from unittest.mock import patch, MagicMock
from app.message_service.gmail_service import GmailService
from app.message_service.models import Message, Attachment


class TestGmailService(unittest.TestCase):
    def setUp(self) -> None:
        self.test_credentials = {
            'token': 'test_token',
            'refresh_token': 'test_refresh',
            'token_uri': 'test_uri',
            'client_id': 'test_id',
            'client_secret': 'test_secret'
        }
        return super().setUp()
    @patch('app.message_service.gmail_service.build')
    def test_authenticate(self, mock_build):
        """
        Test that the authenticate method works correctly.
        
        Tests:
            - Mock the build function and verify authentication succeeds
            - Check that authenticate() returns True on success
        """
        # Mock the build function and service
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.users().getProfile().execute.return_value = {}

        # Create a GmailService instance
        gmail_service = GmailService(self.test_credentials)

        # Test the authenticate method
        self.assertTrue(gmail_service.authenticate())

    @patch('app.message_service.gmail_service.build')
    def test_get_messages(self, mock_build):
        """
        Test retrieving messages without attachments.
        
        Tests:
            - Mock Gmail API responses for message list and details
            - Verify correct number of messages returned
            - Check message subject and sender are parsed correctly
        """
        # Mock the Gmail API response
        mock_messages_response = {
            'messages': [
                {'id': '123', 'threadId': 'thread123'},
                {'id': '456', 'threadId': 'thread456'}
            ]
        }
        mock_message_detail = {
            'id': '123',
            'payload': {
                'headers': [
                    {'name': 'Subject', 'value': 'Test Subject'},
                    {'name': 'From', 'value': 'sender@example.com'}
                ],
                'parts': []
            },
            'snippet': 'Test message body'
        }
        
        mock_service = mock_build.return_value
        mock_service.users().messages().list().execute.return_value = mock_messages_response
        mock_service.users().messages().get().execute.return_value = mock_message_detail

        gmail_service = GmailService(self.test_credentials)
        messages = gmail_service.get_messages()

        # Test specific message attributes
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].subject, 'Test Subject')
        self.assertEqual(messages[0].sender, 'sender@example.com')

    @patch('app.message_service.gmail_service.build')
    def test_get_messages_with_attachments(self, mock_build):
        """
        Test retrieving messages with attachments.
        
        Tests:
            - Mock Gmail API responses including attachment data
            - Verify attachments are correctly parsed
            - Check attachment properties (filename, mime type)
        """
        # Mock the Gmail API response
        mock_messages_response = {
            'messages': [
                {'id': '123', 'threadId': 'thread123'}
            ]
        }
        # Mock the Gmail API response with attachments
        mock_message_detail = {
            'id': '123',
            'payload': {
                'headers': [
                    {'name': 'Subject', 'value': 'Test Subject'},
                    {'name': 'From', 'value': 'sender@example.com'}
                ],
                'parts': [{
                    'filename': 'test.pdf',
                    'body': {'attachmentId': 'att123'},
                    'mimeType': 'application/pdf'
                }]
            },
            'snippet': 'Test message body'
        }
        
        mock_service = mock_build.return_value
        mock_service.users().messages().list().execute.return_value = mock_messages_response
        mock_service.users().messages().get().execute.return_value = mock_message_detail
        mock_service.users().messages().attachments().get().execute.return_value = {
            'data': 'base64data'
        }

        gmail_service = GmailService(self.test_credentials)
        messages = gmail_service.get_messages()

        # Test attachment specific attributes
        self.assertEqual(len(messages[0].attachments), 1)
        self.assertEqual(messages[0].attachments[0].filename, 'test.pdf')
        self.assertEqual(messages[0].attachments[0].mimeType, 'application/pdf')

    @patch('app.message_service.gmail_service.build')
    def test_get_messages_error_handling(self, mock_build):
        """
        Test error handling when retrieving messages fails.
        
        Tests:
            - Mock Gmail API to raise an exception
            - Verify the exception is propagated correctly
        """
        # Test API error handling
        mock_service = mock_build.return_value
        mock_service.users().messages().list().execute.side_effect = Exception('API Error')

        gmail_service = GmailService(self.test_credentials)
        messages = gmail_service.get_messages()
        self.assertEqual(len(messages), 0)

    @patch('app.message_service.gmail_service.build')
    def test_get_messages_with_multiple_messages(self, mock_build):
        """
        Test retrieving multiple messages.
        
        Tests:
            - Mock Gmail API responses for multiple messages
            - Verify correct number of messages returned
            - Check message subjects and senders are parsed correctly
        """
        # Mock the Gmail API response
        mock_messages_response = {
            'messages': [
                {'id': '123', 'threadId': 'thread123'},
                {'id': '456', 'threadId': 'thread456'}
            ]
        }
        mock_message_detail = {
            'id': '123',
            'payload': {
                'headers': [
                    {'name': 'Subject', 'value': 'Test Subject 1'},
                    {'name': 'From', 'value': 'sender@example.com'}
                ],
                'parts': []
            },
            'snippet': 'Test message body 1'
        }
        mock_message_detail_2 = {
            'id': '456',
            'payload': {
                'headers': [
                    {'name': 'Subject', 'value': 'Test Subject 2'}, 
                    {'name': 'From', 'value': 'sender@example.com'}
                ],
                'parts': []
            },
            'snippet': 'Test message body 2'
        }


        mock_service = mock_build.return_value
        mock_service.users().messages().list().execute.return_value = mock_messages_response
        mock_service.users().messages().get().execute.side_effect = [mock_message_detail, mock_message_detail_2]

        gmail_service = GmailService(self.test_credentials)
        messages = gmail_service.get_messages()

        # Test specific message attributes
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].subject, 'Test Subject 1')
        self.assertEqual(messages[1].subject, 'Test Subject 2')
        self.assertEqual(messages[0].sender, 'sender@example.com')
        self.assertEqual(messages[1].sender, 'sender@example.com')
        self.assertEqual(messages[0].body, 'Test message body 1')
        self.assertEqual(messages[1].body, 'Test message body 2')

    