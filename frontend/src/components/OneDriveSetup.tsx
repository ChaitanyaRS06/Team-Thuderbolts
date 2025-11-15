import React, { useState, useEffect } from 'react';
import {
  Cloud,
  CheckCircle,
  AlertCircle,
  ExternalLink,
  ChevronDown,
  ChevronRight,
} from 'lucide-react';

interface OneDriveSetupProps {
  onConfigured?: () => void;
}

const steps = [
  {
    title: 'Register Application in Azure Portal',
    content: `To integrate OneDrive, you need to create an app registration in Azure:

1. Go to Azure Portal: https://portal.azure.com
2. Navigate to "Azure Active Directory" > "App registrations"
3. Click "New registration"
4. Enter a name (e.g., "UVA Research Assistant")
5. Select "Accounts in this organizational directory only"
6. Click "Register"`,
  },
  {
    title: 'Configure API Permissions',
    content: `Add the required Microsoft Graph permissions:

1. In your app registration, go to "API permissions"
2. Click "Add a permission" > "Microsoft Graph" > "Delegated permissions"
3. Add these permissions:
   - Files.ReadWrite.All
   - User.Read
4. Click "Grant admin consent" (requires admin privileges)`,
  },
  {
    title: 'Create Client Secret',
    content: `Generate a client secret for authentication:

1. Go to "Certificates & secrets"
2. Click "New client secret"
3. Add a description (e.g., "UVA Research Assistant Key")
4. Select expiration period (recommend 24 months)
5. Click "Add"
6. IMPORTANT: Copy the secret value immediately (you won't be able to see it again!)`,
  },
  {
    title: 'Get Application Details',
    content: `Collect the required information:

1. Go to the "Overview" page of your app registration
2. Copy the following values:
   - Application (client) ID
   - Directory (tenant) ID
   - Client Secret (from previous step)`,
  },
];

export default function OneDriveSetup({ onConfigured }: OneDriveSetupProps) {
  const [expandedStep, setExpandedStep] = useState<number | null>(0);
  const [status, setStatus] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [testResult, setTestResult] = useState<any>(null);

  const [formData, setFormData] = useState({
    microsoft_client_id: '',
    microsoft_client_secret: '',
    microsoft_tenant_id: '',
    onedrive_root_folder: 'UVA_Research_Assistant',
  });

  useEffect(() => {
    checkOneDriveStatus();
  }, []);

  const checkOneDriveStatus = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/settings/onedrive/status', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setStatus(data);
      }
    } catch (error) {
      console.error('Failed to check OneDrive status:', error);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/settings/onedrive/configure', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (response.ok) {
        setSuccess(data.message + ' ' + data.note);
        await checkOneDriveStatus();
        if (onConfigured) {
          onConfigured();
        }
      } else {
        setError(data.detail || 'Failed to configure OneDrive');
      }
    } catch (error) {
      setError('Network error: ' + (error as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const handleTestConnection = async () => {
    setTesting(true);
    setTestResult(null);
    setError('');

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/settings/onedrive/test', {
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
          <h2 className="text-2xl font-bold text-gray-900">OneDrive Integration Setup</h2>
        </div>
        {status && (
          <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
            status.configured
              ? 'bg-green-100 text-green-800'
              : 'bg-yellow-100 text-yellow-800'
          }`}>
            {status.configured ? (
              <><CheckCircle className="w-4 h-4 mr-1" /> Configured</>
            ) : (
              <><AlertCircle className="w-4 h-4 mr-1" /> Not Configured</>
            )}
          </span>
        )}
      </div>

      {/* Success/Error Messages */}
      {status?.configured && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex">
            <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
            <p className="text-green-800">
              OneDrive is already configured! Documents will be automatically synced to:{' '}
              <strong>{status.root_folder}</strong>
            </p>
          </div>
        </div>
      )}

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

      {/* Setup Steps */}
      <div className="bg-white border border-gray-200 rounded-lg">
        <div className="p-4 border-b border-gray-200">
          <h3 className="font-semibold text-gray-900">Setup Instructions</h3>
        </div>
        <div className="divide-y divide-gray-200">
          {steps.map((step, index) => (
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

      {/* Credential Form */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Enter Your Credentials</h3>
        <p className="text-sm text-gray-600 mb-6">
          After following the steps above, enter your Microsoft Azure credentials below.
          These will be securely stored in your server configuration.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Application (Client) ID
            </label>
            <input
              type="text"
              name="microsoft_client_id"
              value={formData.microsoft_client_id}
              onChange={handleInputChange}
              required
              placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-uva-blue"
            />
            <p className="mt-1 text-xs text-gray-500">Found in Azure Portal → App Registration → Overview</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Directory (Tenant) ID
            </label>
            <input
              type="text"
              name="microsoft_tenant_id"
              value={formData.microsoft_tenant_id}
              onChange={handleInputChange}
              required
              placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-uva-blue"
            />
            <p className="mt-1 text-xs text-gray-500">Found in Azure Portal → App Registration → Overview</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Client Secret
            </label>
            <input
              type="password"
              name="microsoft_client_secret"
              value={formData.microsoft_client_secret}
              onChange={handleInputChange}
              required
              placeholder="Your client secret value"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-uva-blue"
            />
            <p className="mt-1 text-xs text-gray-500">Created in Azure Portal → Certificates & secrets</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              OneDrive Root Folder
            </label>
            <input
              type="text"
              name="onedrive_root_folder"
              value={formData.onedrive_root_folder}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-uva-blue"
            />
            <p className="mt-1 text-xs text-gray-500">Folder name where documents will be stored in OneDrive</p>
          </div>

          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex">
              <AlertCircle className="w-5 h-5 text-yellow-600 mr-2 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-yellow-800">
                <strong>Important:</strong> After saving, you'll need to restart the backend application for changes to take effect.
                <br />
                Run: <code className="bg-yellow-100 px-1 py-0.5 rounded">docker-compose restart backend</code>
              </div>
            </div>
          </div>

          <div className="flex space-x-3">
            <button
              type="submit"
              disabled={loading}
              className="flex items-center px-4 py-2 bg-uva-blue text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Saving...
                </>
              ) : (
                <>
                  <Cloud className="w-4 h-4 mr-2" />
                  Save Configuration
                </>
              )}
            </button>

            <a
              href="https://portal.azure.com"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
            >
              Open Azure Portal
              <ExternalLink className="w-4 h-4 ml-2" />
            </a>
          </div>
        </form>

        {/* Test Connection Section */}
        {status?.configured && (
          <div className="mt-6 pt-6 border-t border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Test Your Connection</h3>
            <p className="text-sm text-gray-600 mb-4">
              Verify that your OneDrive configuration is working correctly.
            </p>
            <button
              onClick={handleTestConnection}
              disabled={testing}
              className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {testing ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Testing Connection...
                </>
              ) : (
                <>
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Test Connection
                </>
              )}
            </button>

            {testResult && testResult.success && (
              <div className="mt-4 bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex">
                  <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
                  <div className="text-sm text-green-800">
                    <strong>Connection Successful!</strong>
                    {testResult.drive_type && (
                      <p className="mt-1">Drive Type: {testResult.drive_type}</p>
                    )}
                    {testResult.owner && (
                      <p>Owner: {testResult.owner}</p>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
