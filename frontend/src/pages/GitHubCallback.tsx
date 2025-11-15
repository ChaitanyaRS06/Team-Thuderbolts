import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Github, CheckCircle, AlertCircle, Loader } from 'lucide-react';

export default function GitHubCallback() {
  const navigate = useNavigate();
  const location = useLocation();
  const [status, setStatus] = useState<'processing' | 'success' | 'error'>('processing');
  const [message, setMessage] = useState('Connecting to GitHub...');
  const [error, setError] = useState('');

  useEffect(() => {
    const handleCallback = async () => {
      const params = new URLSearchParams(location.search);
      const code = params.get('code');
      const state = params.get('state');
      const error = params.get('error');

      // Check for OAuth errors
      if (error) {
        setStatus('error');
        setError(`GitHub authorization failed: ${error}`);
        setMessage('Authorization Failed');
        setTimeout(() => navigate('/settings?tab=github'), 3000);
        return;
      }

      // Verify we have required parameters
      if (!code || !state) {
        setStatus('error');
        setError('Missing authorization code or state');
        setMessage('Invalid Callback');
        setTimeout(() => navigate('/settings?tab=github'), 3000);
        return;
      }

      // Verify state matches what we stored
      const storedState = localStorage.getItem('github_oauth_state');
      if (state !== storedState) {
        setStatus('error');
        setError('State mismatch - possible CSRF attack');
        setMessage('Security Error');
        setTimeout(() => navigate('/settings?tab=github'), 3000);
        return;
      }

      // Remove stored state
      localStorage.removeItem('github_oauth_state');

      try {
        setMessage('Exchanging authorization code for tokens...');

        // Exchange code for tokens
        const token = localStorage.getItem('token');
        const response = await fetch(
          `http://localhost:8000/github/oauth/callback?code=${code}&state=${state}`,
          {
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          }
        );

        const data = await response.json();

        if (response.ok && data.success) {
          setStatus('success');
          setMessage(`Successfully connected to GitHub as @${data.username || 'user'}!`);

          // Redirect to settings page after 2 seconds
          setTimeout(() => {
            navigate('/settings?tab=github');
          }, 2000);
        } else {
          setStatus('error');
          setError(data.detail || 'Failed to complete GitHub authorization');
          setMessage('Connection Failed');
          setTimeout(() => navigate('/settings?tab=github'), 3000);
        }
      } catch (err) {
        setStatus('error');
        setError('Network error: ' + (err as Error).message);
        setMessage('Connection Error');
        setTimeout(() => navigate('/settings?tab=github'), 3000);
      }
    };

    handleCallback();
  }, [location, navigate]);

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full">
        <div className="flex flex-col items-center text-center">
          <div className="mb-6">
            {status === 'processing' && (
              <div className="relative">
                <Github className="w-16 h-16 text-gray-900" />
                <Loader className="w-8 h-8 text-blue-600 absolute -bottom-2 -right-2 animate-spin" />
              </div>
            )}
            {status === 'success' && (
              <div className="relative">
                <Github className="w-16 h-16 text-gray-900" />
                <CheckCircle className="w-8 h-8 text-green-600 absolute -bottom-2 -right-2" />
              </div>
            )}
            {status === 'error' && (
              <div className="relative">
                <Github className="w-16 h-16 text-gray-900" />
                <AlertCircle className="w-8 h-8 text-red-600 absolute -bottom-2 -right-2" />
              </div>
            )}
          </div>

          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            {message}
          </h2>

          {status === 'processing' && (
            <p className="text-gray-600 mb-6">
              Please wait while we complete your GitHub authorization...
            </p>
          )}

          {status === 'success' && (
            <div className="text-green-600 mb-6">
              <p className="font-medium">GitHub connected successfully!</p>
              <p className="text-sm text-gray-600 mt-2">Redirecting to settings...</p>
            </div>
          )}

          {status === 'error' && (
            <div className="text-red-600 mb-6">
              <p className="font-medium">Failed to connect GitHub</p>
              {error && (
                <p className="text-sm text-red-700 mt-2 bg-red-50 p-3 rounded-md">
                  {error}
                </p>
              )}
              <p className="text-sm text-gray-600 mt-2">Redirecting back to settings...</p>
            </div>
          )}

          {status === 'processing' && (
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div className="bg-blue-600 h-2 rounded-full animate-pulse" style={{ width: '60%' }}></div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
