'use client'

import React, { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
// Removed unused Tabs, Input, and Textarea imports
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { 
  CheckCircle2, 
  Clock, 
  AlertCircle, 
  Target,
  TrendingUp,
  Users,
  Zap,
  Settings
} from 'lucide-react'

interface Task {
  id: string
  title: string
  description: string
  category: 'frontend' | 'backend' | 'integration' | 'testing' | 'optimization'
  priority: 'low' | 'medium' | 'high' | 'critical'
  status: 'todo' | 'in-progress' | 'completed' | 'blocked'
  assignee?: string
  dueDate?: string
  tags: string[]
  progress: number
  estimatedHours: number
  actualHours: number
  dependencies: string[]
  createdAt: string
  updatedAt: string
}

const ENHANCEMENT_TASKS: Task[] = [
  // Phase 1: Advanced Workflow Builder
  {
    id: 'task-1',
    title: 'Dynamic Node Types & Custom Components',
    description: 'Add custom React Flow node components with rich UI, validation, and error highlighting',
    category: 'frontend',
    priority: 'high',
    status: 'in-progress',
    progress: 30,
    estimatedHours: 16,
    actualHours: 5,
    tags: ['workflow', 'ui', 'react-flow'],
    dependencies: [],
    createdAt: '2025-09-27T10:00:00Z',
    updatedAt: '2025-09-27T11:30:00Z'
  },
  {
    id: 'task-2',
    title: 'Real-time Collaboration System',
    description: 'Multi-user workflow editing with conflict resolution and real-time sync',
    category: 'backend',
    priority: 'high',
    status: 'todo',
    progress: 0,
    estimatedHours: 24,
    actualHours: 0,
    tags: ['collaboration', 'websocket', 'real-time'],
    dependencies: ['task-1'],
    createdAt: '2025-09-27T10:00:00Z',
    updatedAt: '2025-09-27T10:00:00Z'
  },
  {
    id: 'task-3',
    title: 'Advanced Scheduling Engine',
    description: 'Implement cron-like scheduling, retry mechanisms, and debugging capabilities',
    category: 'backend',
    priority: 'medium',
    status: 'todo',
    progress: 0,
    estimatedHours: 20,
    actualHours: 0,
    tags: ['scheduling', 'cron', 'debugging'],
    dependencies: [],
    createdAt: '2025-09-27T10:00:00Z',
    updatedAt: '2025-09-27T10:00:00Z'
  },

  // Phase 2: Enhanced Agent Intelligence
  {
    id: 'task-4',
    title: 'AI-Powered Agent Selection',
    description: 'Implement intelligent agent matching based on task requirements and performance',
    category: 'backend',
    priority: 'high',
    status: 'todo',
    progress: 0,
    estimatedHours: 18,
    actualHours: 0,
    tags: ['ai', 'agent-selection', 'optimization'],
    dependencies: [],
    createdAt: '2025-09-27T10:00:00Z',
    updatedAt: '2025-09-27T10:00:00Z'
  },
  {
    id: 'task-5',
    title: 'Performance Analytics Dashboard',
    description: 'Real-time metrics, trend analysis, and performance optimization suggestions',
    category: 'frontend',
    priority: 'medium',
    status: 'todo',
    progress: 0,
    estimatedHours: 14,
    actualHours: 0,
    tags: ['analytics', 'dashboard', 'metrics'],
    dependencies: ['task-4'],
    createdAt: '2025-09-27T10:00:00Z',
    updatedAt: '2025-09-27T10:00:00Z'
  },

  // Phase 3: Multi-Modal Processing
  {
    id: 'task-6',
    title: 'Advanced File Processing',
    description: 'Support for images, audio, video with AI-powered content analysis',
    category: 'backend',
    priority: 'high',
    status: 'todo',
    progress: 0,
    estimatedHours: 22,
    actualHours: 0,
    tags: ['multimodal', 'ai', 'file-processing'],
    dependencies: [],
    createdAt: '2025-09-27T10:00:00Z',
    updatedAt: '2025-09-27T10:00:00Z'
  },
  {
    id: 'task-7',
    title: 'Smart Content Generation',
    description: 'AI-powered content creation with templates and customization options',
    category: 'integration',
    priority: 'medium',
    status: 'todo',
    progress: 0,
    estimatedHours: 16,
    actualHours: 0,
    tags: ['content-generation', 'ai', 'templates'],
    dependencies: ['task-6'],
    createdAt: '2025-09-27T10:00:00Z',
    updatedAt: '2025-09-27T10:00:00Z'
  },

  // Phase 4: Advanced Automation
  {
    id: 'task-8',
    title: 'Workflow Templates & Marketplace',
    description: 'Create, share, and discover workflow templates with community features',
    category: 'frontend',
    priority: 'medium',
    status: 'todo',
    progress: 0,
    estimatedHours: 20,
    actualHours: 0,
    tags: ['templates', 'marketplace', 'community'],
    dependencies: ['task-1', 'task-2'],
    createdAt: '2025-09-27T10:00:00Z',
    updatedAt: '2025-09-27T10:00:00Z'
  },
  {
    id: 'task-9',
    title: 'API Integration Hub',
    description: 'Connect with external services, webhooks, and third-party APIs',
    category: 'integration',
    priority: 'high',
    status: 'todo',
    progress: 0,
    estimatedHours: 18,
    actualHours: 0,
    tags: ['api', 'integration', 'webhooks'],
    dependencies: [],
    createdAt: '2025-09-27T10:00:00Z',
    updatedAt: '2025-09-27T10:00:00Z'
  },

  // Phase 5: More Features
  {
    id: 'task-10',
    title: 'Advanced Security & Permissions',
    description: 'Role-based access control, audit logs, and security monitoring',
    category: 'backend',
    priority: 'critical',
    status: 'todo',
    progress: 0,
    estimatedHours: 24,
    actualHours: 0,
    tags: ['security', 'permissions', 'audit'],
    dependencies: ['task-2'],
    createdAt: '2025-09-27T10:00:00Z',
    updatedAt: '2025-09-27T10:00:00Z'
  }
]

const TaskManager: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>(ENHANCEMENT_TASKS)
  const [filterStatus, setFilterStatus] = useState<string>('all')
  const [filterCategory, setFilterCategory] = useState<string>('all')
  const [filterPriority, setFilterPriority] = useState<string>('all')
  
  const filteredTasks = tasks.filter(task => {
    if (filterStatus !== 'all' && task.status !== filterStatus) return false
    if (filterCategory !== 'all' && task.category !== filterCategory) return false
    if (filterPriority !== 'all' && task.priority !== filterPriority) return false
    return true
  })

  const getStatusColor = (status: Task['status']) => {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-100 border-green-200'
      case 'in-progress': return 'text-blue-600 bg-blue-100 border-blue-200'
      case 'blocked': return 'text-red-600 bg-red-100 border-red-200'
      default: return 'text-gray-600 bg-gray-100 border-gray-200'
    }
  }

  const getPriorityColor = (priority: Task['priority']) => {
    switch (priority) {
      case 'critical': return 'text-red-600 bg-red-100 border-red-200'
      case 'high': return 'text-orange-600 bg-orange-100 border-orange-200'
      case 'medium': return 'text-yellow-600 bg-yellow-100 border-yellow-200'
      default: return 'text-gray-600 bg-gray-100 border-gray-200'
    }
  }

  const getStatusIcon = (status: Task['status']) => {
    switch (status) {
      case 'completed': return <CheckCircle2 className="h-4 w-4" />
      case 'in-progress': return <Clock className="h-4 w-4" />
      case 'blocked': return <AlertCircle className="h-4 w-4" />
      default: return <Target className="h-4 w-4" />
    }
  }

  const getCategoryIcon = (category: Task['category']) => {
    switch (category) {
      case 'frontend': return <Zap className="h-4 w-4" />
      case 'backend': return <Settings className="h-4 w-4" />
      case 'integration': return <Users className="h-4 w-4" />
      default: return <Target className="h-4 w-4" />
    }
  }

  const calculateOverallProgress = () => {
    const totalTasks = tasks.length
    
    const progressSum = tasks.reduce((sum, task) => sum + task.progress, 0)
    return Math.round(progressSum / totalTasks)
  }

  const updateTaskStatus = (taskId: string, status: Task['status']) => {
    setTasks(prev => prev.map(task => 
      task.id === taskId 
        ? { ...task, status, updatedAt: new Date().toISOString() }
        : task
    ))
  }

  return (
    <div className="space-y-6">
      {/* Header with Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              <Target className="h-5 w-5 text-blue-500" />
              <div>
                <p className="text-2xl font-bold">{tasks.length}</p>
                <p className="text-sm text-muted-foreground">Total Tasks</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              <CheckCircle2 className="h-5 w-5 text-green-500" />
              <div>
                <p className="text-2xl font-bold">
                  {tasks.filter(t => t.status === 'completed').length}
                </p>
                <p className="text-sm text-muted-foreground">Completed</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              <Clock className="h-5 w-5 text-blue-500" />
              <div>
                <p className="text-2xl font-bold">
                  {tasks.filter(t => t.status === 'in-progress').length}
                </p>
                <p className="text-sm text-muted-foreground">In Progress</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              <TrendingUp className="h-5 w-5 text-purple-500" />
              <div>
                <p className="text-2xl font-bold">{calculateOverallProgress()}%</p>
                <p className="text-sm text-muted-foreground">Overall Progress</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Progress Overview */}
      <Card>
        <CardHeader>
          <CardTitle>Enhancement Progress</CardTitle>
          <CardDescription>
            Overall progress of the multi-agent system enhancement project
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Project Completion</span>
              <span>{calculateOverallProgress()}%</span>
            </div>
            <Progress value={calculateOverallProgress()} className="w-full" />
          </div>
        </CardContent>
      </Card>

      {/* Filters and Controls */}
      <div className="flex flex-wrap gap-4 items-center">
        <Select value={filterStatus} onValueChange={setFilterStatus}>
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="All Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="todo">To Do</SelectItem>
            <SelectItem value="in-progress">In Progress</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
            <SelectItem value="blocked">Blocked</SelectItem>
          </SelectContent>
        </Select>

        <Select value={filterCategory} onValueChange={setFilterCategory}>
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="All Categories" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Categories</SelectItem>
            <SelectItem value="frontend">Frontend</SelectItem>
            <SelectItem value="backend">Backend</SelectItem>
            <SelectItem value="integration">Integration</SelectItem>
            <SelectItem value="testing">Testing</SelectItem>
            <SelectItem value="optimization">Optimization</SelectItem>
          </SelectContent>
        </Select>

        <Select value={filterPriority} onValueChange={setFilterPriority}>
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="All Priorities" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Priorities</SelectItem>
            <SelectItem value="critical">Critical</SelectItem>
            <SelectItem value="high">High</SelectItem>
            <SelectItem value="medium">Medium</SelectItem>
            <SelectItem value="low">Low</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Task List */}
      <div className="grid gap-4">
        {filteredTasks.map((task) => (
          <Card key={task.id} className="hover:shadow-md transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    {getStatusIcon(task.status)}
                    <h3 className="font-semibold text-lg">{task.title}</h3>
                    <Badge 
                      className={`px-2 py-1 text-xs border ${getStatusColor(task.status)}`}
                    >
                      {task.status.replace('-', ' ').toUpperCase()}
                    </Badge>
                    <Badge 
                      className={`px-2 py-1 text-xs border ${getPriorityColor(task.priority)}`}
                    >
                      {task.priority.toUpperCase()}
                    </Badge>
                  </div>
                  
                  <p className="text-muted-foreground mb-4">{task.description}</p>
                  
                  <div className="flex items-center space-x-6 mb-4">
                    <div className="flex items-center space-x-2">
                      {getCategoryIcon(task.category)}
                      <span className="text-sm capitalize">{task.category}</span>
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {task.estimatedHours}h estimated
                    </div>
                    {task.actualHours > 0 && (
                      <div className="text-sm text-muted-foreground">
                        {task.actualHours}h actual
                      </div>
                    )}
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Progress</span>
                      <span>{task.progress}%</span>
                    </div>
                    <Progress value={task.progress} className="w-full" />
                  </div>
                  
                  {task.tags.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-4">
                      {task.tags.map((tag, index) => (
                        <Badge key={index} variant="secondary" className="text-xs">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
                
                <div className="ml-4">
                  <Select 
                    value={task.status} 
                    onValueChange={(value: Task['status']) => updateTaskStatus(task.id, value)}
                  >
                    <SelectTrigger className="w-[120px]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="todo">To Do</SelectItem>
                      <SelectItem value="in-progress">In Progress</SelectItem>
                      <SelectItem value="completed">Completed</SelectItem>
                      <SelectItem value="blocked">Blocked</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}

export default TaskManager