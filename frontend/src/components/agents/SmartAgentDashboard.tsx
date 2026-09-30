'use client'

import React, { useState, useEffect } from 'react'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs'
import {
  Badge,
} from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import {
  Alert,
  AlertDescription,
  AlertTitle,
} from '@/components/ui/alert'
import { Progress } from '@/components/ui/progress'
import {
  Activity,
  Brain,
  Cpu,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Clock,
  Zap,
  Users,
  BarChart3,
  Eye,
  MessageSquare,
  Settings,
  Loader2,
  RefreshCw,
} from 'lucide-react'
import { useToast } from '@/hooks/use-toast'

interface AgentConfiguration {
  accuracy?: number
  avg_response_time?: number
  features?: string[]
  performance_metrics?: Record<string, unknown>
}

interface Agent {
  id: string
  name: string
  type: string
  status: string
  capabilities: string[]
  configuration: AgentConfiguration
}

interface PerformanceData {
  agent_id: string
  success_rate: number
  avg_response_time: number
  accuracy: number
  total_executions: number
  error_types: Record<string, number>
}

interface AgentRecommendation {
  agent: Agent
  suitability_score: number
  recommendation_reason: string
}

interface SystemOverview {
  agents: {
    total: number
    utilization_rate: number
    by_status: Record<string, number>
  }
  tasks: {
    total: number
    success_rate: number
    by_status: Record<string, number>
  }
  sessions: {
    total: number
    active: number
  }
  messages: {
    total: number
    agent_messages: number
  }
}

interface Insight {
  type: 'positive' | 'warning' | 'info'
  category: string
  title: string
  description: string
  impact: 'low' | 'medium' | 'high'
  actionable: boolean
  suggested_action?: string
}

interface Recommendation {
  type: string
  category: string
  title: string
  description: string
  priority: 'low' | 'medium' | 'high'
  estimated_impact: string
  actions?: string[]
}

interface DashboardData {
  overview: SystemOverview
  agent_metrics: Record<string, unknown>
  performance_trends: Record<string, unknown>
  insights: Insight[]
  recommendations: Recommendation[]
}

