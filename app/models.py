from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from sqlalchemy.orm import relationship

Base = declarative_base()

# Define engine and SessionLocal at module level
engine = create_engine("sqlite:///mail_tasks.db")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    tasks = relationship("Task", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', is_active={self.is_active})>"

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