# backend/app/mcp_servers/google_drive_mcp.py
"""
Google Drive MCP (Model Context Protocol) Server
Handles file operations with Google Drive using OAuth 2.0
"""
import json
import os
import io
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from app.config import settings
from app.models import GoogleDriveToken
import logging

logger = logging.getLogger(__name__)

# OAuth 2.0 scopes
SCOPES = ['https://www.googleapis.com/auth/drive']

class GoogleDriveMCPServer:
    """
    MCP Server for Google Drive integration using OAuth 2.0
    Provides tools for file upload, download, and management in Google Drive
    """

    def __init__(self, user_id: int, db: Session):
        """
        Initialize Google Drive MCP Server with user OAuth tokens

        Args:
            user_id: Database ID of the user
            db: Database session
        """
        self.user_id = user_id
        self.db = db
        self.root_folder_name = settings.google_drive_root_folder
        self.service = None
        self.root_folder_id = None
        self.credentials = None

        try:
            self._initialize_service()
        except Exception as e:
            logger.error(f"Failed to initialize Google Drive service for user {user_id}: {e}")

    def _get_user_credentials(self) -> Optional[Credentials]:
        """Get user's OAuth credentials from database"""
        token_record = self.db.query(GoogleDriveToken).filter(
            GoogleDriveToken.user_id == self.user_id
        ).first()

        if not token_record:
            logger.warning(f"No Google Drive token found for user {self.user_id}")
            return None

        # Create credentials object
        credentials = Credentials(
            token=token_record.access_token,
            refresh_token=token_record.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.google_drive_client_id,
            client_secret=settings.google_drive_client_secret,
            scopes=SCOPES
        )

        # Check if token needs refresh
        if credentials.expired and credentials.refresh_token:
            try:
                from google.auth.transport.requests import Request
                credentials.refresh(Request())

                # Update token in database
                token_record.access_token = credentials.token
                token_record.token_expiry = credentials.expiry
                token_record.updated_at = datetime.utcnow()
                self.db.commit()

                logger.info(f"Refreshed access token for user {self.user_id}")
            except Exception as e:
                logger.error(f"Failed to refresh token for user {self.user_id}: {e}")
                raise

        return credentials

    def _initialize_service(self):
        """Initialize Google Drive service with user OAuth credentials"""
        try:
            if not settings.google_drive_client_id or not settings.google_drive_client_secret:
                logger.warning("Google Drive OAuth not configured (missing client_id or client_secret)")
                return

            self.credentials = self._get_user_credentials()

            if not self.credentials:
                logger.warning(f"User {self.user_id} has not authorized Google Drive access")
                return

            self.service = build('drive', 'v3', credentials=self.credentials)
            logger.info(f"Google Drive service initialized for user {self.user_id}")

        except Exception as e:
            logger.error(f"Error initializing Google Drive service: {e}")
            raise

    async def _get_or_create_root_folder(self) -> str:
        """Get or create the root folder for the application"""
        if not self.service:
            raise Exception("Google Drive not configured or user not authorized")

        if self.root_folder_id:
            return self.root_folder_id

        try:
            # Search for existing root folder
            query = f"name='{self.root_folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()

            folders = results.get('files', [])

            if folders:
                self.root_folder_id = folders[0]['id']
                logger.info(f"Found existing root folder: {self.root_folder_id} for user {self.user_id}")
            else:
                # Create new root folder
                folder_metadata = {
                    'name': self.root_folder_name,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                folder = self.service.files().create(
                    body=folder_metadata,
                    fields='id, name'
                ).execute()

                self.root_folder_id = folder.get('id')
                logger.info(f"Created root folder: {self.root_folder_id} for user {self.user_id}")

            return self.root_folder_id

        except Exception as e:
            logger.error(f"Error getting/creating root folder: {e}")
            raise

    async def _get_or_create_subfolder(self, folder_name: str, parent_id: str) -> str:
        """Get or create a subfolder within a parent folder"""
        if not self.service:
            raise Exception("Google Drive not configured")

        try:
            # Search for existing subfolder
            query = f"name='{folder_name}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()

            folders = results.get('files', [])

            if folders:
                return folders[0]['id']
            else:
                # Create new subfolder
                folder_metadata = {
                    'name': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [parent_id]
                }
                folder = self.service.files().create(
                    body=folder_metadata,
                    fields='id'
                ).execute()

                return folder.get('id')

        except Exception as e:
            logger.error(f"Error getting/creating subfolder: {e}")
            raise

    async def upload_file(
        self,
        file_path: str,
        filename: str,
        folder: str
    ) -> str:
        """
        Upload a file to Google Drive

        Args:
            file_path: Local path to the file
            filename: Name to use in Google Drive
            folder: Subfolder within root (e.g., 'dataset', 'research_paper', 'results')

        Returns:
            Google Drive file ID
        """
        if not self.service:
            logger.warning(f"Google Drive not configured for user {self.user_id}, skipping upload")
            return None

        try:
            # Get or create root folder
            root_folder_id = await self._get_or_create_root_folder()

            # Get or create subfolder
            subfolder_id = await self._get_or_create_subfolder(folder, root_folder_id)

            # Prepare file metadata
            file_metadata = {
                'name': filename,
                'parents': [subfolder_id]
            }

            # Upload file
            media = MediaFileUpload(file_path, resumable=True)
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink'
            ).execute()

            file_id = file.get('id')
            web_link = file.get('webViewLink')

            logger.info(f"File uploaded to Google Drive for user {self.user_id}: {filename} (ID: {file_id})")
            logger.info(f"View at: {web_link}")

            return file_id

        except Exception as e:
            logger.error(f"Google Drive upload error for user {self.user_id}: {e}")
            raise

    async def download_file(self, file_id: str, local_path: str) -> bool:
        """Download a file from Google Drive"""
        if not self.service:
            logger.warning("Google Drive not configured")
            return False

        try:
            request = self.service.files().get_media(fileId=file_id)

            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            fh = io.FileIO(local_path, 'wb')
            downloader = MediaIoBaseDownload(fh, request)

            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    logger.info(f"Download progress: {int(status.progress() * 100)}%")

            logger.info(f"File downloaded successfully to: {local_path}")
            return True

        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            return False

    async def list_files(self, folder: str) -> List[Dict[str, Any]]:
        """List files in a Google Drive folder"""
        if not self.service:
            return []

        try:
            # Get root folder
            root_folder_id = await self._get_or_create_root_folder()

            # Get subfolder
            subfolder_id = await self._get_or_create_subfolder(folder, root_folder_id)

            # List files in subfolder
            query = f"'{subfolder_id}' in parents and trashed=false"
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, mimeType, size, createdTime, modifiedTime, webViewLink)',
                pageSize=100
            ).execute()

            files = results.get('files', [])

            formatted_files = []
            for file in files:
                formatted_files.append({
                    'id': file.get('id'),
                    'name': file.get('name'),
                    'size': file.get('size', 0),
                    'created': file.get('createdTime'),
                    'modified': file.get('modifiedTime'),
                    'is_folder': file.get('mimeType') == 'application/vnd.google-apps.folder',
                    'web_link': file.get('webViewLink')
                })

            return formatted_files

        except Exception as e:
            logger.error(f"Error listing files: {e}")
            return []

    async def delete_file(self, file_id: str) -> bool:
        """Delete a file from Google Drive"""
        if not self.service:
            return False

        try:
            self.service.files().delete(fileId=file_id).execute()
            logger.info(f"File deleted successfully: {file_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return False

    async def test_connection(self) -> Dict[str, Any]:
        """Test Google Drive connection"""
        if not self.service:
            return {
                "success": False,
                "error": "Google Drive not configured or user not authorized. Please authorize access first."
            }

        try:
            # Try to get user info / about
            about = self.service.about().get(fields='user, storageQuota').execute()

            user = about.get('user', {})
            quota = about.get('storageQuota', {})

            logger.info(f"Google Drive connection test successful for user {self.user_id}")

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
            logger.error(f"Google Drive connection test failed for user {self.user_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_tools(self) -> list:
        """
        Return MCP tool definitions for Google Drive operations
        This follows the Model Context Protocol specification
        """
        return [
            {
                "name": "upload_to_google_drive",
                "description": "Upload a file to Google Drive",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Local file path"},
                        "filename": {"type": "string", "description": "Filename in Google Drive"},
                        "folder": {"type": "string", "description": "Target folder (dataset/research_paper/results)"}
                    },
                    "required": ["file_path", "filename", "folder"]
                }
            },
            {
                "name": "list_google_drive_files",
                "description": "List files in a Google Drive folder",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "folder": {"type": "string", "description": "Folder name to list"}
                    },
                    "required": ["folder"]
                }
            },
            {
                "name": "download_from_google_drive",
                "description": "Download a file from Google Drive",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "file_id": {"type": "string", "description": "Google Drive file ID"},
                        "local_path": {"type": "string", "description": "Local destination path"}
                    },
                    "required": ["file_id", "local_path"]
                }
            }
        ]

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an MCP tool"""
        if tool_name == "upload_to_google_drive":
            file_id = await self.upload_file(**arguments)
            return {"success": True, "file_id": file_id}
        elif tool_name == "list_google_drive_files":
            files = await self.list_files(arguments["folder"])
            return {"success": True, "files": files}
        elif tool_name == "download_from_google_drive":
            success = await self.download_file(arguments["file_id"], arguments["local_path"])
            return {"success": success}
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
