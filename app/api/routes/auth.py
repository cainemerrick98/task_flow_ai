from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import jwt
import logging
from datetime import datetime

from app.models import User, GmailCredentials, get_db
from app.auth.google import create_auth_flow, get_flow_and_credentials

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/auth/login")
async def login():    
    flow = create_auth_flow()
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    return RedirectResponse(authorization_url)

@router.get("/auth/callback")
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
            user = User(email=user_email, is_active=True, is_google_authenticated=True)
            db.add(user)
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
        
        return RedirectResponse(url="/auth/success")

    except Exception as e:
        logger.error(f"Auth callback error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")

@router.get("/auth/success")
async def success():
    return {"message": "Successfully authenticated with Gmail"} 