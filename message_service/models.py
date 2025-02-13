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


