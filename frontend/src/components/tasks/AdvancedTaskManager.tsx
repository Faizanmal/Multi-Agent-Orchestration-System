'use client'

import React, { useState, useCallback, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  CheckSquare,
  Clock,
  User,
  Calendar,
  AlertCircle,
  Plus,
  Search,
  MoreHorizontal,
  Edit,
  Star,
  Target,
  TrendingUp,
  Zap,
  Loader2,
  Trash2,
} from 'lucide-react'
import {
  getTasks,
  createTask,
  updateTask,
  deleteTask,
  type Task as ApiTask,
} from '@/lib/api'

type UiStatus = 'todo' | 'in-progress' | 'completed' | 'blocked'
type UiPriority = 'low' | 'medium' | 'high' | 'urgent'
type UiCategory = 'feature' | 'bug' | 'improvement' | 'research' | 'documentation'

interface SubTask {
  id: string
  title: string
  completed: boolean
}

interface Task {
  id: string
  title: string
  description: string
  status: UiStatus
  priority: UiPriority
  category: UiCategory
  assignee?: string
  dueDate?: string
  createdAt: string
  updatedAt: string
  tags: string[]
  subtasks: SubTask[]
  estimatedHours: number
  actualHours?: number
  dependencies: string[]
}

interface TaskStats {
  total: number
  completed: number
  inProgress: number
  todo: number
  blocked: number
  completionRate: number
  avgCompletionTime: number
}

function mapApiStatusToUi(status: string): UiStatus {
  switch (status) {
    case 'pending':
      return 'todo'
    case 'in_progress':
      return 'in-progress'
    case 'completed':
      return 'completed'
    case 'failed':
    case 'cancelled':
      return 'blocked'
    case 'todo':
    case 'in-progress':
    case 'blocked':
      return status
    default:
      return 'todo'
  }
}

function mapUiStatusToApi(status: UiStatus): ApiTask['status'] {
  switch (status) {
    case 'todo':
      return 'pending'
    case 'in-progress':
      return 'in_progress'
    case 'completed':
      return 'completed'
    case 'blocked':
      return 'failed'
    default:
      return 'pending'
  }
}

function mapApiPriorityToUi(priority: unknown): UiPriority {
  if (typeof priority === 'number') {
    if (priority >= 4) return 'urgent'
    if (priority >= 3) return 'high'
    if (priority >= 2) return 'medium'
    return 'low'
  }
  const p = String(priority || 'normal').toLowerCase()
  if (p === 'urgent') return 'urgent'
  if (p === 'high') return 'high'
  if (p === 'low') return 'low'
  if (p === 'medium' || p === 'normal') return 'medium'
  return 'medium'
}

function mapUiPriorityToApi(priority: UiPriority): string {
  switch (priority) {
    case 'medium':
      return 'normal'
    default:
      return priority
  }
}

function mapApiTaskToUi(raw: ApiTask & Record<string, unknown>): Task {
  const agent = raw.assigned_agent as unknown
  let assignee: string | undefined
  if (typeof agent === 'string') assignee = agent
  else if (agent && typeof agent === 'object' && 'name' in agent) {
    assignee = String((agent as { name: string }).name)
  }

  const subtasksRaw = Array.isArray(raw.subtasks) ? raw.subtasks : []
  const subtasks: SubTask[] = subtasksRaw.map((st: Record<string, unknown>, i: number) => ({
    id: String(st.id ?? `${raw.id}-${i}`),
    title: String(st.title ?? 'Subtask'),
    completed: st.status === 'completed' || st.completed === true,
  }))

  const durationSec =
    typeof raw.duration === 'number'
      ? raw.duration
      : typeof raw.estimated_duration === 'number'
        ? raw.estimated_duration
        : undefined
  const actualSec =
    typeof raw.actual_duration === 'number' ? raw.actual_duration : undefined

  const categoryRaw = String(raw.task_type || raw.category || 'feature').toLowerCase()
  const category = (
    ['feature', 'bug', 'improvement', 'research', 'documentation'].includes(categoryRaw)
      ? categoryRaw
      : 'feature'
  ) as UiCategory

  const tags =
    Array.isArray(raw.tags)
      ? (raw.tags as string[])
      : Array.isArray((raw.requirements as { tags?: string[] })?.tags)
        ? ((raw.requirements as { tags: string[] }).tags)
        : []

  return {
    id: String(raw.id),
    title: raw.title || 'Untitled',
    description: raw.description || '',
    status: mapApiStatusToUi(String(raw.status)),
    priority: mapApiPriorityToUi(raw.priority),
    category,
    assignee,
    dueDate: raw.completed_at ? undefined : undefined,
    createdAt: String(raw.created_at || new Date().toISOString()),
    updatedAt: String(raw.updated_at || raw.created_at || new Date().toISOString()),
    tags,
    subtasks,
    estimatedHours: durationSec ? Math.max(1, Math.round(durationSec / 3600)) : 8,
    actualHours: actualSec ? Math.round((actualSec / 3600) * 10) / 10 : undefined,
    dependencies: [],
  }
}

