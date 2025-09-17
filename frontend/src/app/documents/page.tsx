'use client'

import { useState, useCallback, useEffect } from 'react'
import { useAuthStore } from '@/stores/authStore'
import Link from 'next/link'
import { 
  Upload, 
  FileText, 
  Search, 
  Settings, 
  Loader2, 
  CheckCircle, 
  AlertCircle,
  Home,
  FileUp,
  Eye,
  Download
} from 'lucide-react'

interface UploadResult {
  success: boolean
  message: string
  document_id?: string
  task_id?: string
  processing_async: boolean
  metadata?: any
}

interface SearchResult {
  title: string
  content: string
  page_id?: string
  url?: string
  created_time?: string
  metadata?: any
}

export default function DocumentsPage() {
  const [dragActive, setDragActive] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadResults, setUploadResults] = useState<UploadResult[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<SearchResult[]>([])
  const [searching, setSearching] = useState(false)
  const [status, setStatus] = useState<any>(null)
  const { accessToken } = useAuthStore()

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await fetch('/api/v1/documents/status', { headers: accessToken ? { 'authorization': `Bearer ${accessToken}` } : undefined })
        if (res.ok) {
          const data = await res.json()
          setStatus(data)
        }
      } catch (e) {
        console.error('Failed to fetch system status', e)
      }
    }
    fetchStatus()
  }, [accessToken])

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }, [])

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    const files = Array.from(e.dataTransfer.files)
    await uploadFiles(files)
  }, [])

  const handleFileSelect = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    await uploadFiles(files)
  }, [])

  const uploadFiles = async (files: File[]) => {
    if (files.length === 0) return
    
    setUploading(true)
    const results: UploadResult[] = []
    
    for (const file of files) {
      try {
        const formData = new FormData()
        formData.append('file', file)
        formData.append('process_async', 'false')
        formData.append('metadata', JSON.stringify({
          uploaded_from: 'documents_page',
          timestamp: new Date().toISOString()
        }))

        const response = await fetch('/api/v1/documents/upload', {
          method: 'POST',
          headers: accessToken ? { 'authorization': `Bearer ${accessToken}` } : undefined,
          body: formData
        })

        const result = await response.json()
        results.push(result)
        
      } catch (error) {
        results.push({
          success: false,
          message: `Failed to upload ${file.name}: ${error}`,
          processing_async: false
        })
      }
    }
    
    setUploadResults(prev => [...results, ...prev])
    setUploading(false)
  }

  const handleSearch = async () => {
    if (!searchQuery.trim()) return
    
    setSearching(true)
    try {
      const response = await fetch('/api/v1/documents/search', {
        method: 'POST',
        headers: accessToken ? { 'Content-Type': 'application/json', 'authorization': `Bearer ${accessToken}` } : { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: searchQuery,
          limit: 20
        })
      })

      const data = await response.json()
      if (data.success) {
        setSearchResults(data.results || [])
      }
    } catch (error) {
      console.error('Search failed:', error)
    } finally {
      setSearching(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-indigo-50 dark:from-slate-900 dark:via-slate-900 dark:to-indigo-900/20 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center">
                <FileText className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Documents</h1>
                <p className="text-slate-600 dark:text-slate-400">
                  Upload, process, and search your documents with AI-powered plugins
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <Link 
                href="/settings"
                className="btn-secondary flex items-center gap-2"
              >
                <Settings className="h-4 w-4" />
                Settings
              </Link>
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

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Upload Section */}
          <div className="lg:col-span-2 space-y-6">
            {/* Upload Area */}
            <div className="glass-card p-8">
              <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-4">
                Upload Documents
              </h2>
              
              <div
                className={`border-2 border-dashed rounded-xl p-12 text-center transition-all duration-200 ${
                  dragActive 
                    ? 'border-indigo-400 bg-indigo-50 dark:bg-indigo-900/20' 
                    : 'border-slate-300 dark:border-slate-600 hover:border-indigo-400'
                } ${uploading ? 'pointer-events-none opacity-50' : ''}`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
              >
                {uploading ? (
                  <div className="flex flex-col items-center gap-4">
                    <Loader2 className="h-12 w-12 animate-spin text-indigo-500" />
                    <p className="text-slate-600 dark:text-slate-400">Processing documents...</p>
                  </div>
                ) : (
                  <div className="flex flex-col items-center gap-4">
                    <div className="w-16 h-16 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full flex items-center justify-center">
                      <FileUp className="h-8 w-8 text-white" />
                    </div>
                    <div>
                      <p className="text-lg font-medium text-slate-900 dark:text-white mb-2">
                        Drop files here or click to browse
                      </p>
                      <p className="text-sm text-slate-600 dark:text-slate-400">
                        Supports PDF, DOCX, TXT, and code files
                      </p>
                    </div>
                    <input
                      type="file"
                      multiple
                      onChange={handleFileSelect}
                      className="hidden"
                      id="file-upload"
                      accept=".pdf,.docx,.txt,.md,.py,.js,.ts,.jsx,.tsx,.json,.xml,.html,.css"
                    />
                    <label
                      htmlFor="file-upload"
                      className="btn-primary cursor-pointer"
                    >
                      Choose Files
                    </label>
                  </div>
                )}
              </div>
            </div>

            {/* Upload Results */}
            {uploadResults.length > 0 && (
              <div className="glass-card p-6">
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
                  Upload Results
                </h3>
                <div className="space-y-3">
                  {uploadResults.map((result, index) => (
                    <div
                      key={index}
                      className={`flex items-center gap-3 p-3 rounded-lg ${
                        result.success 
                          ? 'bg-emerald-50 dark:bg-emerald-900/20'
                          : 'bg-red-50 dark:bg-red-900/20'
                      }`}
                    >
                      {result.success ? (
                        <CheckCircle className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
                      ) : (
                        <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400" />
                      )}
                      <div className="flex-1">
                        <p className={`font-medium ${
                          result.success 
                            ? 'text-emerald-900 dark:text-emerald-100'
                            : 'text-red-900 dark:text-red-100'
                        }`}>
                          {result.message}
                        </p>
                        {result.document_id && (
                          <p className="text-xs text-emerald-600 dark:text-emerald-400">
                            Document ID: {result.document_id}
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Search Section */}
          <div className="space-y-6">
            {/* Search Box */}
            <div className="glass-card p-6">
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
                Search Documents
              </h3>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search across all documents..."
                  className="input-modern flex-1"
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                />
                <button
                  onClick={handleSearch}
                  disabled={searching || !searchQuery.trim()}
                  className="btn-primary flex items-center gap-2"
                >
                  {searching ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Search className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>

            {/* Search Results */}
            {searchResults.length > 0 && (
              <div className="glass-card p-6">
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
                  Search Results ({searchResults.length})
                </h3>
                <div className="space-y-3">
                  {searchResults.map((result, index) => (
                    <div key={index} className="p-3 border border-slate-200 dark:border-slate-700 rounded-lg">
                      <h4 className="font-medium text-slate-900 dark:text-white mb-1">
                        {result.title || 'Untitled Document'}
                      </h4>
                      <p className="text-sm text-slate-600 dark:text-slate-400 mb-2 line-clamp-2">
                        {result.content.substring(0, 150)}...
                      </p>
                      <div className="flex items-center gap-2">
                        {result.url && (
                          <a
                            href={result.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-indigo-600 dark:text-indigo-400 hover:underline flex items-center gap-1"
                          >
                            <Eye className="h-3 w-3" />
                            View
                          </a>
                        )}
                        {result.created_time && (
                          <span className="text-xs text-slate-500">
                            {new Date(result.created_time).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Status Card */}
            <div className="glass-card p-6">
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
                System Status
              </h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-600 dark:text-slate-400">Plugin System:</span>
                  <span className="text-emerald-600 dark:text-emerald-400 font-medium">{status ? 'Active' : 'Checking...'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-600 dark:text-slate-400">Parsers:</span>
                  <span className="text-slate-900 dark:text-white">
                    {status ? status.enabled_plugins?.parsers : '—'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-600 dark:text-slate-400">Storage:</span>
                  <span className="text-slate-900 dark:text-white">
                    {status ? status.enabled_plugins?.storage : '—'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
