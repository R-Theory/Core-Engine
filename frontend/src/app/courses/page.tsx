'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { coursesApi } from '@/lib/api'
import { Layout } from '@/components/layout/Layout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { PageHeader } from '@/components/ui/page-header'
import { EmptyState } from '@/components/ui/empty-state'
import { 
  Plus, 
  Search, 
  Filter, 
  BookOpen, 
  Calendar, 
  User, 
  MoreVertical,
  Grid3X3,
  List,
  Star,
  Clock
} from 'lucide-react'

export default function CoursesPage() {
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [searchQuery, setSearchQuery] = useState('')

  const { data: courses = [], isLoading } = useQuery({
    queryKey: ['courses'],
    queryFn: () => coursesApi.getCourses().then(res => res.data),
  })

  const filteredCourses = courses.filter((course: any) =>
    course.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    course.code?.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <PageHeader
          title="Courses"
          description="Manage your academic courses and track progress"
          actions={
            <Button className="perplexity-button">
              <Plus className="h-4 w-4 mr-2" />
              Add Course
            </Button>
          }
        />

        {/* Search and Filters */}
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search courses..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="perplexity-input w-full pl-10"
            />
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" className="border-gray-200">
              <Filter className="h-4 w-4 mr-2" />
              Filter
            </Button>
            <div className="flex border border-gray-200 dark:border-gray-700 rounded-lg p-1">
              <button
                onClick={() => setViewMode('grid')}
                className={`p-2 rounded ${viewMode === 'grid' ? 'bg-gray-100 dark:bg-gray-800' : 'hover:bg-gray-50 dark:hover:bg-gray-800'}`}
              >
                <Grid3X3 className="h-4 w-4" />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`p-2 rounded ${viewMode === 'list' ? 'bg-gray-100 dark:bg-gray-800' : 'hover:bg-gray-50 dark:hover:bg-gray-800'}`}
              >
                <List className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Courses Grid/List */}
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(6)].map((_, i) => (
              <Card key={i} className="perplexity-card border-0 animate-pulse">
                <CardHeader>
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
                  <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded"></div>
                    <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-2/3"></div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : filteredCourses.length > 0 ? (
          <div className={viewMode === 'grid' 
            ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6'
            : 'space-y-4'
          }>
            {filteredCourses.map((course: any) => (
              <Card key={course.id} className="perplexity-card border-0 group hover:shadow-xl transition-all duration-300 cursor-pointer">
                <CardHeader className="flex flex-row items-start justify-between space-y-0">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                      <span className="text-xs font-medium text-blue-600 dark:text-blue-400 uppercase tracking-wider">
                        {course.semester} {course.year}
                      </span>
                    </div>
                    <CardTitle className="text-lg font-semibold text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                      {course.name}
                    </CardTitle>
                    <p className="text-sm text-gray-500 dark:text-gray-400 font-mono">
                      {course.code}
                    </p>
                  </div>
                  <button className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors opacity-0 group-hover:opacity-100">
                    <MoreVertical className="h-4 w-4 text-gray-400" />
                  </button>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-sm text-gray-600 dark:text-gray-300 line-clamp-2">
                    {course.description || 'No description available'}
                  </p>
                  
                  <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
                    <div className="flex items-center gap-1">
                      <User className="h-3 w-3" />
                      <span>{course.instructor || 'TBA'}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      <span>Active</span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-2 border-t border-gray-100 dark:border-gray-800">
                    <div className="flex items-center gap-1">
                      <Star className="h-4 w-4 text-yellow-500 fill-current" />
                      <span className="text-sm font-medium text-gray-700 dark:text-gray-300">4.2</span>
                    </div>
                    <Button variant="ghost" size="sm" className="text-blue-600 hover:text-blue-700 hover:bg-blue-50 dark:hover:bg-blue-900/20">
                      View Course
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <Card className="perplexity-card border-0">
            <EmptyState
              icon={BookOpen}
              title="No courses found"
              description={searchQuery 
                ? `No courses match "${searchQuery}". Try adjusting your search.`
                : "Get started by adding your first course to begin tracking your academic progress."
              }
              action={{
                label: "Add Your First Course",
                onClick: () => console.log('Add course'),
                icon: Plus
              }}
            />
          </Card>
        )}
      </div>
    </Layout>
  )
}