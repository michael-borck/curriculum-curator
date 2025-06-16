// LLM Provider Setup Component
// Allows users to configure and test LLM providers

import React, { useState, useEffect } from 'react';
import { useLLM } from '../hooks/useLLM';

interface LLMProviderSetupProps {
  isOpen: boolean;
  onClose: () => void;
  onProviderReady?: (providerId: string) => void;
}

export function LLMProviderSetup({ isOpen, onClose, onProviderReady }: LLMProviderSetupProps) {
  const llm = useLLM();
  const [selectedProvider, setSelectedProvider] = useState<string>('');
  const [apiKey, setApiKey] = useState('');
  const [baseUrl, setBaseUrl] = useState('');
  const [testResult, setTestResult] = useState<any>(null);
  const [isTesting, setIsTesting] = useState(false);
  const [showApiKeyForm, setShowApiKeyForm] = useState(false);

  useEffect(() => {
    if (isOpen) {
      llm.loadProviders();
    }
  }, [isOpen]);

  useEffect(() => {
    // Auto-select the first available provider
    if (llm.providers.length > 0 && !selectedProvider) {
      const availableProvider = llm.providers.find(p => p.status === 'available');
      if (availableProvider) {
        setSelectedProvider(availableProvider.id);
      } else {
        setSelectedProvider(llm.providers[0].id);
      }
    }
  }, [llm.providers, selectedProvider]);

  if (!isOpen) return null;

  const handleProviderSelect = (providerId: string) => {
    setSelectedProvider(providerId);
    setShowApiKeyForm(false);
    setTestResult(null);
    setApiKey('');
    setBaseUrl('');
  };

  const handleTestProvider = async () => {
    if (!selectedProvider) return;
    
    setIsTesting(true);
    setTestResult(null);
    
    try {
      const result = await llm.testGeneration(
        'Hello! Please respond with a brief test message to confirm the connection is working.',
        undefined,
        0.1
      );
      setTestResult(result);
      
      if (result.success && onProviderReady) {
        onProviderReady(selectedProvider);
      }
    } catch (error) {
      setTestResult({
        success: false,
        error: `Test failed: ${error}`
      });
    } finally {
      setIsTesting(false);
    }
  };

  const handleSaveApiKey = async () => {
    if (!selectedProvider || !apiKey.trim()) return;
    
    try {
      await llm.storeApiKey(selectedProvider, apiKey.trim(), baseUrl || undefined);
      setShowApiKeyForm(false);
      setApiKey('');
      setBaseUrl('');
      
      // Test the provider after saving
      await handleTestProvider();
    } catch (error) {
      setTestResult({
        success: false,
        error: `Failed to save API key: ${error}`
      });
    }
  };

  const selectedProviderInfo = llm.providers.find(p => p.id === selectedProvider);

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000
    }}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: '12px',
        padding: '32px',
        maxWidth: '600px',
        width: '90%',
        maxHeight: '80vh',
        overflow: 'auto',
        boxShadow: '0 10px 25px rgba(0, 0, 0, 0.2)'
      }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <h2 style={{ margin: 0, color: '#1e293b', fontSize: '20px' }}>
            🤖 LLM Provider Setup
          </h2>
          <button
            onClick={onClose}
            style={{
              padding: '4px',
              border: 'none',
              background: 'none',
              fontSize: '20px',
              cursor: 'pointer',
              color: '#64748b'
            }}
          >
            ✕
          </button>
        </div>

        {/* Status Overview */}
        {llm.hasAvailableProvider ? (
          <div style={{
            backgroundColor: '#dcfce7',
            border: '1px solid #16a34a',
            borderRadius: '8px',
            padding: '16px',
            marginBottom: '24px'
          }}>
            <h3 style={{ margin: '0 0 8px 0', color: '#166534', fontSize: '16px' }}>
              ✅ LLM Provider Ready
            </h3>
            <p style={{ margin: 0, color: '#166534', fontSize: '14px' }}>
              You have a working LLM provider configured. Content generation is ready!
            </p>
          </div>
        ) : (
          <div style={{
            backgroundColor: '#fef3c7',
            border: '1px solid #d97706',
            borderRadius: '8px',
            padding: '16px',
            marginBottom: '24px'
          }}>
            <h3 style={{ margin: '0 0 8px 0', color: '#92400e', fontSize: '16px' }}>
              ⚠️ Setup Required
            </h3>
            <p style={{ margin: 0, color: '#92400e', fontSize: '14px' }}>
              Please configure an LLM provider to enable content generation.
            </p>
          </div>
        )}

        {/* Provider Selection */}
        <div style={{ marginBottom: '24px' }}>
          <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', color: '#1e293b' }}>
            Available Providers
          </h3>
          
          <div style={{ display: 'grid', gap: '12px' }}>
            {llm.providers.map((provider) => (
              <div
                key={provider.id}
                onClick={() => handleProviderSelect(provider.id)}
                style={{
                  padding: '16px',
                  border: `2px solid ${selectedProvider === provider.id ? '#3b82f6' : '#e5e7eb'}`,
                  borderRadius: '8px',
                  cursor: 'pointer',
                  backgroundColor: selectedProvider === provider.id ? '#dbeafe' : 'white',
                  transition: 'all 0.2s'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <h4 style={{ margin: '0 0 4px 0', fontSize: '14px', fontWeight: '600' }}>
                      {provider.name}
                    </h4>
                    <p style={{ margin: '0 0 8px 0', fontSize: '12px', color: '#64748b' }}>
                      {provider.is_local ? '🏠 Local' : '☁️ Cloud'} • 
                      {provider.requires_api_key ? ' Requires API Key' : ' No API Key Required'}
                    </p>
                  </div>
                  <div style={{
                    padding: '4px 8px',
                    borderRadius: '4px',
                    fontSize: '12px',
                    fontWeight: '500',
                    backgroundColor: provider.status === 'available' ? '#dcfce7' : 
                                   provider.status === 'not_configured' ? '#fef3c7' : '#fee2e2',
                    color: provider.status === 'available' ? '#166534' : 
                           provider.status === 'not_configured' ? '#92400e' : '#dc2626'
                  }}>
                    {provider.status === 'available' ? 'Ready' :
                     provider.status === 'not_configured' ? 'Configure' :
                     provider.status === 'not_installed' ? 'Install' : 'Error'}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Provider Configuration */}
        {selectedProviderInfo && (
          <div style={{ marginBottom: '24px' }}>
            <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', color: '#1e293b' }}>
              Configure {selectedProviderInfo.name}
            </h3>

            {selectedProviderInfo.id === 'ollama' && selectedProviderInfo.status === 'not_installed' && (
              <div style={{
                backgroundColor: '#f0f9ff',
                border: '1px solid #bfdbfe',
                borderRadius: '8px',
                padding: '16px',
                marginBottom: '16px'
              }}>
                <h4 style={{ margin: '0 0 8px 0', color: '#1e40af', fontSize: '14px' }}>
                  📥 Install Ollama
                </h4>
                <p style={{ margin: '0 0 12px 0', color: '#1e40af', fontSize: '13px' }}>
                  Ollama provides local LLM capabilities without requiring API keys or internet connectivity.
                </p>
                <a
                  href="https://ollama.ai"
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    display: 'inline-block',
                    padding: '8px 16px',
                    backgroundColor: '#3b82f6',
                    color: 'white',
                    textDecoration: 'none',
                    borderRadius: '6px',
                    fontSize: '13px',
                    fontWeight: '500'
                  }}
                >
                  Download Ollama
                </a>
              </div>
            )}

            {selectedProviderInfo.requires_api_key && selectedProviderInfo.status === 'not_configured' && (
              <div>
                {!showApiKeyForm ? (
                  <button
                    onClick={() => setShowApiKeyForm(true)}
                    style={{
                      padding: '12px 20px',
                      backgroundColor: '#3b82f6',
                      color: 'white',
                      border: 'none',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      fontSize: '14px',
                      fontWeight: '500'
                    }}
                  >
                    🔑 Add API Key
                  </button>
                ) : (
                  <div style={{
                    backgroundColor: '#f8fafc',
                    border: '1px solid #e2e8f0',
                    borderRadius: '8px',
                    padding: '16px'
                  }}>
                    <div style={{ marginBottom: '16px' }}>
                      <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: '500' }}>
                        API Key *
                      </label>
                      <input
                        type="password"
                        value={apiKey}
                        onChange={(e) => setApiKey(e.target.value)}
                        placeholder="Enter your API key..."
                        style={{
                          width: '100%',
                          padding: '10px',
                          border: '1px solid #d1d5db',
                          borderRadius: '6px',
                          fontSize: '14px'
                        }}
                      />
                    </div>
                    
                    {selectedProviderInfo.id !== 'openai' && (
                      <div style={{ marginBottom: '16px' }}>
                        <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: '500' }}>
                          Base URL (optional)
                        </label>
                        <input
                          type="text"
                          value={baseUrl}
                          onChange={(e) => setBaseUrl(e.target.value)}
                          placeholder="Custom API endpoint..."
                          style={{
                            width: '100%',
                            padding: '10px',
                            border: '1px solid #d1d5db',
                            borderRadius: '6px',
                            fontSize: '14px'
                          }}
                        />
                      </div>
                    )}

                    <div style={{ display: 'flex', gap: '12px' }}>
                      <button
                        onClick={handleSaveApiKey}
                        disabled={!apiKey.trim()}
                        style={{
                          padding: '10px 16px',
                          backgroundColor: apiKey.trim() ? '#16a34a' : '#9ca3af',
                          color: 'white',
                          border: 'none',
                          borderRadius: '6px',
                          cursor: apiKey.trim() ? 'pointer' : 'not-allowed',
                          fontSize: '14px',
                          fontWeight: '500'
                        }}
                      >
                        Save & Test
                      </button>
                      <button
                        onClick={() => setShowApiKeyForm(false)}
                        style={{
                          padding: '10px 16px',
                          backgroundColor: '#f3f4f6',
                          color: '#374151',
                          border: '1px solid #d1d5db',
                          borderRadius: '6px',
                          cursor: 'pointer',
                          fontSize: '14px'
                        }}
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}

            {selectedProviderInfo.status === 'available' && (
              <button
                onClick={handleTestProvider}
                disabled={isTesting}
                style={{
                  padding: '12px 20px',
                  backgroundColor: isTesting ? '#9ca3af' : '#16a34a',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: isTesting ? 'not-allowed' : 'pointer',
                  fontSize: '14px',
                  fontWeight: '500',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}
              >
                {isTesting ? '🔄 Testing...' : '🧪 Test Connection'}
              </button>
            )}
          </div>
        )}

        {/* Test Results */}
        {testResult && (
          <div style={{
            backgroundColor: testResult.success ? '#dcfce7' : '#fee2e2',
            border: `1px solid ${testResult.success ? '#16a34a' : '#dc2626'}`,
            borderRadius: '8px',
            padding: '16px',
            marginBottom: '24px'
          }}>
            <h4 style={{
              margin: '0 0 8px 0',
              color: testResult.success ? '#166534' : '#dc2626',
              fontSize: '14px'
            }}>
              {testResult.success ? '✅ Test Successful' : '❌ Test Failed'}
            </h4>
            
            {testResult.success ? (
              <div style={{ fontSize: '13px', color: '#166534' }}>
                <p style={{ margin: '0 0 8px 0' }}>
                  <strong>Response:</strong> {testResult.content?.substring(0, 100)}...
                </p>
                <p style={{ margin: '0 0 4px 0' }}>
                  <strong>Model:</strong> {testResult.model_used}
                </p>
                <p style={{ margin: 0 }}>
                  <strong>Response Time:</strong> {testResult.response_time_ms}ms
                </p>
              </div>
            ) : (
              <p style={{ margin: 0, color: '#dc2626', fontSize: '13px' }}>
                {testResult.error}
              </p>
            )}
          </div>
        )}

        {/* Action Buttons */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
          <button
            onClick={onClose}
            style={{
              padding: '12px 20px',
              border: '1px solid #d1d5db',
              backgroundColor: '#f3f4f6',
              color: '#374151',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            {llm.hasAvailableProvider ? 'Close' : 'Skip for Now'}
          </button>
          
          {llm.hasAvailableProvider && (
            <button
              onClick={() => {
                if (onProviderReady && selectedProvider) {
                  onProviderReady(selectedProvider);
                }
                onClose();
              }}
              style={{
                padding: '12px 20px',
                backgroundColor: '#16a34a',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '500'
              }}
            >
              Continue with {selectedProviderInfo?.name}
            </button>
          )}
        </div>

        {/* Loading State */}
        {llm.isLoading && (
          <div style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(255, 255, 255, 0.8)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderRadius: '12px'
          }}>
            <div style={{
              width: '32px',
              height: '32px',
              border: '3px solid #f3f4f6',
              borderTop: '3px solid #3b82f6',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite'
            }} />
          </div>
        )}
      </div>
    </div>
  );
}