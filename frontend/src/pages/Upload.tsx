import { useState } from 'react';
import { Upload as UploadIcon, FileText, CheckCircle, AlertCircle } from 'lucide-react';
import { documentsAPI, embeddingsAPI } from '../lib/api';

export default function UploadPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [documentType, setDocumentType] = useState<string>('research_paper');
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setSuccess('');
      setError('');
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a file');
      return;
    }

    setUploading(true);
    setError('');
    setSuccess('');

    try {
      // Upload document
      const doc = await documentsAPI.upload(selectedFile, documentType);
      setSuccess(`File uploaded successfully! Processing...`);

      // Process document
      setProcessing(true);
      await documentsAPI.process(doc.id);

      // Generate embeddings
      await embeddingsAPI.generate(doc.id);

      setSuccess(
        `Success! "${selectedFile.name}" has been uploaded, processed, and is ready for search.`
      );
      setSelectedFile(null);
      // Reset file input
      const fileInput = document.getElementById('file-input') as HTMLInputElement;
      if (fileInput) fileInput.value = '';
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
      setProcessing(false);
    }
  };

  const documentTypes = [
    { value: 'dataset', label: 'Dataset', description: 'Research data files' },
    { value: 'research_paper', label: 'Research Paper', description: 'Published papers, articles' },
    { value: 'results', label: 'Results', description: 'Experimental results' },
    { value: 'other', label: 'Other', description: 'Other documents' },
  ];

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Upload Documents</h1>
        <p className="text-gray-600">
          Upload your research papers, datasets, or results. The AI will analyze and index them for easy searching.
        </p>
      </div>

      {success && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-start space-x-3">
          <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
          <p className="text-green-800">{success}</p>
        </div>
      )}

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <p className="text-red-800">{error}</p>
        </div>
      )}

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
        {/* Document Type Selection */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-3">
            What type of document are you uploading?
          </label>
          <div className="grid grid-cols-2 gap-4">
            {documentTypes.map((type) => (
              <button
                key={type.value}
                onClick={() => setDocumentType(type.value)}
                className={`p-4 rounded-lg border-2 text-left transition-all ${
                  documentType === type.value
                    ? 'border-uva-orange bg-orange-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="font-medium text-gray-900">{type.label}</div>
                <div className="text-sm text-gray-500 mt-1">{type.description}</div>
              </button>
            ))}
          </div>
        </div>

        {/* File Upload */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Select PDF file
          </label>
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-uva-orange transition-colors">
            <input
              id="file-input"
              type="file"
              accept=".pdf"
              onChange={handleFileChange}
              className="hidden"
            />
            <label htmlFor="file-input" className="cursor-pointer">
              <UploadIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              {selectedFile ? (
                <div className="flex items-center justify-center space-x-2">
                  <FileText className="w-5 h-5 text-uva-orange" />
                  <span className="text-gray-900 font-medium">{selectedFile.name}</span>
                </div>
              ) : (
                <>
                  <p className="text-gray-600 mb-2">
                    Click to browse or drag and drop
                  </p>
                  <p className="text-sm text-gray-500">PDF files only</p>
                </>
              )}
            </label>
          </div>
        </div>

        {/* Upload Button */}
        <button
          onClick={handleUpload}
          disabled={!selectedFile || uploading || processing}
          className="mt-6 w-full bg-uva-orange hover:bg-orange-600 text-white font-semibold py-3 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {uploading
            ? 'Uploading...'
            : processing
            ? 'Processing and indexing...'
            : 'Upload and Process'}
        </button>

        {/* Info Box */}
        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
          <h3 className="font-medium text-blue-900 mb-2">What happens after upload?</h3>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>1. File is uploaded to the server and synced to OneDrive</li>
            <li>2. Text is extracted from your PDF</li>
            <li>3. Content is analyzed and indexed for semantic search</li>
            <li>4. You can then ask questions about the document!</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
