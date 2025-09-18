'use client'

import { useState, useEffect } from 'react'
import { 
  Globe, 
  Bot, 
  CheckCircle, 
  XCircle, 
  Settings, 
  Loader2, 
  Plus,
  Eye,
  EyeOff,
  BookOpen,
  GitBranch,
  FileText,
  Cloud,
  AlertCircle
} from 'lucide-react'

interface Integration {
  id?: string
  service_name: string
  service_display_name: string
  description: string
  integration_type: string
  capabilities: string[]
  is_connected: boolean
  connection_status: 'connected' | 'disconnected' | 'error' | 'testing'
  connection_error?: string
  last_sync?: string
  config_fields: Array<{
    name: string
    type: 'text' | 'password' | 'url' | 'select'
    label: string
    placeholder?: string
    required: boolean
    description?: string
    options?: string[]
  }>
}

interface IntegrationManagerProps {
  className?: string
}

export default function IntegrationManager({ className = '' }: IntegrationManagerProps) {
  const [integrations, setIntegrations] = useState<Integration[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedIntegration, setSelectedIntegration] = useState<Integration | null>(null)
  const [configuring, setConfiguring] = useState(false)
  const [testing, setTesting] = useState(false)
  const [syncingAll, setSyncingAll] = useState(false)

  // Get service icon
  const getServiceIcon = (serviceName: string) => {
    switch (serviceName.toLowerCase()) {
      case 'canvas':
        return BookOpen
      case 'github':
        return GitBranch
      case 'notion':
        return FileText
      case 'googledrive':
      case 'google_drive':
        return Cloud
      default:
        return Globe
    }
  }

  // Get integration type badge color
  const getTypeColor = (type: string) => {
    switch (type.toLowerCase()) {
      case 'lms':
        return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
      case 'code_repo':
        return 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300'
      case 'knowledge':
        return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'
      case 'storage':
        return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300'
      default:
        return 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300'
    }
  }

  // Fetch available integrations
  const fetchIntegrations = async () => {
    try {
      const [availableResponse, statusResponse] = await Promise.all([
        fetch('/api/v1/settings/integrations/available'),
        fetch('/api/v1/settings/integrations/sync-status')
      ])

      if (availableResponse.ok) {
        const availableData = await availableResponse.json()
        const statusData = statusResponse.ok ? await statusResponse.json() : []

        // Create a map of connected integrations
        const statusMap = new Map(
          statusData.map((item: any) => [item.service_name, item])
        )

        // Transform backend data to frontend format
        const transformedIntegrations = Object.entries(availableData).map(([key, value]: [string, any]) => {
          const status = statusMap.get(key)

          return {
            id: status?.integration_id,
            service_name: key,
            service_display_name: value.service_name,
            description: getServiceDescription(key),
            integration_type: value.integration_type,
            capabilities: value.capabilities,
            is_connected: status?.is_connected || false,
            connection_status: status?.is_connected
              ? (status.connection_error ? 'error' : 'connected')
              : 'disconnected' as const,
            connection_error: status?.connection_error,
            last_sync: status?.last_sync,
            config_fields: getConfigFields(key)
          }
        })

        setIntegrations(transformedIntegrations)
      }
    } catch (error) {
      console.error('Failed to fetch integrations:', error)
    } finally {
      setLoading(false)
    }
  }

  // Get service description
  const getServiceDescription = (serviceName: string) => {
    switch (serviceName.toLowerCase()) {
      case 'canvas':
        return 'Sync courses, assignments, and grades from Canvas LMS'
      case 'github':
        return 'Connect repositories, issues, and pull requests'
      case 'notion':
        return 'Import pages, databases, and knowledge content'
      case 'googledrive':
        return 'Access and sync files from Google Drive'
      default:
        return 'External service integration'
    }
  }

  // Get configuration fields for each service
  const getConfigFields = (serviceName: string) => {
    switch (serviceName.toLowerCase()) {
      case 'canvas':
        return [
          {
            name: 'api_url',
            type: 'url' as const,
            label: 'Canvas API URL',
            placeholder: 'https://university.instructure.com/api/v1',
            required: true,
            description: 'Your institution\'s Canvas API endpoint (include /api/v1)'
          },
          {
            name: 'access_token',
            type: 'password' as const,
            label: 'Access Token',
            placeholder: 'Canvas API access token',
            required: true,
            description: 'Generate from Canvas Account > Settings > Approved Integrations'
          },
          {
            name: 'instance_name',
            type: 'text' as const,
            label: 'Instance Name (Optional)',
            placeholder: 'My University Canvas',
            required: false,
            description: 'Friendly name to identify this Canvas instance'
          }
        ]
      case 'github':
        return [
          {
            name: 'auth_mode',
            type: 'select' as const,
            label: 'Authentication Mode',
            placeholder: 'Select authentication mode',
            required: true,
            description: 'Choose between OAuth (personal access token) or GitHub App',
            options: ['oauth', 'app']
          },
          {
            name: 'access_token',
            type: 'password' as const,
            label: 'GitHub Token (OAuth)',
            placeholder: 'ghp_xxxxxxxxxxxx',
            required: false,
            description: 'Personal Access Token (required for OAuth mode)'
          },
          {
            name: 'app_id',
            type: 'text' as const,
            label: 'App ID (GitHub App)',
            placeholder: '123456',
            required: false,
            description: 'GitHub App ID (required for App mode)'
          },
          {
            name: 'installation_id',
            type: 'text' as const,
            label: 'Installation ID (GitHub App)',
            placeholder: '12345678',
            required: false,
            description: 'GitHub App Installation ID (required for App mode)'
          },
          {
            name: 'private_key',
            type: 'password' as const,
            label: 'Private Key (GitHub App)',
            placeholder: '-----BEGIN RSA PRIVATE KEY-----...',
            required: false,
            description: 'GitHub App Private Key (required for App mode)'
          },
          {
            name: 'username',
            type: 'text' as const,
            label: 'GitHub Username',
            placeholder: 'your-username',
            required: false,
            description: 'Your GitHub username (optional, for user-specific repos)'
          }
        ]
      case 'notion':
        return [
          {
            name: 'integration_token',
            type: 'password' as const,
            label: 'Integration Token',
            placeholder: 'secret_xxxxxxxxxxxx',
            required: true,
            description: 'Internal Integration Token from Notion integrations page'
          }
        ]
      default:
        return []
    }
  }

  // Test integration connection
  const testConnection = async (serviceName: string, config: Record<string, string>) => {
    setTesting(true)
    try {
      // Determine the provider ID based on service name and auth mode
      let providerId = serviceName
      if (serviceName === 'github' && config.auth_mode === 'app') {
        providerId = 'github_app'
      }

      const response = await fetch(`/api/v1/credentials/${providerId}/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      })

      const result = await response.json()
      return result.success
    } catch (error) {
      console.error('Connection test failed:', error)
      return false
    } finally {
      setTesting(false)
    }
  }

  // Setup integration
  const setupIntegration = async (serviceName: string, config: Record<string, string>) => {
    try {
      const response = await fetch('/api/v1/settings/integrations/setup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ service_name: serviceName, config })
      })
      
      if (response.ok) {
        // Refresh integrations list
        await fetchIntegrations()
        setSelectedIntegration(null)
        setConfiguring(false)
        return true
      }
      return false
    } catch (error) {
      console.error('Setup failed:', error)
      return false
    }
  }

  // Sync all integrations
  const syncAllIntegrations = async () => {
    setSyncingAll(true)
    try {
      const response = await fetch('/api/v1/settings/integrations/sync', {
        method: 'POST'
      })
      
      if (response.ok) {
        // Refresh status
        await fetchIntegrations()
      }
    } catch (error) {
      console.error('Sync failed:', error)
    } finally {
      setSyncingAll(false)
    }
  }

  useEffect(() => {
    fetchIntegrations()
  }, [])

  if (loading) {
    return (
      <div className={`flex items-center justify-center py-12 ${className}`}>
        <Loader2 className="h-8 w-8 animate-spin text-indigo-500" />
      </div>
    )
  }

  return (
    <div className={`space-y-8 ${className}`}>
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold text-slate-900 dark:text-white mb-2">
            Integrations & Services
          </h2>
          <p className="text-slate-600 dark:text-slate-400">
            Connect external services to sync data and enhance your workflow
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <button
            onClick={syncAllIntegrations}
            disabled={syncingAll}
            className="btn-secondary flex items-center gap-2"
          >
            {syncingAll ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Settings className="h-4 w-4" />
            )}
            Sync All
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {integrations.map((integration, index) => {
          const Icon = getServiceIcon(integration.service_name)
          
          return (
            <div key={index} className="glass-card-hover p-6 relative group">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center">
                    <Icon className="h-6 w-6 text-white" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-slate-900 dark:text-white">
                      {integration.service_display_name}
                    </h3>
                    <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium mt-1 ${getTypeColor(integration.integration_type)}`}>
                      {integration.integration_type.replace('_', ' ')}
                    </span>
                  </div>
                </div>
                
                <div className="flex items-center gap-2">
                  <div className={`w-3 h-3 rounded-full ${
                    integration.connection_status === 'connected' ? 'bg-emerald-500' :
                    integration.connection_status === 'error' ? 'bg-red-500' :
                    integration.connection_status === 'testing' ? 'bg-yellow-500' :
                    'bg-slate-400'
                  }`} />
                  <span className={`text-xs font-medium ${
                    integration.connection_status === 'connected' ? 'text-emerald-600 dark:text-emerald-400' :
                    integration.connection_status === 'error' ? 'text-red-600 dark:text-red-400' :
                    integration.connection_status === 'testing' ? 'text-yellow-600 dark:text-yellow-400' :
                    'text-slate-500'
                  }`}>
                    {integration.connection_status === 'connected' ? 'Connected' :
                     integration.connection_status === 'error' ? 'Error' :
                     integration.connection_status === 'testing' ? 'Testing' :
                     'Not Connected'}
                  </span>
                </div>
              </div>

              <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
                {integration.description}
              </p>

              <div className="flex flex-wrap gap-1 mb-4">
                {integration.capabilities.map((capability) => (
                  <span
                    key={capability}
                    className="px-2 py-1 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 text-xs rounded-md"
                  >
                    {capability}
                  </span>
                ))}
              </div>

              {/* Connection Status Info */}
              {integration.last_sync && (
                <div className="mb-4 p-2 bg-slate-50 dark:bg-slate-800 rounded-lg">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-500">Last sync:</span>
                    <span className="text-slate-700 dark:text-slate-300">
                      {new Date(integration.last_sync).toLocaleString()}
                    </span>
                  </div>
                </div>
              )}

              {integration.connection_error && (
                <div className="flex items-center gap-2 mb-4 p-2 bg-red-50 dark:bg-red-900/20 rounded-lg">
                  <AlertCircle className="h-4 w-4 text-red-500" />
                  <span className="text-xs text-red-600 dark:text-red-400">
                    {integration.connection_error}
                  </span>
                </div>
              )}

              <div className="flex gap-2">
                <button
                  onClick={() => {
                    setSelectedIntegration(integration)
                    setConfiguring(true)
                  }}
                  className={`flex-1 py-2 px-4 rounded-lg font-medium transition-colors ${
                    integration.is_connected
                      ? 'bg-emerald-100 hover:bg-emerald-200 text-emerald-700 dark:bg-emerald-900/30 dark:hover:bg-emerald-900/50 dark:text-emerald-300'
                      : 'bg-indigo-100 hover:bg-indigo-200 text-indigo-700 dark:bg-indigo-900/30 dark:hover:bg-indigo-900/50 dark:text-indigo-300'
                  }`}
                >
                  {integration.is_connected ? 'Configure' : 'Setup'}
                </button>

                {integration.is_connected && integration.id && (
                  <button
                    onClick={async () => {
                      try {
                        await fetch(`/api/v1/settings/integrations/${integration.id}/sync`, {
                          method: 'POST'
                        })
                        await fetchIntegrations() // Refresh status
                        alert('Sync completed!')
                      } catch (error) {
                        alert('Sync failed')
                      }
                    }}
                    className="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-600 dark:bg-slate-800 dark:hover:bg-slate-700 dark:text-slate-300 rounded-lg font-medium transition-colors"
                    title="Sync now"
                  >
                    <Settings className="h-4 w-4" />
                  </button>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Configuration Modal */}
      {configuring && selectedIntegration && (
        <IntegrationConfigModal
          integration={selectedIntegration}
          onClose={() => {
            setConfiguring(false)
            setSelectedIntegration(null)
          }}
          onTest={testConnection}
          onSetup={setupIntegration}
          testing={testing}
        />
      )}
    </div>
  )
}

// Configuration Modal Component
interface IntegrationConfigModalProps {
  integration: Integration
  onClose: () => void
  onTest: (serviceName: string, config: Record<string, string>) => Promise<boolean>
  onSetup: (serviceName: string, config: Record<string, string>) => Promise<boolean>
  testing: boolean
}

function IntegrationConfigModal({ 
  integration, 
  onClose, 
  onTest, 
  onSetup, 
  testing 
}: IntegrationConfigModalProps) {
  const [config, setConfig] = useState<Record<string, string>>({})
  const [showPasswords, setShowPasswords] = useState<Record<string, boolean>>({})
  const [testResult, setTestResult] = useState<boolean | null>(null)
  const [saving, setSaving] = useState(false)

  const Icon = integration.service_name === 'canvas' ? BookOpen :
              integration.service_name === 'github' ? GitBranch :
              integration.service_name === 'notion' ? FileText : Globe

  const handleTest = async () => {
    const result = await onTest(integration.service_name, config)
    setTestResult(result)
  }

  const handleSave = async () => {
    setSaving(true)
    const success = await onSetup(integration.service_name, config)
    if (success) {
      onClose()
    }
    setSaving(false)
  }

  const togglePasswordVisibility = (fieldName: string) => {
    setShowPasswords(prev => ({
      ...prev,
      [fieldName]: !prev[fieldName]
    }))
  }

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-slate-200 dark:border-slate-700">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
              <Icon className="h-5 w-5 text-white" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                Configure {integration.service_display_name}
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                {integration.description}
              </p>
            </div>
          </div>
        </div>

        <div className="p-6 space-y-4">
          {integration.config_fields.map((field) => (
            <div key={field.name}>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                {field.label}
                {field.required && <span className="text-red-500">*</span>}
              </label>
              
              <div className="relative">
                {field.type === 'select' ? (
                  <select
                    value={config[field.name] || ''}
                    onChange={(e) => setConfig(prev => ({ ...prev, [field.name]: e.target.value }))}
                    className="input-modern w-full"
                    required={field.required}
                  >
                    <option value="">{field.placeholder || 'Select an option'}</option>
                    {field.options?.map((option) => (
                      <option key={option} value={option}>
                        {option === 'oauth' ? 'OAuth (Personal Access Token)' :
                         option === 'app' ? 'GitHub App' : option}
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    type={field.type === 'password' && !showPasswords[field.name] ? 'password' : 'text'}
                    value={config[field.name] || ''}
                    onChange={(e) => setConfig(prev => ({ ...prev, [field.name]: e.target.value }))}
                    placeholder={field.placeholder}
                    className="input-modern w-full pr-10"
                    required={field.required}
                  />
                )}

                {field.type === 'password' && (
                  <button
                    type="button"
                    onClick={() => togglePasswordVisibility(field.name)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                  >
                    {showPasswords[field.name] ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </button>
                )}
              </div>
              
              {field.description && (
                <p className="text-xs text-slate-500 mt-1">{field.description}</p>
              )}
            </div>
          ))}

          {testResult !== null && (
            <div className={`flex items-center gap-2 p-3 rounded-lg ${
              testResult 
                ? 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-300'
                : 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300'
            }`}>
              {testResult ? (
                <CheckCircle className="h-4 w-4" />
              ) : (
                <XCircle className="h-4 w-4" />
              )}
              <span className="text-sm">
                {testResult ? 'Connection successful!' : 'Connection failed. Please check your credentials.'}
              </span>
            </div>
          )}
        </div>

        <div className="p-6 border-t border-slate-200 dark:border-slate-700 flex gap-3">
          <button
            onClick={onClose}
            className="btn-secondary flex-1"
          >
            Cancel
          </button>
          
          <button
            onClick={handleTest}
            disabled={testing || !Object.values(config).some(v => v)}
            className="btn-secondary flex-1 flex items-center justify-center gap-2"
          >
            {testing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              'Test'
            )}
          </button>
          
          <button
            onClick={handleSave}
            disabled={saving || testResult !== true}
            className="btn-primary flex-1 flex items-center justify-center gap-2"
          >
            {saving ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              'Save'
            )}
          </button>
        </div>
      </div>
    </div>
  )
}