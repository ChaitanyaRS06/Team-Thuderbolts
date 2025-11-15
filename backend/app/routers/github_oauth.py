# backend/app/routers/github_oauth.py
"""
GitHub OAuth 2.0 Flow
Handles user authorization and token management
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import logging
import secrets
import requests

from app.auth import get_current_active_user
from app.models import User, GitHubToken
from app.database import get_db
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# GitHub OAuth URLs
GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_API_URL = "https://api.github.com"

# OAuth scopes - what permissions we need
SCOPES = ["repo", "read:user", "read:org"]

# Store state tokens temporarily (in production, use Redis or database)
oauth_states = {}

class OAuthURLResponse(BaseModel):
    auth_url: str
    state: str

class OAuthStatusResponse(BaseModel):
    connected: bool
    username: Optional[str] = None
    name: Optional[str] = None


@router.get("/oauth/authorize")
async def get_oauth_url(
    redirect_uri: str,
    current_user: User = Depends(get_current_active_user)
) -> OAuthURLResponse:
    """
    Generate OAuth authorization URL for user to grant GitHub access

    Args:
        redirect_uri: Frontend callback URL (e.g., http://localhost:5174/settings/github/callback)

    Returns:
        Authorization URL and state token
    """
    if not settings.github_client_id:
        raise HTTPException(
            status_code=500,
            detail="GitHub OAuth is not configured. Please set GITHUB_CLIENT_ID in .env"
        )

    try:
        # Generate random state for CSRF protection
        state = secrets.token_urlsafe(32)

        # Store state with user_id for verification in callback
        oauth_states[state] = {
            "user_id": current_user.id,
            "created_at": datetime.utcnow(),
            "redirect_uri": redirect_uri
        }

        # Generate authorization URL
        scope_str = " ".join(SCOPES)
        auth_url = (
            f"{GITHUB_AUTHORIZE_URL}?"
            f"client_id={settings.github_client_id}&"
            f"redirect_uri={redirect_uri}&"
            f"scope={scope_str}&"
            f"state={state}"
        )

        logger.info(f"Generated GitHub OAuth URL for user {current_user.id}")

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
    Handle OAuth callback from GitHub
    This endpoint receives the authorization code and exchanges it for tokens

    Args:
        code: Authorization code from GitHub
        state: State token for CSRF protection
    """
    if not settings.github_client_id or not settings.github_client_secret:
        raise HTTPException(
            status_code=500,
            detail="GitHub OAuth is not configured"
        )

    try:
        # Verify state token
        if state not in oauth_states:
            raise HTTPException(
                status_code=400,
                detail="Invalid or expired state token"
            )

        state_data = oauth_states[state]
        user_id = state_data["user_id"]

        # Remove used state token
        del oauth_states[state]

        # Exchange authorization code for access token
        token_response = requests.post(
            GITHUB_TOKEN_URL,
            headers={
                "Accept": "application/json"
            },
            data={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
                "redirect_uri": state_data["redirect_uri"]
            }
        )

        token_response.raise_for_status()
        token_data = token_response.json()

        if "error" in token_data:
            raise Exception(token_data.get("error_description", token_data["error"]))

        access_token = token_data.get("access_token")
        token_type = token_data.get("token_type", "bearer")
        scope = token_data.get("scope", "")

        if not access_token:
            raise Exception("No access token received from GitHub")

        # Get user info from GitHub
        user_response = requests.get(
            f"{GITHUB_API_URL}/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json"
            }
        )
        user_response.raise_for_status()
        github_user = user_response.json()

        # Store or update token in database
        existing_token = db.query(GitHubToken).filter(
            GitHubToken.user_id == user_id
        ).first()

        if existing_token:
            # Update existing token
            existing_token.access_token = access_token
            existing_token.token_type = token_type
            existing_token.scope = scope
            existing_token.updated_at = datetime.utcnow()
        else:
            # Create new token record
            new_token = GitHubToken(
                user_id=user_id,
                access_token=access_token,
                token_type=token_type,
                scope=scope,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(new_token)

        db.commit()

        logger.info(f"GitHub OAuth tokens saved for user {user_id}, username: {github_user.get('login')}")

        return {
            "success": True,
            "message": "GitHub connected successfully",
            "username": github_user.get("login"),
            "name": github_user.get("name")
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
    """Check if user has connected their GitHub"""
    try:
        token = db.query(GitHubToken).filter(
            GitHubToken.user_id == current_user.id
        ).first()

        if not token:
            return OAuthStatusResponse(connected=False)

        # Try to get user info to verify connection
        username = None
        name = None
        try:
            user_response = requests.get(
                f"{GITHUB_API_URL}/user",
                headers={
                    "Authorization": f"Bearer {token.access_token}",
                    "Accept": "application/vnd.github+json"
                }
            )
            if user_response.status_code == 200:
                github_user = user_response.json()
                username = github_user.get("login")
                name = github_user.get("name")
        except Exception as e:
            logger.warning(f"Could not verify GitHub connection: {e}")

        return OAuthStatusResponse(
            connected=True,
            username=username,
            name=name
        )

    except Exception as e:
        logger.error(f"Error checking OAuth status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check connection status: {str(e)}"
        )


@router.post("/oauth/disconnect")
async def disconnect_github(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Disconnect user's GitHub by removing stored tokens"""
    try:
        token = db.query(GitHubToken).filter(
            GitHubToken.user_id == current_user.id
        ).first()

        if token:
            db.delete(token)
            db.commit()
            logger.info(f"GitHub disconnected for user {current_user.id}")
            return {"success": True, "message": "GitHub disconnected"}
        else:
            return {"success": False, "message": "No GitHub connection found"}

    except Exception as e:
        logger.error(f"Error disconnecting GitHub: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to disconnect: {str(e)}"
        )


@router.post("/oauth/test")
async def test_oauth_connection(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Test GitHub connection with current OAuth token"""
    try:
        from app.mcp_servers.github_mcp import GitHubMCPServer

        mcp_server = GitHubMCPServer(user_id=current_user.id, db=db)
        result = await mcp_server.test_connection()
        return result

    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Connection test failed: {str(e)}"
        )
