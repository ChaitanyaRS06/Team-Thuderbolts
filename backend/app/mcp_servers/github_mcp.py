# backend/app/mcp_servers/github_mcp.py
"""
GitHub MCP (Model Context Protocol) Server
Handles GitHub API operations using OAuth 2.0
"""
import requests
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
import logging

from app.config import settings
from app.models import GitHubToken

logger = logging.getLogger(__name__)

class GitHubMCPServer:
    """
    MCP Server for GitHub integration
    Provides tools for repository access, issues, pull requests, and code search
    """

    def __init__(self, user_id: int, db: Session):
        """
        Initialize GitHub MCP Server with user OAuth token

        Args:
            user_id: Database ID of the user
            db: Database session
        """
        self.user_id = user_id
        self.db = db
        self.base_url = "https://api.github.com"
        self.access_token = None

        try:
            self._initialize_token()
        except Exception as e:
            logger.error(f"Failed to initialize GitHub token for user {user_id}: {e}")

    def _initialize_token(self):
        """Get user's OAuth token from database"""
        token_record = self.db.query(GitHubToken).filter(
            GitHubToken.user_id == self.user_id
        ).first()

        if token_record:
            self.access_token = token_record.access_token
            logger.info(f"GitHub token loaded for user {self.user_id}")
        else:
            logger.warning(f"No GitHub token found for user {self.user_id}")

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for GitHub API requests"""
        if not self.access_token:
            raise Exception("GitHub not connected. Please authorize access first.")

        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    async def get_user_info(self) -> Dict[str, Any]:
        """Get authenticated user's GitHub profile"""
        try:
            response = requests.get(
                f"{self.base_url}/user",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            raise

    async def list_repositories(self, per_page: int = 30, page: int = 1) -> List[Dict[str, Any]]:
        """List user's repositories"""
        try:
            response = requests.get(
                f"{self.base_url}/user/repos",
                headers=self._get_headers(),
                params={
                    "per_page": per_page,
                    "page": page,
                    "sort": "updated",
                    "direction": "desc"
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error listing repositories: {e}")
            raise

    async def get_repository(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get details of a specific repository"""
        try:
            response = requests.get(
                f"{self.base_url}/repos/{owner}/{repo}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting repository: {e}")
            raise

    async def get_repository_contents(
        self,
        owner: str,
        repo: str,
        path: str = ""
    ) -> List[Dict[str, Any]]:
        """Get contents of a repository path"""
        try:
            response = requests.get(
                f"{self.base_url}/repos/{owner}/{repo}/contents/{path}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting repository contents: {e}")
            raise

    async def get_file_content(
        self,
        owner: str,
        repo: str,
        path: str
    ) -> Dict[str, Any]:
        """Get content of a specific file"""
        try:
            response = requests.get(
                f"{self.base_url}/repos/{owner}/{repo}/contents/{path}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting file content: {e}")
            raise

    async def search_code(
        self,
        query: str,
        per_page: int = 30,
        page: int = 1
    ) -> Dict[str, Any]:
        """Search code across GitHub"""
        try:
            response = requests.get(
                f"{self.base_url}/search/code",
                headers=self._get_headers(),
                params={
                    "q": query,
                    "per_page": per_page,
                    "page": page
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error searching code: {e}")
            raise

    async def list_issues(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        per_page: int = 30,
        page: int = 1
    ) -> List[Dict[str, Any]]:
        """List issues for a repository"""
        try:
            response = requests.get(
                f"{self.base_url}/repos/{owner}/{repo}/issues",
                headers=self._get_headers(),
                params={
                    "state": state,
                    "per_page": per_page,
                    "page": page
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error listing issues: {e}")
            raise

    async def list_pull_requests(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        per_page: int = 30,
        page: int = 1
    ) -> List[Dict[str, Any]]:
        """List pull requests for a repository"""
        try:
            response = requests.get(
                f"{self.base_url}/repos/{owner}/{repo}/pulls",
                headers=self._get_headers(),
                params={
                    "state": state,
                    "per_page": per_page,
                    "page": page
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error listing pull requests: {e}")
            raise

    async def get_readme(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get repository README"""
        try:
            response = requests.get(
                f"{self.base_url}/repos/{owner}/{repo}/readme",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting README: {e}")
            raise

    async def test_connection(self) -> Dict[str, Any]:
        """Test GitHub API connection"""
        if not self.access_token:
            return {
                "success": False,
                "error": "GitHub not connected. Please authorize access first."
            }

        try:
            user_info = await self.get_user_info()

            return {
                "success": True,
                "message": "GitHub connection successful",
                "username": user_info.get("login"),
                "name": user_info.get("name"),
                "email": user_info.get("email"),
                "public_repos": user_info.get("public_repos"),
                "private_repos": user_info.get("total_private_repos"),
                "followers": user_info.get("followers"),
                "following": user_info.get("following")
            }

        except Exception as e:
            logger.error(f"GitHub connection test failed for user {self.user_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_tools(self) -> list:
        """
        Return MCP tool definitions for GitHub operations
        This follows the Model Context Protocol specification
        """
        return [
            {
                "name": "github_list_repos",
                "description": "List user's GitHub repositories",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "per_page": {"type": "integer", "description": "Results per page", "default": 30},
                        "page": {"type": "integer", "description": "Page number", "default": 1}
                    }
                }
            },
            {
                "name": "github_get_repo",
                "description": "Get details of a specific repository",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string", "description": "Repository owner"},
                        "repo": {"type": "string", "description": "Repository name"}
                    },
                    "required": ["owner", "repo"]
                }
            },
            {
                "name": "github_search_code",
                "description": "Search code across GitHub repositories",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "per_page": {"type": "integer", "description": "Results per page", "default": 30}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "github_get_file",
                "description": "Get content of a specific file",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string", "description": "Repository owner"},
                        "repo": {"type": "string", "description": "Repository name"},
                        "path": {"type": "string", "description": "File path"}
                    },
                    "required": ["owner", "repo", "path"]
                }
            },
            {
                "name": "github_list_issues",
                "description": "List issues for a repository",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string", "description": "Repository owner"},
                        "repo": {"type": "string", "description": "Repository name"},
                        "state": {"type": "string", "description": "Issue state: open, closed, all", "default": "open"}
                    },
                    "required": ["owner", "repo"]
                }
            }
        ]

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an MCP tool"""
        if tool_name == "github_list_repos":
            repos = await self.list_repositories(**arguments)
            return {"success": True, "repositories": repos}
        elif tool_name == "github_get_repo":
            repo = await self.get_repository(**arguments)
            return {"success": True, "repository": repo}
        elif tool_name == "github_search_code":
            results = await self.search_code(**arguments)
            return {"success": True, "results": results}
        elif tool_name == "github_get_file":
            file_content = await self.get_file_content(**arguments)
            return {"success": True, "file": file_content}
        elif tool_name == "github_list_issues":
            issues = await self.list_issues(**arguments)
            return {"success": True, "issues": issues}
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
