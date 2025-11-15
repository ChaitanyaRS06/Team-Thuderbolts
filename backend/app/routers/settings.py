# backend/app/routers/settings.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.auth import get_current_active_user
from app.models import User
from app.database import get_db
import os
import re
import base64

router = APIRouter()

class GoogleDriveConfig(BaseModel):
    google_drive_credentials_json: str
    google_drive_root_folder: str = "UVA_Research_Assistant"

class EmbeddingConfig(BaseModel):
    provider: str  # "huggingface" or "openai"

# Note: Google Drive OAuth configuration is now handled through the /google-drive/oauth endpoints
# The old service account configuration endpoint has been removed in favor of OAuth 2.0

@router.get("/google-drive/status")
async def get_google_drive_status(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """Check if user has connected their Google Drive via OAuth"""
    from app.config import settings
    from app.models import GoogleDriveToken
    from sqlalchemy.orm import Session

    # Check if OAuth is configured at system level
    oauth_configured = bool(settings.google_drive_client_id and settings.google_drive_client_secret)

    # Check if user has authorized
    token = db.query(GoogleDriveToken).filter(
        GoogleDriveToken.user_id == current_user.id
    ).first()

    user_connected = bool(token)

    return {
        "oauth_configured": oauth_configured,
        "user_connected": user_connected,
        "root_folder": settings.google_drive_root_folder,
        "requires_setup": not oauth_configured
    }

@router.post("/google-drive/test")
async def test_google_drive_connection(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """Test Google Drive connection with user's OAuth credentials"""
    from app.mcp_servers.google_drive_mcp import GoogleDriveMCPServer

    try:
        mcp_server = GoogleDriveMCPServer(user_id=current_user.id, db=db)
        result = await mcp_server.test_connection()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Connection test failed: {str(e)}"
        )

@router.post("/embedding/configure")
async def configure_embedding_provider(
    config: EmbeddingConfig,
    current_user: User = Depends(get_current_active_user)
):
    """
    Configure embedding provider (huggingface or openai)
    Only admin users can modify system configuration
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Only administrators can configure embedding provider"
        )

    if config.provider not in ["huggingface", "openai"]:
        raise HTTPException(
            status_code=400,
            detail="Provider must be 'huggingface' or 'openai'"
        )

    try:
        env_path = ".env"

        # Read current .env content
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                env_content = f.read()
        else:
            raise HTTPException(status_code=500, detail=".env file not found")

        # Update embedding provider
        pattern = r'^EMBEDDING_PROVIDER=.*$'
        replacement = f'EMBEDDING_PROVIDER={config.provider}'

        if re.search(pattern, env_content, re.MULTILINE):
            env_content = re.sub(pattern, replacement, env_content, flags=re.MULTILINE)
        else:
            # Add after embedding settings
            if "# Embedding Settings" in env_content:
                section_pattern = r'(# Embedding Settings\n)'
                env_content = re.sub(
                    section_pattern,
                    rf'\1EMBEDDING_PROVIDER={config.provider}\n',
                    env_content
                )

        # Write updated content
        with open(env_path, 'w') as f:
            f.write(env_content)

        return {
            "message": f"Embedding provider set to {config.provider}",
            "note": "Restart the application to apply changes",
            "provider": config.provider
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update configuration: {str(e)}"
        )

@router.get("/system/info")
async def get_system_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current system configuration"""
    from app.config import settings

    return {
        "embedding": {
            "provider": settings.embedding_provider,
            "model": settings.openai_embedding_model if settings.embedding_provider == "openai" else settings.embedding_model
        },
        "google_drive": {
            "configured": bool(settings.google_drive_client_id and settings.google_drive_client_secret),
            "root_folder": settings.google_drive_root_folder
        },
        "llm": {
            "provider": "anthropic",
            "model": settings.anthropic_model
        }
    }
