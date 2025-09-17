'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, FileText, Settings, Brain, Upload } from 'lucide-react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  contextUsed?: {
    profile_used: boolean;
    documents_referenced: number;
    technical_context: boolean;
    current_context: boolean;
  };
}

interface UserContext {
  bio?: string;
  learning_style?: string;
  experience_level?: string;
  current_courses?: string[];
  current_projects?: string[];
  preferred_programming_languages?: string[];
}

interface AIProvider {
  available: boolean;
  configured: boolean;
  models: string[];
  status: string;
}

export default function AIChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [userContext, setUserContext] = useState<UserContext>({});
  const [showContextPanel, setShowContextPanel] = useState(false);
  const [conversationId, setConversationId] = useState<string>('');
  const [providers, setProviders] = useState<Record<string, AIProvider>>({});
  const [selectedProvider, setSelectedProvider] = useState('openai');
  const [selectedModel, setSelectedModel] = useState('gpt-4');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Load user context and AI providers on component mount
    loadUserContext();
    loadAIProviders();
  }, []);

  const loadUserContext = async () => {
    try {
      const response = await fetch('/api/v1/ai-context/context');
      if (response.ok) {
        const data = await response.json();
        if (data.success && data.context) {
          setUserContext({
            bio: data.context.user_profile?.bio,
            learning_style: data.context.user_profile?.learning_style,
            experience_level: data.context.user_profile?.experience_level,
            current_courses: data.context.current_context?.courses || [],
            current_projects: data.context.current_context?.projects || [],
            preferred_programming_languages: data.context.technical_profile?.programming_languages || [],
          });
        }
      }
    } catch (error) {
      console.error('Failed to load user context:', error);
    }
  };

  const loadAIProviders = async () => {
    try {
      const response = await fetch('/api/v1/ai-context/providers');
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setProviders(data.providers);
          
          // Set default provider and model based on what's available and configured
          const configuredProviders = Object.entries(data.providers).filter(([_, provider]) => provider.configured);
          if (configuredProviders.length > 0) {
            const [providerName, provider] = configuredProviders[0];
            setSelectedProvider(providerName);
            if (provider.models.length > 0) {
              setSelectedModel(provider.models[0]);
            }
          }
        }
      }
    } catch (error) {
      console.error('Failed to load AI providers:', error);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputMessage,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/v1/ai-context/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: inputMessage,
          conversation_id: conversationId,
          ai_provider: selectedProvider,
          ai_model: selectedModel,
          include_context: true,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          const assistantMessage: Message = {
            id: (Date.now() + 1).toString(),
            role: 'assistant',
            content: data.response,
            timestamp: new Date(),
            contextUsed: data.context_used,
          };

          setMessages(prev => [...prev, assistantMessage]);
          setConversationId(data.conversation_id);
        }
      } else {
        throw new Error('Failed to send message');
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const ContextIndicator = ({ context }: { context?: Message['contextUsed'] }) => {
    if (!context) return null;

    const indicators = [];
    if (context.profile_used) indicators.push('Profile');
    if (context.documents_referenced > 0) indicators.push(`${context.documents_referenced} Docs`);
    if (context.technical_context) indicators.push('Tech Context');
    if (context.current_context) indicators.push('Current Projects');

    if (indicators.length === 0) return null;

    return (
      <div className="flex flex-wrap gap-1 mt-2">
        {indicators.map((indicator, index) => (
          <span
            key={index}
            className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-indigo-100 text-indigo-700 border border-indigo-200"
          >
            <Brain className="w-3 h-3 mr-1" />
            {indicator}
          </span>
        ))}
      </div>
    );
  };

  return (
    <div className="h-screen flex flex-col bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-md border-b border-gray-200/60 px-6 py-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center">
              <Bot className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-gray-900">AI Assistant</h1>
              <p className="text-sm text-gray-500">Personalized to your learning style and context</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {/* AI Provider Selection */}
            <select
              value={selectedProvider}
              onChange={(e) => {
                setSelectedProvider(e.target.value);
                const provider = providers[e.target.value];
                if (provider && provider.models.length > 0) {
                  setSelectedModel(provider.models[0]);
                }
              }}
              className="px-3 py-1 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {Object.entries(providers).map(([name, provider]) => (
                <option key={name} value={name} disabled={!provider.configured}>
                  {name.charAt(0).toUpperCase() + name.slice(1)} {!provider.configured && '(Not configured)'}
                </option>
              ))}
            </select>
            
            {/* Model Selection */}
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="px-3 py-1 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {providers[selectedProvider]?.models.map((model) => (
                <option key={model} value={model}>
                  {model}
                </option>
              ))}
            </select>
            
            <button
              onClick={() => setShowContextPanel(!showContextPanel)}
              className={`p-2 rounded-lg transition-colors ${
                showContextPanel
                  ? 'bg-indigo-100 text-indigo-600'
                  : 'hover:bg-gray-100 text-gray-600'
              }`}
            >
              <Settings className="w-5 h-5" />
            </button>
            <button className="p-2 rounded-lg hover:bg-gray-100 text-gray-600">
              <Upload className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Context Panel */}
        {showContextPanel && (
          <div className="w-80 bg-white/60 backdrop-blur-md border-r border-gray-200/60 p-4 overflow-y-auto">
            <h3 className="font-semibold text-gray-900 mb-4">Your Context</h3>
            
            <div className="space-y-4">
              {userContext.bio && (
                <div className="bg-white/50 rounded-lg p-3">
                  <h4 className="font-medium text-gray-700 mb-2">Background</h4>
                  <p className="text-sm text-gray-600">{userContext.bio}</p>
                </div>
              )}
              
              {userContext.learning_style && (
                <div className="bg-white/50 rounded-lg p-3">
                  <h4 className="font-medium text-gray-700 mb-2">Learning Style</h4>
                  <span className="inline-block px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs">
                    {userContext.learning_style}
                  </span>
                </div>
              )}
              
              {userContext.current_courses && userContext.current_courses.length > 0 && (
                <div className="bg-white/50 rounded-lg p-3">
                  <h4 className="font-medium text-gray-700 mb-2">Current Courses</h4>
                  <div className="flex flex-wrap gap-1">
                    {userContext.current_courses.map((course, index) => (
                      <span
                        key={index}
                        className="inline-block px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs"
                      >
                        {course}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              
              {userContext.preferred_programming_languages && userContext.preferred_programming_languages.length > 0 && (
                <div className="bg-white/50 rounded-lg p-3">
                  <h4 className="font-medium text-gray-700 mb-2">Programming Languages</h4>
                  <div className="flex flex-wrap gap-1">
                    {userContext.preferred_programming_languages.map((lang, index) => (
                      <span
                        key={index}
                        className="inline-block px-2 py-1 bg-purple-100 text-purple-700 rounded-full text-xs"
                      >
                        {lang}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Chat Area */}
        <div className="flex-1 flex flex-col">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {messages.length === 0 && (
              <div className="text-center py-12">
                <div className="w-16 h-16 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Bot className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Welcome to your AI Assistant
                </h3>
                <p className="text-gray-500 max-w-md mx-auto mb-4">
                  I'm here to help with your studies and projects. I'll use your personal context
                  to provide more relevant and personalized assistance.
                </p>
                
                {/* Configuration Status */}
                {Object.keys(providers).length > 0 && (
                  <div className="max-w-md mx-auto">
                    {!providers[selectedProvider]?.configured && (
                      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                        <p className="text-sm text-yellow-700 mb-2">
                          <strong>Configuration needed:</strong> The {selectedProvider} provider requires an API key.
                        </p>
                        <p className="text-xs text-yellow-600">
                          Add your API key to the environment variables to enable full AI integration.
                        </p>
                      </div>
                    )}
                    
                    {providers[selectedProvider]?.configured && (
                      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                        <p className="text-sm text-green-700">
                          <strong>Ready to chat!</strong> Using {selectedProvider} with {selectedModel}
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex items-start space-x-3 ${
                  message.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''
                }`}
              >
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                    message.role === 'user'
                      ? 'bg-blue-500 text-white'
                      : 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white'
                  }`}
                >
                  {message.role === 'user' ? (
                    <User className="w-4 h-4" />
                  ) : (
                    <Bot className="w-4 h-4" />
                  )}
                </div>
                
                <div
                  className={`flex-1 max-w-3xl ${
                    message.role === 'user' ? 'text-right' : ''
                  }`}
                >
                  <div
                    className={`rounded-2xl px-4 py-3 ${
                      message.role === 'user'
                        ? 'bg-blue-500 text-white ml-auto inline-block'
                        : 'bg-white/80 backdrop-blur-sm border border-gray-200/60 text-gray-900'
                    }`}
                  >
                    <div className="whitespace-pre-wrap">{message.content}</div>
                  </div>
                  
                  <ContextIndicator context={message.contextUsed} />
                  
                  <div
                    className={`text-xs text-gray-500 mt-2 ${
                      message.role === 'user' ? 'text-right' : ''
                    }`}
                  >
                    {message.timestamp.toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex items-start space-x-3">
                <div className="w-8 h-8 rounded-full bg-gradient-to-r from-indigo-500 to-purple-600 text-white flex items-center justify-center">
                  <Bot className="w-4 h-4" />
                </div>
                <div className="bg-white/80 backdrop-blur-sm border border-gray-200/60 rounded-2xl px-4 py-3">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="p-6 bg-white/60 backdrop-blur-md border-t border-gray-200/60">
            <div className="flex items-end space-x-3">
              <div className="flex-1 relative">
                <textarea
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask me anything about your studies, projects, or programming..."
                  className="w-full px-4 py-3 pr-12 border border-gray-200 rounded-2xl resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent bg-white/80 backdrop-blur-sm"
                  rows={1}
                  style={{
                    minHeight: '48px',
                    maxHeight: '120px',
                    height: `${Math.min(120, Math.max(48, inputMessage.split('\n').length * 24))}px`
                  }}
                />
              </div>
              <button
                onClick={sendMessage}
                disabled={!inputMessage.trim() || isLoading}
                className="w-12 h-12 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 disabled:from-gray-300 disabled:to-gray-300 text-white rounded-2xl flex items-center justify-center transition-all duration-200 transform hover:-translate-y-0.5 disabled:transform-none flex-shrink-0"
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}