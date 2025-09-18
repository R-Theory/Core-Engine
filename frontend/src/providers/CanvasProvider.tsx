'use client'

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { useSettingsStore } from '@/stores/settingsStore'
import { api } from '@/lib/api'

interface CanvasInstance {
  id: string
  name: string
  api_url: string
  is_active: boolean
  is_connected: boolean
  last_sync?: string
  connection_error?: string
}

interface CanvasData {
  courses: any[]
  assignments: any[]
  announcements: any[]
  grades: any[]
}

interface CanvasContextType {
  // Canvas instances
  canvasInstances: CanvasInstance[]
  activeCanvasId?: string
  activeCanvas?: CanvasInstance

  // Canvas data
  canvasData: CanvasData
  isLoadingData: boolean
  dataError?: string

  // Actions
  setActiveCanvas: (canvasId: string) => void
  refreshCanvasData: () => Promise<void>
  syncCanvas: (canvasId?: string) => Promise<void>

  // Utils
  isCanvasConnected: boolean
  hasCanvasData: boolean
}

const CanvasContext = createContext<CanvasContextType | undefined>(undefined)

interface CanvasProviderProps {
  children: ReactNode
}

export function CanvasProvider({ children }: CanvasProviderProps) {
  const { integrations, canvasConfig, setActiveCanvas: setActiveCanvasInStore } = useSettingsStore()

  const [canvasData, setCanvasData] = useState<CanvasData>({
    courses: [],
    assignments: [],
    announcements: [],
    grades: []
  })
  const [isLoadingData, setIsLoadingData] = useState(false)
  const [dataError, setDataError] = useState<string>()

  // Get Canvas instances from integrations
  const canvasInstances: CanvasInstance[] = integrations
    .filter(integration => integration.service_name === 'canvas')
    .map(integration => ({
      id: integration.id || integration.service_name,
      name: integration.display_name || 'Canvas',
      api_url: integration.service_name, // This would come from config
      is_active: integration.id === canvasConfig.active_canvas_id,
      is_connected: integration.is_connected,
      last_sync: integration.last_sync,
      connection_error: integration.connection_error
    }))

  // Get active Canvas instance
  const activeCanvas = canvasInstances.find(
    instance => instance.id === canvasConfig.active_canvas_id
  ) || canvasInstances.find(instance => instance.is_connected)

  const activeCanvasId = activeCanvas?.id

  // Set active Canvas
  const setActiveCanvas = (canvasId: string) => {
    setActiveCanvasInStore(canvasId)
  }

  // Refresh Canvas data
  const refreshCanvasData = async () => {
    if (!activeCanvas?.is_connected) {
      setCanvasData({
        courses: [],
        assignments: [],
        announcements: [],
        grades: []
      })
      return
    }

    setIsLoadingData(true)
    setDataError(undefined)

    try {
      const [coursesRes, assignmentsRes] = await Promise.all([
        api.get('/api/v1/courses').catch(() => ({ data: [] })),
        api.get('/api/v1/assignments').catch(() => ({ data: [] }))
      ])

      setCanvasData({
        courses: coursesRes.data || [],
        assignments: assignmentsRes.data || [],
        announcements: [], // TODO: Add announcements API
        grades: [] // TODO: Add grades API
      })
    } catch (error: any) {
      setDataError(error?.response?.data?.detail || 'Failed to load Canvas data')
      setCanvasData({
        courses: [],
        assignments: [],
        announcements: [],
        grades: []
      })
    } finally {
      setIsLoadingData(false)
    }
  }

  // Sync Canvas
  const syncCanvas = async (canvasId?: string) => {
    const targetCanvasId = canvasId || activeCanvasId
    if (!targetCanvasId) return

    try {
      await api.post(`/api/v1/settings/integrations/${targetCanvasId}/sync`)
      await refreshCanvasData()
    } catch (error: any) {
      throw new Error(error?.response?.data?.detail || 'Failed to sync Canvas')
    }
  }

  // Load Canvas data when active Canvas changes
  useEffect(() => {
    refreshCanvasData()
  }, [activeCanvasId])

  // Computed values
  const isCanvasConnected = canvasInstances.some(instance => instance.is_connected)
  const hasCanvasData = canvasData.courses.length > 0 || canvasData.assignments.length > 0

  const contextValue: CanvasContextType = {
    canvasInstances,
    activeCanvasId,
    activeCanvas,
    canvasData,
    isLoadingData,
    dataError,
    setActiveCanvas,
    refreshCanvasData,
    syncCanvas,
    isCanvasConnected,
    hasCanvasData
  }

  return (
    <CanvasContext.Provider value={contextValue}>
      {children}
    </CanvasContext.Provider>
  )
}

export function useCanvas() {
  const context = useContext(CanvasContext)
  if (context === undefined) {
    throw new Error('useCanvas must be used within a CanvasProvider')
  }
  return context
}

// Canvas-specific hooks for common use cases
export function useCanvasCourses() {
  const { canvasData, isLoadingData, dataError, refreshCanvasData } = useCanvas()
  return {
    courses: canvasData.courses,
    loading: isLoadingData,
    error: dataError,
    refresh: refreshCanvasData
  }
}

export function useCanvasAssignments() {
  const { canvasData, isLoadingData, dataError, refreshCanvasData } = useCanvas()
  return {
    assignments: canvasData.assignments,
    loading: isLoadingData,
    error: dataError,
    refresh: refreshCanvasData
  }
}

export function useCanvasConnection() {
  const {
    canvasInstances,
    activeCanvas,
    isCanvasConnected,
    setActiveCanvas,
    syncCanvas
  } = useCanvas()

  return {
    instances: canvasInstances,
    activeInstance: activeCanvas,
    isConnected: isCanvasConnected,
    setActive: setActiveCanvas,
    sync: syncCanvas
  }
}