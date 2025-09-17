'use client'

import { ReactNode, useState } from 'react'
import { ChevronLeft, ChevronRight, Search, Filter } from 'lucide-react'
import { Button } from './button'
import { cn } from '@/lib/utils'

interface Column<T = any> {
  key: string
  title: string
  render?: (value: any, item: T) => ReactNode
  sortable?: boolean
  width?: string
}

interface DataTableProps<T = any> {
  data: T[]
  columns: Column<T>[]
  loading?: boolean
  searchable?: boolean
  filterable?: boolean
  pagination?: {
    page: number
    pageSize: number
    total: number
    onPageChange: (page: number) => void
  }
  onSearch?: (query: string) => void
  onFilter?: () => void
  className?: string
  emptyState?: ReactNode
}

export function DataTable<T = any>({
  data,
  columns,
  loading = false,
  searchable = false,
  filterable = false,
  pagination,
  onSearch,
  onFilter,
  className,
  emptyState
}: DataTableProps<T>) {
  const [searchQuery, setSearchQuery] = useState('')
  const [sortField, setSortField] = useState<string | null>(null)
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc')

  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('asc')
    }
  }

  const handleSearch = (query: string) => {
    setSearchQuery(query)
    onSearch?.(query)
  }

  const renderPagination = () => {
    if (!pagination) return null

    const { page, pageSize, total, onPageChange } = pagination
    const totalPages = Math.ceil(total / pageSize)
    const startItem = (page - 1) * pageSize + 1
    const endItem = Math.min(page * pageSize, total)

    return (
      <div className="flex items-center justify-between px-6 py-3 border-t border-gray-200/50 dark:border-gray-700/50 bg-gray-50/50 dark:bg-gray-800/50">
        <div className="text-sm text-gray-700 dark:text-gray-300">
          Showing {startItem} to {endItem} of {total} results
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1}
          >
            <ChevronLeft className="h-4 w-4" />
            Previous
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages}
          >
            Next
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className={cn("perplexity-card", className)}>
        <div className="p-8 text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="text-gray-600 dark:text-gray-400 mt-2">Loading...</p>
        </div>
      </div>
    )
  }

  if (data.length === 0 && emptyState) {
    return (
      <div className={cn("perplexity-card", className)}>
        {emptyState}
      </div>
    )
  }

  return (
    <div className={cn("perplexity-card overflow-hidden", className)}>
      {/* Search and Filter Bar */}
      {(searchable || filterable) && (
        <div className="p-6 border-b border-gray-200/50 dark:border-gray-700/50">
          <div className="flex items-center space-x-4">
            {searchable && (
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search..."
                  value={searchQuery}
                  onChange={(e) => handleSearch(e.target.value)}
                  className="perplexity-input w-full pl-10"
                />
              </div>
            )}
            {filterable && (
              <Button variant="outline" onClick={onFilter}>
                <Filter className="h-4 w-4 mr-2" />
                Filter
              </Button>
            )}
          </div>
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50/50 dark:bg-gray-800/50">
            <tr>
              {columns.map((column) => (
                <th
                  key={column.key}
                  className={cn(
                    "px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider",
                    column.sortable && "cursor-pointer hover:text-gray-700 dark:hover:text-gray-200",
                    column.width && `w-${column.width}`
                  )}
                  onClick={column.sortable ? () => handleSort(column.key) : undefined}
                >
                  <div className="flex items-center space-x-1">
                    <span>{column.title}</span>
                    {column.sortable && sortField === column.key && (
                      <span className="text-blue-600">
                        {sortDirection === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200/50 dark:divide-gray-700/50">
            {data.map((item, index) => (
              <tr
                key={index}
                className="hover:bg-gray-50/50 dark:hover:bg-gray-800/50 transition-colors"
              >
                {columns.map((column) => (
                  <td
                    key={column.key}
                    className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white"
                  >
                    {column.render 
                      ? column.render(item[column.key], item)
                      : item[column.key]
                    }
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {renderPagination()}
    </div>
  )
}