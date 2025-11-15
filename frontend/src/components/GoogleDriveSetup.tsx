import React, { useState, useEffect } from 'react';
import {
  Cloud,
  CheckCircle,
  AlertCircle,
  ExternalLink,
  ChevronDown,
  ChevronRight,
  Link as LinkIcon,
  XCircle,
} from 'lucide-react';

interface GoogleDriveSetupProps {
  onConfigured?: () => void;
}

const adminSteps = [
  {
    title: 'Create Google Cloud Project (Admin Only)',
    content: `Admin needs to set up OAuth 2.0 credentials in Google Cloud Console:

1. Go to Google Cloud Console: https://console.cloud.google.com
2. Click "Select a project" at the top > "New Project"
3. Enter project name: "UVA Research Assistant"
4. Click "Create" and wait for the project to be created`,
  },
  {
    title: 'Enable Google Drive API (Admin Only)',
    content: `Enable the Google Drive API for your project:

1. In Google Cloud Console, go to "APIs & Services" > "Library"
2. Search for "Google Drive API"
3. Click on "Google Drive API" and click "Enable"
4. Wait for the API to be enabled`,
  },
  {
    title: 'Create OAuth 2.0 Credentials (Admin Only)',
    content: `Create OAuth 2.0 credentials for user authorization:

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. If prompted, configure OAuth consent screen first:
   - User Type: External (or Internal if G Suite)
   - App name: "UVA Research Assistant"
   - Support email: your email
   - Scopes: Add Google Drive API scope
   - Test users: Add your email for testing
4. For Application type, select "Web application"
5. Enter name: "UVA Research Assistant Web"
6. Add Authorized redirect URI: http://localhost:5173/settings/google-drive/callback
7. Click "Create"
8. Copy the Client ID and Client Secret`,
  },
  {
    title: 'Configure Backend (Admin Only)',
    content: `Add the OAuth credentials to your backend .env file:

1. Open the backend/.env file
2. Add the following lines:
   GOOGLE_DRIVE_CLIENT_ID=your_client_id_here
   GOOGLE_DRIVE_CLIENT_SECRET=your_client_secret_here
3. Save the file
4. Restart the backend: docker-compose restart backend`,
  },
];

