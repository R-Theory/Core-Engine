'use client'

import { useQuery } from '@tanstack/react-query'
import { coursesApi, assignmentsApi, workflowsApi } from '@/lib/api'
import { useAuthStore } from '@/stores/authStore'
import { useCanvas, useCanvasCourses, useCanvasAssignments, useCanvasConnection } from '@/providers/CanvasProvider'
import { Layout } from '@/components/layout/Layout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useRouter } from 'next/navigation'
import { 
  BookOpen, 
  Calendar, 
  Zap, 
  Plus, 
  TrendingUp, 
  Clock, 
  Target,
  ArrowRight,
  Sparkles,
  Activity
} from 'lucide-react'
import { formatDate } from '@/lib/utils'

export default function DashboardPage() {
  const { user } = useAuthStore()
  const router = useRouter()

  // Canvas integration
  const { isCanvasConnected, hasCanvasData, activeCanvas } = useCanvas()
  const { courses: canvasCourses, loading: coursesLoading } = useCanvasCourses()
  const { assignments: canvasAssignments, loading: assignmentsLoading } = useCanvasAssignments()

  // Fallback to local API if Canvas not connected
  const { data: localCourses = [] } = useQuery({
    queryKey: ['courses'],
    queryFn: () => coursesApi.getCourses().then(res => res.data),
    enabled: !isCanvasConnected
  })

  const { data: localAssignments = [] } = useQuery({
    queryKey: ['assignments'],
    queryFn: () => assignmentsApi.getAssignments().then(res => res.data),
    enabled: !isCanvasConnected
  })

  const { data: workflows = [] } = useQuery({
    queryKey: ['workflows'],
    queryFn: () => workflowsApi.getWorkflows().then(res => res.data),
  })

  // Use Canvas data when available, otherwise use local data
  const courses = isCanvasConnected ? canvasCourses : localCourses
  const assignments = isCanvasConnected ? canvasAssignments : localAssignments

  const upcomingAssignments = assignments
    .filter((a: any) => a.due_date && new Date(a.due_date) > new Date())
    .slice(0, 5)

  const recentActivity = [
    { type: 'course', title: 'New assignment in CS 101', time: '2 hours ago', icon: BookOpen },
    { type: 'workflow', title: 'Weekly sync completed', time: '4 hours ago', icon: Zap },
    { type: 'resource', title: 'Uploaded lecture notes', time: '1 day ago', icon: Plus },
  ]

  return (
    <Layout>
      <div className="space-y-8">
        {/* Welcome Header */}
        <div className="relative overflow-hidden">
          <div className="perplexity-card p-8 bg-gradient-to-r from-blue-600/10 via-purple-600/10 to-pink-600/10 border-0">
            <div className="relative z-10">
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                Welcome back, {user?.first_name || user?.username}! 👋
              </h1>
              <p className="text-lg text-gray-600 dark:text-gray-300 mb-6">
                Here's what's happening with your studies today.
              </p>
              <div className="flex flex-wrap gap-4">
                <Button 
                  className="perplexity-button"
                  onClick={() => router.push('/ai-chat')}
                >
                  <Sparkles className="h-4 w-4 mr-2" />
                  AI Study Assistant
                </Button>
                <Button variant="outline" className="border-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800">
                  <Plus className="h-4 w-4 mr-2" />
                  Quick Add
                </Button>
              </div>
            </div>
            <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-blue-400/20 to-purple-400/20 rounded-full blur-3xl"></div>
          </div>
        </div>

        {/* Canvas Connection Status */}
        {isCanvasConnected && (
          <div className="mb-6 p-4 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 rounded-lg">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 bg-emerald-500 rounded-full"></div>
                <div>
                  <p className="text-sm font-medium text-emerald-800 dark:text-emerald-200">
                    Connected to {activeCanvas?.name || 'Canvas'}
                  </p>
                  <p className="text-xs text-emerald-600 dark:text-emerald-400">
                    Academic data is synced from Canvas LMS
                  </p>
                </div>
              </div>
              <button
                onClick={() => router.push('/settings')}
                className="text-xs text-emerald-600 hover:text-emerald-700 dark:text-emerald-400 dark:hover:text-emerald-300"
              >
                Manage
              </button>
            </div>
          </div>
        )}

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card className="perplexity-card border-0">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400 flex items-center gap-2">
                Active Courses
                {isCanvasConnected && (
                  <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-xs rounded-full">
                    Canvas
                  </span>
                )}
              </CardTitle>
              <BookOpen className="h-5 w-5 text-blue-600" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-gray-900 dark:text-white mb-1">
                {coursesLoading ? '...' : courses.length}
              </div>
              <p className="text-sm text-gray-500 dark:text-gray-400 flex items-center">
                <TrendingUp className="h-3 w-3 mr-1 text-green-500" />
                {isCanvasConnected ? 'From Canvas' : '+2 this semester'}
              </p>
            </CardContent>
          </Card>

          <Card className="perplexity-card border-0">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400 flex items-center gap-2">
                Due This Week
                {isCanvasConnected && (
                  <span className="px-2 py-1 bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300 text-xs rounded-full">
                    Canvas
                  </span>
                )}
              </CardTitle>
              <Clock className="h-5 w-5 text-orange-600" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-gray-900 dark:text-white mb-1">
                {assignmentsLoading ? '...' : upcomingAssignments.length}
              </div>
              <p className="text-sm text-gray-500 dark:text-gray-400 flex items-center">
                <Target className="h-3 w-3 mr-1 text-orange-500" />
                {isCanvasConnected ? 'From Canvas' : '3 high priority'}
              </p>
            </CardContent>
          </Card>

          <Card className="perplexity-card border-0">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
                Active Workflows
              </CardTitle>
              <Zap className="h-5 w-5 text-purple-600" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-gray-900 dark:text-white mb-1">
                {workflows.filter((w: any) => w.is_active).length}
              </div>
              <p className="text-sm text-gray-500 dark:text-gray-400 flex items-center">
                <Activity className="h-3 w-3 mr-1 text-purple-500" />
                2 running now
              </p>
            </CardContent>
          </Card>

          <Card className="perplexity-card border-0">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
                Study Streak
              </CardTitle>
              <Calendar className="h-5 w-5 text-green-600" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-gray-900 dark:text-white mb-1">
                12
              </div>
              <p className="text-sm text-gray-500 dark:text-gray-400 flex items-center">
                <TrendingUp className="h-3 w-3 mr-1 text-green-500" />
                days in a row
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Upcoming Assignments */}
          <div className="lg:col-span-2">
            <Card className="perplexity-card border-0">
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="text-xl font-semibold text-gray-900 dark:text-white">
                  Upcoming Assignments
                </CardTitle>
                <Button variant="ghost" size="sm" className="text-blue-600 hover:text-blue-700">
                  View all
                  <ArrowRight className="h-4 w-4 ml-1" />
                </Button>
              </CardHeader>
              <CardContent className="space-y-4">
                {upcomingAssignments.length > 0 ? (
                  upcomingAssignments.map((assignment: any) => (
                    <div
                      key={assignment.id}
                      className="flex items-center justify-between p-4 bg-gray-50/50 dark:bg-gray-800/50 rounded-xl hover:bg-gray-100/50 dark:hover:bg-gray-700/50 transition-all duration-200 group cursor-pointer"
                    >
                      <div className="flex items-center space-x-4">
                        <div className="w-3 h-3 bg-orange-500 rounded-full"></div>
                        <div>
                          <h4 className="font-medium text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                            {assignment.title}
                          </h4>
                          <p className="text-sm text-gray-500 dark:text-gray-400">
                            Due: {formatDate(assignment.due_date)}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                          assignment.status === 'active' 
                            ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                            : 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400'
                        }`}>
                          {assignment.status}
                        </span>
                        <ArrowRight className="h-4 w-4 text-gray-400 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors" />
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-12">
                    <Calendar className="h-16 w-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                      No upcoming assignments
                    </h3>
                    <p className="text-gray-500 dark:text-gray-400 mb-4">
                      You're all caught up! Great work.
                    </p>
                    <Button className="perplexity-button">
                      <Plus className="h-4 w-4 mr-2" />
                      Add Assignment
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Recent Activity & Quick Actions */}
          <div className="space-y-6">
            {/* Recent Activity */}
            <Card className="perplexity-card border-0">
              <CardHeader>
                <CardTitle className="text-lg font-semibold text-gray-900 dark:text-white">
                  Recent Activity
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {recentActivity.map((activity, index) => (
                  <div key={index} className="flex items-start space-x-3 p-3 rounded-lg hover:bg-gray-50/50 dark:hover:bg-gray-800/50 transition-colors cursor-pointer">
                    <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center">
                      <activity.icon className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 dark:text-white">
                        {activity.title}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {activity.time}
                      </p>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Quick Actions */}
            <Card className="perplexity-card border-0">
              <CardHeader>
                <CardTitle className="text-lg font-semibold text-gray-900 dark:text-white">
                  Quick Actions
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button variant="outline" className="w-full justify-start h-12 border-gray-200 hover:bg-gray-50 dark:hover:bg-gray-800">
                  <BookOpen className="h-5 w-5 mr-3 text-blue-600" />
                  <span className="text-left">
                    <div className="font-medium">Add Course</div>
                    <div className="text-xs text-gray-500">Create a new course</div>
                  </span>
                </Button>
                <Button variant="outline" className="w-full justify-start h-12 border-gray-200 hover:bg-gray-50 dark:hover:bg-gray-800">
                  <Zap className="h-5 w-5 mr-3 text-purple-600" />
                  <span className="text-left">
                    <div className="font-medium">New Workflow</div>
                    <div className="text-xs text-gray-500">Automate your tasks</div>
                  </span>
                </Button>
                <Button variant="outline" className="w-full justify-start h-12 border-gray-200 hover:bg-gray-50 dark:hover:bg-gray-800">
                  <Plus className="h-5 w-5 mr-3 text-green-600" />
                  <span className="text-left">
                    <div className="font-medium">Upload Resource</div>
                    <div className="text-xs text-gray-500">Add files or links</div>
                  </span>
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </Layout>
  )
}