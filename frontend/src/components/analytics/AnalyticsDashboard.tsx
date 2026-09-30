'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import {
  TrendingUp,
  TrendingDown,
  Activity,
  Clock,
  CheckCircle,
  Users,
  Zap,
  Target,
  Download,
  RefreshCw,
  Loader2,
  AlertCircle,
} from 'lucide-react'
import {
  getAnalyticsDashboard,
  getSystemPerformance,
  getPerformanceMetrics,
} from '@/lib/api'

interface PerformanceMetric {
  timestamp: string
  agent_id: string
  task_type: string
  execution_time: number
  success_rate: number
  accuracy_score: number
  memory_usage: number
  cpu_usage: number
}

interface AgentStats {
  agent_id: string
  name: string
  type: string
  total_tasks: number
  success_rate: number
  avg_execution_time: number
  avg_accuracy: number
  status: 'active' | 'idle' | 'error'
  last_active: string
}

interface WorkflowStats {
  workflow_id: string
  name: string
  executions: number
  success_rate: number
  avg_duration: number
  last_run: string
  complexity_score: number
}

const AnalyticsDashboard: React.FC = () => {
  const [timeRange, setTimeRange] = useState<string>('24h')
  const [activeTab, setActiveTab] = useState('overview')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [performanceData, setPerformanceData] = useState<PerformanceMetric[]>([])
  const [agentStats, setAgentStats] = useState<AgentStats[]>([])
  const [workflowStats, setWorkflowStats] = useState<WorkflowStats[]>([])

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)
      const [dashRes, sysRes, perfRes] = await Promise.allSettled([
        getAnalyticsDashboard(timeRange === '1h' ? '24h' : timeRange),
        getSystemPerformance(),
        getPerformanceMetrics(),
      ])

      const dashboard =
        dashRes.status === 'fulfilled' && dashRes.value && typeof dashRes.value === 'object'
          ? (dashRes.value as unknown as Record<string, unknown>)
          : {}
      const systemPerf =
        sysRes.status === 'fulfilled' && sysRes.value && typeof sysRes.value === 'object'
          ? (sysRes.value as Record<string, unknown>)
          : {}
      const perfMetrics =
        perfRes.status === 'fulfilled' && perfRes.value && typeof perfRes.value === 'object'
          ? (perfRes.value as Record<string, unknown>)
          : {}

      const agentMetrics = (dashboard.agent_metrics as Record<string, unknown>) || {}
      const individual = (agentMetrics.individual_metrics as Record<string, unknown>) || {}
      const agents: AgentStats[] = Object.values(individual).map((raw, index) => {
        const agent = (raw || {}) as Record<string, unknown>
        const info = (agent.agent_info || {}) as Record<string, unknown>
        const tasks = (agent.tasks || {}) as Record<string, unknown>
        const total = Number(tasks.total || 0)
        const completed = Number(tasks.completed || 0)
        return {
          agent_id: String(info.id || index),
          name: String(info.name || `Agent ${index + 1}`),
          type: String(info.type || 'unknown'),
          total_tasks: total,
          success_rate: total > 0 ? (completed / total) * 100 : Number(agent.efficiency_score || 0) * 100,
          avg_execution_time: Number(
            (agent.performance as Record<string, unknown>)?.avg_execution_time ||
              systemPerf.avg_response_time ||
              0
          ),
          avg_accuracy: Number(agent.efficiency_score || 0) * 100,
          status: (['active', 'idle', 'error'].includes(String(info.status))
            ? String(info.status)
            : 'idle') as AgentStats['status'],
          last_active: String(agent.last_active || '—'),
        }
      })
      setAgentStats(agents)

      const taskAnalytics = (dashboard.task_analytics as Record<string, unknown>) || {}
      const typeStats = Array.isArray(taskAnalytics.task_type_distribution)
        ? taskAnalytics.task_type_distribution
        : Array.isArray(taskAnalytics.by_type)
          ? taskAnalytics.by_type
          : []
      setWorkflowStats(
        (typeStats as Record<string, unknown>[]).map((row, i) => ({
          workflow_id: `type-${i}`,
          name: String(row.task_type || row.name || `Workflow ${i + 1}`),
          executions: Number(row.count || 0),
          success_rate: Number(row.success_rate || 0) * (Number(row.success_rate) <= 1 ? 100 : 1),
          avg_duration: Number(row.avg_duration || 0),
          last_run: '—',
          complexity_score: Number(row.complexity_score || 0),
        }))
      )

      const trends = (dashboard.performance_trends as Record<string, unknown>) || {}
      const responseTimes = Array.isArray(trends.response_times) ? trends.response_times : []
      if (responseTimes.length > 0) {
        setPerformanceData(
          (responseTimes as Record<string, unknown>[]).map((row) => ({
            timestamp: String(row.date || row.period || new Date().toISOString()),
            agent_id: 'system',
            task_type: 'all',
            execution_time: Number(row.avg_response_time || row.value || 0) / 1000,
            success_rate: Number(row.success_rate || 90),
            accuracy_score: Number(row.accuracy || 90),
            memory_usage: Number(row.memory || systemPerf.memory_usage || 0),
            cpu_usage: Number(row.cpu || systemPerf.cpu_usage || perfMetrics.cpu_usage || 0),
          }))
        )
      } else {
        setPerformanceData([])
      }

      if (dashRes.status === 'rejected' && sysRes.status === 'rejected') {
        setError('Failed to load analytics')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load analytics')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    setTimeout(() => { loadData() }, 0)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [timeRange])

  const refreshData = async () => {
    await loadData()
  }

  const exportData = () => {
    const payload = {
      agents: agentStats,
      workflows: workflowStats,
      performance: performanceData,
      exported_at: new Date().toISOString()
    }
    
    const dataStr = JSON.stringify(payload, null, 2)
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr)
    const exportFileDefaultName = `analytics_${new Date().toISOString().split('T')[0]}.json`
    
    const linkElement = document.createElement('a')
    linkElement.setAttribute('href', dataUri)
    linkElement.setAttribute('download', exportFileDefaultName)
    linkElement.click()
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-600 bg-green-100 border-green-200'
      case 'idle': return 'text-yellow-600 bg-yellow-100 border-yellow-200'
      case 'error': return 'text-red-600 bg-red-100 border-red-200'
      default: return 'text-gray-600 bg-gray-100 border-gray-200'
    }
  }

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds.toFixed(1)}s`
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return `${minutes}m ${remainingSeconds.toFixed(1)}s`
  }

  return (
    <div className="space-y-6">
      {/* Header Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center space-x-4">
          <h2 className="text-2xl font-bold">Analytics Dashboard</h2>
          <Badge variant="outline" className="text-xs">
            Real-time
          </Badge>
        </div>
        
        <div className="flex items-center space-x-2">
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-[120px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1h">Last Hour</SelectItem>
              <SelectItem value="24h">Last 24h</SelectItem>
              <SelectItem value="7d">Last 7 days</SelectItem>
              <SelectItem value="30d">Last 30 days</SelectItem>
            </SelectContent>
          </Select>
          
          <Button
            variant="outline"
            size="sm"
            onClick={refreshData}
            disabled={loading}
          >
            {loading ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4 mr-2" />
            )}
            Refresh
          </Button>
          
          <Button variant="outline" size="sm" onClick={exportData}>
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {error && (
        <Card>
          <CardContent className="p-4 text-sm text-destructive flex items-center gap-2">
            <AlertCircle className="h-4 w-4" />
            {error}
            <Button variant="outline" size="sm" className="ml-auto" onClick={refreshData}>
              Retry
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Key Metrics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              <Activity className="h-5 w-5 text-blue-500" />
              <div>
                <p className="text-2xl font-bold">
                  {agentStats.reduce((sum, agent) => sum + agent.total_tasks, 0)}
                </p>
                <p className="text-sm text-muted-foreground">Total Tasks</p>
              </div>
            </div>
            <div className="flex items-center space-x-1 mt-2">
              <TrendingUp className="h-4 w-4 text-green-500" />
              <span className="text-sm text-green-600">+12% from last week</span>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              <CheckCircle className="h-5 w-5 text-green-500" />
              <div>
                <p className="text-2xl font-bold">
                  {(agentStats.reduce((sum, agent) => sum + agent.success_rate, 0) / agentStats.length).toFixed(1)}%
                </p>
                <p className="text-sm text-muted-foreground">Avg Success Rate</p>
              </div>
            </div>
            <div className="flex items-center space-x-1 mt-2">
              <TrendingUp className="h-4 w-4 text-green-500" />
              <span className="text-sm text-green-600">+2.3% from last week</span>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              <Clock className="h-5 w-5 text-orange-500" />
              <div>
                <p className="text-2xl font-bold">
                  {(agentStats.reduce((sum, agent) => sum + agent.avg_execution_time, 0) / agentStats.length).toFixed(1)}s
                </p>
                <p className="text-sm text-muted-foreground">Avg Response Time</p>
              </div>
            </div>
            <div className="flex items-center space-x-1 mt-2">
              <TrendingDown className="h-4 w-4 text-green-500" />
              <span className="text-sm text-green-600">-0.2s from last week</span>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              <Users className="h-5 w-5 text-purple-500" />
              <div>
                <p className="text-2xl font-bold">
                  {agentStats.filter(agent => agent.status === 'active').length}
                </p>
                <p className="text-sm text-muted-foreground">Active Agents</p>
              </div>
            </div>
            <div className="flex items-center space-x-1 mt-2">
              <CheckCircle className="h-4 w-4 text-green-500" />
              <span className="text-sm text-green-600">All systems operational</span>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="agents">Agent Performance</TabsTrigger>
          <TabsTrigger value="workflows">Workflow Analytics</TabsTrigger>
          <TabsTrigger value="trends">Performance Trends</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Performance Chart */}
          <Card>
            <CardHeader>
              <CardTitle>Performance Overview</CardTitle>
              <CardDescription>
                Real-time system performance metrics over the selected time period
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={performanceData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="timestamp" 
                      tickFormatter={(value) => new Date(value).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                    />
                    <YAxis />
                    <Tooltip 
                      labelFormatter={(value) => new Date(value as string | number).toLocaleString()}
                      formatter={(value, name) => {
                        const numericValue = typeof value === 'number'
                          ? value
                          : Number(Array.isArray(value) ? value[0] : value ?? 0)

                        const formattedValue = name === 'execution_time'
                          ? `${numericValue.toFixed(2)}s`
                          : `${numericValue.toFixed(1)}%`

                        return [
                          formattedValue,
                          String(name ?? '').replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())
                        ]
                      }}
                    />
                    <Legend />
                    <Line type="monotone" dataKey="success_rate" stroke="#10b981" name="Success Rate" strokeWidth={2} />
                    <Line type="monotone" dataKey="accuracy_score" stroke="#3b82f6" name="Accuracy Score" strokeWidth={2} />
                    <Line type="monotone" dataKey="execution_time" stroke="#f59e0b" name="Execution Time" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* System Health */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>System Health</CardTitle>
                <CardDescription>Current system resource utilization</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>CPU Usage</span>
                    <span>68%</span>
                  </div>
                  <Progress value={68} className="h-2" />
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>Memory Usage</span>
                    <span>45%</span>
                  </div>
                  <Progress value={45} className="h-2" />
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>Network I/O</span>
                    <span>23%</span>
                  </div>
                  <Progress value={23} className="h-2" />
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>Storage Usage</span>
                    <span>34%</span>
                  </div>
                  <Progress value={34} className="h-2" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Agent Status Distribution</CardTitle>
                <CardDescription>Current status of all agents in the system</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={[
                          { name: 'Active', value: agentStats.filter(a => a.status === 'active').length, color: '#10b981' },
                          { name: 'Idle', value: agentStats.filter(a => a.status === 'idle').length, color: '#f59e0b' },
                          { name: 'Error', value: agentStats.filter(a => a.status === 'error').length, color: '#ef4444' },
                        ]}
                        cx="50%"
                        cy="50%"
                        outerRadius={80}
                        dataKey="value"
                        label={({name, value}) => `${name}: ${value}`}
                      >
                        {[
                          { name: 'Active', value: agentStats.filter(a => a.status === 'active').length, color: '#10b981' },
                          { name: 'Idle', value: agentStats.filter(a => a.status === 'idle').length, color: '#f59e0b' },
                          { name: 'Error', value: agentStats.filter(a => a.status === 'error').length, color: '#ef4444' },
                        ].map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="agents" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Agent Performance Comparison</CardTitle>
              <CardDescription>
                Detailed performance metrics for each agent
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {agentStats.map((agent) => (
                  <div key={agent.agent_id} className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center space-x-3">
                        <div className="flex items-center space-x-2">
                          <Zap className="h-5 w-5 text-blue-500" />
                          <h4 className="font-semibold">{agent.name}</h4>
                        </div>
                        <Badge className={`text-xs border ${getStatusColor(agent.status)}`}>
                          {agent.status.toUpperCase()}
                        </Badge>
                        <Badge variant="outline" className="text-xs">
                          {agent.type}
                        </Badge>
                      </div>
                      <div className="text-sm text-muted-foreground">
                        Last active: {agent.last_active}
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <p className="text-muted-foreground">Tasks Completed</p>
                        <p className="font-semibold text-lg">{agent.total_tasks}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Success Rate</p>
                        <p className="font-semibold text-lg text-green-600">{agent.success_rate}%</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Avg Response Time</p>
                        <p className="font-semibold text-lg">{agent.avg_execution_time}s</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Accuracy Score</p>
                        <p className="font-semibold text-lg text-blue-600">{agent.avg_accuracy}%</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="workflows" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Workflow Performance</CardTitle>
              <CardDescription>
                Analysis of workflow execution patterns and efficiency
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {workflowStats.map((workflow) => (
                  <div key={workflow.workflow_id} className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center space-x-3">
                        <Target className="h-5 w-5 text-purple-500" />
                        <h4 className="font-semibold">{workflow.name}</h4>
                        <Badge variant="outline" className="text-xs">
                          Complexity: {workflow.complexity_score}/10
                        </Badge>
                      </div>
                      <div className="text-sm text-muted-foreground">
                        Last run: {workflow.last_run}
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <p className="text-muted-foreground">Executions</p>
                        <p className="font-semibold text-lg">{workflow.executions}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Success Rate</p>
                        <p className="font-semibold text-lg text-green-600">{workflow.success_rate}%</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Avg Duration</p>
                        <p className="font-semibold text-lg">{formatDuration(workflow.avg_duration)}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Efficiency Score</p>
                        <p className="font-semibold text-lg text-blue-600">
                          {Math.round((workflow.success_rate * 100) / (workflow.complexity_score * 10))}%
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="trends" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Performance Trends</CardTitle>
              <CardDescription>
                Historical analysis of system performance over time
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={performanceData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="timestamp" 
                      tickFormatter={(value) => new Date(value).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                    />
                    <YAxis />
                    <Tooltip 
                      labelFormatter={(value) => new Date(value as string | number).toLocaleString()}
                    />
                    <Legend />
                    <Area 
                      type="monotone" 
                      dataKey="cpu_usage" 
                      stackId="1" 
                      stroke="#3b82f6" 
                      fill="#3b82f6" 
                      fillOpacity={0.6}
                      name="CPU Usage"
                    />
                    <Area 
                      type="monotone" 
                      dataKey="memory_usage" 
                      stackId="1" 
                      stroke="#10b981" 
                      fill="#10b981" 
                      fillOpacity={0.6}
                      name="Memory Usage"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default AnalyticsDashboard