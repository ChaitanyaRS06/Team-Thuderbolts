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

            # Initialize Graph client with access token
            credential = ClientSecretCredential(
                tenant_id=self.tenant_id,
                client_id=self.client_id,
                client_secret=self.client_secret
            )
            client = GraphServiceClient(credential)

            # Ensure folder structure exists
            folder_path = f"{self.root_folder}/{folder}"
            await self._ensure_folder_exists(client, folder_path)

            # Read file content
            with open(file_path, 'rb') as f:
                file_content = f.read()

            # Upload file to OneDrive
            # Using /me/drive/root:/{path}:/content for file upload
            upload_path = f"/me/drive/root:/{folder_path}/{filename}:/content"

            # For files larger than 4MB, use upload session
            file_size = os.path.getsize(file_path)
            if file_size > 4 * 1024 * 1024:  # 4MB
                print(f"Large file detected ({file_size} bytes), using upload session")
                # Upload session for large files would be implemented here
                # For now, we'll use the simple upload

            # Simple upload for smaller files
            import httpx
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/octet-stream"
            }

            async with httpx.AsyncClient() as http_client:
                response = await http_client.put(
                    f"https://graph.microsoft.com/v1.0{upload_path}",
                    headers=headers,
                    content=file_content,
                    timeout=300.0
                )

                if response.status_code in [200, 201]:
                    onedrive_path = f"{folder_path}/{filename}"
                    print(f"File uploaded successfully to: {onedrive_path}")
                    return onedrive_path
                else:
                    raise Exception(f"Upload failed: {response.status_code} - {response.text}")

        except Exception as e:
            print(f"OneDrive upload error: {e}")
            raise

    async def _ensure_folder_exists(self, client, folder_path: str):
        """Ensure folder structure exists in OneDrive"""
        try:
            # Split the path and create folders one by one
            parts = folder_path.strip('/').split('/')
            current_path = ""

            for part in parts:
                parent_path = current_path if current_path else "root"
                current_path = f"{current_path}/{part}" if current_path else part

                try:
                    # Try to get the folder
                    await client.me.drive.root.item_with_path(current_path).get()
                except:
                    # Folder doesn't exist, create it
                    folder_item = DriveItem()
                    folder_item.name = part
                    folder_item.folder = Folder()

                    if parent_path == "root":
                        await client.me.drive.root.children.post(folder_item)
                    else:
                        await client.me.drive.root.item_with_path(parent_path).children.post(folder_item)

                    print(f"Created folder: {current_path}")
        except Exception as e:
            print(f"Error ensuring folder exists: {e}")
            # Continue anyway - the upload might still work

    async def download_file(self, onedrive_path: str, local_path: str, user_email: str) -> bool:
        """Download a file from OneDrive"""
        if not self.msal_app:
            print("Warning: OneDrive not configured")
            return False

        try:
            token = await self.get_access_token(user_email)

            import httpx
            headers = {"Authorization": f"Bearer {token}"}

            download_url = f"https://graph.microsoft.com/v1.0/me/drive/root:/{onedrive_path}:/content"

            async with httpx.AsyncClient() as client:
                response = await client.get(download_url, headers=headers, timeout=300.0)

                if response.status_code == 200:
                    os.makedirs(os.path.dirname(local_path), exist_ok=True)
                    with open(local_path, 'wb') as f:
                        f.write(response.content)
                    print(f"File downloaded successfully to: {local_path}")
                    return True
                else:
                    print(f"Download failed: {response.status_code}")
                    return False

        except Exception as e:
            print(f"Error downloading file: {e}")
            return False

    async def list_files(self, folder_path: str, user_email: str) -> list:
        """List files in a OneDrive folder"""
        if not self.msal_app:
            return []

        try:
            token = await self.get_access_token(user_email)

            import httpx
            headers = {"Authorization": f"Bearer {token}"}

            list_url = f"https://graph.microsoft.com/v1.0/me/drive/root:/{folder_path}:/children"

            async with httpx.AsyncClient() as client:
                response = await client.get(list_url, headers=headers, timeout=60.0)

                if response.status_code == 200:
                    data = response.json()
                    files = []
                    for item in data.get('value', []):
                        files.append({
                            'name': item.get('name'),
                            'size': item.get('size'),
                            'created': item.get('createdDateTime'),
                            'modified': item.get('lastModifiedDateTime'),
                            'is_folder': 'folder' in item,
                            'id': item.get('id')
                        })
                    return files
                else:
                    print(f"List files failed: {response.status_code}")
                    return []

        except Exception as e:
            print(f"Error listing files: {e}")
            return []

    async def delete_file(self, onedrive_path: str, user_email: str) -> bool:
        """Delete a file from OneDrive"""
        if not self.msal_app:
            return False

        try:
            token = await self.get_access_token(user_email)

            import httpx
            headers = {"Authorization": f"Bearer {token}"}

            delete_url = f"https://graph.microsoft.com/v1.0/me/drive/root:/{onedrive_path}"

            async with httpx.AsyncClient() as client:
                response = await client.delete(delete_url, headers=headers, timeout=60.0)

                if response.status_code in [200, 204]:
                    print(f"File deleted successfully: {onedrive_path}")
                    return True
                else:
                    print(f"Delete failed: {response.status_code}")
                    return False

        except Exception as e:
            print(f"Error deleting file: {e}")
            return False

    async def test_connection(self, user_email: str) -> Dict[str, Any]:
        """Test OneDrive connection"""
        if not self.msal_app:
            return {
                "success": False,
                "error": "OneDrive not configured. Please set Microsoft credentials."
            }

        try:
            # Get access token
            token = await self.get_access_token(user_email)

            # Test by getting user's drive info
            import httpx
            headers = {"Authorization": f"Bearer {token}"}

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://graph.microsoft.com/v1.0/me/drive",
                    headers=headers,
                    timeout=30.0
                )

                if response.status_code == 200:
                    drive_info = response.json()
                    return {
                        "success": True,
                        "message": "OneDrive connection successful",
                        "drive_type": drive_info.get('driveType'),
                        "owner": drive_info.get('owner', {}).get('user', {}).get('displayName')
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to connect: HTTP {response.status_code}"
                    }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

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
