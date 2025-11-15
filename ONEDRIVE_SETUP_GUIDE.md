# OneDrive Integration Setup Guide

## Overview
The UVA Research Assistant now includes full OneDrive integration, allowing you to automatically sync all uploaded documents to your institutional OneDrive account. This guide will walk you through the complete setup process.

## Features

✅ **Automatic Document Sync** - All uploaded PDFs are automatically stored in OneDrive
✅ **Azure AD Integration** - Secure authentication using Microsoft Azure Active Directory
✅ **Organized Storage** - Documents organized by type (dataset, research_paper, results, etc.)
✅ **Connection Testing** - Built-in tool to verify your OneDrive connection
✅ **Seamless Experience** - Works transparently in the background

## Prerequisites

Before setting up OneDrive integration, you need:

1. **Microsoft 365 Account** - A UVA institutional account with OneDrive access
2. **Azure Portal Access** - Ability to create app registrations (may require admin privileges)
3. **Administrator Role** - Admin access in the UVA Research Assistant application

## Step-by-Step Setup

### Part 1: Azure App Registration

#### Step 1: Access Azure Portal
1. Navigate to [Azure Portal](https://portal.azure.com)
2. Sign in with your UVA institutional account
3. From the left sidebar, click **Azure Active Directory**

#### Step 2: Create App Registration
1. In Azure AD, navigate to **App registrations**
2. Click **+ New registration**
3. Fill in the registration form:
   - **Name**: `UVA Research Assistant` (or any descriptive name)
   - **Supported account types**: Select **Accounts in this organizational directory only**
   - **Redirect URI**: Leave blank for now
4. Click **Register**

#### Step 3: Note Your Application IDs
After registration, you'll see the **Overview** page. Copy these values:
- **Application (client) ID**: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
- **Directory (tenant) ID**: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

Keep these safe - you'll need them later!

#### Step 4: Create Client Secret
1. In your app registration, click **Certificates & secrets** in the left menu
2. Under **Client secrets**, click **+ New client secret**
3. Enter a description: `UVA Research Assistant Key`
4. Select expiration: Recommended **24 months**
5. Click **Add**
6. **CRITICAL**: Copy the **Value** immediately! You won't be able to see it again
   - Format: `xxx~xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

#### Step 5: Configure API Permissions
1. Click **API permissions** in the left menu
2. Click **+ Add a permission**
3. Select **Microsoft Graph**
4. Choose **Application permissions** (not Delegated)
5. Search for and add these permissions:
   - `Files.ReadWrite.All`
   - `User.Read.All`
6. Click **Add permissions**
7. **Important**: Click **Grant admin consent for [Your Organization]**
   - This requires admin privileges
   - If you don't have admin rights, contact your IT department

### Part 2: Configure UVA Research Assistant

#### Step 1: Access Settings Page
1. Log in to the UVA Research Assistant dashboard
2. Navigate to **Settings** from the left sidebar
3. Click on the **OneDrive Integration** tab

#### Step 2: Enter Credentials
You'll see a form with the following fields:

1. **Application (Client) ID**
   - Paste the Client ID from Azure Portal
   - Example: `a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6`

2. **Directory (Tenant) ID**
   - Paste the Tenant ID from Azure Portal
   - Example: `q6r7s8t9-u0v1-w2x3-y4z5-a6b7c8d9e0f1`

3. **Client Secret**
   - Paste the secret value you copied earlier
   - Format: `xxx~xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

4. **OneDrive Root Folder** (Optional)
   - Default: `UVA_Research_Assistant`
   - You can change this to any folder name
   - This folder will be created in your OneDrive root

#### Step 3: Save Configuration
1. Click **Save Configuration**
2. Wait for the confirmation message
3. **Important**: Restart the backend as instructed:
   ```bash
   docker-compose restart backend
   ```

#### Step 4: Test Connection
1. After restart, refresh the Settings page
2. You should see a **Test Your Connection** section
3. Click **Test Connection**
4. If successful, you'll see:
   - ✅ Connection Successful!
   - Drive Type: business
   - Owner: Your Name

## How It Works

### Document Upload Flow

When you upload a document through the UVA Research Assistant:

1. **Local Storage**: Document is first saved locally in `uploads/{user_id}/`
2. **Database Record**: Document metadata is saved to the database
3. **OneDrive Sync**: Document is uploaded to OneDrive in the background:
   - Path: `{OneDrive Root}/{Document Type}/{filename}`
   - Example: `UVA_Research_Assistant/research_paper/20250115_123456_paper.pdf`
4. **Reference Stored**: OneDrive path is saved in the database

### Document Types & Folders

Documents are organized by type:
- **dataset** → Research datasets
- **research_paper** → Academic papers
- **results** → Research results
- **grant** → Grant proposals
- **other** → Miscellaneous documents

### Document Deletion

When you delete a document:
1. File is removed from local storage
2. File is deleted from OneDrive (if it was synced)
3. Database record is removed

## Troubleshooting

### Common Issues

#### 1. "Authentication failed" Error
**Cause**: Invalid credentials or expired secret
**Solution**:
- Verify all three credentials are correct
- Check if the client secret has expired in Azure Portal
- Generate a new secret if needed

#### 2. "Insufficient privileges" Error
**Cause**: API permissions not granted
**Solution**:
- Ensure admin consent was granted in Azure Portal
- Check that `Files.ReadWrite.All` permission is present
- Verify the permission type is **Application** (not Delegated)

#### 3. Connection Test Fails
**Cause**: Network issues or incorrect tenant
**Solution**:
- Verify your network can reach `graph.microsoft.com`
- Double-check the Tenant ID matches your organization
- Ensure the app registration is in the correct Azure AD tenant

#### 4. Files Not Appearing in OneDrive
**Cause**: OneDrive sync delay or configuration issue
**Solution**:
- Check backend logs for upload errors:
  ```bash
  docker-compose logs backend | grep -i onedrive
  ```
- Verify OneDrive status shows "Configured" in Settings
- Run the connection test again

### Getting Help

If you encounter issues:

1. **Check Logs**:
   ```bash
   docker-compose logs backend | tail -50
   ```

2. **Verify Configuration**:
   - Go to Settings → System Info
   - Check OneDrive status

3. **Re-run Setup**:
   - You can update credentials anytime in Settings
   - After updating, always restart the backend

## Security Considerations

### Credential Storage
- Credentials are stored in the `.env` file on the server
- The `.env` file should never be committed to version control
- Ensure proper file permissions: `chmod 600 .env`

### Access Control
- Only admin users can configure OneDrive integration
- Each user's documents are isolated by user ID
- OneDrive access uses application-level permissions

### Secret Rotation
- Client secrets expire based on your configuration (max 24 months)
- Set a calendar reminder to rotate secrets before expiration
- Rotating secrets:
  1. Create new secret in Azure Portal
  2. Update in UVA Research Assistant Settings
  3. Restart backend
  4. Delete old secret from Azure Portal

## API Reference

### Backend Endpoints

#### Configure OneDrive
```
POST /settings/onedrive/configure
Authorization: Bearer {token}
Content-Type: application/json

{
  "microsoft_client_id": "xxx",
  "microsoft_client_secret": "xxx",
  "microsoft_tenant_id": "xxx",
  "onedrive_root_folder": "UVA_Research_Assistant"
}
```

#### Check Status
```
GET /settings/onedrive/status
Authorization: Bearer {token}
```

#### Test Connection
```
POST /settings/onedrive/test
Authorization: Bearer {token}
```

### MCP Server Methods

The OneDrive MCP server provides these operations:

- `upload_file()` - Upload file to OneDrive
- `download_file()` - Download file from OneDrive
- `list_files()` - List files in a folder
- `delete_file()` - Delete file from OneDrive
- `test_connection()` - Test OneDrive connection

## Advanced Configuration

### Custom Folder Structure

You can customize the OneDrive root folder name:

1. Go to Settings → OneDrive Integration
2. Change "OneDrive Root Folder" field
3. Save and restart backend

### Large File Uploads

For files larger than 4MB, the system will use Microsoft Graph upload sessions:
- Supports files up to 250GB
- Progress tracking available
- Automatic retry on failure

## Benefits of OneDrive Integration

1. **Backup & Recovery**: All documents safely stored in Microsoft cloud
2. **Accessibility**: Access your research documents from anywhere
3. **Collaboration**: Share OneDrive folders with team members
4. **Compliance**: Meets institutional data storage requirements
5. **Storage Limits**: Leverage UVA's institutional OneDrive storage quota

## Next Steps

After setting up OneDrive:

1. **Upload a Test Document** to verify the integration works
2. **Check OneDrive** to see the folder structure was created
3. **Configure Notifications** (if available) for upload success/failure
4. **Set Up Regular Backups** of the `.env` file

---

## Quick Reference Card

### Azure Portal Links
- **App Registrations**: https://portal.azure.com/#view/Microsoft_AAD_IAM/ActiveDirectoryMenuBlade/~/RegisteredApps
- **API Permissions**: App Registration → API permissions
- **Client Secrets**: App Registration → Certificates & secrets

### Required Permissions
- Application permissions (not Delegated)
- `Files.ReadWrite.All`
- `User.Read.All`
- Admin consent granted

### Configuration Values
- **Client ID**: From Azure Portal → App Registration → Overview
- **Tenant ID**: From Azure Portal → App Registration → Overview
- **Client Secret**: From Azure Portal → App Registration → Certificates & secrets
- **Root Folder**: Your choice (default: `UVA_Research_Assistant`)

---

**Last Updated**: 2025-01-15
**Version**: 1.0
**Support**: Contact your system administrator for Azure access issues
