import { useState } from 'react';
import { Upload as UploadIcon, FileText, CheckCircle, AlertCircle, X, Loader } from 'lucide-react';
import { documentsAPI, embeddingsAPI } from '../lib/api';

interface FileStatus {
  file: File;
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'error';
  error?: string;
  documentId?: number;
}

export default function UploadPage() {
  const [selectedFiles, setSelectedFiles] = useState<FileStatus[]>([]);
  const [documentType, setDocumentType] = useState<string>('research_paper');
  const [uploading, setUploading] = useState(false);
  const [currentFileIndex, setCurrentFileIndex] = useState<number>(-1);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const newFiles = Array.from(e.target.files).map(file => ({
        file,
        status: 'pending' as const
      }));
      setSelectedFiles(prev => [...prev, ...newFiles]);
      setSuccess('');
      setError('');
    }
  };

  const removeFile = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleUploadAll = async () => {
    if (selectedFiles.length === 0) {
      setError('Please select at least one file');
      return;
    }

    setUploading(true);
    setError('');
    setSuccess('');

    // Process files one by one
    for (let i = 0; i < selectedFiles.length; i++) {
      setCurrentFileIndex(i);
      const fileStatus = selectedFiles[i];

      try {
        // Update status to uploading
        setSelectedFiles(prev => {
          const updated = [...prev];
          updated[i] = { ...updated[i], status: 'uploading' };
          return updated;
        });

        // Upload document
        const doc = await documentsAPI.upload(fileStatus.file, documentType);

        // Update status to processing
        setSelectedFiles(prev => {
          const updated = [...prev];
          updated[i] = { ...updated[i], status: 'processing', documentId: doc.id };
          return updated;
        });

        // Process document
        await documentsAPI.process(doc.id);

        // Generate embeddings
        await embeddingsAPI.generate(doc.id);

        // Update status to completed
        setSelectedFiles(prev => {
          const updated = [...prev];
          updated[i] = { ...updated[i], status: 'completed' };
          return updated;
        });

      } catch (err: any) {
        // Update status to error
        setSelectedFiles(prev => {
          const updated = [...prev];
          updated[i] = {
            ...updated[i],
            status: 'error',
            error: err.response?.data?.detail || 'Upload failed'
          };
          return updated;
        });
      }
    }

    setUploading(false);
    setCurrentFileIndex(-1);

    // Check if all succeeded
    const allCompleted = selectedFiles.every(f => f.status === 'completed');
    const successCount = selectedFiles.filter(f => f.status === 'completed').length;
    const errorCount = selectedFiles.filter(f => f.status === 'error').length;

    if (allCompleted) {
      setSuccess(`Successfully uploaded and processed all ${selectedFiles.length} documents!`);
    } else {
      setSuccess(`Processed ${successCount} documents successfully. ${errorCount} failed.`);
    }
  };

  const documentTypes = [
    { value: 'dataset', label: 'Dataset', description: 'Research data files' },
    { value: 'research_paper', label: 'Research Paper', description: 'Published papers, articles' },
    { value: 'results', label: 'Results', description: 'Experimental results' },
    { value: 'other', label: 'Other', description: 'Other documents' },
  ];

  const getStatusIcon = (status: FileStatus['status']) => {
    switch (status) {
      case 'pending':
        return <FileText className="w-5 h-5 text-gray-400" />;
      case 'uploading':
        return <Loader className="w-5 h-5 text-blue-500 animate-spin" />;
      case 'processing':
        return <Loader className="w-5 h-5 text-orange-500 animate-spin" />;
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
    }
  };

  const getStatusText = (status: FileStatus['status']) => {
    switch (status) {
      case 'pending':
        return 'Waiting...';
      case 'uploading':
        return 'Uploading...';
      case 'processing':
        return 'Processing & Indexing...';
      case 'completed':
        return 'Completed';
      case 'error':
        return 'Failed';
    }
  };

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
                disabled={uploading}
                className={`p-4 rounded-lg border-2 text-left transition-all disabled:opacity-50 disabled:cursor-not-allowed ${
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
            Select PDF files (multiple allowed)
          </label>
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-uva-orange transition-colors">
            <input
              id="file-input"
              type="file"
              accept=".pdf"
              multiple
              onChange={handleFileChange}
              disabled={uploading}
              className="hidden"
            />
            <label htmlFor="file-input" className={uploading ? 'cursor-not-allowed' : 'cursor-pointer'}>
              <UploadIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600 mb-2">
                Click to browse or drag and drop
              </p>
              <p className="text-sm text-gray-500">PDF files only • Multiple files supported</p>
            </label>
          </div>
        </div>

        {/* Selected Files List */}
        {selectedFiles.length > 0 && (
          <div className="mt-6">
            <h3 className="text-sm font-medium text-gray-700 mb-3">
              Selected Files ({selectedFiles.length})
            </h3>
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {selectedFiles.map((fileStatus, index) => (
                <div
                  key={index}
                  className={`flex items-center justify-between p-3 rounded-lg border ${
                    fileStatus.status === 'completed'
                      ? 'bg-green-50 border-green-200'
                      : fileStatus.status === 'error'
                      ? 'bg-red-50 border-red-200'
                      : 'bg-gray-50 border-gray-200'
                  }`}
                >
                  <div className="flex items-center space-x-3 flex-1 min-w-0">
                    {getStatusIcon(fileStatus.status)}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {fileStatus.file.name}
                      </p>
                      <p className="text-xs text-gray-500">
                        {getStatusText(fileStatus.status)}
                        {fileStatus.error && ` - ${fileStatus.error}`}
                      </p>
                    </div>
                  </div>
                  {!uploading && fileStatus.status === 'pending' && (
                    <button
                      onClick={() => removeFile(index)}
                      className="ml-2 p-1 hover:bg-gray-200 rounded"
                    >
                      <X className="w-4 h-4 text-gray-500" />
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Upload Button */}
        <button
          onClick={handleUploadAll}
          disabled={selectedFiles.length === 0 || uploading}
          className="mt-6 w-full bg-uva-orange hover:bg-orange-600 text-white font-semibold py-3 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {uploading
            ? `Processing ${currentFileIndex + 1} of ${selectedFiles.length}...`
            : `Upload and Process ${selectedFiles.length} ${selectedFiles.length === 1 ? 'File' : 'Files'}`}
        </button>

        {/* Clear All Button */}
        {selectedFiles.length > 0 && !uploading && (
          <button
            onClick={() => setSelectedFiles([])}
            className="mt-3 w-full bg-gray-200 hover:bg-gray-300 text-gray-700 font-medium py-2 rounded-lg transition-colors"
          >
            Clear All
          </button>
        )}

        {/* Info Box */}
        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
          <h3 className="font-medium text-blue-900 mb-2">What happens after upload?</h3>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>1. Files are uploaded to local storage one by one</li>
            <li>2. Text is extracted from each PDF</li>
            <li>3. Content is analyzed and indexed for semantic search</li>
            <li>4. Embeddings are generated using HuggingFace (384 dimensions)</li>
            <li>5. You can then ask questions about the documents!</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
