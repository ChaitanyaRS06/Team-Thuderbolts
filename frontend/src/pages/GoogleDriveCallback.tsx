import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { CheckCircle, AlertCircle, Cloud } from 'lucide-react';

export default function GoogleDriveCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('');

  useEffect(() => {
    handleOAuthCallback();
  }, []);

  const handleOAuthCallback = async () => {
    try {
      const code = searchParams.get('code');
      const state = searchParams.get('state');
      const error = searchParams.get('error');

      // Handle OAuth error
      if (error) {
        setStatus('error');
        setMessage(`Authorization failed: ${error}`);
        setTimeout(() => navigate('/settings'), 3000);
        return;
      }

      // Validate required parameters
      if (!code || !state) {
        setStatus('error');
        setMessage('Missing authorization code or state');
        setTimeout(() => navigate('/settings'), 3000);
        return;
      }

      // Verify state matches
      const storedState = localStorage.getItem('oauth_state');
      if (state !== storedState) {
        setStatus('error');
        setMessage('Invalid state token - possible security issue');
        setTimeout(() => navigate('/settings'), 3000);
        return;
      }

      // Clear stored state
      localStorage.removeItem('oauth_state');

      // Exchange code for tokens
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/google-drive/oauth/callback?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setStatus('success');
        setMessage(`Google Drive connected successfully! Account: ${data.user_email || 'Unknown'}`);
        setTimeout(() => navigate('/settings'), 2000);
      } else {
        setStatus('error');
        setMessage(data.detail || 'Failed to complete authorization');
        setTimeout(() => navigate('/settings'), 3000);
      }
    } catch (error) {
      setStatus('error');
      setMessage('Network error: ' + (error as Error).message);
      setTimeout(() => navigate('/settings'), 3000);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8">
        <div className="flex flex-col items-center">
          <Cloud className="w-16 h-16 text-uva-blue mb-4" />

          {status === 'loading' && (
            <>
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-uva-blue mb-4"></div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Connecting Google Drive</h2>
              <p className="text-gray-600 text-center">Please wait while we complete the authorization...</p>
            </>
          )}

          {status === 'success' && (
            <>
              <CheckCircle className="w-16 h-16 text-green-600 mb-4" />
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Success!</h2>
              <p className="text-gray-600 text-center">{message}</p>
              <p className="text-sm text-gray-500 mt-4">Redirecting to settings...</p>
            </>
          )}

          {status === 'error' && (
            <>
              <AlertCircle className="w-16 h-16 text-red-600 mb-4" />
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Authorization Failed</h2>
              <p className="text-red-600 text-center">{message}</p>
              <p className="text-sm text-gray-500 mt-4">Redirecting to settings...</p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
