'use client'

import { ReactNode } from 'react'
import { Sidebar } from './Sidebar'
import { Header } from './Header'
import { Breadcrumb } from './Breadcrumb'
import { cn } from '@/lib/utils'

interface BreadcrumbItem {
  label: string
  href?: string
  icon?: React.ComponentType<any>
}

interface LayoutProps {
  children: ReactNode
  className?: string
  breadcrumbs?: BreadcrumbItem[]
  showBreadcrumbs?: boolean
}

export function Layout({ 
  children, 
  className, 
  breadcrumbs,
  showBreadcrumbs = true 
}: LayoutProps) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-blue-50 dark:from-gray-900 dark:via-gray-900 dark:to-blue-900/20">
      <div className="flex h-screen">
        {/* Sidebar */}
        <Sidebar />
        
        {/* Main Content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Header */}
          <Header />
          
          {/* Breadcrumb Navigation */}
          {showBreadcrumbs && (
            <div className="px-6 py-3 border-b border-gray-200/50 dark:border-gray-700/50 bg-white/50 dark:bg-gray-900/50 backdrop-blur-sm">
              <Breadcrumb items={breadcrumbs} />
            </div>
          )}
          
          {/* Page Content */}
          <main className={cn(
            "flex-1 overflow-y-auto p-6",
            className
          )}>
            {children}
          </main>
        </div>
      </div>
    </div>
  )
}