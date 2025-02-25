from google_auth_oauthlib.flow import Flow
from fastapi import Request
from app.config import settings

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