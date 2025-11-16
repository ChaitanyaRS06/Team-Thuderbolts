import { useState, useEffect } from 'react';
import { Send, Sparkles, BookOpen, Globe, Building2, Loader, Trash2, MessageSquare } from 'lucide-react';
import { ragAPI, RAGResponse } from '../lib/api';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: RAGResponse['sources'];
  reasoning?: RAGResponse['reasoning_steps'];
  confidence?: number;
  timestamp?: string;
}

interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: string;
  updatedAt: string;
}

const STORAGE_KEY = 'chat_conversations';
const MAX_CONVERSATIONS = 4;

export default function AssistantPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedModel] = useState('claude-3-5-sonnet-20241022');
  const [showReasoning, setShowReasoning] = useState(false);
  const [showHistory, setShowHistory] = useState(false);

  // Load conversations from localStorage on mount
  useEffect(() => {
    const loadConversations = () => {
      try {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) {
          const parsed: Conversation[] = JSON.parse(stored);
          setConversations(parsed);

          // Load the most recent conversation
          if (parsed.length > 0) {
            const mostRecent = parsed[0];
            setCurrentConversationId(mostRecent.id);
            setMessages(mostRecent.messages);
          }
        }
      } catch (error) {
        console.error('Error loading conversations:', error);
      }
    };
    loadConversations();
  }, []);

  // Save conversations to localStorage whenever they change
  useEffect(() => {
    if (conversations.length > 0) {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));
      } catch (error) {
        console.error('Error saving conversations:', error);
      }
    }
  }, [conversations]);

  // Update current conversation when messages change
  useEffect(() => {
    if (messages.length > 0) {
      saveCurrentConversation();
    }
  }, [messages]);

  const saveCurrentConversation = () => {
    const conversationTitle = messages.length > 0
      ? messages[0].content.slice(0, 50) + (messages[0].content.length > 50 ? '...' : '')
      : 'New Conversation';

    const updatedConversation: Conversation = {
      id: currentConversationId || generateId(),
      title: conversationTitle,
      messages: messages,
      createdAt: currentConversationId
        ? conversations.find(c => c.id === currentConversationId)?.createdAt || new Date().toISOString()
        : new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };

    setConversations(prev => {
      // Remove current conversation if it exists
      const filtered = prev.filter(c => c.id !== updatedConversation.id);

      // Add updated conversation at the beginning
      const updated = [updatedConversation, ...filtered];

      // Keep only last MAX_CONVERSATIONS
      return updated.slice(0, MAX_CONVERSATIONS);
    });

    if (!currentConversationId) {
      setCurrentConversationId(updatedConversation.id);
    }
  };

  const generateId = () => {
    return `conv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  };

  const startNewConversation = () => {
    setMessages([]);
    setCurrentConversationId(null);
    setShowHistory(false);
  };

  const loadConversation = (conversationId: string) => {
    const conversation = conversations.find(c => c.id === conversationId);
    if (conversation) {
      setMessages(conversation.messages);
      setCurrentConversationId(conversationId);
      setShowHistory(false);
    }
  };

  const deleteConversation = (conversationId: string) => {
    setConversations(prev => prev.filter(c => c.id !== conversationId));
    if (currentConversationId === conversationId) {
      startNewConversation();
    }
  };

  const clearAllHistory = () => {
    if (confirm('Are you sure you want to clear all chat history?')) {
      setConversations([]);
      setMessages([]);
      setCurrentConversationId(null);
      localStorage.removeItem(STORAGE_KEY);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString()
    };
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
        timestamp: new Date().toISOString()
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      const errorMessage: Message = {
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your question. Please try again.',
        timestamp: new Date().toISOString()
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
    <div className="h-screen flex bg-gray-50">
      {/* Sidebar - Chat History */}
      {showHistory && (
        <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Chat History</h2>
              <button
                onClick={() => setShowHistory(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            <button
              onClick={startNewConversation}
              className="w-full bg-uva-orange text-white px-4 py-2 rounded-lg hover:bg-orange-600 transition-colors"
            >
              + New Chat
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-2">
            {conversations.length === 0 ? (
              <p className="text-sm text-gray-500 text-center py-8">No conversations yet</p>
            ) : (
              conversations.map((conv) => (
                <div
                  key={conv.id}
                  className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                    conv.id === currentConversationId
                      ? 'bg-uva-orange/10 border-uva-orange'
                      : 'bg-white border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => loadConversation(conv.id)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {conv.title}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        {new Date(conv.updatedAt).toLocaleDateString()} • {conv.messages.length} messages
                      </p>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteConversation(conv.id);
                      }}
                      className="text-gray-400 hover:text-red-600 ml-2"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>

          {conversations.length > 0 && (
            <div className="p-4 border-t border-gray-200">
              <button
                onClick={clearAllHistory}
                className="w-full text-sm text-red-600 hover:text-red-700 py-2"
              >
                Clear All History
              </button>
              <p className="text-xs text-gray-500 text-center mt-2">
                Keeping last {MAX_CONVERSATIONS} conversations
              </p>
            </div>
          )}
        </div>
      )}

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setShowHistory(!showHistory)}
                className="text-gray-600 hover:text-gray-900 transition-colors"
              >
                <MessageSquare className="w-6 h-6" />
              </button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">AI Research Assistant</h1>
                <p className="text-sm text-gray-600">
                  Powered by Claude 3.5 Sonnet •
                  {conversations.length > 0 && ` ${conversations.length}/${MAX_CONVERSATIONS} conversations saved`}
                </p>
              </div>
            </div>
            {messages.length > 0 && (
              <button
                onClick={startNewConversation}
                className="px-4 py-2 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors"
              >
                New Chat
              </button>
            )}
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
    </div>
  );
}
