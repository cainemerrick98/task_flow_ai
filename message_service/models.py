from pydantic import BaseModel

class Attachment(BaseModel):
    filename: str
    mimeType: str
    data: str

class Message(BaseModel):
    id: str
    subject: str
    sender: str
    body: str
    attachments: list[Attachment]

    def __str__(self):
        return f"""
        Sender: {self.sender}
        Subject: {self.subject}
        Body: {self.body}
        Attachments: {self.attachments} 
        """

    def __repr__(self):
        return self.__str__()
