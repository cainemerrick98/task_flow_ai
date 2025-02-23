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
import json

app = FastAPI()

logger = logging.getLogger(__name__)

@app.post("/process_messages")
async def process_messages(
    access_token: str = Depends(OAuth2AuthorizationCodeBearer(settings.GOOGLE_AUTH_URL, settings.GOOGLE_TOKEN_URL)),
    max_messages: Optional[int] = Query(default=50, le=100)
):
    try:
        print("starting process messages")
        credentials = Credentials(token=access_token)
        gmail_service = GmailService(credentials)
        
        # Add debug logging
        logger.debug(f"Access token: {access_token[:10]}...")
        logger.debug(f"Credentials valid: {credentials.valid}")
        logger.debug(f"Credentials expired: {credentials.expired}")
        
        if not gmail_service.authenticate():
            logger.error("Gmail service authentication failed")
            raise HTTPException(status_code=401, detail="Failed to authenticate")

        messages = gmail_service.get_messages(limit=max_messages)
        
        task_identifier = TaskIdentifier()
        tasks = []
        
        for message in messages:
            try:
                task = task_identifier.get_task(message)
                if task:
                    tasks.append(task)
            except Exception as e:
                # Log the error but continue processing other messages
                logger.error(f"Error processing message {message.id}: {str(e)}")
        
        #Add debug logging for final tasks
        print(f"Final tasks type: {type(tasks)}")
        print(f"Final tasks content: {tasks}")
        print(f"Final tasks length: {len(tasks)}")
        print(f"Final tasks json: {[task.model_dump_json() for task in tasks]}")
                
        return JSONResponse(content={
            "total_messages_processed": len(messages),
            "tasks_identified": len(tasks),
            "tasks": [task.model_dump_json() for task in tasks]
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
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
        include_granted_scopes='true'
    )
    
    return RedirectResponse(authorization_url)

@app.get("/auth/callback")
async def callback(request: Request):
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
    
    # Get authorization code from request
    code = request.query_params.get("code")
    flow.fetch_token(code=code)
    
    credentials = flow.credentials
    
    # Return the access token (in production, you'd want to store this securely)
    return {
        "access_token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run('app.app:app', host="127.0.0.1", port=8000, reload=True)
