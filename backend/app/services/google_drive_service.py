# backend/app/services/google_drive_service.py
"""
Google Drive Service - Wrapper around Google Drive MCP Server
"""
from app.mcp_servers.google_drive_mcp import GoogleDriveMCPServer
from sqlalchemy.orm import Session
from typing import Dict, Any

class GoogleDriveService:
    """Service layer for Google Drive operations using OAuth 2.0"""

    def __init__(self, user_id: int, db: Session):
        """
        Initialize Google Drive service for a specific user

        Args:
            user_id: Database ID of the user
            db: Database session
        """
        self.mcp_server = GoogleDriveMCPServer(user_id=user_id, db=db)

    async def upload_file(
        self,
        file_path: str,
        filename: str,
        folder: str
    ) -> str:
        """Upload a file to Google Drive"""
        return await self.mcp_server.upload_file(
            file_path=file_path,
            filename=filename,
            folder=folder
        )

    async def list_files(self, folder: str) -> list:
        """List files in Google Drive folder"""
        return await self.mcp_server.list_files(folder)

    async def download_file(self, file_id: str, local_path: str) -> bool:
        """Download file from Google Drive"""
        return await self.mcp_server.download_file(file_id, local_path)
