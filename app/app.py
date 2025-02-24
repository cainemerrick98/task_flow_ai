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
            user = User(email=user_email, is_active=True, is_gmail_authenticated=True)        
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

def poll_gmail(user: User) -> List[Message]:
    """
    Poll Gmail for new messages and return a list of tasks
    """
    credentials = GmailCredentials.get_credentials(user.id)
    if credentials and credentials.is_expired:
        credentials.refresh()
    
    gmail_service = GmailService(credentials)
    messages = gmail_service.get_messages(limit=50)
    task_identifier = TaskIdentifier()
    tasks = []
    for message in messages:
        task = task_identifier.get_task(message)
        if task:
            tasks.append(task)
    return tasks

def poll_userbase():
    with get_db() as db:
        print("Polling userbase")
        users = db.query(User).all()
        print(users)
        for user in users:
            print(user)
            if user.is_active and user.is_gmail_authenticated:
                tasks = poll_gmail(user)
                for task in tasks:
                    print(task)
                    task.user_id = user.id
                    db.add(Task(**task))
                db.commit()
    print("Done polling userbase")

if __name__ == "__main__":

    schedule.every(10).seconds.do(poll_userbase)

    from app.models import create_database
    create_database()
    import uvicorn
    uvicorn.run('app.app:app', host="127.0.0.1", port=8000, reload=True)
    
