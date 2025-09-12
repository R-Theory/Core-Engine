'use client'

import { useQuery } from '@tanstack/react-query'
import { coursesApi, assignmentsApi, workflowsApi } from '@/lib/api'
import { useAuthStore } from '@/stores/authStore'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { BookOpen, Calendar, Zap, Plus } from 'lucide-react'

export default function DashboardPage() {
  const { user } = useAuthStore()

  const { data: courses = [] } = useQuery({
    queryKey: ['courses'],
    queryFn: () => coursesApi.getCourses().then(res => res.data),
  })

  const { data: assignments = [] } = useQuery({
    queryKey: ['assignments'],
    queryFn: () => assignmentsApi.getAssignments().then(res => res.data),
  })

  const { data: workflows = [] } = useQuery({
    queryKey: ['workflows'],
    queryFn: () => workflowsApi.getWorkflows().then(res => res.data),
  })

  const upcomingAssignments = assignments
    .filter((a: any) => a.due_date && new Date(a.due_date) > new Date())
    .slice(0, 5)

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          Welcome back, {user?.first_name || user?.username}!
        </h1>
        <p className="text-gray-600 mt-2">
          Here's what's happening with your studies today.
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Courses</CardTitle>
            <BookOpen className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{courses.length}</div>
            <p className="text-xs text-muted-foreground">
              Courses this semester
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Upcoming Tasks</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{upcomingAssignments.length}</div>
            <p className="text-xs text-muted-foreground">
              Due in the next 7 days
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Workflows</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{workflows.filter((w: any) => w.is_active).length}</div>
            <p className="text-xs text-muted-foreground">
              Automation workflows
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Upcoming Assignments */}
        <Card>
          <CardHeader>
            <CardTitle>Upcoming Assignments</CardTitle>
          </CardHeader>
          <CardContent>
            {upcomingAssignments.length > 0 ? (
              <div className="space-y-4">
                {upcomingAssignments.map((assignment: any) => (
                  <div key={assignment.id} className="flex items-center justify-between p-3 border rounded-lg">
                    <div>
                      <h4 className="font-medium">{assignment.title}</h4>
                      <p className="text-sm text-gray-600">
                        Due: {new Date(assignment.due_date).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="text-sm text-gray-500">
                      {assignment.status}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <Calendar className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">No upcoming assignments</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Courses */}
        <Card>
          <CardHeader>
            <CardTitle>Your Courses</CardTitle>
          </CardHeader>
          <CardContent>
            {courses.length > 0 ? (
              <div className="space-y-4">
                {courses.slice(0, 5).map((course: any) => (
                  <div key={course.id} className="flex items-center justify-between p-3 border rounded-lg">
                    <div>
                      <h4 className="font-medium">{course.name}</h4>
                      <p className="text-sm text-gray-600">
                        {course.code} • {course.instructor}
                      </p>
                    </div>
                    <Button variant="outline" size="sm">
                      View
                    </Button>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600 mb-4">No courses yet</p>
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  Add Course
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <div className="mt-8">
        <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Button variant="outline" className="h-20 flex-col">
            <BookOpen className="h-6 w-6 mb-2" />
            Add Course
          </Button>
          <Button variant="outline" className="h-20 flex-col">
            <Calendar className="h-6 w-6 mb-2" />
            New Assignment
          </Button>
          <Button variant="outline" className="h-20 flex-col">
            <Zap className="h-6 w-6 mb-2" />
            Create Workflow
          </Button>
          <Button variant="outline" className="h-20 flex-col">
            <Plus className="h-6 w-6 mb-2" />
            Upload Resource
          </Button>
        </div>
      </div>
    </div>
  )
}