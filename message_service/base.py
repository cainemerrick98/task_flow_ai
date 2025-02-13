from message_service.models import Message

class BaseMessageService:
    """
    Base class for all message services. 
    This class defines the interface for all message services.

    """
    def __init__(self):
        raise NotImplementedError("Subclasses must implement this method.")

    def authenticate(self):
        """
        Authenticate the message service.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def get_messages(self) -> list[Message]     :
        """
        Get messages from the message service.
        """
        raise NotImplementedError("Subclasses must implement this method.")
    
    
    

