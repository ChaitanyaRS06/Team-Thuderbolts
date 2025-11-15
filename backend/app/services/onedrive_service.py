# backend/app/services/onedrive_service.py
"""
OneDrive Service - Wrapper around OneDrive MCP Server
"""
from app.mcp_servers.onedrive_mcp import OneDriveMCPServer
from typing import Dict, Any

class OneDriveService:
    """Service layer for OneDrive operations"""

    def __init__(self):
        self.mcp_server = OneDriveMCPServer()

    async def upload_file(
        self,
        file_path: str,
        filename: str,
        folder: str,
        user_email: str
    ) -> str:
        """Upload a file to OneDrive"""
        return await self.mcp_server.upload_file(
            file_path=file_path,
            filename=filename,
            folder=folder,
            user_email=user_email
        )

    async def list_files(self, folder_path: str) -> list:
        """List files in OneDrive folder"""
        return await self.mcp_server.list_files(folder_path)

    async def download_file(self, onedrive_path: str, local_path: str) -> bool:
        """Download file from OneDrive"""
        return await self.mcp_server.download_file(onedrive_path, local_path)
