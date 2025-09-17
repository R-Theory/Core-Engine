'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { ChevronRight, Home } from 'lucide-react'
import { cn } from '@/lib/utils'

interface BreadcrumbItem {
  label: string
  href?: string
  icon?: React.ComponentType<any>
}

interface BreadcrumbProps {
  items?: BreadcrumbItem[]
  className?: string
}

// Default breadcrumb mapping based on routes
const routeMapping: Record<string, BreadcrumbItem[]> = {
  '/dashboard': [
    { label: 'Dashboard', icon: Home }
  ],
  '/courses': [
    { label: 'Dashboard', href: '/dashboard', icon: Home },
    { label: 'Courses' }
  ],
  '/resources': [
    { label: 'Dashboard', href: '/dashboard', icon: Home },
    { label: 'Resources' }
  ],
  '/workflows': [
    { label: 'Dashboard', href: '/dashboard', icon: Home },
    { label: 'Workflows' }
  ],
  '/agents': [
    { label: 'Dashboard', href: '/dashboard', icon: Home },
    { label: 'AI Agents' }
  ],
  '/plugins': [
    { label: 'Dashboard', href: '/dashboard', icon: Home },
    { label: 'Plugins' }
  ],
  '/settings': [
    { label: 'Dashboard', href: '/dashboard', icon: Home },
    { label: 'Settings' }
  ]
}

export function Breadcrumb({ items, className }: BreadcrumbProps) {
  const pathname = usePathname()
  
  // Use provided items or generate from pathname
  const breadcrumbItems = items || routeMapping[pathname] || [
    { label: 'Dashboard', href: '/dashboard', icon: Home }
  ]

  if (breadcrumbItems.length <= 1) {
    return null // Don't show breadcrumb for single items
  }

  return (
    <nav className={cn("flex items-center space-x-2 text-sm", className)}>
      {breadcrumbItems.map((item, index) => {
        const isLast = index === breadcrumbItems.length - 1
        const IconComponent = item.icon

        return (
          <div key={index} className="flex items-center space-x-2">
            {index > 0 && (
              <ChevronRight className="h-4 w-4 text-gray-400 dark:text-gray-600" />
            )}
            
            {item.href && !isLast ? (
              <Link
                href={item.href}
                className="flex items-center space-x-1 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 transition-colors"
              >
                {IconComponent && (
                  <IconComponent className="h-4 w-4" />
                )}
                <span>{item.label}</span>
              </Link>
            ) : (
              <div className="flex items-center space-x-1">
                {IconComponent && (
                  <IconComponent className={cn(
                    "h-4 w-4",
                    isLast 
                      ? "text-blue-600 dark:text-blue-400" 
                      : "text-gray-600 dark:text-gray-400"
                  )} />
                )}
                <span className={cn(
                  "font-medium",
                  isLast 
                    ? "text-blue-600 dark:text-blue-400" 
                    : "text-gray-600 dark:text-gray-400"
                )}>
                  {item.label}
                </span>
              </div>
            )}
          </div>
        )
      })}
    </nav>
  )
}

// Hook for dynamically setting breadcrumbs
export function useBreadcrumb(items: BreadcrumbItem[]) {
  // This can be extended to use context if needed for complex breadcrumb management
  return items
}