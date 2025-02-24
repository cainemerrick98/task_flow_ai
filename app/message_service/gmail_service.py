from app.message_service.base import BaseMessageService
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build 
from app.message_service.models import Message, Attachment
from googleapiclient.errors import HttpError


class GmailService(BaseMessageService):
    def __init__(self, credentials: Credentials):
        """
        Initialize Gmail service with OAuth2 credentials
        
        Args:
            credentials: Google OAuth2 Credentials object
        """
        self.credentials = credentials
        self.service = None
        self.authenticate()
    
    def authenticate(self) -> bool:
        """
        Authenticate the Gmail service.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            print("Creating Gmail service...")
            self.service = build('gmail', 'v1', credentials=self.credentials)
            
            print("Testing connection with getProfile...")
            profile = self.service.users().getProfile(userId='me').execute()
            print(f"Successfully connected to Gmail for: {profile.get('emailAddress')}")
            return True
            
        except HttpError as e:
            print(f"Gmail API HTTP error: {e.resp.status} - {e.content}")
            self.service = None
            return False
        except Exception as e:
            print(f"Authentication failed with unexpected error: {str(e)}")
            print(f"Error type: {type(e)}")
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
            # Only get messages from inbox by excluding social and promotions labels
            for msg in results.get('messages', []):
                message = self.service.users().messages().get(
                    userId='me', 
                    id=msg['id'],
                ).execute()
                
                # Skip messages with social/promotions labels
                labels = message.get('labelIds', [])
                if 'UNREAD' in labels and 'INBOX' in labels and 'CATEGORY_SOCIAL' not in labels and 'CATEGORY_PROMOTIONS' not in labels:
                    print(labels)
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
                    
                    #TODO: Mark message as read
                    #Need to add scope to credentials to modify messages
                    
                    # self.service.users().messages().modify(
                    #     userId='me',
                    #     id=msg['id'],
                    #     body={'removeLabelIds': ['UNREAD']}
                    # ).execute()
            return messages
        
        except Exception as e:
            print(f"Error retrieving messages: {str(e)}")
            return []