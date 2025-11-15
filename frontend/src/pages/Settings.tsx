import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Settings as SettingsIcon } from 'lucide-react';
import GoogleDriveSetup from '../components/GoogleDriveSetup';
import GitHubSetup from '../components/GitHubSetup';
import EmbeddingSettings from '../components/EmbeddingSettings';

export default function Settings() {
  const [searchParams, setSearchParams] = useSearchParams();
  const tabFromUrl = searchParams.get('tab') as 'google-drive' | 'github' | 'embedding' | 'system' | null;
  const [currentTab, setCurrentTab] = useState<'google-drive' | 'github' | 'embedding' | 'system'>(
    tabFromUrl || 'google-drive'
  );
  const [systemInfo, setSystemInfo] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (tabFromUrl) {
      setCurrentTab(tabFromUrl);
    }
  }, [tabFromUrl]);

  useEffect(() => {
    fetchSystemInfo();
  }, []);

  const fetchSystemInfo = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/settings/system/info', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setSystemInfo(data);
      }
    } catch (error) {
      console.error('Failed to fetch system info:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-uva-blue"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center space-x-3 mb-6">
          <SettingsIcon className="w-8 h-8 text-uva-blue" />
          <h1 className="text-3xl font-bold text-gray-900">System Settings</h1>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-lg shadow-sm mb-6">
          <div className="border-b border-gray-200">
            <nav className="flex -mb-px">
              <button
                onClick={() => setCurrentTab('google-drive')}
                className={`py-4 px-6 border-b-2 font-medium text-sm ${
                  currentTab === 'google-drive'
                    ? 'border-uva-blue text-uva-blue'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Google Drive Integration
              </button>
              <button
                onClick={() => setCurrentTab('github')}
                className={`py-4 px-6 border-b-2 font-medium text-sm ${
                  currentTab === 'github'
                    ? 'border-uva-blue text-uva-blue'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                GitHub Integration
              </button>
              <button
                onClick={() => setCurrentTab('embedding')}
                className={`py-4 px-6 border-b-2 font-medium text-sm ${
                  currentTab === 'embedding'
                    ? 'border-uva-blue text-uva-blue'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Embedding Settings
              </button>
              <button
                onClick={() => setCurrentTab('system')}
                className={`py-4 px-6 border-b-2 font-medium text-sm ${
                  currentTab === 'system'
                    ? 'border-uva-blue text-uva-blue'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                System Info
              </button>
            </nav>
          </div>

          <div className="p-6">
            {currentTab === 'google-drive' && <GoogleDriveSetup onConfigured={fetchSystemInfo} />}
            {currentTab === 'github' && <GitHubSetup onConfigured={fetchSystemInfo} />}
            {currentTab === 'embedding' && <EmbeddingSettings onConfigured={fetchSystemInfo} />}
            {currentTab === 'system' && systemInfo && (
              <div className="space-y-4">
                <h2 className="text-xl font-semibold mb-4">Current Configuration</h2>

                <div className="bg-blue-50 border-l-4 border-blue-400 p-4">
                  <h3 className="font-medium text-blue-900">Embedding Provider</h3>
                  <p className="text-blue-700">
                    {systemInfo.embedding.provider} - {systemInfo.embedding.model}
                  </p>
                </div>

                <div className={`border-l-4 p-4 ${
                  systemInfo.google_drive.configured
                    ? 'bg-green-50 border-green-400'
                    : 'bg-yellow-50 border-yellow-400'
                }`}>
                  <h3 className={`font-medium ${
                    systemInfo.google_drive.configured ? 'text-green-900' : 'text-yellow-900'
                  }`}>
                    Google Drive Integration
                  </h3>
                  <p className={systemInfo.google_drive.configured ? 'text-green-700' : 'text-yellow-700'}>
                    Status: {systemInfo.google_drive.configured ? 'Configured' : 'Not Configured'}
                    {systemInfo.google_drive.configured && ` - Root Folder: ${systemInfo.google_drive.root_folder}`}
                  </p>
                </div>

                <div className="bg-blue-50 border-l-4 border-blue-400 p-4">
                  <h3 className="font-medium text-blue-900">LLM Provider</h3>
                  <p className="text-blue-700">
                    {systemInfo.llm.provider} - {systemInfo.llm.model}
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
