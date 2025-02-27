from google_auth_oauthlib.flow import Flow
from fastapi import Request, APIRouter, HTTPException, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
import jwt
import logging
from datetime import datetime

from app.config import settings
from app.models import User, GmailCredentials, get_db


router = APIRouter()
logger = logging.getLogger(__name__)

def create_auth_flow():
    """Create and return an OAuth flow for Google authentication"""
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
    return flow

def get_flow_and_credentials(request: Request):
    """Get an OAuth flow and fetch credentials based on the request"""
    flow = create_auth_flow()
    flow.fetch_token(
        code=request.query_params.get("code"),
        authorization_response=str(request.url)
    )
    return flow, flow.credentials 


@router.get("/integrations/google/integrate")
async def login():    
    flow = create_auth_flow()
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    return RedirectResponse(authorization_url)



@router.get("/integrations/google/callback")
async def callback(request: Request, db: Session = Depends(get_db)):
    try:
        flow, credentials = get_flow_and_credentials(request)
        
        # Extract user email from token
        if credentials.id_token:
            try:
                decoded_token = jwt.decode(credentials.id_token, options={"verify_signature": False})
                user_email = decoded_token.get("email")
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Failed to decode id_token: {str(e)}")
        else:
            raise HTTPException(status_code=400, detail="id_token not found in credentials")

        if not user_email:
            raise HTTPException(status_code=400, detail="User email not found in token")

        # Create or update user
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            raise HTTPException(status_code=400, detail="User not found")
        
        if not user.is_google_authenticated:
            user.is_google_authenticated = True
            db.commit()

        # Store credentials
        db.add(
            GmailCredentials(
                user_id=user.id, 
                token=credentials.token, 
                refresh_token=credentials.refresh_token, 
                token_expiry=datetime.fromtimestamp(credentials.expiry.timestamp())
            ))
        db.commit()
        
        return JSONResponse(status_code=200, content={"message": "Successfully authenticated with Gmail"})

    except Exception as e:
        logger.error(f"Auth callback error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")


