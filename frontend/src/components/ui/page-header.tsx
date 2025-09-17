'use client'

import { ReactNode } from 'react'
import { Button } from './button'
import { cn } from '@/lib/utils'

interface PageHeaderProps {
  title: string
  description?: string
  children?: ReactNode
  className?: string
  actions?: ReactNode
}

export function PageHeader({ 
  title, 
  description, 
  children, 
  className,
  actions 
}: PageHeaderProps) {
  return (
    <div className={cn("mb-8", className)}>
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white">
            {title}
          </h1>
          {description && (
            <p className="text-gray-600 dark:text-gray-400 text-base">
              {description}
            </p>
          )}
        </div>
        {actions && (
          <div className="flex items-center space-x-3">
            {actions}
          </div>
        )}
      </div>
      {children && (
        <div className="mt-6">
          {children}
        </div>
      )}
    </div>
  )
}

interface PageHeaderActionsProps {
  children: ReactNode
  className?: string
}

export function PageHeaderActions({ children, className }: PageHeaderActionsProps) {
  return (
    <div className={cn("flex items-center space-x-3", className)}>
      {children}
    </div>
  )
}