const SmartAgentDashboard: React.FC = () => {
  const [agents, setAgents] = useState<Agent[]>([])
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null)
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null)
  const [performanceData, setPerformanceData] = useState<PerformanceData | null>(null)
  const [agentRecommendations, setAgentRecommendations] = useState<AgentRecommendation[]>([])
  const [loading, setLoading] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  
  // Task Selection Form
  const [taskType, setTaskType] = useState('')
  const [taskDescription, setTaskDescription] = useState('')
  const [requirements, setRequirements] = useState('')

  const { toast } = useToast()

  const taskTypes = [
    'text', 'vision', 'image', 'reasoning', 'logic', 
    'action', 'execution', 'memory', 'storage', 
    'orchestration', 'coordination'
  ]
  const loadInitialData = async () => {
    setLoading(true)
    try {
      await Promise.all([
        loadAgents(),
        loadDashboardData()
      ])
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
      toast({
        title: 'Error',
        description: 'Failed to load dashboard data',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  const loadAgents = async () => {
    try {
      const response = await fetch('/api/agents/agents/')
      const data = await response.json()
      setAgents(data.results || data)
    } catch (error) {
      console.error('Error loading agents:', error)
    }
  }

  const loadDashboardData = async () => {
    try {
      const response = await fetch('/api/agents/analytics/dashboard_data/')
      const data = await response.json()
      setDashboardData(data)
    } catch (error) {
      console.error('Error loading dashboard data:', error)
    }
  }

  const refreshData = async () => {
    setRefreshing(true)
    await loadInitialData()
    setRefreshing(false)
    
    toast({
      title: 'Data Refreshed',
      description: 'Dashboard data has been updated',
    })
  }

  const selectBestAgent = async () => {
    if (!taskType || !taskDescription) {
      toast({
        title: 'Missing Information',
        description: 'Please provide task type and description',
        variant: 'destructive',
      })
      return
    }

    setLoading(true)
    try {
      const response = await fetch('/api/agents/smart-agents/select_best_agent/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          task_type: taskType,
          description: taskDescription,
          requirements: requirements ? JSON.parse(requirements) : {}
        })
      })

      const data = await response.json()
      
      if (response.ok) {
        setSelectedAgent(data.selected_agent)
        toast({
          title: 'Agent Selected',
          description: `${data.selected_agent.name} has been selected for your task`,
        })
      } else {
        toast({
          title: 'Selection Failed',
          description: data.error || 'Failed to select agent',
          variant: 'destructive',
        })
      }
    } catch (error) {
      console.error('Failed to select agent:', error)
      toast({
        title: 'Error',
        description: 'Failed to select agent',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  const getAgentRecommendations = async () => {
    if (!taskType || !taskDescription) {
      toast({
        title: 'Missing Information',
        description: 'Please provide task type and description',
        variant: 'destructive',
      })
      return
    }

    setLoading(true)
    try {
      const response = await fetch('/api/agents/smart-agents/get_agent_recommendations/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          task_type: taskType,
          description: taskDescription,
          count: 5
        })
      })

      const data = await response.json()
      
      if (response.ok) {
        setAgentRecommendations(data.recommendations)
      } else {
        toast({
          title: 'Failed to get recommendations',
          description: data.error || 'Unknown error occurred',
          variant: 'destructive',
        })
      }
    } catch (error) {
      console.error('Failed to get agent recommendations:', error)
      toast({
        title: 'Error',
        description: 'Failed to get agent recommendations',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  const loadAgentPerformance = async (agentId: string) => {
    try {
      const response = await fetch(`/api/agents/smart-agents/${agentId}/performance_analysis/`)
      const data = await response.json()
      
      if (response.ok) {
        setPerformanceData(data.performance_data)
      }
    } catch (error) {
      console.error('Error loading agent performance:', error)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active': return 'bg-green-500'
      case 'idle': return 'bg-blue-500'
      case 'processing': return 'bg-yellow-500'
      case 'error': return 'bg-red-500'
      case 'offline': return 'bg-gray-500'
      default: return 'bg-gray-500'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active': return <CheckCircle className="w-4 h-4" />
      case 'processing': return <Loader2 className="w-4 h-4 animate-spin" />
      case 'error': return <AlertTriangle className="w-4 h-4" />
      default: return <Clock className="w-4 h-4" />
    }
  }
    useEffect(() => {
        const initData = async () => {
          setLoading(true)
          try {
            await Promise.all([
              loadAgents(),
              loadDashboardData()
            ])
          } catch (error) {
            console.error('Failed to load dashboard data:', error)
            toast({
              title: 'Error',
              description: 'Failed to load dashboard data',
              variant: 'destructive',
            })
          } finally {
            setLoading(false)
          }
        }
        initData()
      }, [toast])

  if (loading && !dashboardData) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4" />
          <p>Loading Smart Agent Dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Smart Agent Dashboard</h1>
          <p className="text-muted-foreground">
            Intelligent agent selection and performance monitoring
          </p>
        </div>
        <Button 
          onClick={refreshData} 
          disabled={refreshing}
          variant="outline"
          className="flex items-center gap-2"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="selection">Agent Selection</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="insights">Insights</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          {dashboardData?.overview && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Total Agents</CardTitle>
                  <Users className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {dashboardData.overview.agents.total}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {Math.round(dashboardData.overview.agents.utilization_rate * 100)}% utilization
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Active Tasks</CardTitle>
                  <Activity className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {dashboardData.overview.tasks.total}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {Math.round(dashboardData.overview.tasks.success_rate * 100)}% success rate
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Active Sessions</CardTitle>
                  <MessageSquare className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {dashboardData.overview.sessions.active}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {dashboardData.overview.sessions.total} total
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Messages</CardTitle>
                  <MessageSquare className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {dashboardData.overview.messages.total}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {dashboardData.overview.messages.agent_messages} from agents
                  </p>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Agent Status Grid */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Cpu className="w-5 h-5" />
                Agent Status Overview
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {agents.map((agent) => (
                  <div 
                    key={agent.id}
                    className="p-4 border rounded-lg hover:shadow-md transition-shadow cursor-pointer"
                    onClick={() => loadAgentPerformance(agent.id)}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-semibold truncate">{agent.name}</h3>
                      <div className="flex items-center gap-1">
                        {getStatusIcon(agent.status)}
                        <div className={`w-2 h-2 rounded-full ${getStatusColor(agent.status)}`} />
                      </div>
                    </div>
                    <p className="text-sm text-muted-foreground mb-2">{agent.type}</p>
                    <div className="flex flex-wrap gap-1">
                      {agent.capabilities.slice(0, 2).map((capability, idx) => (
                        <Badge key={idx} variant="secondary" className="text-xs">
                          {capability}
                        </Badge>
                      ))}
                      {agent.capabilities.length > 2 && (
                        <Badge variant="secondary" className="text-xs">
                          +{agent.capabilities.length - 2}
                        </Badge>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="selection" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Brain className="w-5 h-5" />
                Smart Agent Selection
              </CardTitle>
              <CardDescription>
                Let AI select the best agent for your task automatically
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="task-type">Task Type</Label>
                  <Select value={taskType} onValueChange={setTaskType}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select task type" />
                    </SelectTrigger>
                    <SelectContent>
                      {taskTypes.map((type) => (
                        <SelectItem key={type} value={type}>
                          {type}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="requirements">Requirements (JSON)</Label>
                  <Input
                    id="requirements"
                    placeholder='{"min_accuracy": 0.9}'
                    value={requirements}
                    onChange={(e) => setRequirements(e.target.value)}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="task-description">Task Description</Label>
                <Textarea
                  id="task-description"
                  placeholder="Describe your task in detail..."
                  value={taskDescription}
                  onChange={(e) => setTaskDescription(e.target.value)}
                  rows={3}
                />
              </div>

              <div className="flex gap-2">
                <Button onClick={selectBestAgent} disabled={loading}>
                  {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Zap className="w-4 h-4 mr-2" />}
                  Select Best Agent
                </Button>
                <Button onClick={getAgentRecommendations} variant="outline" disabled={loading}>
                  {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Eye className="w-4 h-4 mr-2" />}
                  Get Recommendations
                </Button>
              </div>

              {selectedAgent && (
                <Alert>
                  <CheckCircle className="h-4 w-4" />
                  <AlertTitle>Selected Agent</AlertTitle>
                  <AlertDescription>
                    <strong>{selectedAgent.name}</strong> ({selectedAgent.type}) has been selected as the best match for your task.
                  </AlertDescription>
                </Alert>
              )}

              {agentRecommendations.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Agent Recommendations</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {agentRecommendations.map((rec) => (
                        <div key={rec.agent.id} className="flex items-center justify-between p-3 border rounded">
                          <div>
                            <h4 className="font-semibold">{rec.agent.name}</h4>
                            <p className="text-sm text-muted-foreground">{rec.agent.type}</p>
                            <p className="text-xs text-muted-foreground mt-1">{rec.recommendation_reason}</p>
                          </div>
                          <div className="text-right">
                            <div className="text-sm font-semibold">
                              {Math.round(rec.suitability_score * 100)}%
                            </div>
                            <Progress value={rec.suitability_score * 100} className="w-20 mt-1" />
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="performance" className="space-y-4">
          {performanceData && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="w-5 h-5" />
                  Agent Performance Analysis
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                  <div className="text-center">
                    <div className="text-2xl font-bold">
                      {Math.round(performanceData.success_rate * 100)}%
                    </div>
                    <p className="text-sm text-muted-foreground">Success Rate</p>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold">
                      {performanceData.avg_response_time.toFixed(1)}s
                    </div>
                    <p className="text-sm text-muted-foreground">Avg Response Time</p>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold">
                      {Math.round(performanceData.accuracy * 100)}%
                    </div>
                    <p className="text-sm text-muted-foreground">Accuracy</p>
                  </div>
                </div>

                <div className="space-y-4">
                  <h4 className="font-semibold">Error Analysis</h4>
                  <div className="space-y-2">
                    {Object.entries(performanceData.error_types).map(([errorType, count]) => (
                      <div key={errorType} className="flex justify-between items-center">
                        <span className="capitalize">{errorType.replace('_', ' ')}</span>
                        <Badge variant="destructive">{count}</Badge>
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="insights" className="space-y-4">
          {dashboardData?.insights && (
            <div className="space-y-4">
              {dashboardData.insights.map((insight, index) => (
                <Alert key={index} className={
                  insight.type === 'positive' ? 'border-green-200' :
                  insight.type === 'warning' ? 'border-yellow-200' : 
                  'border-blue-200'
                }>
                  {insight.type === 'positive' ? <TrendingUp className="h-4 w-4" /> :
                   insight.type === 'warning' ? <AlertTriangle className="h-4 w-4" /> :
                   <Activity className="h-4 w-4" />}
                  <AlertTitle>{insight.title}</AlertTitle>
                  <AlertDescription>
                    {insight.description}
                    {insight.suggested_action && (
                      <div className="mt-2 p-2 bg-muted rounded text-sm">
                        <strong>Suggested Action:</strong> {insight.suggested_action}
                      </div>
                    )}
                  </AlertDescription>
                </Alert>
              ))}
            </div>
          )}

          {dashboardData?.recommendations && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Settings className="w-5 h-5" />
                  Optimization Recommendations
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {dashboardData.recommendations.map((rec, index) => (
                    <div key={index} className="border rounded-lg p-4">
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="font-semibold">{rec.title}</h4>
                        <Badge variant={
                          rec.priority === 'high' ? 'destructive' :
                          rec.priority === 'medium' ? 'default' : 
                          'secondary'
                        }>
                          {rec.priority} priority
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground mb-3">{rec.description}</p>
                      {rec.actions && (
                        <div>
                          <p className="text-sm font-semibold mb-1">Recommended Actions:</p>
                          <ul className="text-sm space-y-1">
                            {rec.actions.map((action, actionIndex) => (
                              <li key={actionIndex} className="flex items-center gap-2">
                                <div className="w-1.5 h-1.5 bg-current rounded-full" />
                                {action}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default SmartAgentDashboard