from app.message_service.base import BaseMessageService
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build 
from app.message_service.models import Message, Attachment


class GmailService(BaseMessageService):
    def __init__(self, credentials_dict):
        """
        Initialize Gmail service with OAuth2 credentials
        
        Args:
            credentials_dict (dict): Dictionary containing OAuth2 credentials with keys:
                token, refresh_token, token_uri, client_id, client_secret
        """
        self.credentials_dict = credentials_dict
        self.service = None
        self.authenticate()
    
    def authenticate(self) -> bool:
        """
        Authenticate the Gmail service.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            credentials = Credentials.from_authorized_user_info(self.credentials_dict)
            self.service = build('gmail', 'v1', credentials=credentials)
            # Test the connection
            self.service.users().getProfile(userId='me').execute()
            return True
        except Exception as e:
            print(f"Authentication failed: {str(e)}")
            self.service = None
            return False
    
    def _ensure_authenticated(self) -> bool:
        """
        Ensure service is authenticated before making API calls
        
        Returns:
            bool: True if authenticated, False otherwise
        """
        if self.service is None:
            return self.authenticate()
        return True

    def get_messages(self, limit: int = 10) -> list[Message]:
        if not self._ensure_authenticated():
            return []
            
        try:
            results = self.service.users().messages().list(
                userId='me',
                maxResults=limit,
                q='is:unread'  # Only get unread messages
            ).execute()
            messages = []
            for msg in results.get('messages', []):
                message = self.service.users().messages().get(
                    userId='me',
                    id=msg['id']
                ).execute()
                
                headers = message['payload']['headers']
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
                
                # Handle attachments
                attachments = []
                if 'parts' in message['payload']:
                    parts = message['payload']['parts']
                    for part in parts:
                        if part.get('filename'):
                            attachment_id = part['body'].get('attachmentId')
                            if attachment_id:
                                attachment = self.service.users().messages().attachments().get(
                                    userId='me',
                                    messageId=msg['id'],
                                    id=attachment_id
                                ).execute()
                                attachments.append({
                                    'filename': part['filename'],
                                    'mimeType': part['mimeType'],
                                    'data': attachment['data']
                                })
                messages.append(Message(
                    id=msg['id'],
                    subject=subject,
                    sender=sender,
                    body=message['snippet'],
                    attachments=[Attachment(**attachment) for attachment in attachments]
                ))
            return messages
        
        except Exception as e:
            print(f"Error retrieving messages: {str(e)}")
            return []