const AdvancedTaskManager: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [priorityFilter, setPriorityFilter] = useState<string>('all')
  const [assigneeFilter, setAssigneeFilter] = useState<string>('all')
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [newTask, setNewTask] = useState<Partial<Task>>({
    title: '',
    description: '',
    priority: 'medium',
    category: 'feature',
    estimatedHours: 8,
    tags: []
  })

  const loadTasks = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const res = await getTasks()
      const results = (res.results || []) as Array<ApiTask & Record<string, unknown>>
      setTasks(results.map(mapApiTaskToUi))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load tasks')
      setTasks([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    setTimeout(() => { loadTasks() }, 0)
  }, [loadTasks])

  const filteredTasks = tasks.filter(task => {
    const matchesSearch = task.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         task.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         task.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
    
    const matchesStatus = statusFilter === 'all' || task.status === statusFilter
    const matchesPriority = priorityFilter === 'all' || task.priority === priorityFilter
    const matchesAssignee = assigneeFilter === 'all' || task.assignee === assigneeFilter
    
    return matchesSearch && matchesStatus && matchesPriority && matchesAssignee
  })

  const assignees = Array.from(new Set(tasks.map(t => t.assignee).filter(Boolean))) as string[]

  const taskStats: TaskStats = {
    total: tasks.length,
    completed: tasks.filter(t => t.status === 'completed').length,
    inProgress: tasks.filter(t => t.status === 'in-progress').length,
    todo: tasks.filter(t => t.status === 'todo').length,
    blocked: tasks.filter(t => t.status === 'blocked').length,
    completionRate: tasks.length
      ? (tasks.filter(t => t.status === 'completed').length / tasks.length) * 100
      : 0,
    avgCompletionTime: (() => {
      const withHours = tasks.filter(t => t.actualHours)
      if (!withHours.length) return 0
      return withHours.reduce((acc, t) => acc + (t.actualHours || 0), 0) / withHours.length
    })()
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent': return 'bg-red-100 text-red-800 border-red-200'
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-200'
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'low': return 'bg-green-100 text-green-800 border-green-200'
      default: return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800'
      case 'in-progress': return 'bg-blue-100 text-blue-800'
      case 'blocked': return 'bg-red-100 text-red-800'
      case 'todo': return 'bg-gray-100 text-gray-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'feature': return <Star className="w-4 h-4" />
      case 'bug': return <AlertCircle className="w-4 h-4" />
      case 'improvement': return <TrendingUp className="w-4 h-4" />
      case 'research': return <Target className="w-4 h-4" />
      case 'documentation': return <CheckSquare className="w-4 h-4" />
      default: return <CheckSquare className="w-4 h-4" />
    }
  }

  const handleCreateTask = useCallback(async () => {
    try {
      setSaving(true)
      setError(null)
      const created = await createTask({
        title: newTask.title || 'New Task',
        description: newTask.description || '',
        status: 'pending',
        priority: mapUiPriorityToApi(newTask.priority || 'medium') as unknown as number,
      } as Partial<ApiTask>)
      setTasks(prev => [...prev, mapApiTaskToUi(created as ApiTask & Record<string, unknown>)])
      setNewTask({
        title: '',
        description: '',
        priority: 'medium',
        category: 'feature',
        estimatedHours: 8,
        tags: []
      })
      setShowCreateDialog(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create task')
    } finally {
      setSaving(false)
    }
  }, [newTask])

  const handleUpdateTaskStatus = useCallback(async (taskId: string, newStatus: Task['status']) => {
    const previous = tasks
    setTasks(prev => prev.map(task =>
      task.id === taskId
        ? { ...task, status: newStatus, updatedAt: new Date().toISOString() }
        : task
    ))
    try {
      await updateTask(taskId, { status: mapUiStatusToApi(newStatus) })
    } catch (err) {
      setTasks(previous)
      setError(err instanceof Error ? err.message : 'Failed to update task')
    }
  }, [tasks])

  const handleDeleteTask = useCallback(async (taskId: string) => {
    const previous = tasks
    setTasks(prev => prev.filter(t => t.id !== taskId))
    try {
      await deleteTask(taskId)
    } catch (err) {
      setTasks(previous)
      setError(err instanceof Error ? err.message : 'Failed to delete task')
    }
  }, [tasks])

  const TaskCard: React.FC<{ task: Task }> = ({ task }) => {
    const completedSubtasks = task.subtasks.filter(st => st.completed).length
    const totalSubtasks = task.subtasks.length
    const progress = totalSubtasks > 0 ? (completedSubtasks / totalSubtasks) * 100 : 0

    return (
      <Card className="hover:shadow-md transition-shadow cursor-pointer">
        <CardHeader className="pb-2">
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-2">
              {getCategoryIcon(task.category)}
              <CardTitle className="text-base">{task.title}</CardTitle>
            </div>
            
            <div className="flex items-center space-x-2">
              <Badge className={getPriorityColor(task.priority)}>
                {task.priority}
              </Badge>
              <Badge className={getStatusColor(task.status)}>
                {task.status.replace('-', ' ')}
              </Badge>
            </div>
          </div>
        </CardHeader>
        
        <CardContent className="space-y-3">
          <p className="text-sm text-muted-foreground line-clamp-2">
            {task.description}
          </p>
          
          {totalSubtasks > 0 && (
            <div className="space-y-1">
              <div className="flex justify-between text-sm">
                <span>Progress</span>
                <span>{completedSubtasks}/{totalSubtasks}</span>
              </div>
              <Progress value={progress} className="h-2" />
            </div>
          )}
          
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <div className="flex items-center space-x-3">
              {task.assignee && (
                <div className="flex items-center space-x-1">
                  <User className="w-3 h-3" />
                  <span>{task.assignee}</span>
                </div>
              )}
              {task.dueDate && (
                <div className="flex items-center space-x-1">
                  <Calendar className="w-3 h-3" />
                  <span>{new Date(task.dueDate).toLocaleDateString()}</span>
                </div>
              )}
              <div className="flex items-center space-x-1">
                <Clock className="w-3 h-3" />
                <span>{task.estimatedHours}h</span>
              </div>
            </div>
            
            <Button variant="ghost" size="sm">
              <MoreHorizontal className="w-4 h-4" />
            </Button>
          </div>
          
          {task.tags.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {task.tags.slice(0, 3).map(tag => (
                <Badge key={tag} variant="secondary" className="text-xs">
                  {tag}
                </Badge>
              ))}
              {task.tags.length > 3 && (
                <Badge variant="secondary" className="text-xs">
                  +{task.tags.length - 3}
                </Badge>
              )}
            </div>
          )}
          
          <div className="flex space-x-2">
            {task.status !== 'completed' && (
              <Button 
                size="sm" 
                variant="outline"
                onClick={() => handleUpdateTaskStatus(task.id, 
                  task.status === 'todo' ? 'in-progress' : 'completed'
                )}
              >
                {task.status === 'todo' ? 'Start' : 'Complete'}
              </Button>
            )}
            <Button size="sm" variant="ghost">
              <Edit className="w-4 h-4" />
            </Button>
            <Button
              size="sm"
              variant="ghost"
              className="text-destructive"
              onClick={() => handleDeleteTask(task.id)}
            >
              <Trash2 className="w-4 h-4" />
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Task Management</h1>
          <p className="text-muted-foreground">
            Organize and track your development tasks
          </p>
        </div>
        
        <Button onClick={() => setShowCreateDialog(true)}>
          <Plus className="w-4 h-4 mr-2" />
          New Task
        </Button>
      </div>

      {error && (
        <Card className="border-destructive/50 bg-destructive/5">
          <CardContent className="flex items-center gap-3 p-4 text-sm text-destructive">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
            <Button variant="outline" size="sm" className="ml-auto" onClick={loadTasks}>
              Retry
            </Button>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <CheckSquare className="w-4 h-4 text-blue-500" />
              <div>
                <p className="text-sm text-muted-foreground">Total</p>
                <p className="text-2xl font-bold">{taskStats.total}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Target className="w-4 h-4 text-gray-500" />
              <div>
                <p className="text-sm text-muted-foreground">Todo</p>
                <p className="text-2xl font-bold">{taskStats.todo}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Zap className="w-4 h-4 text-blue-500" />
              <div>
                <p className="text-sm text-muted-foreground">In Progress</p>
                <p className="text-2xl font-bold">{taskStats.inProgress}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <CheckSquare className="w-4 h-4 text-green-500" />
              <div>
                <p className="text-sm text-muted-foreground">Completed</p>
                <p className="text-2xl font-bold">{taskStats.completed}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 text-red-500" />
              <div>
                <p className="text-sm text-muted-foreground">Blocked</p>
                <p className="text-2xl font-bold">{taskStats.blocked}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <TrendingUp className="w-4 h-4 text-green-500" />
              <div>
                <p className="text-sm text-muted-foreground">Completion</p>
                <p className="text-2xl font-bold">{taskStats.completionRate.toFixed(1)}%</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="flex flex-wrap items-center gap-4">
        <div className="flex items-center space-x-2">
          <Search className="w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search tasks..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-64"
          />
        </div>
        
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="todo">Todo</SelectItem>
            <SelectItem value="in-progress">In Progress</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
            <SelectItem value="blocked">Blocked</SelectItem>
          </SelectContent>
        </Select>
        
        <Select value={priorityFilter} onValueChange={setPriorityFilter}>
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="Priority" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Priority</SelectItem>
            <SelectItem value="urgent">Urgent</SelectItem>
            <SelectItem value="high">High</SelectItem>
            <SelectItem value="medium">Medium</SelectItem>
            <SelectItem value="low">Low</SelectItem>
          </SelectContent>
        </Select>
        
        <Select value={assigneeFilter} onValueChange={setAssigneeFilter}>
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="Assignee" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Assignees</SelectItem>
            {assignees.map(name => (
              <SelectItem key={name} value={name}>{name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-16 text-muted-foreground">
          <Loader2 className="w-8 h-8 animate-spin mr-3" />
          Loading tasks...
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredTasks.map(task => (
            <TaskCard key={task.id} task={task} />
          ))}
          
          {filteredTasks.length === 0 && (
            <div className="col-span-full text-center py-12 text-muted-foreground">
              <CheckSquare className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p className="text-lg">No tasks found</p>
              <p className="text-sm">Try adjusting your filters or create a new task</p>
            </div>
          )}
        </div>
      )}

      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Create New Task</DialogTitle>
            <DialogDescription>
              Add a new task to your project workflow
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">Task Title</label>
              <Input
                placeholder="Enter task title..."
                value={newTask.title}
                onChange={(e) => setNewTask({ ...newTask, title: e.target.value })}
              />
            </div>
            
            <div>
              <label className="text-sm font-medium">Description</label>
              <Textarea
                placeholder="Describe the task..."
                rows={3}
                value={newTask.description}
                onChange={(e) => setNewTask({ ...newTask, description: e.target.value })}
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium">Priority</label>
                <Select 
                  value={newTask.priority} 
                  onValueChange={(value: Task['priority']) => setNewTask({ ...newTask, priority: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="low">Low</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="high">High</SelectItem>
                    <SelectItem value="urgent">Urgent</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <label className="text-sm font-medium">Category</label>
                <Select 
                  value={newTask.category} 
                  onValueChange={(value: Task['category']) => setNewTask({ ...newTask, category: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="feature">Feature</SelectItem>
                    <SelectItem value="bug">Bug Fix</SelectItem>
                    <SelectItem value="improvement">Improvement</SelectItem>
                    <SelectItem value="research">Research</SelectItem>
                    <SelectItem value="documentation">Documentation</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            <div>
              <label className="text-sm font-medium">Estimated Hours</label>
              <Input
                type="number"
                placeholder="8"
                value={newTask.estimatedHours}
                onChange={(e) => setNewTask({ ...newTask, estimatedHours: parseInt(e.target.value) || 8 })}
              />
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateTask} disabled={saving}>
              {saving ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Creating...
                </>
              ) : (
                'Create Task'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default AdvancedTaskManager
