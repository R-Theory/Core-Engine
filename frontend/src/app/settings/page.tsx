'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { 
  User, 
  Shield, 
  Palette, 
  Plug, 
  Bot, 
  Key, 
  Bell, 
  Globe,
  Database,
  Brain,
  FileText,
  Upload,
  Settings as SettingsIcon,
  ArrowLeft,
  ArrowRight,
  Home
} from 'lucide-react'
import IntegrationManager from '@/components/integrations/IntegrationManager'
import { api } from '@/lib/api'
import { useSettingsStore } from '@/stores/settingsStore'
import { useAuthStore } from '@/stores/authStore'

interface SettingsSection {
  id: string
  title: string
  description: string
  icon: any
  component: React.ComponentType
}

export default function SettingsPage() {
  const [activeSection, setActiveSection] = useState('account')

  const sections: SettingsSection[] = [
    {
      id: 'account',
      title: 'Account & Profile',
      description: 'Personal information and account settings',
      icon: User,
      component: AccountSection
    },
    {
      id: 'me',
      title: 'AI Context & Me',
      description: 'Personal context for AI models and assistants',
      icon: Brain,
      component: AIContextSection
    },
    {
      id: 'integrations',
      title: 'Integrations & Services',
      description: 'Connect external APIs and services',
      icon: Plug,
      component: IntegrationsSection
    },
    {
      id: 'credentials',
      title: 'Security & Credentials',
      description: 'API keys, tokens, and security settings',
      icon: Key,
      component: CredentialsSection
    },
    {
      id: 'plugins',
      title: 'Plugins & Extensions',
      description: 'Manage installed plugins and extensions',
      icon: Bot,
      component: PluginsSection
    },
    {
      id: 'preferences',
      title: 'Preferences & Appearance',
      description: 'UI preferences and application settings',
      icon: Palette,
      component: PreferencesSection
    },
    {
      id: 'notifications',
      title: 'Notifications',
      description: 'Email, push, and workflow notifications',
      icon: Bell,
      component: NotificationsSection
    },
    {
      id: 'data',
      title: 'Data & Privacy',
      description: 'Data export, import, and privacy controls',
      icon: Database,
      component: DataSection
    }
  ]

  const ActiveComponent = sections.find(s => s.id === activeSection)?.component || AccountSection

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-indigo-50 dark:from-slate-900 dark:via-slate-900 dark:to-indigo-900/20 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center">
                <SettingsIcon className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Settings</h1>
                <p className="text-slate-600 dark:text-slate-400">
                  Configure your Core Engine experience, integrations, and AI context
                </p>
              </div>
            </div>
            
            {/* Navigation Buttons */}
            <div className="flex items-center gap-3">
              <Link 
                href="/dashboard"
                className="btn-secondary flex items-center gap-2"
              >
                <Home className="h-4 w-4" />
                Dashboard
              </Link>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar */}
          <div className="lg:col-span-1">
            <nav className="glass-card p-6 sticky top-6">
              <div className="space-y-2">
                {sections.map((section) => {
                  const Icon = section.icon
                  const isActive = activeSection === section.id
                  
                  return (
                    <button
                      key={section.id}
                      onClick={() => setActiveSection(section.id)}
                      className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-left transition-all duration-200 ${
                        isActive 
                          ? 'bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-900/30 dark:to-purple-900/30 text-indigo-700 dark:text-indigo-300 font-medium' 
                          : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-100/80 dark:hover:bg-slate-800/80'
                      }`}
                    >
                      <Icon className="h-5 w-5 flex-shrink-0" />
                      <div>
                        <div className="font-medium">{section.title}</div>
                        <div className="text-xs text-slate-500 dark:text-slate-500 mt-0.5">
                          {section.description}
                        </div>
                      </div>
                    </button>
                  )
                })}
              </div>
            </nav>
          </div>

          {/* Content */}
          <div className="lg:col-span-3">
            <div className="glass-card p-8">
              <ActiveComponent />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// Account & Profile Section
function AccountSection() {
  const { profile, loading, errors, loadProfile, saveProfile, updateProfile } = useSettingsStore()
  const { user, updateUser } = useAuthStore()
  const [accountData, setAccountData] = useState({
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    username: user?.username || '',
    email: user?.email || ''
  })

  const [profileData, setProfileData] = useState(profile)

  useEffect(() => {
    loadProfile()
  }, [loadProfile])

  useEffect(() => {
    setProfileData(profile)
  }, [profile])

  useEffect(() => {
    if (user) {
      setAccountData({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        username: user.username || '',
        email: user.email || ''
      })
    }
  }, [user])

  const handleAccountChange = (field: string, value: string) => {
    setAccountData(prev => ({ ...prev, [field]: value }))
  }

  const handleProfileChange = (field: string, value: string) => {
    const newProfile = { ...profileData, [field]: value }
    setProfileData(newProfile)
    updateProfile(newProfile)
  }

  const handleSave = async () => {
    try {
      // Save account info
      const accountResponse = await api.put('/api/v1/settings/account', accountData)
      if (accountResponse.data.status === 'success') {
        updateUser(accountData)
      }

      // Save profile info
      await saveProfile(profileData)

      alert('Account information saved successfully!')
    } catch (error: any) {
      alert(error?.response?.data?.detail || 'Failed to save account information')
    }
  }

  if (loading.profile) {
    return (
      <div className="space-y-8">
        <div className="text-center py-12">
          <User className="h-16 w-16 text-slate-400 mx-auto mb-4 animate-pulse" />
          <p className="text-slate-600 dark:text-slate-400">Loading your profile...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-semibold text-slate-900 dark:text-white mb-2">Account & Profile</h2>
        <p className="text-slate-600 dark:text-slate-400">Manage your personal information and account settings</p>
      </div>

      {errors.profile && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm text-red-700">{errors.profile}</p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              First Name
            </label>
            <input
              type="text"
              className="input-modern w-full"
              placeholder="Your first name"
              value={accountData.first_name}
              onChange={(e) => handleAccountChange('first_name', e.target.value)}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Last Name
            </label>
            <input
              type="text"
              className="input-modern w-full"
              placeholder="Your last name"
              value={accountData.last_name}
              onChange={(e) => handleAccountChange('last_name', e.target.value)}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Email Address
            </label>
            <input
              type="email"
              className="input-modern w-full bg-slate-50 dark:bg-slate-800"
              placeholder="your@email.com"
              value={accountData.email}
              disabled
              title="Email cannot be changed here"
            />
            <p className="text-xs text-slate-500 mt-1">Contact support to change your email address</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              University/Institution
            </label>
            <input
              type="text"
              className="input-modern w-full"
              placeholder="Your university or institution"
              value={profileData.university || ''}
              onChange={(e) => handleProfileChange('university', e.target.value)}
            />
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Username
            </label>
            <input
              type="text"
              className="input-modern w-full"
              placeholder="Your username"
              value={accountData.username}
              onChange={(e) => handleAccountChange('username', e.target.value)}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Student ID
            </label>
            <input
              type="text"
              className="input-modern w-full"
              placeholder="Your student ID"
              value={profileData.student_id || ''}
              onChange={(e) => handleProfileChange('student_id', e.target.value)}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Academic Year
            </label>
            <select
              className="input-modern w-full"
              value={profileData.academic_year || ''}
              onChange={(e) => handleProfileChange('academic_year', e.target.value)}
            >
              <option value="">Select academic year</option>
              <option value="freshman">Freshman</option>
              <option value="sophomore">Sophomore</option>
              <option value="junior">Junior</option>
              <option value="senior">Senior</option>
              <option value="graduate">Graduate</option>
              <option value="phd">PhD</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Major/Field of Study
            </label>
            <input
              type="text"
              className="input-modern w-full"
              placeholder="Computer Science, Engineering, etc."
              value={profileData.major || ''}
              onChange={(e) => handleProfileChange('major', e.target.value)}
            />
          </div>
        </div>
      </div>

      <div className="border-t border-slate-200 dark:border-slate-700 pt-6">
        <button
          className="btn-primary"
          onClick={handleSave}
          disabled={loading.saving}
        >
          {loading.saving ? 'Saving...' : 'Save Changes'}
        </button>
      </div>
    </div>
  )
}

// AI Context & Me Section
function AIContextSection() {
  const [context, setContext] = useState({
    bio: '',
    current_courses: [],
    current_projects: [],
    learning_style: 'mixed',
    experience_level: 'intermediate',
    preferred_explanation_style: 'detailed',
    communication_style: 'friendly',
    preferred_programming_languages: [],
    technical_expertise: [],
    tools_and_platforms: []
  })
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [uploading, setUploading] = useState(false)

  useEffect(() => {
    loadUserContext()
    loadContextDocuments()
  }, [])

  const loadUserContext = async () => {
    try {
      setLoading(true)
      const response = await fetch('/api/v1/ai-context/context')
      if (response.ok) {
        const data = await response.json()
        if (data.success && data.context) {
          setContext({
            bio: data.context.user_profile?.bio || '',
            current_courses: data.context.current_context?.courses || [],
            current_projects: data.context.current_context?.projects || [],
            learning_style: data.context.user_profile?.learning_style || 'mixed',
            experience_level: data.context.user_profile?.experience_level || 'intermediate',
            preferred_explanation_style: data.context.ai_preferences?.explanation_style || 'detailed',
            communication_style: data.context.user_profile?.communication_style || 'friendly',
            preferred_programming_languages: data.context.technical_profile?.programming_languages || [],
            technical_expertise: data.context.technical_profile?.expertise || [],
            tools_and_platforms: data.context.technical_profile?.tools || []
          })
        }
      }
    } catch (error) {
      console.error('Failed to load user context:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadContextDocuments = async () => {
    try {
      const response = await fetch('/api/v1/ai-context/context/documents')
      if (response.ok) {
        const data = await response.json()
        if (data.success) {
          setDocuments(data.documents)
        }
      }
    } catch (error) {
      console.error('Failed to load context documents:', error)
    }
  }

  const saveContext = async () => {
    try {
      setSaving(true)
      const response = await fetch('/api/v1/ai-context/context', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(context)
      })

      if (response.ok) {
        alert('AI context saved successfully!')
      } else {
        alert('Failed to save AI context')
      }
    } catch (error) {
      console.error('Failed to save context:', error)
      alert('Failed to save AI context')
    } finally {
      setSaving(false)
    }
  }

  const handleFileUpload = async (event) => {
    const files = event.target.files
    if (!files || files.length === 0) return

    try {
      setUploading(true)
      for (const file of files) {
        const formData = new FormData()
        formData.append('file', file)
        formData.append('document_type', 'context_document')

        const response = await fetch('/api/v1/ai-context/context/documents', {
          method: 'POST',
          body: formData
        })

        if (response.ok) {
          const data = await response.json()
          if (data.success) {
            await loadContextDocuments() // Refresh the document list
          }
        }
      }
      alert('Documents uploaded successfully!')
    } catch (error) {
      console.error('Failed to upload documents:', error)
      alert('Failed to upload documents')
    } finally {
      setUploading(false)
      event.target.value = '' // Reset file input
    }
  }

  const handleArrayInput = (field, value) => {
    const items = value.split(',').map(item => item.trim()).filter(Boolean)
    setContext(prev => ({ ...prev, [field]: items }))
  }

  if (loading) {
    return (
      <div className="space-y-8">
        <div className="text-center py-12">
          <Brain className="h-16 w-16 text-slate-400 mx-auto mb-4 animate-pulse" />
          <p className="text-slate-600 dark:text-slate-400">Loading your AI context...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-semibold text-slate-900 dark:text-white mb-2">AI Context & Me</h2>
        <p className="text-slate-600 dark:text-slate-400">
          Provide context about yourself to help AI assistants give more personalized and relevant responses
        </p>
      </div>

      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
            Personal Bio & Background
          </label>
          <textarea 
            className="input-modern w-full h-32" 
            placeholder="Tell the AI about yourself - your interests, goals, learning style, current projects, etc. This helps AI assistants provide more relevant and personalized help."
            value={context.bio}
            onChange={(e) => setContext(prev => ({ ...prev, bio: e.target.value }))}
          />
          <p className="text-xs text-slate-500 mt-1">This information is encrypted and only used to improve AI responses</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Current Courses (comma-separated)
            </label>
            <input 
              type="text"
              className="input-modern w-full" 
              placeholder="CS 101, Data Structures, Machine Learning..."
              value={context.current_courses.join(', ')}
              onChange={(e) => handleArrayInput('current_courses', e.target.value)}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Current Projects (comma-separated)
            </label>
            <input 
              type="text"
              className="input-modern w-full" 
              placeholder="Web app, Research paper, Mobile game..."
              value={context.current_projects.join(', ')}
              onChange={(e) => handleArrayInput('current_projects', e.target.value)}
            />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Preferred Learning Style
            </label>
            <select 
              className="input-modern w-full"
              value={context.learning_style}
              onChange={(e) => setContext(prev => ({ ...prev, learning_style: e.target.value }))}
            >
              <option value="visual">Visual (diagrams, examples)</option>
              <option value="hands-on">Hands-on (code examples, exercises)</option>
              <option value="theoretical">Theoretical (concepts, explanations)</option>
              <option value="mixed">Mixed approach</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Experience Level
            </label>
            <select 
              className="input-modern w-full"
              value={context.experience_level}
              onChange={(e) => setContext(prev => ({ ...prev, experience_level: e.target.value }))}
            >
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
              <option value="expert">Expert</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
            Programming Languages (comma-separated)
          </label>
          <input 
            type="text"
            className="input-modern w-full" 
            placeholder="Python, JavaScript, Java, C++..."
            value={context.preferred_programming_languages.join(', ')}
            onChange={(e) => handleArrayInput('preferred_programming_languages', e.target.value)}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
            Technical Expertise (comma-separated)
          </label>
          <input 
            type="text"
            className="input-modern w-full" 
            placeholder="Web Development, Machine Learning, Data Science, Mobile Development..."
            value={context.technical_expertise.join(', ')}
            onChange={(e) => handleArrayInput('technical_expertise', e.target.value)}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
            Upload Context Documents
          </label>
          <div className="border-2 border-dashed border-slate-300 dark:border-slate-600 rounded-xl p-8 text-center">
            <Upload className="h-12 w-12 text-slate-400 mx-auto mb-4" />
            <p className="text-slate-600 dark:text-slate-400 mb-2">
              Upload documents that provide context about you
            </p>
            <p className="text-xs text-slate-500 mb-4">
              Resumes, project descriptions, research papers, etc. (PDF, DOC, TXT)
            </p>
            <input
              type="file"
              multiple
              accept=".pdf,.doc,.docx,.txt,.md"
              onChange={handleFileUpload}
              className="hidden"
              id="context-file-upload"
              disabled={uploading}
            />
            <label 
              htmlFor="context-file-upload" 
              className={`btn-secondary cursor-pointer ${uploading ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              {uploading ? 'Uploading...' : 'Choose Files'}
            </label>
          </div>

          {documents.length > 0 && (
            <div className="mt-4 space-y-2">
              <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300">Uploaded Documents:</h4>
              {documents.map((doc) => (
                <div key={doc.id} className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                  <div className="flex items-center gap-3">
                    <FileText className="h-5 w-5 text-slate-400" />
                    <div>
                      <p className="text-sm font-medium text-slate-900 dark:text-white">{doc.filename}</p>
                      <p className="text-xs text-slate-500">
                        {doc.document_type} • {Math.round(doc.file_size / 1024)}KB
                      </p>
                    </div>
                  </div>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    doc.processing_status === 'completed' 
                      ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                      : doc.processing_status === 'processing'
                      ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
                      : 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400'
                  }`}>
                    {doc.processing_status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="border-t border-slate-200 dark:border-slate-700 pt-6">
        <button 
          className="btn-primary"
          onClick={saveContext}
          disabled={saving}
        >
          {saving ? 'Saving...' : 'Save AI Context'}
        </button>
      </div>
    </div>
  )
}

// Integrations & Services Section
function IntegrationsSection() {
  return <IntegrationManager />
}

// Credentials Section - Modular & Extensible
function CredentialsSection() {
  const [providers, setProviders] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedProvider, setSelectedProvider] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Define available credential providers
  const credentialProviders = [
    {
      id: 'notion',
      name: 'Notion',
      description: 'Document storage and knowledge management',
      icon: '📝',
      category: 'storage',
      fields: [
        { name: 'integration_token', label: 'Integration Token', type: 'password', placeholder: 'secret_xxx...' },
        { name: 'database_id', label: 'Database ID', type: 'text', placeholder: 'abc123...' }
      ]
    },
    {
      id: 'openai',
      name: 'OpenAI',
      description: 'GPT models for AI assistance',
      icon: '🤖',
      category: 'ai',
      fields: [
        { name: 'api_key', label: 'API Key', type: 'password', placeholder: 'sk-...' }
      ]
    },
    {
      id: 'anthropic',
      name: 'Anthropic Claude',
      description: 'Claude AI models for advanced reasoning',
      icon: '🧠',
      category: 'ai',
      fields: [
        { name: 'api_key', label: 'API Key', type: 'password', placeholder: 'sk-ant-...' }
      ]
    },
    {
      id: 'github',
      name: 'GitHub (OAuth)',
      description: 'Personal GitHub access with OAuth token',
      icon: '🐙',
      category: 'development',
      fields: [
        { name: 'access_token', label: 'Personal Access Token', type: 'password', placeholder: 'ghp_...' }
      ]
    },
    {
      id: 'github_app',
      name: 'GitHub App',
      description: 'GitHub App with installation-based permissions',
      icon: '🔧',
      category: 'development',
      fields: [
        { name: 'app_id', label: 'App ID', type: 'text', placeholder: '123456' },
        { name: 'private_key', label: 'Private Key', type: 'textarea', placeholder: '-----BEGIN RSA PRIVATE KEY-----\n...' },
        { name: 'installation_id', label: 'Installation ID', type: 'text', placeholder: '12345678' }
      ]
    },
    {
      id: 'canvas',
      name: 'Canvas LMS',
      description: 'Learning management system integration',
      icon: '🎓',
      category: 'education',
      fields: [
        { name: 'api_key', label: 'API Key', type: 'password', placeholder: 'canvas_token...' },
        { name: 'base_url', label: 'Canvas URL', type: 'url', placeholder: 'https://your-school.instructure.com' }
      ]
    }
  ]

  const loadProviderStatuses = async () => {
    setLoading(true)
    setError(null)
    try {
      // Load status for each provider
      const statuses = await Promise.allSettled(
        credentialProviders.map(async (provider) => {
          try {
            const { data } = await api.get(`/api/v1/credentials/${provider.id}`)
            return { ...provider, ...data, status: 'loaded' }
          } catch (e) {
            return { ...provider, configured: false, status: 'error' }
          }
        })
      )
      
      setProviders(statuses.map((result, index) => 
        result.status === 'fulfilled' 
          ? result.value 
          : { ...credentialProviders[index], configured: false, status: 'unavailable' }
      ))
    } catch (e: any) {
      setError('Failed to load credential providers')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadProviderStatuses() }, [])

  const categoryGroups = providers.reduce((acc, provider) => {
    const category = provider.category || 'other'
    if (!acc[category]) acc[category] = []
    acc[category].push(provider)
    return acc
  }, {} as Record<string, any[]>)

  const categoryDisplayNames: Record<string, string> = {
    storage: 'Document Storage',
    ai: 'AI Models',
    development: 'Development Tools',
    education: 'Educational Platforms',
    other: 'Other Services'
  }

  if (selectedProvider) {
    const provider = providers.find(p => p.id === selectedProvider)
    return (
      <ProviderConfigForm 
        provider={provider} 
        onBack={() => setSelectedProvider(null)}
        onSave={loadProviderStatuses}
      />
    )
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold text-slate-900 dark:text-white mb-2">Security & Credentials</h2>
          <p className="text-slate-600 dark:text-slate-400">
            Connect external services securely. All credentials are encrypted and stored per user.
          </p>
        </div>
        
        {/* Quick Stats */}
        <div className="flex items-center gap-4 text-sm">
          <div className="text-center">
            <div className="text-lg font-semibold text-emerald-600 dark:text-emerald-400">
              {providers.filter(p => p.configured).length}
            </div>
            <div className="text-xs text-slate-500">Connected</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-semibold text-slate-600 dark:text-slate-400">
              {providers.length}
            </div>
            <div className="text-xs text-slate-500">Available</div>
          </div>
        </div>
      </div>

      {loading && (
        <div className="text-center py-12">
          <div className="animate-spin h-8 w-8 border-2 border-indigo-500 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-slate-600 dark:text-slate-400">Loading credential providers...</p>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {!loading && (
        <div className="space-y-8">
          {Object.entries(categoryGroups).map(([category, categoryProviders]) => (
            <div key={category}>
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
                {categoryDisplayNames[category] || category}
                <span className="text-xs bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded-full text-slate-600 dark:text-slate-400">
                  {categoryProviders.length}
                </span>
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {categoryProviders.map((provider) => (
                  <div
                    key={provider.id}
                    className="glass-card p-6 hover:shadow-lg transition-all duration-200 cursor-pointer group"
                    onClick={() => setSelectedProvider(provider.id)}
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className="text-2xl">{provider.icon}</div>
                        <div>
                          <h4 className="font-semibold text-slate-900 dark:text-white group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                            {provider.name}
                          </h4>
                          <p className="text-xs text-slate-500">{provider.description}</p>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          provider.configured 
                            ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'
                            : provider.status === 'unavailable'
                            ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                            : 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-400'
                        }`}>
                          {provider.configured ? 'Connected' : provider.status === 'unavailable' ? 'Unavailable' : 'Setup'}
                        </span>
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-slate-500">
                        {provider.fields?.length || 0} credentials required
                      </span>
                      <ArrowRight className="h-4 w-4 text-slate-400 group-hover:text-indigo-500 transition-colors" />
                    </div>
                    
                    {provider.last_updated && (
                      <div className="text-xs text-slate-400 mt-2">
                        Updated {new Date(provider.last_updated).toLocaleDateString()}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// Provider Configuration Form Component
function ProviderConfigForm({ provider, onBack, onSave }: { provider: any, onBack: () => void, onSave: () => void }) {
  const [credentials, setCredentials] = useState<Record<string, string>>({})
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [testingConnection, setTestingConnection] = useState(false)

  const handleSave = async () => {
    setSaving(true)
    setError(null)
    try {
      await api.post(`/api/v1/credentials/${provider.id}`, credentials)
      await onSave()
      onBack()
    } catch (e: any) {
      setError(e?.message || 'Failed to save credentials')
    } finally {
      setSaving(false)
    }
  }

  const handleTestConnection = async () => {
    setTestingConnection(true)
    try {
      await api.post(`/api/v1/credentials/${provider.id}/test`, credentials)
      alert('Connection test successful!')
    } catch (e: any) {
      alert(`Connection test failed: ${e?.message || 'Unknown error'}`)
    } finally {
      setTestingConnection(false)
    }
  }

  const handleDisconnect = async () => {
    if (!confirm(`Disconnect ${provider.name}? This will remove all stored credentials.`)) return
    
    try {
      await api.delete(`/api/v1/credentials/${provider.id}`)
      await onSave()
      onBack()
    } catch (e: any) {
      setError(e?.message || 'Failed to disconnect')
    }
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center gap-4">
        <button
          onClick={onBack}
          className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400"
        >
          <ArrowLeft className="h-5 w-5" />
        </button>
        <div className="flex items-center gap-3">
          <div className="text-3xl">{provider.icon}</div>
          <div>
            <h2 className="text-2xl font-semibold text-slate-900 dark:text-white">{provider.name}</h2>
            <p className="text-slate-600 dark:text-slate-400">{provider.description}</p>
          </div>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${
            provider.configured 
              ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'
              : 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-400'
          }`}>
            {provider.configured ? 'Connected' : 'Not Connected'}
          </span>
        </div>
      </div>

      <div className="glass-card p-8 space-y-6">
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {provider.fields?.map((field: any) => (
            <div key={field.name} className="space-y-2">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                {field.label}
              </label>
              {field.type === 'textarea' ? (
                <textarea
                  value={credentials[field.name] || ''}
                  onChange={(e) => setCredentials(prev => ({ ...prev, [field.name]: e.target.value }))}
                  placeholder={field.placeholder}
                  rows={8}
                  className="input-modern w-full font-mono text-sm"
                />
              ) : (
                <input
                  type={field.type}
                  value={credentials[field.name] || ''}
                  onChange={(e) => setCredentials(prev => ({ ...prev, [field.name]: e.target.value }))}
                  placeholder={field.placeholder}
                  className="input-modern w-full"
                />
              )}
            </div>
          ))}
        </div>

        <div className="flex items-center gap-4 pt-6 border-t border-slate-200 dark:border-slate-700">
          <button
            onClick={handleSave}
            disabled={saving || !Object.keys(credentials).length}
            className="btn-primary"
          >
            {saving ? 'Saving...' : provider.configured ? 'Update Credentials' : 'Connect'}
          </button>
          
          {Object.keys(credentials).length > 0 && (
            <button
              onClick={handleTestConnection}
              disabled={testingConnection}
              className="btn-secondary"
            >
              {testingConnection ? 'Testing...' : 'Test Connection'}
            </button>
          )}
          
          {provider.configured && (
            <button
              onClick={handleDisconnect}
              className="btn-secondary text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
            >
              Disconnect
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

// Plugins Section (Document Engine Plugins)
function PluginsSection() {
  const [loading, setLoading] = useState(true)
  const [plugins, setPlugins] = useState<any[]>([])
  const [error, setError] = useState<string | null>(null)
  const [expanded, setExpanded] = useState<Record<string, boolean>>({})
  const [configs, setConfigs] = useState<Record<string, any>>({})

  const loadPlugins = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch('/api/v1/documents/plugins')
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      const list = Object.entries(data.plugins || {}).map(([name, info]: any) => ({ name, ...(info as any) }))
      setPlugins(list)
      // initialize configs from current plugin configs
      const nextConfigs: Record<string, any> = {}
      list.forEach((p: any) => { nextConfigs[p.name] = p.config?.config || {} })
      setConfigs(nextConfigs)
    } catch (e: any) {
      setError(e?.message || 'Failed to load plugins')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadPlugins() }, [])

  const togglePlugin = async (name: string, enabled: boolean) => {
    try {
      const path = enabled ? 'enable' : 'disable'
      const res = await fetch(`/api/v1/documents/plugins/${name}/${path}`, { method: 'POST' })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      await loadPlugins()
    } catch (e) {
      console.error('Toggle plugin failed', e)
    }
  }

  const saveConfig = async (name: string, enabled: boolean, priority: number = 100) => {
    try {
      const body = {
        plugin_name: name,
        enabled,
        config: configs[name] || {},
        priority,
      }
      const res = await fetch('/api/v1/documents/plugins/configure', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      await loadPlugins()
    } catch (e) {
      console.error('Save config failed', e)
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-semibold text-slate-900 dark:text-white mb-2">Document Plugins</h2>
        <p className="text-slate-600 dark:text-slate-400">Enable, disable, and configure document engine plugins</p>
      </div>

      {loading && (
        <div className="text-slate-600 dark:text-slate-400">Loading plugins...</div>
      )}
      {error && (
        <div className="text-red-600 dark:text-red-400">{error}</div>
      )}

      {!loading && plugins.length === 0 && (
        <div className="text-slate-600 dark:text-slate-400">No plugins found.</div>
      )}

      <div className="space-y-4">
        {plugins.map((p: any) => {
          const meta = p.metadata || {}
          const enabled = !!p.enabled
          const cfgSchema = meta.config_schema || {}
          const hasConfig = Object.keys(cfgSchema).length > 0
          return (
            <div key={p.name} className="p-4 border border-slate-200 dark:border-slate-700 rounded-xl">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-slate-900 dark:text-white">{meta.name || p.name}</span>
                    <span className="text-xs text-slate-500">v{meta.version}</span>
                  </div>
                  <div className="text-sm text-slate-600 dark:text-slate-400">{meta.description}</div>
                  <div className="mt-1 text-xs text-slate-500">Type: {meta.plugin_type} • Status: {String(p.status)}</div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => togglePlugin(p.name, !enabled)}
                    className={`px-3 py-1 rounded-md text-sm ${enabled ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300' : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300'}`}
                  >
                    {enabled ? 'Disable' : 'Enable'}
                  </button>
                  {hasConfig && (
                    <button
                      onClick={() => setExpanded(prev => ({ ...prev, [p.name]: !prev[p.name] }))}
                      className="px-3 py-1 rounded-md text-sm bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200"
                    >
                      {expanded[p.name] ? 'Hide Config' : 'Configure'}
                    </button>
                  )}
                </div>
              </div>

              {hasConfig && expanded[p.name] && (
                <div className="mt-4 space-y-3">
                  {Object.entries(cfgSchema).map(([key, def]: any) => (
                    <div key={key} className="flex flex-col gap-1">
                      <label className="text-sm text-slate-700 dark:text-slate-300">{key}</label>
                      <input
                        type={(def as any).type === 'string' ? 'text' : 'text'}
                        value={configs[p.name]?.[key] ?? ''}
                        onChange={(e) => setConfigs(prev => ({ ...prev, [p.name]: { ...(prev[p.name] || {}), [key]: e.target.value } }))}
                        placeholder={(def as any).description || key}
                        className="input-modern"
                      />
                    </div>
                  ))}
                  <div className="pt-2">
                    <button
                      onClick={() => saveConfig(p.name, enabled, p.config?.priority ?? 100)}
                      className="btn-primary"
                    >
                      Save Configuration
                    </button>
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

// Preferences & Appearance Section
function PreferencesSection() {
  const { preferences, loading, errors, loadPreferences, savePreferences, updatePreferences } = useSettingsStore()

  useEffect(() => {
    loadPreferences()
  }, [loadPreferences])

  const handlePreferenceChange = (field: string, value: string | boolean) => {
    const newPreferences = { ...preferences, [field]: value }
    updatePreferences(newPreferences)
  }

  const handleSave = async () => {
    try {
      await savePreferences(preferences)
      alert('Preferences saved successfully!')
    } catch (error: any) {
      alert(error?.response?.data?.detail || 'Failed to save preferences')
    }
  }

  if (loading.preferences) {
    return (
      <div className="space-y-8">
        <div className="text-center py-12">
          <Palette className="h-16 w-16 text-slate-400 mx-auto mb-4 animate-pulse" />
          <p className="text-slate-600 dark:text-slate-400">Loading your preferences...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-semibold text-slate-900 dark:text-white mb-2">Preferences & Appearance</h2>
        <p className="text-slate-600 dark:text-slate-400">Customize the look and feel of your workspace</p>
      </div>

      {errors.preferences && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm text-red-700">{errors.preferences}</p>
        </div>
      )}

      <div className="space-y-8">
        {/* Appearance Settings */}
        <div>
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Appearance</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Theme
              </label>
              <select
                className="input-modern w-full"
                value={preferences.theme}
                onChange={(e) => handlePreferenceChange('theme', e.target.value)}
              >
                <option value="light">Light</option>
                <option value="dark">Dark</option>
                <option value="system">System</option>
              </select>
              <p className="text-xs text-slate-500 mt-1">Choose your preferred color scheme</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Language
              </label>
              <select
                className="input-modern w-full"
                value={preferences.language}
                onChange={(e) => handlePreferenceChange('language', e.target.value)}
              >
                <option value="en">English</option>
                <option value="es">Español</option>
                <option value="fr">Français</option>
                <option value="de">Deutsch</option>
                <option value="zh">中文</option>
              </select>
              <p className="text-xs text-slate-500 mt-1">Interface language</p>
            </div>
          </div>
        </div>

        {/* AI Assistant Settings */}
        <div className="border-t border-slate-200 dark:border-slate-700 pt-8">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">AI Assistant</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Default AI Model
              </label>
              <select
                className="input-modern w-full"
                value={preferences.default_ai_model || ''}
                onChange={(e) => handlePreferenceChange('default_ai_model', e.target.value)}
              >
                <option value="">Auto-select</option>
                <option value="gpt-4">GPT-4 (OpenAI)</option>
                <option value="gpt-3.5-turbo">GPT-3.5 Turbo (OpenAI)</option>
                <option value="claude-3">Claude 3 (Anthropic)</option>
                <option value="claude-2">Claude 2 (Anthropic)</option>
              </select>
              <p className="text-xs text-slate-500 mt-1">Preferred model for AI assistance</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Response Style
              </label>
              <select
                className="input-modern w-full"
                value={preferences.ai_response_style}
                onChange={(e) => handlePreferenceChange('ai_response_style', e.target.value)}
              >
                <option value="concise">Concise</option>
                <option value="detailed">Detailed</option>
                <option value="conversational">Conversational</option>
                <option value="technical">Technical</option>
              </select>
              <p className="text-xs text-slate-500 mt-1">How detailed AI responses should be</p>
            </div>
          </div>
        </div>

        {/* Regional Settings */}
        <div className="border-t border-slate-200 dark:border-slate-700 pt-8">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Regional</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Timezone
              </label>
              <select
                className="input-modern w-full"
                value={preferences.timezone || ''}
                onChange={(e) => handlePreferenceChange('timezone', e.target.value)}
              >
                <option value="">Auto-detect</option>
                <option value="America/New_York">Eastern Time (ET)</option>
                <option value="America/Chicago">Central Time (CT)</option>
                <option value="America/Denver">Mountain Time (MT)</option>
                <option value="America/Los_Angeles">Pacific Time (PT)</option>
                <option value="Europe/London">GMT (London)</option>
                <option value="Europe/Paris">CET (Paris)</option>
                <option value="Asia/Tokyo">JST (Tokyo)</option>
                <option value="Asia/Shanghai">CST (Shanghai)</option>
              </select>
              <p className="text-xs text-slate-500 mt-1">Your local timezone for dates and times</p>
            </div>
          </div>
        </div>

        {/* Privacy Settings */}
        <div className="border-t border-slate-200 dark:border-slate-700 pt-8">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Privacy</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
                  Public Profile
                </label>
                <p className="text-xs text-slate-500">Allow others to see your profile information</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  className="sr-only peer"
                  checked={preferences.public_profile}
                  onChange={(e) => handlePreferenceChange('public_profile', e.target.checked)}
                />
                <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-300 dark:peer-focus:ring-indigo-800 rounded-full peer dark:bg-slate-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-slate-600 peer-checked:bg-indigo-600"></div>
              </label>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
                  Analytics & Data Sharing
                </label>
                <p className="text-xs text-slate-500">Help improve the platform by sharing anonymous usage data</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  className="sr-only peer"
                  checked={preferences.data_sharing_analytics}
                  onChange={(e) => handlePreferenceChange('data_sharing_analytics', e.target.checked)}
                />
                <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-300 dark:peer-focus:ring-indigo-800 rounded-full peer dark:bg-slate-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-slate-600 peer-checked:bg-indigo-600"></div>
              </label>
            </div>
          </div>
        </div>
      </div>

      <div className="border-t border-slate-200 dark:border-slate-700 pt-6">
        <button
          className="btn-primary"
          onClick={handleSave}
          disabled={loading.saving}
        >
          {loading.saving ? 'Saving...' : 'Save Preferences'}
        </button>
      </div>
    </div>
  )
}

function NotificationsSection() {
  const { preferences, loading, errors, loadPreferences, savePreferences, updatePreferences } = useSettingsStore()

  useEffect(() => {
    loadPreferences()
  }, [loadPreferences])

  const handleNotificationChange = (field: string, value: boolean) => {
    const newPreferences = { ...preferences, [field]: value }
    updatePreferences(newPreferences)
  }

  const handleSave = async () => {
    try {
      await savePreferences(preferences)
      alert('Notification settings saved successfully!')
    } catch (error: any) {
      alert(error?.response?.data?.detail || 'Failed to save notification settings')
    }
  }

  if (loading.preferences) {
    return (
      <div className="space-y-8">
        <div className="text-center py-12">
          <Bell className="h-16 w-16 text-slate-400 mx-auto mb-4 animate-pulse" />
          <p className="text-slate-600 dark:text-slate-400">Loading notification settings...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-semibold text-slate-900 dark:text-white mb-2">Notifications</h2>
        <p className="text-slate-600 dark:text-slate-400">Configure how and when you receive notifications</p>
      </div>

      {errors.preferences && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm text-red-700">{errors.preferences}</p>
        </div>
      )}

      <div className="space-y-8">
        {/* Email Notifications */}
        <div>
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Email Notifications</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
                  Email Notifications
                </label>
                <p className="text-xs text-slate-500">Receive notifications via email</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  className="sr-only peer"
                  checked={preferences.email_notifications}
                  onChange={(e) => handleNotificationChange('email_notifications', e.target.checked)}
                />
                <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-300 dark:peer-focus:ring-indigo-800 rounded-full peer dark:bg-slate-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-slate-600 peer-checked:bg-indigo-600"></div>
              </label>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
                  Assignment Reminders
                </label>
                <p className="text-xs text-slate-500">Get reminded about upcoming assignments and due dates</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  className="sr-only peer"
                  checked={preferences.assignment_reminders}
                  onChange={(e) => handleNotificationChange('assignment_reminders', e.target.checked)}
                />
                <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-300 dark:peer-focus:ring-indigo-800 rounded-full peer dark:bg-slate-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-slate-600 peer-checked:bg-indigo-600"></div>
              </label>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
                  Workflow Notifications
                </label>
                <p className="text-xs text-slate-500">Get notified when workflows complete or fail</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  className="sr-only peer"
                  checked={preferences.workflow_notifications}
                  onChange={(e) => handleNotificationChange('workflow_notifications', e.target.checked)}
                />
                <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-300 dark:peer-focus:ring-indigo-800 rounded-full peer dark:bg-slate-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-slate-600 peer-checked:bg-indigo-600"></div>
              </label>
            </div>
          </div>
        </div>

        {/* Push Notifications */}
        <div className="border-t border-slate-200 dark:border-slate-700 pt-8">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Push Notifications</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
                  Browser Notifications
                </label>
                <p className="text-xs text-slate-500">Receive push notifications in your browser</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  className="sr-only peer"
                  checked={preferences.push_notifications}
                  onChange={(e) => handleNotificationChange('push_notifications', e.target.checked)}
                />
                <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-300 dark:peer-focus:ring-indigo-800 rounded-full peer dark:bg-slate-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-slate-600 peer-checked:bg-indigo-600"></div>
              </label>
            </div>

            {preferences.push_notifications && (
              <div className="ml-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <p className="text-sm text-blue-700 dark:text-blue-300 mb-2">
                  Push notifications require browser permission
                </p>
                <button
                  className="btn-secondary text-sm"
                  onClick={() => {
                    if ('Notification' in window) {
                      Notification.requestPermission().then(permission => {
                        if (permission === 'granted') {
                          alert('Notifications enabled!')
                        } else {
                          alert('Please enable notifications in your browser settings')
                        }
                      })
                    }
                  }}
                >
                  Request Permission
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Notification Schedule */}
        <div className="border-t border-slate-200 dark:border-slate-700 pt-8">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Schedule</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Assignment Reminder Timing
              </label>
              <select className="input-modern w-full max-w-xs">
                <option value="1">1 day before due date</option>
                <option value="2">2 days before due date</option>
                <option value="3">3 days before due date</option>
                <option value="7">1 week before due date</option>
              </select>
              <p className="text-xs text-slate-500 mt-1">When to send assignment reminders</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Daily Summary
              </label>
              <select className="input-modern w-full max-w-xs">
                <option value="none">Disabled</option>
                <option value="morning">Morning (8:00 AM)</option>
                <option value="evening">Evening (6:00 PM)</option>
              </select>
              <p className="text-xs text-slate-500 mt-1">Receive a daily summary of tasks and updates</p>
            </div>
          </div>
        </div>
      </div>

      <div className="border-t border-slate-200 dark:border-slate-700 pt-6">
        <button
          className="btn-primary"
          onClick={handleSave}
          disabled={loading.saving}
        >
          {loading.saving ? 'Saving...' : 'Save Notification Settings'}
        </button>
      </div>
    </div>
  )
}

function DataSection() {
  const [isExporting, setIsExporting] = useState(false)
  const [isClearing, setIsClearing] = useState(false)

  const handleExportData = async () => {
    setIsExporting(true)
    try {
      const response = await api.get('/api/v1/settings/export', {
        responseType: 'blob'
      })

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `core-engine-data-${new Date().toISOString().split('T')[0]}.json`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)

      alert('Data exported successfully!')
    } catch (error: any) {
      alert(error?.response?.data?.detail || 'Failed to export data')
    } finally {
      setIsExporting(false)
    }
  }

  const handleImportData = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = async (e) => {
      try {
        const data = JSON.parse(e.target?.result as string)

        if (confirm('This will overwrite your current settings. Are you sure?')) {
          const response = await api.post('/api/v1/settings/import', data)
          if (response.data.status === 'success') {
            alert('Data imported successfully! Please refresh the page.')
            window.location.reload()
          }
        }
      } catch (error: any) {
        alert(error?.response?.data?.detail || 'Failed to import data')
      }
    }
    reader.readAsText(file)

    // Reset input
    event.target.value = ''
  }

  const handleClearCache = async () => {
    if (!confirm('This will clear all cached data. Are you sure?')) return

    setIsClearing(true)
    try {
      await api.post('/api/v1/settings/clear-cache')

      // Clear localStorage
      localStorage.removeItem('settings-storage')
      localStorage.removeItem('auth-storage')

      alert('Cache cleared successfully!')
      window.location.reload()
    } catch (error: any) {
      alert(error?.response?.data?.detail || 'Failed to clear cache')
    } finally {
      setIsClearing(false)
    }
  }

  const handleDeleteAccount = async () => {
    const confirmation = prompt(
      'This action cannot be undone. Type "DELETE" to confirm account deletion:'
    )

    if (confirmation !== 'DELETE') {
      alert('Account deletion cancelled')
      return
    }

    try {
      await api.delete('/api/v1/settings/account')
      alert('Account deleted successfully')
      window.location.href = '/auth/login'
    } catch (error: any) {
      alert(error?.response?.data?.detail || 'Failed to delete account')
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-semibold text-slate-900 dark:text-white mb-2">Data & Privacy</h2>
        <p className="text-slate-600 dark:text-slate-400">Export, import, and manage your data</p>
      </div>

      <div className="space-y-8">
        {/* Data Export */}
        <div>
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Data Export</h3>
          <div className="space-y-4">
            <div className="glass-card p-6">
              <div className="flex items-start justify-between">
                <div>
                  <h4 className="font-semibold text-slate-900 dark:text-white mb-2">
                    Export All Data
                  </h4>
                  <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
                    Download a complete backup of your profile, settings, integrations, and AI context data in JSON format.
                  </p>
                  <ul className="text-xs text-slate-500 space-y-1">
                    <li>• User profile and account information</li>
                    <li>• Application preferences and settings</li>
                    <li>• Integration configurations (credentials excluded)</li>
                    <li>• AI context and conversation history</li>
                    <li>• Course and assignment data</li>
                  </ul>
                </div>
                <button
                  className="btn-primary"
                  onClick={handleExportData}
                  disabled={isExporting}
                >
                  {isExporting ? 'Exporting...' : 'Export Data'}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Data Import */}
        <div className="border-t border-slate-200 dark:border-slate-700 pt-8">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Data Import</h3>
          <div className="space-y-4">
            <div className="glass-card p-6">
              <div className="flex items-start justify-between">
                <div>
                  <h4 className="font-semibold text-slate-900 dark:text-white mb-2">
                    Import Settings
                  </h4>
                  <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
                    Restore your data from a previously exported backup file. This will overwrite your current settings.
                  </p>
                  <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-3">
                    <p className="text-xs text-yellow-700 dark:text-yellow-300">
                      <strong>Warning:</strong> This will replace all your current settings. Make sure to export your current data first if you want to keep it.
                    </p>
                  </div>
                </div>
                <div>
                  <input
                    type="file"
                    accept=".json"
                    onChange={handleImportData}
                    className="hidden"
                    id="import-file"
                  />
                  <label
                    htmlFor="import-file"
                    className="btn-secondary cursor-pointer"
                  >
                    Import Data
                  </label>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Cache Management */}
        <div className="border-t border-slate-200 dark:border-slate-700 pt-8">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Cache Management</h3>
          <div className="space-y-4">
            <div className="glass-card p-6">
              <div className="flex items-start justify-between">
                <div>
                  <h4 className="font-semibold text-slate-900 dark:text-white mb-2">
                    Clear Cache
                  </h4>
                  <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
                    Clear all cached data including temporary files, session data, and browser storage. This may help resolve performance issues.
                  </p>
                  <p className="text-xs text-slate-500">
                    You will need to sign in again after clearing the cache.
                  </p>
                </div>
                <button
                  className="btn-secondary"
                  onClick={handleClearCache}
                  disabled={isClearing}
                >
                  {isClearing ? 'Clearing...' : 'Clear Cache'}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Privacy Settings */}
        <div className="border-t border-slate-200 dark:border-slate-700 pt-8">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Privacy</h3>
          <div className="space-y-4">
            <div className="glass-card p-6">
              <h4 className="font-semibold text-slate-900 dark:text-white mb-4">Data Processing</h4>
              <div className="space-y-3 text-sm text-slate-600 dark:text-slate-400">
                <p>
                  <strong>Personal Data:</strong> Your profile information, settings, and AI context are stored securely and are only accessible to you.
                </p>
                <p>
                  <strong>Integration Data:</strong> Credentials for external services are encrypted using industry-standard encryption and stored separately from your profile.
                </p>
                <p>
                  <strong>AI Interactions:</strong> Conversations with AI assistants are stored locally to provide context but are not shared with third parties.
                </p>
                <p>
                  <strong>Analytics:</strong> If enabled, anonymous usage data helps improve the platform but never includes personal information.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Danger Zone */}
        <div className="border-t border-red-200 dark:border-red-800 pt-8">
          <h3 className="text-lg font-semibold text-red-600 dark:text-red-400 mb-4">Danger Zone</h3>
          <div className="space-y-4">
            <div className="border border-red-200 dark:border-red-800 rounded-lg p-6">
              <div className="flex items-start justify-between">
                <div>
                  <h4 className="font-semibold text-red-900 dark:text-red-100 mb-2">
                    Delete Account
                  </h4>
                  <p className="text-sm text-red-700 dark:text-red-300 mb-4">
                    Permanently delete your account and all associated data. This action cannot be undone.
                  </p>
                  <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
                    <p className="text-xs text-red-700 dark:text-red-300">
                      <strong>Warning:</strong> This will permanently delete your account, profile, settings, AI context, and all data. There is no way to recover this information.
                    </p>
                  </div>
                </div>
                <button
                  className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors"
                  onClick={handleDeleteAccount}
                >
                  Delete Account
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
