# backend/app/routers/google_drive_oauth.py
"""
Google Drive OAuth 2.0 Flow
Handles user authorization and token management
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional
import logging
import secrets

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from app.auth import get_current_active_user
from app.models import User, GoogleDriveToken
from app.database import get_db
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# OAuth 2.0 scopes - full drive access needed for folder operations
SCOPES = ['https://www.googleapis.com/auth/drive']

# Store state tokens temporarily (in production, use Redis or database)
oauth_states = {}

class OAuthURLResponse(BaseModel):
    auth_url: str
    state: str

class OAuthStatusResponse(BaseModel):
    connected: bool
    user_email: Optional[str] = None
    token_expiry: Optional[datetime] = None


def get_oauth_flow(state: Optional[str] = None, redirect_uri: Optional[str] = None):
    """Create OAuth flow instance"""
    if not settings.google_drive_client_id or not settings.google_drive_client_secret:
        raise HTTPException(
            status_code=500,
            detail="Google Drive OAuth is not configured. Please set GOOGLE_DRIVE_CLIENT_ID and GOOGLE_DRIVE_CLIENT_SECRET in .env"
        )

    client_config = {
        "web": {
            "client_id": settings.google_drive_client_id,
            "client_secret": settings.google_drive_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri] if redirect_uri else []
        }
    }

    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        state=state
    )

    if redirect_uri:
        flow.redirect_uri = redirect_uri

    return flow


@router.get("/oauth/authorize")
async def get_oauth_url(
    redirect_uri: str,
    current_user: User = Depends(get_current_active_user)
) -> OAuthURLResponse:
    """
    Generate OAuth authorization URL for user to grant Google Drive access

    Args:
        redirect_uri: Frontend callback URL (e.g., http://localhost:5173/settings/google-drive/callback)

    Returns:
        Authorization URL and state token
    """
    try:
        # Generate random state for CSRF protection
        state = secrets.token_urlsafe(32)

        # Store state with user_id for verification in callback
        oauth_states[state] = {
            "user_id": current_user.id,
            "created_at": datetime.utcnow(),
            "redirect_uri": redirect_uri
        }

        # Create OAuth flow
        flow = get_oauth_flow(state=state, redirect_uri=redirect_uri)

        # Generate authorization URL
        auth_url, _ = flow.authorization_url(
            access_type='offline',  # Request refresh token
            include_granted_scopes='true',
            prompt='consent'  # Force consent screen to ensure refresh token
        )

        logger.info(f"Generated OAuth URL for user {current_user.id}")

        return OAuthURLResponse(
            auth_url=auth_url,
            state=state
        )

    except Exception as e:
        logger.error(f"Error generating OAuth URL: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate authorization URL: {str(e)}"
        )


@router.get("/oauth/callback")
async def oauth_callback(
    code: str,
    state: str,
    db: Session = Depends(get_db)
):
    """
    Handle OAuth callback from Google
    This endpoint receives the authorization code and exchanges it for tokens

    Args:
        code: Authorization code from Google
        state: State token for CSRF protection
    """
    try:
        # Verify state token
        if state not in oauth_states:
            raise HTTPException(
                status_code=400,
                detail="Invalid or expired state token"
            )

        state_data = oauth_states[state]
        user_id = state_data["user_id"]
        redirect_uri = state_data["redirect_uri"]

        # Remove used state token
        del oauth_states[state]

        # Exchange authorization code for tokens
        flow = get_oauth_flow(state=state, redirect_uri=redirect_uri)
        flow.fetch_token(code=code)

        credentials = flow.credentials

        # Get user info from Google
        service = build('drive', 'v3', credentials=credentials)
        about = service.about().get(fields='user').execute()
        user_email = about.get('user', {}).get('emailAddress')

        # Store or update tokens in database
        existing_token = db.query(GoogleDriveToken).filter(
            GoogleDriveToken.user_id == user_id
        ).first()

        if existing_token:
            # Update existing token
            existing_token.access_token = credentials.token
            existing_token.refresh_token = credentials.refresh_token or existing_token.refresh_token
            existing_token.token_expiry = credentials.expiry
            existing_token.updated_at = datetime.utcnow()
        else:
            # Create new token record
            new_token = GoogleDriveToken(
                user_id=user_id,
                access_token=credentials.token,
                refresh_token=credentials.refresh_token,
                token_expiry=credentials.expiry,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(new_token)

        db.commit()

        logger.info(f"OAuth tokens saved for user {user_id}, email: {user_email}")

        return {
            "success": True,
            "message": "Google Drive connected successfully",
            "user_email": user_email
        }

    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to complete authorization: {str(e)}"
        )


@router.get("/oauth/status")
async def get_oauth_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> OAuthStatusResponse:
    """Check if user has connected their Google Drive"""
    try:
        token = db.query(GoogleDriveToken).filter(
            GoogleDriveToken.user_id == current_user.id
        ).first()

        if not token:
            return OAuthStatusResponse(connected=False)

        # Check if token is expired
        is_expired = False
        if token.token_expiry:
            is_expired = token.token_expiry < datetime.utcnow()

        # Try to get user info to verify connection
        user_email = None
        if not is_expired:
            try:
                credentials = Credentials(
                    token=token.access_token,
                    refresh_token=token.refresh_token,
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=settings.google_drive_client_id,
                    client_secret=settings.google_drive_client_secret
                )

                service = build('drive', 'v3', credentials=credentials)
                about = service.about().get(fields='user').execute()
                user_email = about.get('user', {}).get('emailAddress')
            except Exception as e:
                logger.warning(f"Could not verify Google Drive connection: {e}")

        return OAuthStatusResponse(
            connected=True,
            user_email=user_email,
            token_expiry=token.token_expiry
        )

    except Exception as e:
        logger.error(f"Error checking OAuth status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check connection status: {str(e)}"
        )


@router.post("/oauth/disconnect")
async def disconnect_google_drive(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Disconnect user's Google Drive by removing stored tokens"""
    try:
        token = db.query(GoogleDriveToken).filter(
            GoogleDriveToken.user_id == current_user.id
        ).first()

        if token:
            db.delete(token)
            db.commit()
            logger.info(f"Google Drive disconnected for user {current_user.id}")
            return {"success": True, "message": "Google Drive disconnected"}
        else:
            return {"success": False, "message": "No Google Drive connection found"}

    except Exception as e:
        logger.error(f"Error disconnecting Google Drive: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to disconnect: {str(e)}"
        )


@router.post("/oauth/test")
async def test_oauth_connection(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Test Google Drive connection with current OAuth tokens"""
    try:
        token = db.query(GoogleDriveToken).filter(
            GoogleDriveToken.user_id == current_user.id
        ).first()

        if not token:
            raise HTTPException(
                status_code=400,
                detail="Google Drive not connected. Please authorize access first."
            )

        # Create credentials from stored tokens
        credentials = Credentials(
            token=token.access_token,
            refresh_token=token.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.google_drive_client_id,
            client_secret=settings.google_drive_client_secret,
            scopes=SCOPES
        )

        # Build Drive service
        service = build('drive', 'v3', credentials=credentials)

        # Get user info and storage quota
        about = service.about().get(fields='user, storageQuota').execute()

        user = about.get('user', {})
        quota = about.get('storageQuota', {})

        # Update tokens if they were refreshed
        if credentials.token != token.access_token:
            token.access_token = credentials.token
            token.token_expiry = credentials.expiry
            token.updated_at = datetime.utcnow()
            db.commit()
            logger.info(f"Refreshed access token for user {current_user.id}")

        return {
            "success": True,
            "message": "Google Drive connection successful",
            "user_email": user.get('emailAddress'),
            "user_name": user.get('displayName'),
            "storage_limit": quota.get('limit'),
            "storage_used": quota.get('usage'),
            "storage_used_in_drive": quota.get('usageInDrive')
        }

    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Connection test failed: {str(e)}"
        )
