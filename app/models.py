from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from sqlalchemy.orm import relationship
from cryptography.fernet import Fernet
from app.config import settings
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

cipher = Fernet(settings.FERNET_KEY)

def encrypt_token(token):
    return cipher.encrypt(token.encode()).decode()

def decrypt_token(encrypted_token):
    return cipher.decrypt(encrypted_token.encode()).decode()


Base = declarative_base()

# Define engine and SessionLocal at module level
engine = create_engine("sqlite:///mail_tasks.db")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    is_google_authenticated = Column(Boolean, default=False)
    is_outlook_authenticated = Column(Boolean, default=False)
    is_slack_authenticated = Column(Boolean, default=False)
    tasks = relationship("Task", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', is_active={self.is_active})>"
    
class GmailCredentials(Base):
    __tablename__ = "gmail_credentials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    encrypted_token = Column(String, nullable=False)
    encrypted_refresh_token = Column(String, nullable=True)
    token_expiry = Column(DateTime, nullable=True) 
    
    def __repr__(self):
        return f"<GmailCredentials(id={self.id}, token_expiry={self.token_expiry})>"

    @property
    def is_expired(self):
        return self.token_expiry and self.token_expiry < datetime.now()
    
    def update_token(self):
        credentials = Credentials(
            token=self.token,
            refresh_token=self.refresh_token,
            token_uri=settings.GOOGLE_TOKEN_URL,
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET
        )
        credentials.refresh(Request())
        
        self.token = encrypt_token(credentials.token)
        self.refresh_token = encrypt_token(credentials.refresh_token)
        self.token_expiry = credentials.expiry

    @property
    def token(self):
        return decrypt_token(self.encrypted_token) if self.encrypted_token else None
    
    @property
    def refresh_token(self):
        return decrypt_token(self.encrypted_refresh_token) if self.encrypted_refresh_token else None
    

    def get_credentials(self):
        credentials = Credentials(
            token=self.token,
            refresh_token=self.refresh_token,
            token_uri=settings.GOOGLE_TOKEN_URL,
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            scopes=settings.GOOGLE_SCOPES
        )   
        return credentials
    @token.setter
    def token(self, value):
        self.encrypted_token = encrypt_token(value) if value else None

    @refresh_token.setter
    def refresh_token(self, value):
        self.encrypted_refresh_token = encrypt_token(value) if value else None  

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    due_date = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="tasks") 

    def __repr__(self):
        return f"<Task(id={self.id}, user_id={self.user_id}, title='{self.title}', completed={self.completed})>"

def create_database():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
