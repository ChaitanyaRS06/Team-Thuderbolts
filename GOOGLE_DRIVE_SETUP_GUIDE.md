# Google Drive Integration Setup Guide

## Overview
The UVA Research Assistant now includes full Google Drive integration, allowing you to automatically sync all uploaded documents to your Google Drive account. This guide will walk you through the complete setup process.

## Features

✅ **Automatic Document Sync** - All uploaded PDFs are automatically stored in Google Drive
✅ **Service Account Authentication** - Secure server-to-server authentication
✅ **Organized Storage** - Documents organized by type (dataset, research_paper, results, etc.)
✅ **Connection Testing** - Built-in tool to verify your Google Drive connection
✅ **Seamless Experience** - Works transparently in the background

## Prerequisites

Before setting up Google Drive integration, you need:

1. **Google Account** - Any Google account with Drive access
2. **Google Cloud Console Access** - Ability to create projects and service accounts
3. **Administrator Role** - Admin access in the UVA Research Assistant application

## Step-by-Step Setup

### Part 1: Google Cloud Console Setup

#### Step 1: Create Google Cloud Project
1. Navigate to [Google Cloud Console](https://console.cloud.google.com)
2. Sign in with your Google account
3. Click **"Select a project"** dropdown at the top
4. Click **"New Project"**
5. Enter project name: `UVA Research Assistant` (or any descriptive name)
6. (Optional) Select an organization if you have one
7. Click **"Create"**
8. Wait for the project to be created (usually takes a few seconds)

#### Step 2: Enable Google Drive API
1. Make sure your new project is selected in the dropdown at the top
2. Go to **"APIs & Services"** > **"Library"** (from left sidebar)
3. Search for **"Google Drive API"**
4. Click on **"Google Drive API"** in the results
5. Click the **"Enable"** button
6. Wait for the API to be enabled

#### Step 3: Create Service Account
1. Go to **"APIs & Services"** > **"Credentials"**
2. Click **"Create Credentials"** button at the top
3. Select **"Service Account"**
4. Fill in the service account details:
   - **Service account name**: `uva-research-assistant`
   - **Service account ID**: (auto-generated, you can modify if desired)
   - **Service account description**: `Service account for UVA Research Assistant`
5. Click **"Create and Continue"**
6. **Optional**: Skip adding roles (or add "Basic > Editor" if you want broader access)
7. Click **"Continue"**
8. **Optional**: Skip granting user access
9. Click **"Done"**

#### Step 4: Generate Service Account Key (JSON)
1. In the **"Credentials"** page, you should now see your service account listed
2. Click on the **service account email** (e.g., `uva-research-assistant@your-project.iam.gserviceaccount.com`)
3. Go to the **"Keys"** tab
4. Click **"Add Key"** > **"Create new key"**
5. Select **"JSON"** as the key type
6. Click **"Create"**
7. A JSON file will download automatically to your computer
8. **IMPORTANT**: Keep this file secure! It grants access to Google Drive

#### Step 5: Share Drive Access (Optional but Recommended)
If you want to view the uploaded files in your personal Drive:

1. Go to [Google Drive](https://drive.google.com)
2. Find or create the folder where you want files stored (e.g., "UVA_Research_Assistant")
3. Right-click the folder > **"Share"**
4. Add your service account email (from Step 3)
5. Give it **"Editor"** permission
6. Click **"Share"**

### Part 2: Configure UVA Research Assistant

#### Step 1: Access Settings Page
1. Log in to the UVA Research Assistant dashboard
2. Click on **"Connect Google Drive"** button in the left sidebar OR
3. Navigate to **Settings** > **Google Drive Integration** tab

#### Step 2: Upload Service Account Key
1. You'll see a form with a file upload area
2. Click **"Upload a file"** or drag and drop the JSON key file you downloaded
3. The system will validate it's a proper JSON file
4. Set the **"Google Drive Root Folder"** name (default: `UVA_Research_Assistant`)
   - This folder will be created in the service account's drive
   - You can change this to any folder name you prefer

#### Step 3: Save Configuration
1. Click **"Save Configuration"**
2. Wait for the confirmation message
3. **Important**: Restart the backend as instructed:
   ```bash
   docker-compose restart backend
   ```

#### Step 4: Test Connection
1. After restart, refresh the Settings page
2. You should see a **"Test Your Connection"** section
3. Click **"Test Connection"**
4. If successful, you'll see:
   - ✅ Connection Successful!
   - Service Account email
   - Storage usage information

## How It Works

### Document Upload Flow

When you upload a document through the UVA Research Assistant:

1. **Local Storage**: Document is first saved locally in `uploads/{user_id}/`
2. **Database Record**: Document metadata is saved to the database
3. **Google Drive Sync**: Document is uploaded to Google Drive in the background:
   - Path: `{Root Folder}/{Document Type}/{filename}`
   - Example: `UVA_Research_Assistant/research_paper/20250115_123456_paper.pdf`
4. **File ID Stored**: Google Drive file ID is saved in the database

### Document Types & Folders

Documents are organized by type:
- **dataset** → Research datasets
- **research_paper** → Academic papers
- **results** → Research results
- **other** → Miscellaneous documents

### Document Deletion

When you delete a document:
1. File is removed from local storage
2. File is deleted from Google Drive
3. Database record is removed

## Troubleshooting

### Common Issues

#### 1. "Invalid JSON file" Error
**Cause**: The uploaded file is not a valid JSON key file
**Solution**:
- Ensure you downloaded the JSON format (not P12)
- Re-download the key from Google Cloud Console
- Don't modify the JSON file manually

#### 2. "Connection test failed" Error
**Cause**: Service account doesn't have proper permissions
**Solution**:
- Verify the Google Drive API is enabled
- Ensure the service account key is not expired or revoked
- Check that the JSON file is complete and unmodified

#### 3. Files Not Appearing in Personal Drive
**Cause**: Service account has its own Drive space
**Solution**:
- Service account files are stored in the service account's Drive
- To see them in your personal Drive, share specific folders with the service account (see Step 5 in Part 1)
- Or access files programmatically using the file IDs stored in the database

#### 4. Upload Fails Silently
**Cause**: Insufficient permissions or quota exceeded
**Solution**:
- Check backend logs:
  ```bash
  docker-compose logs backend | grep -i "google\|drive"
  ```
- Verify Google Cloud project has not exceeded quota
- Ensure billing is enabled on the Google Cloud project (if required)

#### 5. "Backend restart required" but it's still not working
**Cause**: Configuration not fully loaded
**Solution**:
- Do a full restart instead:
  ```bash
  docker-compose down
  docker-compose up -d
  ```
- Check logs for any startup errors

### Getting Help

If you encounter issues:

1. **Check Logs**:
   ```bash
   docker-compose logs backend | tail -50
   ```

2. **Verify Configuration**:
   - Go to Settings → System Info
   - Check Google Drive status

3. **Re-run Setup**:
   - You can update credentials anytime in Settings
   - After updating, always restart the backend

## Security Considerations

### Credential Storage
- Service account key is stored in the `.env` file on the server
- The `.env` file should never be committed to version control
- Ensure proper file permissions: `chmod 600 .env`

### Access Control
- Only admin users can configure Google Drive integration
- Each user's documents are isolated by user ID
- Service account has limited scope (only Drive access)

### Key Rotation
- Service account keys don't expire by default, but you can rotate them
- Rotating keys:
  1. Create new key in Google Cloud Console
  2. Update in UVA Research Assistant Settings
  3. Restart backend
  4. Delete old key from Google Cloud Console

## API Reference

### Backend Endpoints

#### Configure Google Drive
```
POST /settings/google-drive/configure
Authorization: Bearer {token}
Content-Type: application/json

{
  "google_drive_credentials_json": "{...}",
  "google_drive_root_folder": "UVA_Research_Assistant"
}
```

#### Check Status
```
GET /settings/google-drive/status
Authorization: Bearer {token}
```

#### Test Connection
```
POST /settings/google-drive/test
Authorization: Bearer {token}
```

### MCP Server Methods

The Google Drive MCP server provides these operations:

- `upload_file()` - Upload file to Google Drive
- `download_file()` - Download file from Google Drive
- `list_files()` - List files in a folder
- `delete_file()` - Delete file from Google Drive
- `test_connection()` - Test Google Drive connection

## Advanced Configuration

### Custom Folder Structure

You can customize the Google Drive root folder name:

1. Go to Settings → Google Drive Integration
2. Change "Google Drive Root Folder" field
3. Save and restart backend

### Large File Uploads

The system supports files of any size:
- Uses Google Drive API resumable upload
- Automatic retry on failure
- Progress tracking available

### Accessing Files via Google Drive Web

To access uploaded files in Google Drive web interface:

1. Option A: Share the service account's root folder with your personal account
2. Option B: Use the file ID stored in the database to construct a direct link:
   ```
   https://drive.google.com/file/d/{file_id}/view
   ```

## Benefits of Google Drive Integration

1. **Unlimited Storage**: Leverage Google Drive's generous storage limits
2. **Accessibility**: Access your research documents from anywhere
3. **Collaboration**: Share Drive folders with team members
4. **Backup & Recovery**: All documents safely stored in Google cloud
5. **Version History**: Google Drive maintains version history automatically
6. **Search**: Use Google Drive's powerful search across all documents

## Cost Considerations

### Free Tier
- Google Drive API: **Free** for most use cases
- First 15 GB of storage per account: **Free**
- Service account usage: **Free**

### Paid Features (Optional)
- If you need more than 15 GB: Google One subscription
- If you need higher API quotas: Contact Google Cloud support

## Next Steps

After setting up Google Drive:

1. **Upload a Test Document** to verify the integration works
2. **Check Google Drive** to see the folder structure was created
3. **Configure Backup** of the service account JSON key
4. **Set Up Monitoring** (optional) for upload success/failure

## Comparison: Google Drive vs OneDrive

| Feature | Google Drive | OneDrive (Previous) |
|---------|-------------|---------------------|
| **Setup Complexity** | Easy (one JSON file) | Complex (3 credentials, admin consent) |
| **Authentication** | Service Account | OAuth 2.0 |
| **Organization Required** | No | Yes (Azure AD tenant) |
| **Institutional Account** | Optional | Required |
| **API Quotas** | Generous | More restrictive |
| **Storage Limit** | 15 GB free (expandable) | Depends on institution |
| **Personal Access** | Via sharing | Automatic (if using personal OneDrive) |

---

## Quick Reference Card

### Google Cloud Console Links
- **Cloud Console Home**: https://console.cloud.google.com
- **APIs & Services**: https://console.cloud.google.com/apis
- **Credentials**: https://console.cloud.google.com/apis/credentials
- **Drive API Library**: https://console.cloud.google.com/apis/library/drive.googleapis.com

### Required Permissions
- Google Drive API enabled
- Service account created
- JSON key file generated

### Configuration Values
- **Service Account JSON**: Downloaded from Google Cloud Console
- **Root Folder**: Your choice (default: `UVA_Research_Assistant`)

### Testing
After configuration:
1. Navigate to Settings → Google Drive Integration
2. Click "Test Connection"
3. Should see service account email and storage info

---

**Last Updated**: 2025-01-15
**Version**: 1.0
**Support**: Check application logs or Google Cloud Console for issues
