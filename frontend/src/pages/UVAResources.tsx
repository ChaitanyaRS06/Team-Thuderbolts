import { useState } from 'react';
import { Search, Building2, ExternalLink, Loader } from 'lucide-react';
import { uvaAPI } from '../lib/api';

interface UVAResource {
  id: number;
  url: string;
  title: string;
  content: string;
  resource_type: string;
  relevance_score: number;
}

export default function UVAResourcesPage() {
  const [query, setQuery] = useState('');
  const [resourceType, setResourceType] = useState('it_guide');
  const [results, setResults] = useState<UVAResource[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) return;

    setLoading(true);
    try {
      const data = await uvaAPI.search(query, resourceType);
      setResults(data);
      setSearched(true);
    } catch (err) {
      console.error('Search failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const resourceTypes = [
    { value: 'it_guide', label: 'IT Guides' },
    { value: 'onedrive_guide', label: 'OneDrive' },
    { value: 'vpn_guide', label: 'VPN' },
    { value: 'security_policy', label: 'Security' },
    { value: 'authentication_guide', label: 'NetBadge' },
  ];

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">UVA Resources</h1>
        <p className="text-gray-600">
          Search UVA IT resources, guides, and policies
        </p>
      </div>

      {/* Search Interface */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Resource Type
            </label>
            <div className="flex flex-wrap gap-2">
              {resourceTypes.map((type) => (
                <button
                  key={type.value}
                  onClick={() => setResourceType(type.value)}
                  className={`px-4 py-2 rounded-lg border transition-all ${
                    resourceType === type.value
                      ? 'bg-uva-orange text-white border-uva-orange'
                      : 'bg-white text-gray-700 border-gray-300 hover:border-uva-orange'
                  }`}
                >
                  {type.label}
                </button>
              ))}
            </div>
          </div>

          <div className="flex space-x-4">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="e.g., How do I set up OneDrive on my Mac?"
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-uva-orange focus:border-transparent"
            />
            <button
              onClick={handleSearch}
              disabled={loading || !query.trim()}
              className="bg-uva-orange hover:bg-orange-600 text-white px-6 py-3 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              {loading ? (
                <Loader className="w-5 h-5 animate-spin" />
              ) : (
                <Search className="w-5 h-5" />
              )}
              <span>Search</span>
            </button>
          </div>
        </div>
      </div>

      {/* Results */}
      {loading && (
        <div className="text-center py-12">
          <Loader className="w-12 h-12 text-uva-orange animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Searching UVA resources...</p>
        </div>
      )}

      {!loading && searched && results.length === 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
          <Building2 className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No results found</h3>
          <p className="text-gray-500">Try a different search query or resource type</p>
        </div>
      )}

      {!loading && results.length > 0 && (
        <div className="space-y-4">
          {results.map((resource) => (
            <div
              key={resource.id}
              className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <Building2 className="w-5 h-5 text-uva-orange" />
                    <h3 className="text-lg font-semibold text-gray-900">
                      {resource.title}
                    </h3>
                  </div>
                  <span className="inline-block px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full">
                    {resource.resource_type.replace('_', ' ')}
                  </span>
                </div>
                <div className="text-right">
                  <div className="text-sm text-gray-500">Relevance</div>
                  <div className="text-lg font-semibold text-uva-orange">
                    {(resource.relevance_score * 100).toFixed(0)}%
                  </div>
                </div>
              </div>

              <p className="text-gray-700 mb-4 line-clamp-3">{resource.content}</p>

              <a
                href={resource.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center space-x-2 text-uva-orange hover:text-orange-600 font-medium"
              >
                <span>View full article</span>
                <ExternalLink className="w-4 h-4" />
              </a>
            </div>
          ))}
        </div>
      )}

      {/* Info Box */}
      {!searched && (
        <div className="bg-blue-50 rounded-xl p-6">
          <h3 className="font-semibold text-blue-900 mb-3">About UVA Resources</h3>
          <p className="text-blue-800 mb-4">
            Search through indexed UVA IT resources including guides, policies, and FAQs.
            The AI assistant uses semantic search to find the most relevant information.
          </p>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• OneDrive setup and usage guides</li>
            <li>• VPN configuration instructions</li>
            <li>• NetBadge authentication help</li>
            <li>• Security policies and best practices</li>
          </ul>
        </div>
      )}
    </div>
  );
}
