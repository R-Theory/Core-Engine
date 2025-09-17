'use client'

import { ReactNode } from 'react'
import { Button } from './button'
import { cn } from '@/lib/utils'

interface EmptyStateProps {
  icon?: React.ComponentType<any>
  title: string
  description?: string
  action?: {
    label: string
    onClick: () => void
    icon?: React.ComponentType<any>
  }
  children?: ReactNode
  className?: string
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  children,
  className
}: EmptyStateProps) {
  return (
    <div className={cn(
      "flex flex-col items-center justify-center text-center py-12 px-6",
      className
    )}>
      {Icon && (
        <div className="mb-6">
          <Icon className="h-16 w-16 text-gray-300 dark:text-gray-600" />
        </div>
      )}
      
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
        {title}
      </h3>
      
      {description && (
        <p className="text-gray-600 dark:text-gray-400 text-sm max-w-md mb-6">
          {description}
        </p>
      )}
      
      {action && (
        <Button 
          onClick={action.onClick}
          className="perplexity-button flex items-center space-x-2"
        >
          {action.icon && <action.icon className="h-4 w-4" />}
          <span>{action.label}</span>
        </Button>
      )}
      
      {children}
    </div>
  )
}