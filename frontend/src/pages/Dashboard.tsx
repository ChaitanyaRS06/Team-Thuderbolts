import { useState } from 'react';
import { Routes, Route, Link, useNavigate, useLocation } from 'react-router-dom';
import { User } from '../lib/api';
import {
  GraduationCap,
  Upload,
  MessageSquare,
  FileText,
  LogOut,
  Settings,
  HelpCircle,
  Cloud
} from 'lucide-react';
import UploadPage from './Upload';
import AssistantPage from './Assistant';
import DocumentsPage from './Documents';
import UVAResourcesPage from './UVAResources';
import SettingsPage from './Settings';

interface DashboardProps {
  user: User;
  onLogout: () => void;
}

export default function Dashboard({ user, onLogout }: DashboardProps) {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    { path: '/dashboard/assistant', icon: MessageSquare, label: 'Ask Questions' },
    { path: '/dashboard/upload', icon: Upload, label: 'Upload Documents' },
    { path: '/dashboard/documents', icon: FileText, label: 'My Documents' },
    { path: '/dashboard/uva-resources', icon: HelpCircle, label: 'UVA Resources' },
    { path: '/dashboard/settings', icon: Settings, label: 'Settings' },
  ];

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <div className="w-64 bg-uva-blue text-white flex flex-col">
        <div className="p-6 border-b border-blue-800">
          <div className="flex items-center space-x-3 mb-4">
            <div className="w-10 h-10 bg-uva-orange rounded-full flex items-center justify-center">
              <GraduationCap className="w-6 h-6" />
            </div>
            <div>
              <h2 className="font-semibold">UVA Research</h2>
              <p className="text-xs text-blue-200">Assistant</p>
            </div>
          </div>
          <div className="text-sm text-blue-200">
            <p className="font-medium text-white">{user.full_name}</p>
            <p className="text-xs">{user.email}</p>
          </div>
        </div>

        <nav className="flex-1 p-4">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center space-x-3 px-4 py-3 rounded-lg mb-2 transition-colors ${
                  isActive
                    ? 'bg-uva-orange text-white'
                    : 'text-blue-200 hover:bg-blue-800 hover:text-white'
                }`}
              >
                <Icon className="w-5 h-5" />
                <span>{item.label}</span>
              </Link>
            );
          })}

          {/* Google Drive Connect Button */}
          <div className="mt-4 pt-4 border-t border-blue-800">
            <Link
              to="/dashboard/settings"
              className="flex items-center space-x-3 px-4 py-3 rounded-lg mb-2 bg-green-600 hover:bg-green-700 text-white transition-colors"
            >
              <Cloud className="w-5 h-5" />
              <span>Connect Google Drive</span>
            </Link>
          </div>
        </nav>

        <div className="p-4 border-t border-blue-800">
          <button
            onClick={onLogout}
            className="flex items-center space-x-3 px-4 py-3 rounded-lg w-full text-blue-200 hover:bg-blue-800 hover:text-white transition-colors"
          >
            <LogOut className="w-5 h-5" />
            <span>Logout</span>
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto">
        <Routes>
          <Route path="/" element={<AssistantPage />} />
          <Route path="/assistant" element={<AssistantPage />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/documents" element={<DocumentsPage />} />
          <Route path="/uva-resources" element={<UVAResourcesPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </div>
    </div>
  );
}
