# backend/app/routers/settings.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.auth import get_current_active_user
from app.models import User
import os
import re

router = APIRouter()

class OneDriveConfig(BaseModel):
    microsoft_client_id: str
    microsoft_client_secret: str
    microsoft_tenant_id: str
    onedrive_root_folder: str = "UVA_Research_Assistant"

class EmbeddingConfig(BaseModel):
    provider: str  # "huggingface" or "openai"

@router.post("/onedrive/configure")
async def configure_onedrive(
    config: OneDriveConfig,
    current_user: User = Depends(get_current_active_user)
):
    """
    Configure OneDrive integration by updating .env file
    Only admin users can modify system configuration
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Only administrators can configure OneDrive integration"
        )

    try:
        env_path = ".env"

        # Read current .env content
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                env_content = f.read()
        else:
            raise HTTPException(status_code=500, detail=".env file not found")

        # Update OneDrive configuration values
        updates = {
            "MICROSOFT_CLIENT_ID": config.microsoft_client_id,
            "MICROSOFT_CLIENT_SECRET": config.microsoft_client_secret,
            "MICROSOFT_TENANT_ID": config.microsoft_tenant_id,
            "ONEDRIVE_ROOT_FOLDER": config.onedrive_root_folder
        }

        for key, value in updates.items():
            # Pattern to match the existing line
            pattern = rf'^{key}=.*$'
            replacement = f'{key}={value}'

            # Replace if exists, otherwise append
            if re.search(pattern, env_content, re.MULTILINE):
                env_content = re.sub(pattern, replacement, env_content, flags=re.MULTILINE)
            else:
                # Add to Microsoft Graph section
                if "# Microsoft Graph/OneDrive Configuration" in env_content:
                    section_pattern = r'(# Microsoft Graph/OneDrive Configuration.*?\n)'
                    env_content = re.sub(
                        section_pattern,
                        rf'\1{key}={value}\n',
                        env_content,
                        flags=re.DOTALL
                    )

        # Write updated content
        with open(env_path, 'w') as f:
            f.write(env_content)

        return {
            "message": "OneDrive configuration saved successfully",
            "note": "Restart the application to apply changes",
            "configured": True
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update configuration: {str(e)}"
        )

@router.get("/onedrive/status")
async def get_onedrive_status(
    current_user: User = Depends(get_current_active_user)
):
    """Check if OneDrive is configured"""
    from app.config import settings

    configured = all([
        settings.microsoft_client_id,
        settings.microsoft_client_secret,
        settings.microsoft_tenant_id,
        settings.microsoft_client_id != "your_microsoft_client_id"
    ])

    return {
        "configured": configured,
        "root_folder": settings.onedrive_root_folder,
        "client_id_set": bool(settings.microsoft_client_id and settings.microsoft_client_id != "your_microsoft_client_id"),
        "secret_set": bool(settings.microsoft_client_secret and settings.microsoft_client_secret != "your_microsoft_client_secret"),
        "tenant_set": bool(settings.microsoft_tenant_id and settings.microsoft_tenant_id != "your_microsoft_tenant_id")
    }

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
        "onedrive": {
            "configured": bool(
                settings.microsoft_client_id and
                settings.microsoft_client_id != "your_microsoft_client_id"
            ),
            "root_folder": settings.onedrive_root_folder
        },
        "llm": {
            "provider": "anthropic",
            "model": settings.anthropic_model
        }
    }
