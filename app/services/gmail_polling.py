import logging
import threading
import time
from typing import List
from sqlalchemy.orm import Session

from app.models import User, GmailCredentials, Task, get_db
from app.message_service.models import Message
from app.message_service.gmail_service import GmailService
from app.ai_agents.task_identifier import TaskIdentifier

logger = logging.getLogger(__name__)

def poll_gmail(credentials: GmailCredentials, db: Session) -> List[Message]:
    """
    Poll Gmail for new messages and return a list of tasks
    """
    if credentials and credentials.is_expired:
        credentials.update_token()
        db.add(credentials)
        db.commit()
    logger.info(f"Credentials: {credentials}")

    gmail_service = GmailService(credentials.get_credentials())
    messages = gmail_service.get_messages(limit=50)
    task_identifier = TaskIdentifier()
    tasks = []
    for message in messages:
        logger.info(f"Message: {message}")
        task = task_identifier.get_task(message)
        if task:
            tasks.append(task)
    return tasks

def poll_userbase():
    logger.info("Polling userbase")
    db = next(get_db())
    try:
        users = db.query(User).all()
        logger.info(f"Found {len(users)} users")
        for user in users:
            logger.info(f"User: {user}")
            if user.is_active and user.is_google_authenticated:
                credentials = db.query(GmailCredentials).filter(GmailCredentials.user_id == user.id).first()
                tasks = poll_gmail(credentials, db)
                for task in tasks:
                    logger.info(f"Task: {task}")
                    db.add(Task(title=task.title, due_date=task.due_date, description=task.description, user_id=user.id))
                db.commit()
    except Exception as e:
        logger.error(f"Error in polling userbase: {e}")
    finally:
        db.close()
    logger.info("Done polling userbase")

def run_polling():
    thread_name = threading.current_thread().name
    logger.info(f"Starting polling thread: {thread_name}")
    while True:
        try:
            poll_userbase()
        except Exception as e:
            logger.error(f"Error in polling thread: {e}")
        time.sleep(10)

def start_polling_thread():
    """Start and return the polling thread"""
    polling_thread = threading.Thread(target=run_polling, name="PollingThread", daemon=True)
    polling_thread.start()
    return polling_thread 