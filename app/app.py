from fastapi import FastAPI, HTTPException, Depends, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse
from app.message_service.models import Message
from app.ai_agents.task_identifier import TaskIdentifier
from app.message_service.gmail_service import GmailService
from google.oauth2.credentials import Credentials
from fastapi.security import OAuth2AuthorizationCodeBearer
from typing import Optional, List
from datetime import datetime
import logging
from google_auth_oauthlib.flow import Flow
from app.config import settings
from app.models import GmailCredentials, User, Task, get_db, create_database
import schedule
from sqlalchemy.orm import Session
import jwt

app = FastAPI()

logger = logging.getLogger(__name__)

@app.get("/")
async def root():
    return RedirectResponse(url="/auth/login")  

@app.get("/auth/login")
async def login():    
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": settings.GOOGLE_AUTH_URL,
                "token_uri": settings.GOOGLE_TOKEN_URL,
                "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
            }
        },
        scopes=settings.GOOGLE_SCOPES
    )
    
    flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    
    return RedirectResponse(authorization_url)

@app.get("/auth/callback")
async def callback(request: Request, db: Session = Depends(get_db)):
    try:
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "auth_uri": settings.GOOGLE_AUTH_URL,
                    "token_uri": settings.GOOGLE_TOKEN_URL,
                    "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
                }
            },
            scopes=settings.GOOGLE_SCOPES
        )
        
        flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
        flow.fetch_token(
            code=request.query_params.get("code"),
            authorization_response=str(request.url)
        )

        credentials = flow.credentials
        
        if credentials.id_token:
            try:
                decoded_token = jwt.decode(credentials.id_token, options={"verify_signature": False})  # or use a specific key to verify
                user_email = decoded_token.get("email")
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Failed to decode id_token: {str(e)}")
        else:
            raise HTTPException(status_code=400, detail="id_token not found in credentials")

        if not user_email:
            raise HTTPException(status_code=400, detail="User email not found in token")

        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            user = User(email=user_email, is_active=True, is_google_authenticated=True)        
            db.add(user)
            db.commit()

        # Store credentials with expiry time
        db.add(
            GmailCredentials(
                user_id=user.id, 
                token=credentials.token, 
                refresh_token=credentials.refresh_token, 
                token_expiry=datetime.fromtimestamp(credentials.expiry.timestamp())
            ))
        db.commit()
        return RedirectResponse(url="/success")

    except Exception as e:
        logger.error(f"Auth callback error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")

@app.get("/success")
async def success():
    return {"message": "Successfully authenticated with Gmail"}

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

if __name__ == "__main__":
    import threading
    import time

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    def run_polling():
        thread_name = threading.current_thread().name
        logger.info(f"Starting polling thread: {thread_name}")  # Added logging
        while True:
            try:
                poll_userbase()
            except Exception as e:
                logger.error(f"Error in polling thread: {e}")  # Added error logging
            time.sleep(10)

    polling_thread = threading.Thread(target=run_polling, name="PollingThread", daemon=True)
    polling_thread.start()

    create_database()
    import uvicorn
    uvicorn.run('app.app:app', host="127.0.0.1", port=8000, reload=False)  # Disabled reload

    
