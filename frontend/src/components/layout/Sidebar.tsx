'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { cn } from '@/lib/utils'
import {
  LayoutDashboard,
  BookOpen,
  FolderOpen,
  Zap,
  Settings,
  Search,
  Plus,
  ChevronLeft,
  ChevronRight,
  Bot,
  Puzzle,
  Sparkles,
  Command,
  MessageCircle
} from 'lucide-react'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard, badge: null },
  { name: 'AI Chat', href: '/ai-chat', icon: MessageCircle, badge: null },
  { name: 'Courses', href: '/courses', icon: BookOpen, badge: '5' },
  { name: 'Resources', href: '/resources', icon: FolderOpen, badge: null },
  { name: 'Workflows', href: '/workflows', icon: Zap, badge: '2' },
  { name: 'AI Agents', href: '/agents', icon: Bot, badge: null },
  { name: 'Plugins', href: '/plugins', icon: Puzzle, badge: null },
]

const bottomNavigation = [
  { name: 'Settings', href: '/settings', icon: Settings },
]

interface SidebarProps {
  className?: string
}

export function Sidebar({ className }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false)
  const [searchFocused, setSearchFocused] = useState(false)
  const pathname = usePathname()

  return (
    <div className={cn(
      "sidebar-modern flex flex-col transition-all duration-300 ease-in-out",
      collapsed ? "w-16" : "w-72",
      className
    )}>
      {/* Header */}
      <div className="flex items-center justify-between p-6 border-b border-slate-200/50 dark:border-slate-700/50">
        {!collapsed && (
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center">
              <Sparkles className="h-6 w-6 text-white" />
            </div>
            <div>
              <span className="font-bold text-slate-900 dark:text-white text-lg">Core Engine</span>
              <div className="text-xs text-slate-500 dark:text-slate-400">Academic OS</div>
            </div>
          </div>
        )}
        
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4 text-slate-500" />
          ) : (
            <ChevronLeft className="h-4 w-4 text-slate-500" />
          )}
        </button>
      </div>

      {/* Search */}
      {!collapsed && (
        <div className="p-6 pt-4">
          <div className="relative">
            <div className={cn(
              "absolute left-3 top-1/2 transform -translate-y-1/2 flex items-center gap-2",
              searchFocused ? "text-indigo-500" : "text-slate-400"
            )}>
              <Search className="h-4 w-4" />
              {!searchFocused && (
                <div className="hidden md:flex items-center gap-1 text-xs">
                  <Command className="h-3 w-3" />
                  <span>K</span>
                </div>
              )}
            </div>
            <input
              type="text"
              placeholder="Search everything..."
              className="search-modern w-full pl-10 pr-4"
              onFocus={() => setSearchFocused(true)}
              onBlur={() => setSearchFocused(false)}
            />
          </div>
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 px-4 py-2">
        <div className="space-y-1">
          {navigation.map((item) => {
            const isActive = pathname === item.href
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "nav-item",
                  isActive && "active",
                  collapsed && "justify-center px-3"
                )}
                title={collapsed ? item.name : undefined}
              >
                <item.icon className="h-5 w-5 flex-shrink-0" />
                {!collapsed && (
                  <>
                    <span className="font-medium">{item.name}</span>
                    {item.badge && (
                      <span className="ml-auto px-2 py-0.5 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 text-xs font-medium rounded-full">
                        {item.badge}
                      </span>
                    )}
                  </>
                )}
              </Link>
            )
          })}
        </div>

        {/* Divider */}
        <div className="my-6 border-t border-slate-200/50 dark:border-slate-700/50"></div>

        {/* Bottom Navigation */}
        <div className="space-y-1">
          {bottomNavigation.map((item) => {
            const isActive = pathname === item.href
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "nav-item",
                  isActive && "active",
                  collapsed && "justify-center px-3"
                )}
                title={collapsed ? item.name : undefined}
              >
                <item.icon className="h-5 w-5 flex-shrink-0" />
                {!collapsed && (
                  <span className="font-medium">{item.name}</span>
                )}
              </Link>
            )
          })}
        </div>
      </nav>

      {/* Quick Actions */}
      {!collapsed && (
        <div className="p-6 border-t border-slate-200/50 dark:border-slate-700/50">
          <button className="btn-primary w-full flex items-center justify-center gap-2 text-sm">
            <Plus className="h-4 w-4" />
            <span>New Project</span>
          </button>
          
          <div className="mt-4 p-3 bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20 rounded-xl border border-indigo-200/50 dark:border-indigo-700/50">
            <div className="flex items-center gap-2 mb-2">
              <Bot className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
              <span className="text-sm font-medium text-indigo-900 dark:text-indigo-100">AI Assistant</span>
            </div>
            <p className="text-xs text-indigo-700 dark:text-indigo-300 mb-3">
              Need help? Ask the AI assistant anything about your studies.
            </p>
            <Link href="/ai-chat" className="btn-secondary w-full text-xs py-2 block text-center">
              Ask Question
            </Link>
          </div>
        </div>
      )}

      {/* Collapsed Quick Access */}
      {collapsed && (
        <div className="p-3 space-y-3">
          <button
            className="w-10 h-10 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center hover:shadow-lg transition-all duration-200"
            title="New Project"
          >
            <Plus className="h-5 w-5 text-white" />
          </button>
          <Link
            href="/ai-chat"
            className="w-10 h-10 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 rounded-xl flex items-center justify-center hover:bg-indigo-200 dark:hover:bg-indigo-900/50 transition-all duration-200"
            title="AI Assistant"
          >
            <Bot className="h-5 w-5" />
          </Link>
        </div>
      )}
    </div>
  )
}