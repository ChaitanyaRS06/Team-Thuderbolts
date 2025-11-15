# GitHub OAuth Setup Guide

This guide will help you set up GitHub OAuth integration for the UVA Research Assistant.

## Overview

GitHub OAuth allows users to connect their GitHub accounts to access repositories, search code, view issues, pull requests, and more through the MCP (Model Context Protocol) server.

## Prerequisites

- GitHub account (admin rights not required for using the integration)
- Access to GitHub Developer Settings (for initial OAuth app setup)
- Backend and frontend servers running

## Step 1: Create GitHub OAuth App (One-Time Setup)

1. **Go to GitHub Developer Settings**
   - Visit: https://github.com/settings/developers
   - Or navigate: GitHub Settings → Developer settings → OAuth Apps

2. **Create New OAuth App**
   - Click **"New OAuth App"** button
   - Fill in the application details:
     - **Application name**: `UVA Research Assistant` (or your preferred name)
     - **Homepage URL**: `http://localhost:5174`
     - **Application description**: `AI Research Assistant for UVA with GitHub integration`
     - **Authorization callback URL**: `http://localhost:5174/settings/github/callback`

3. **Register the Application**
   - Click **"Register application"**
   - You'll be redirected to your new OAuth app page

4. **Get Client Credentials**
   - Copy the **Client ID** (displayed on the page)
   - Click **"Generate a new client secret"**
   - Copy the **Client Secret** immediately (you won't be able to see it again)

## Step 2: Configure Backend Environment

1. **Open Backend .env File**
   ```bash
   cd backend
   nano .env
   # Or use your preferred editor
   ```

2. **Add GitHub Credentials**
   Update these lines in your `.env` file:
   ```env
   GITHUB_CLIENT_ID=your_client_id_here
   GITHUB_CLIENT_SECRET=your_client_secret_here
   ```

3. **Save the File**

## Step 3: Restart Backend

The backend needs to be restarted to load the new environment variables:

```bash
# From project root directory
docker-compose restart backend

# Or if you need a full restart
docker-compose down
docker-compose up -d
```

## Step 4: Connect Your GitHub Account

1. **Navigate to Settings**
   - Log in to the application
   - Go to **Dashboard → Settings**
   - Click the **"GitHub Integration"** tab

2. **Authorize GitHub**
   - Click **"Connect GitHub"** button
   - You'll be redirected to GitHub OAuth authorization page
   - Review the permissions requested:
     - **repo**: Access to repositories (read/write)
     - **read:user**: Read user profile information
     - **read:org**: Read organization information
   - Click **"Authorize application"**

3. **Verify Connection**
   - You'll be redirected back to Settings
   - Status should show: **"Connected"** with your GitHub username
   - Click **"Test Connection"** to verify the integration works

## Step 5: Test the Integration

After connecting, you can test the GitHub MCP server capabilities:

1. **Test Connection**
   - In Settings → GitHub Integration
   - Click **"Test Connection"** button
   - Should show your GitHub username, name, and repository counts

2. **Use GitHub Features** (in Chat/RAG)
   - List your repositories
   - Search code across GitHub
   - View file contents
   - Check issues and pull requests
   - Access repository READMEs

## OAuth Scopes Explained

The application requests the following GitHub OAuth scopes:

| Scope | Permission | Why Needed |
|-------|------------|------------|
| `repo` | Full repository access | To read repository contents, files, and metadata |
| `read:user` | Read user profile | To display your GitHub username and basic info |
| `read:org` | Read organization info | To access organization repositories you have access to |

## Troubleshooting

### "OAuth not configured" Error

**Problem**: Backend returns "GitHub OAuth is not configured"

**Solution**:
- Verify `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` are set in `backend/.env`
- Ensure backend was restarted after adding credentials
- Check for typos in the credentials

### "State mismatch" Error

**Problem**: OAuth callback fails with "State mismatch - possible CSRF attack"

**Solution**:
- This is a security check to prevent CSRF attacks
- Clear browser local storage and try again
- Make sure you're using the same browser session

### Connection Test Fails

**Problem**: Test connection shows error or fails

**Solution**:
- Verify your GitHub token is still valid (check Settings → GitHub → Status)
- Try disconnecting and reconnecting your GitHub account
- Check if GitHub API is accessible (https://api.github.com)

### Redirect URI Mismatch

**Problem**: GitHub shows "The redirect_uri MUST match the registered callback URL"

**Solution**:
- Verify callback URL in GitHub OAuth app settings exactly matches: `http://localhost:5174/settings/github/callback`
- No trailing slash
- Correct port number (5174, not 5173 or 8000)

## Security Notes

1. **Client Secret Protection**
   - Never commit `GITHUB_CLIENT_SECRET` to version control
   - Keep your `.env` file private
   - Rotate the secret if it's accidentally exposed

2. **User Token Storage**
   - User OAuth tokens are stored encrypted in the database
   - Each user has their own GitHub connection
   - Tokens are used only for that user's requests

3. **OAuth State Token**
   - Random state tokens prevent CSRF attacks
   - States are verified during the callback
   - Expired or invalid states are rejected

## Production Deployment

When deploying to production:

1. **Update OAuth App Settings**
   - Homepage URL: `https://your-domain.com`
   - Callback URL: `https://your-domain.com/settings/github/callback`

2. **Update Environment Variables**
   - Set production URLs in `ALLOWED_ORIGINS`
   - Use the same OAuth app or create a separate production app

3. **Enable HTTPS**
   - GitHub OAuth requires HTTPS in production
   - Use SSL/TLS certificates

## MCP Server Features

Once connected, the GitHub MCP server provides:

### Repository Operations
- **list_repositories**: List all accessible repositories
- **get_repository**: Get details about a specific repository
- **get_readme**: Fetch repository README content

### Code Operations
- **search_code**: Search code across GitHub
- **get_file_content**: Read file contents from repositories

### Project Management
- **list_issues**: View repository issues
- **list_pull_requests**: View pull requests

### Example Usage in Chat

```
User: "Search my GitHub repos for authentication code"
Assistant: *Uses GitHub MCP to search code*

User: "Show me open issues in my main project"
Assistant: *Uses GitHub MCP to list issues*

User: "What's in the README of my research-assistant repo?"
Assistant: *Uses GitHub MCP to fetch README*
```

## Support

If you encounter issues not covered in this guide:

1. Check backend logs: `docker-compose logs backend`
2. Check frontend console for errors (Browser DevTools)
3. Verify all environment variables are set correctly
4. Ensure database migrations are up to date

## References

- [GitHub OAuth Documentation](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps)
- [GitHub API Documentation](https://docs.github.com/en/rest)
- [OAuth 2.0 Specification](https://oauth.net/2/)
