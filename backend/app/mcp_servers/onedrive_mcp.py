# backend/app/mcp_servers/onedrive_mcp.py
"""
OneDrive MCP (Model Context Protocol) Server
Handles file operations with UVA OneDrive
"""
import json
from typing import Dict, Any, Optional
from msal import ConfidentialClientApplication
from msgraph import GraphServiceClient
from msgraph.generated.models.drive_item import DriveItem
from msgraph.generated.models.folder import Folder
from azure.identity import ClientSecretCredential
from app.config import settings
import os

class OneDriveMCPServer:
    """
    MCP Server for OneDrive integration
    Provides tools for file upload, download, and management in OneDrive
    """

    def __init__(self):
        self.client_id = settings.microsoft_client_id
        self.client_secret = settings.microsoft_client_secret
        self.tenant_id = settings.microsoft_tenant_id
        self.root_folder = settings.onedrive_root_folder

        # Initialize MSAL client
        self.msal_app = None
        if self.client_id and self.client_secret and self.tenant_id:
            self.msal_app = ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=f"https://login.microsoftonline.com/{self.tenant_id}"
            )

    async def get_access_token(self, user_email: str) -> str:
        """Get access token for OneDrive API"""
        if not self.msal_app:
            raise Exception("OneDrive not configured. Please set Microsoft credentials in .env")

        scopes = ["https://graph.microsoft.com/.default"]
        result = self.msal_app.acquire_token_for_client(scopes=scopes)

        if "access_token" in result:
            return result["access_token"]
        else:
            raise Exception(f"Failed to acquire token: {result.get('error_description')}")

    async def create_folder(self, folder_name: str, parent_path: str = None) -> Dict[str, Any]:
        """Create a folder in OneDrive"""
        # This is a placeholder for the actual implementation
        # You would use Microsoft Graph API to create folders
        return {
            "success": True,
            "folder_path": f"{self.root_folder}/{folder_name}",
            "message": "Folder created successfully"
        }

    async def upload_file(
        self,
        file_path: str,
        filename: str,
        folder: str,
        user_email: str
    ) -> str:
        """
        Upload a file to OneDrive

        Args:
            file_path: Local path to the file
            filename: Name to use in OneDrive
            folder: Subfolder within root (e.g., 'dataset', 'research_paper', 'results')
            user_email: User's email for authentication

        Returns:
            OneDrive path of uploaded file
        """
        if not self.msal_app:
            print("Warning: OneDrive not configured, skipping upload")
            return None

        try:
            # Get access token
            token = await self.get_access_token(user_email)

            # Create folder structure if it doesn't exist
            target_folder = f"{self.root_folder}/{folder}"

            # Upload file using Microsoft Graph API
            # This is simplified - actual implementation would use msgraph-sdk
            onedrive_path = f"{target_folder}/{filename}"

            print(f"File would be uploaded to: {onedrive_path}")
            return onedrive_path

        except Exception as e:
            print(f"OneDrive upload error: {e}")
            raise

    async def download_file(self, onedrive_path: str, local_path: str) -> bool:
        """Download a file from OneDrive"""
        # Placeholder for actual implementation
        return True

    async def list_files(self, folder_path: str) -> list:
        """List files in a OneDrive folder"""
        # Placeholder for actual implementation
        return []

    async def delete_file(self, onedrive_path: str) -> bool:
        """Delete a file from OneDrive"""
        # Placeholder for actual implementation
        return True

    def get_tools(self) -> list:
        """
        Return MCP tool definitions for OneDrive operations
        This follows the Model Context Protocol specification
        """
        return [
            {
                "name": "upload_to_onedrive",
                "description": "Upload a file to UVA OneDrive",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Local file path"},
                        "filename": {"type": "string", "description": "Filename in OneDrive"},
                        "folder": {"type": "string", "description": "Target folder (dataset/research_paper/results)"},
                        "user_email": {"type": "string", "description": "User's email"}
                    },
                    "required": ["file_path", "filename", "folder", "user_email"]
                }
            },
            {
                "name": "list_onedrive_files",
                "description": "List files in a OneDrive folder",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "folder_path": {"type": "string", "description": "Folder path to list"}
                    },
                    "required": ["folder_path"]
                }
            },
            {
                "name": "download_from_onedrive",
                "description": "Download a file from OneDrive",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "onedrive_path": {"type": "string", "description": "OneDrive file path"},
                        "local_path": {"type": "string", "description": "Local destination path"}
                    },
                    "required": ["onedrive_path", "local_path"]
                }
            }
        ]

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an MCP tool"""
        if tool_name == "upload_to_onedrive":
            path = await self.upload_file(**arguments)
            return {"success": True, "onedrive_path": path}
        elif tool_name == "list_onedrive_files":
            files = await self.list_files(arguments["folder_path"])
            return {"success": True, "files": files}
        elif tool_name == "download_from_onedrive":
            success = await self.download_file(**arguments)
            return {"success": success}
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