export default function GoogleDriveSetup({ onConfigured }: GoogleDriveSetupProps) {
  const [expandedStep, setExpandedStep] = useState<number | null>(null);
  const [status, setStatus] = useState<any>(null);
  const [oauthStatus, setOauthStatus] = useState<any>(null);
  const [connecting, setConnecting] = useState(false);
  const [testing, setTesting] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [testResult, setTestResult] = useState<any>(null);

  useEffect(() => {
    checkGoogleDriveStatus();
    checkOAuthStatus();
  }, []);

  const checkGoogleDriveStatus = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/settings/google-drive/status', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setStatus(data);
      }
    } catch (error) {
      console.error('Failed to check Google Drive status:', error);
    }
  };

  const checkOAuthStatus = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/google-drive/oauth/status', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setOauthStatus(data);
      }
    } catch (error) {
      console.error('Failed to check OAuth status:', error);
    }
  };

  const handleConnectGoogleDrive = async () => {
    setConnecting(true);
    setError('');
    setSuccess('');

    try {
      const token = localStorage.getItem('token');
      const redirectUri = `${window.location.origin}/settings/google-drive/callback`;

      const response = await fetch(`http://localhost:8000/google-drive/oauth/authorize?redirect_uri=${encodeURIComponent(redirectUri)}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      const data = await response.json();

      if (response.ok && data.auth_url) {
        // Store state for verification
        localStorage.setItem('oauth_state', data.state);
        // Redirect to Google OAuth
        window.location.href = data.auth_url;
      } else {
        setError(data.detail || 'Failed to start OAuth flow');
      }
    } catch (error) {
      setError('Network error: ' + (error as Error).message);
    } finally {
      setConnecting(false);
    }
  };

  const handleDisconnect = async () => {
    if (!confirm('Are you sure you want to disconnect Google Drive? Uploaded files will remain in Google Drive.')) {
      return;
    }

    setDisconnecting(true);
    setError('');
    setSuccess('');

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/google-drive/oauth/disconnect', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      const data = await response.json();

      if (response.ok) {
        setSuccess('Google Drive disconnected successfully');
        await checkGoogleDriveStatus();
        await checkOAuthStatus();
        if (onConfigured) {
          onConfigured();
        }
      } else {
        setError(data.detail || 'Failed to disconnect Google Drive');
      }
    } catch (error) {
      setError('Network error: ' + (error as Error).message);
    } finally {
      setDisconnecting(false);
    }
  };

  const handleTestConnection = async () => {
    setTesting(true);
    setTestResult(null);
    setError('');

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/google-drive/oauth/test', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      const data = await response.json();
      setTestResult(data);

      if (data.success) {
        setSuccess('Connection test successful! ' + data.message);
      } else {
        setError('Connection test failed: ' + data.error);
      }
    } catch (error) {
      setError('Connection test error: ' + (error as Error).message);
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Cloud className="w-8 h-8 text-uva-blue" />
          <h2 className="text-2xl font-bold text-gray-900">Google Drive Integration (OAuth 2.0)</h2>
        </div>
        {oauthStatus && (
          <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
            oauthStatus.connected
              ? 'bg-green-100 text-green-800'
              : 'bg-yellow-100 text-yellow-800'
          }`}>
            {oauthStatus.connected ? (
              <><CheckCircle className="w-4 h-4 mr-1" /> Connected</>
            ) : (
              <><AlertCircle className="w-4 h-4 mr-1" /> Not Connected</>
            )}
          </span>
        )}
      </div>

      {/* Success/Error Messages */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex justify-between items-start">
            <div className="flex">
              <AlertCircle className="w-5 h-5 text-red-600 mr-2" />
              <p className="text-red-800">{error}</p>
            </div>
            <button onClick={() => setError('')} className="text-red-600 hover:text-red-800">×</button>
          </div>
        </div>
      )}

      {success && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex justify-between items-start">
            <div className="flex">
              <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
              <p className="text-green-800">{success}</p>
            </div>
            <button onClick={() => setSuccess('')} className="text-green-600 hover:text-green-800">×</button>
          </div>
        </div>
      )}

      {/* OAuth Not Configured Warning */}
      {status && status.requires_setup && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex">
            <AlertCircle className="w-5 h-5 text-yellow-600 mr-2 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-yellow-800">
              <strong>Setup Required:</strong> Google Drive OAuth is not configured.
              An administrator needs to set up OAuth 2.0 credentials in Google Cloud Console
              and add them to the backend .env file. See "Admin Setup Instructions" below.
            </div>
          </div>
        </div>
      )}

      {/* User Connection Status */}
      {status && !status.requires_setup && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Your Google Drive Connection</h3>

          {oauthStatus?.connected ? (
            <div className="space-y-4">
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-center">
                  <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
                  <div>
                    <p className="text-green-800 font-medium">Google Drive Connected</p>
                    {oauthStatus.user_email && (
                      <p className="text-green-700 text-sm">Account: {oauthStatus.user_email}</p>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex space-x-3">
                <button
                  onClick={handleTestConnection}
                  disabled={testing}
                  className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {testing ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Testing...
                    </>
                  ) : (
                    <>
                      <CheckCircle className="w-4 h-4 mr-2" />
                      Test Connection
                    </>
                  )}
                </button>

                <button
                  onClick={handleDisconnect}
                  disabled={disconnecting}
                  className="flex items-center px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {disconnecting ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Disconnecting...
                    </>
                  ) : (
                    <>
                      <XCircle className="w-4 h-4 mr-2" />
                      Disconnect
                    </>
                  )}
                </button>
              </div>

              {testResult && testResult.success && (
                <div className="mt-4 bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="flex">
                    <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
                    <div className="text-sm text-green-800">
                      <strong>Connection Successful!</strong>
                      {testResult.user_email && (
                        <p className="mt-1">Google Account: {testResult.user_email}</p>
                      )}
                      {testResult.user_name && (
                        <p>Name: {testResult.user_name}</p>
                      )}
                      {testResult.storage_used && testResult.storage_limit && (
                        <p>Storage Used: {(parseInt(testResult.storage_used) / 1024 / 1024 / 1024).toFixed(2)} GB / {(parseInt(testResult.storage_limit) / 1024 / 1024 / 1024).toFixed(2)} GB</p>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-4">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex">
                  <AlertCircle className="w-5 h-5 text-blue-600 mr-2" />
                  <div className="text-sm text-blue-800">
                    <p><strong>Ready to Connect:</strong> Click the button below to authorize this application to access your Google Drive.</p>
                    <p className="mt-2">Your files will be organized in a folder called "{status.root_folder}" in your Google Drive.</p>
                  </div>
                </div>
              </div>

              <button
                onClick={handleConnectGoogleDrive}
                disabled={connecting}
                className="flex items-center px-6 py-3 bg-uva-blue text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-lg font-medium"
              >
                {connecting ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                    Connecting...
                  </>
                ) : (
                  <>
                    <LinkIcon className="w-5 h-5 mr-2" />
                    Connect Google Drive
                  </>
                )}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Admin Setup Instructions */}
      <div className="bg-white border border-gray-200 rounded-lg">
        <div className="p-4 border-b border-gray-200">
          <h3 className="font-semibold text-gray-900">Admin Setup Instructions (One-Time)</h3>
          <p className="text-sm text-gray-600 mt-1">
            These steps only need to be completed once by a system administrator
          </p>
        </div>
        <div className="divide-y divide-gray-200">
          {adminSteps.map((step, index) => (
            <div key={index}>
              <button
                onClick={() => setExpandedStep(expandedStep === index ? null : index)}
                className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center space-x-3">
                  <span className="flex items-center justify-center w-6 h-6 rounded-full bg-uva-blue text-white text-sm font-medium">
                    {index + 1}
                  </span>
                  <span className="font-medium text-gray-900">{step.title}</span>
                </div>
                {expandedStep === index ? (
                  <ChevronDown className="w-5 h-5 text-gray-400" />
                ) : (
                  <ChevronRight className="w-5 h-5 text-gray-400" />
                )}
              </button>
              {expandedStep === index && (
                <div className="px-4 py-3 bg-gray-50">
                  <pre className="whitespace-pre-wrap text-sm text-gray-700 font-mono">
                    {step.content}
                  </pre>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Help Link */}
      <div className="flex justify-end">
        <a
          href="https://console.cloud.google.com"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
        >
          Open Google Cloud Console
          <ExternalLink className="w-4 h-4 ml-2" />
        </a>
      </div>
    </div>
  );
}
