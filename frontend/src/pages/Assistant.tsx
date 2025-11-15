import { useState } from 'react';
import { Send, Sparkles, BookOpen, Globe, Building2, Loader } from 'lucide-react';
import { ragAPI, RAGResponse } from '../lib/api';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: RAGResponse['sources'];
  reasoning?: RAGResponse['reasoning_steps'];
  confidence?: number;
}

export default function AssistantPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedModel] = useState('claude-3-5-sonnet-20241022');
  const [showReasoning, setShowReasoning] = useState(false);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage: Message = { role: 'user', content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await ragAPI.ask(input, 3, true, selectedModel);

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.answer,
        sources: response.sources,
        reasoning: response.reasoning_steps,
        confidence: response.confidence_score,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      const errorMessage: Message = {
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your question. Please try again.',
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const getSourceIcon = (type: string) => {
    switch (type) {
      case 'document':
        return <BookOpen className="w-4 h-4" />;
      case 'web':
        return <Globe className="w-4 h-4" />;
      case 'uva_resource':
        return <Building2 className="w-4 h-4" />;
      default:
        return <BookOpen className="w-4 h-4" />;
    }
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">AI Research Assistant</h1>
            <p className="text-sm text-gray-600">Powered by Claude 3.5 Sonnet • Ask questions about your research documents</p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 && (
          <div className="text-center py-12">
            <Sparkles className="w-16 h-16 text-uva-orange mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Welcome to your AI Research Assistant!
            </h2>
            <p className="text-gray-600 max-w-md mx-auto">
              Ask me anything about your uploaded documents, UVA resources, or general research questions.
              I can search your documents, UVA IT resources, and the web to find answers.
            </p>
            <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl mx-auto">
              <div className="bg-white p-4 rounded-lg border border-gray-200">
                <h3 className="font-semibold text-gray-900 mb-2">Example Questions:</h3>
                <ul className="text-sm text-gray-600 space-y-1 text-left">
                  <li>• What are the main findings in my research papers?</li>
                  <li>• How do I securely store data in UVA OneDrive?</li>
                  <li>• Summarize the methodology from my dataset</li>
                </ul>
              </div>
              <div className="bg-white p-4 rounded-lg border border-gray-200">
                <h3 className="font-semibold text-gray-900 mb-2">Features:</h3>
                <ul className="text-sm text-gray-600 space-y-1 text-left">
                  <li>• Multi-source search (docs, UVA, web)</li>
                  <li>• Citation tracking</li>
                  <li>• AI reasoning transparency</li>
                </ul>
              </div>
            </div>
          </div>
        )}

        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-3xl rounded-lg p-4 ${
                message.role === 'user'
                  ? 'bg-uva-orange text-white'
                  : 'bg-white border border-gray-200'
              }`}
            >
              <div className="whitespace-pre-wrap">{message.content}</div>

              {/* Sources */}
              {message.sources && message.sources.length > 0 && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <div className="text-sm font-semibold text-gray-700 mb-2">Sources:</div>
                  <div className="space-y-2">
                    {message.sources.slice(0, 5).map((source, idx) => (
                      <div key={idx} className="flex items-start space-x-2 text-sm">
                        <div className="text-gray-500 mt-0.5">{getSourceIcon(source.type)}</div>
                        <div className="flex-1">
                          <div className="text-gray-900 font-medium">{source.title}</div>
                          {source.url && (
                            <a
                              href={source.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-uva-orange hover:underline text-xs"
                            >
                              {source.url}
                            </a>
                          )}
                          {source.page && (
                            <span className="text-gray-500 text-xs"> (Page {source.page})</span>
                          )}
                          <span className="text-gray-400 text-xs ml-2">
                            Relevance: {(source.relevance * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Confidence Score */}
              {message.confidence !== undefined && (
                <div className="mt-3 flex items-center space-x-2 text-sm">
                  <span className="text-gray-600">Confidence:</span>
                  <div className="flex-1 bg-gray-200 rounded-full h-2 max-w-xs">
                    <div
                      className="bg-uva-orange h-2 rounded-full"
                      style={{ width: `${message.confidence * 100}%` }}
                    />
                  </div>
                  <span className="text-gray-700 font-medium">
                    {(message.confidence * 100).toFixed(0)}%
                  </span>
                </div>
              )}

              {/* Reasoning Steps (Optional) */}
              {message.reasoning && message.reasoning.length > 0 && (
                <div className="mt-3">
                  <button
                    onClick={() => setShowReasoning(!showReasoning)}
                    className="text-sm text-uva-orange hover:underline"
                  >
                    {showReasoning ? 'Hide' : 'Show'} reasoning steps ({message.reasoning.length})
                  </button>
                  {showReasoning && (
                    <div className="mt-2 space-y-2 text-xs">
                      {message.reasoning.map((step, idx) => (
                        <div key={idx} className="bg-gray-50 p-2 rounded">
                          <div className="font-medium text-gray-700">
                            {idx + 1}. {step.stage}
                          </div>
                          <div className="text-gray-600">{step.action}</div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 rounded-lg p-4 flex items-center space-x-3">
              <Loader className="w-5 h-5 text-uva-orange animate-spin" />
              <span className="text-gray-600">Thinking...</span>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="bg-white border-t border-gray-200 p-4">
        <div className="max-w-4xl mx-auto flex space-x-4">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask a question..."
            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-uva-orange focus:border-transparent"
            disabled={loading}
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="bg-uva-orange hover:bg-orange-600 text-white px-6 py-3 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            <Send className="w-5 h-5" />
            <span>Send</span>
          </button>
        </div>
      </div>
    </div>
  );
}
