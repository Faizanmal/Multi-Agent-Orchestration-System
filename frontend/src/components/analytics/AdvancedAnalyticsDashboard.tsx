'use client'

import React, { useCallback, useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts'
import {
  TrendingUp,
  TrendingDown,
  Activity,
  Clock,
  CheckCircle,
  AlertTriangle,
  Zap,
  Users,
  Globe,
  RefreshCw,
  Download,
  BarChart3,
  PieChart as PieChartIcon,
  Target,
  Cpu,
  HardDrive,
  Loader2,
} from 'lucide-react'
import {
  getAnalyticsDashboard,
  getSystemPerformance,
  getAnalyticsInsights,
  getPerformanceMetrics,
} from '@/lib/api'

interface MetricCard {
  title: string
  value: string | number
  change: number
  trend: 'up' | 'down' | 'stable'
  icon: React.ReactNode
  color: string
}

interface ChartData {
  name: string
  value: number
  time?: string
}

interface ExecutionTrendData {
  name: string
  success: number
  failure: number
  time: string
}

interface PerformanceData {
  name: string
  duration: number
  cpu: number
  memory: number
  network: number
}

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4']

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {}
}

function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : []
}

function num(value: unknown, fallback = 0): number {
  const n = typeof value === 'number' ? value : Number(value)
  return Number.isFinite(n) ? n : fallback
}

const AdvancedAnalyticsDashboard: React.FC = () => {
  const [timeRange, setTimeRange] = useState('7d')
  const [refreshing, setRefreshing] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState('overview')
  const [metrics, setMetrics] = useState<MetricCard[]>([])
  const [executionTrendData, setExecutionTrendData] = useState<ExecutionTrendData[]>([])
  const [performanceData, setPerformanceData] = useState<PerformanceData[]>([])
  const [workflowDistribution, setWorkflowDistribution] = useState<ChartData[]>([])
  const [errorTypes, setErrorTypes] = useState<ChartData[]>([])

  const loadData = useCallback(async () => {
    try {
      setRefreshing(true)
      setError(null)
      const [dashRes, sysRes, insightsRes, perfRes] = await Promise.allSettled([
        getAnalyticsDashboard(timeRange),
        getSystemPerformance(),
        getAnalyticsInsights(),
        getPerformanceMetrics(),
      ])

      const dashboard = dashRes.status === 'fulfilled' ? asRecord(dashRes.value) : {}
      const systemPerf = sysRes.status === 'fulfilled' ? asRecord(sysRes.value) : {}
      const insights = insightsRes.status === 'fulfilled' ? asRecord(insightsRes.value) : {}
      const perfMetrics = perfRes.status === 'fulfilled' ? asRecord(perfRes.value) : {}

      const overview = asRecord(dashboard.overview)
      const tasks = asRecord(overview.tasks)
      const sessions = asRecord(overview.sessions)
      const byStatus = asRecord(tasks.by_status)
      const totalTasks = num(tasks.total, num(systemPerf.total_tasks))
      const completed = num(byStatus.completed)
      const failed = num(byStatus.failed, num(systemPerf.failed_tasks))
      const successRate =
        num(tasks.success_rate, num(systemPerf.success_rate)) *
        (num(tasks.success_rate) <= 1 || num(systemPerf.success_rate) <= 1 ? 100 : 1)
      const errorRate = totalTasks > 0 ? (failed / totalTasks) * 100 : 0
      const avgDuration = num(systemPerf.avg_response_time ?? perfMetrics.avg_latency)

      setMetrics([
        {
          title: 'Total Executions',
          value: totalTasks.toLocaleString(),
          change: 0,
          trend: 'stable',
          icon: <Activity className="w-4 h-4" />,
          color: '#3b82f6',
        },
        {
          title: 'Success Rate',
          value: `${successRate.toFixed(1)}%`,
          change: 0,
          trend: successRate >= 90 ? 'up' : 'down',
          icon: <CheckCircle className="w-4 h-4" />,
          color: '#10b981',
        },
        {
          title: 'Avg. Duration',
          value: avgDuration > 0 ? `${(avgDuration / 1000).toFixed(1)}s` : '—',
          change: 0,
          trend: 'stable',
          icon: <Clock className="w-4 h-4" />,
          color: '#f59e0b',
        },
        {
          title: 'Active Workflows',
          value: num(sessions.active, num(sessions.total)),
          change: 0,
          trend: 'up',
          icon: <Zap className="w-4 h-4" />,
          color: '#8b5cf6',
        },
        {
          title: 'Error Rate',
          value: `${errorRate.toFixed(1)}%`,
          change: 0,
          trend: errorRate <= 5 ? 'down' : 'up',
          icon: <AlertTriangle className="w-4 h-4" />,
          color: '#ef4444',
        },
        {
          title: 'Total Users',
          value: num(asRecord(dashboard.user_activity).unique_users, num(overview.users)),
          change: 0,
          trend: 'up',
          icon: <Users className="w-4 h-4" />,
          color: '#06b6d4',
        },
      ])

      const trends = asRecord(dashboard.performance_trends)
      const completion = asArray(trends.task_completion_rate)
      const errors = asArray(trends.error_rates)
      if (completion.length > 0) {
        setExecutionTrendData(
          completion.map((item, i) => {
            const row = asRecord(item)
            const err = asRecord(errors[i])
            const label = String(row.date || row.period || `P${i + 1}`)
            return {
              name: label.slice(0, 10),
              success: num(row.completed ?? row.value, completed),
              failure: num(err.count ?? err.value, failed),
              time: label.slice(0, 10),
            }
          })
        )
      } else if (totalTasks > 0) {
        setExecutionTrendData([
          { name: 'Period', success: completed, failure: failed, time: 'Period' },
        ])
      } else {
        setExecutionTrendData([])
      }

      const responseTimes = asArray(trends.response_times)
      if (responseTimes.length > 0) {
        setPerformanceData(
          responseTimes.map((item, i) => {
            const row = asRecord(item)
            return {
              name: String(row.date || row.period || `D${i + 1}`).slice(0, 10),
              duration: num(row.avg_response_time ?? row.value) / 1000,
              cpu: num(row.cpu, num(systemPerf.cpu_usage)),
              memory: num(row.memory, num(systemPerf.memory_usage)),
              network: num(row.network, 0),
            }
          })
        )
      } else {
        setPerformanceData([])
      }

      const taskAnalytics = asRecord(dashboard.task_analytics)
      const typeStats = asArray(
        taskAnalytics.task_type_distribution ?? taskAnalytics.by_type
      )
      setWorkflowDistribution(
        typeStats.map((item) => {
          const row = asRecord(item)
          return {
            name: String(row.task_type || row.name || 'Other'),
            value: num(row.count ?? row.value),
          }
        })
      )

      const insightList = asArray(insights.insights ?? dashboard.insights)
      const derivedErrors = insightList
        .filter((item) => {
          const t = String(asRecord(item).type || asRecord(item).category || '')
          return t.includes('error') || t.includes('warning') || t.includes('anomaly')
        })
        .map((item) => ({
          name: String(asRecord(item).title || 'Issue'),
          value: 1,
        }))
      setErrorTypes(
        derivedErrors.length > 0
          ? derivedErrors
          : failed > 0
            ? [{ name: 'Failed Tasks', value: failed }]
            : []
      )

      if (dashRes.status === 'rejected' && sysRes.status === 'rejected') {
        setError('Failed to load analytics')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load analytics')
    } finally {
      setRefreshing(false)
      setLoading(false)
    }
  }, [timeRange])

  useEffect(() => {
    setTimeout(() => { loadData() }, 0)
  }, [loadData])

  const handleRefresh = async () => {
    await loadData()
  }

  const MetricCard: React.FC<{ metric: MetricCard }> = ({ metric }) => (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-muted-foreground">{metric.title}</p>
            <p className="text-3xl font-bold" style={{ color: metric.color }}>
              {metric.value}
            </p>
          </div>
          <div 
            className="w-12 h-12 rounded-lg flex items-center justify-center"
            style={{ backgroundColor: `${metric.color}20`, color: metric.color }}
          >
            {metric.icon}
          </div>
        </div>
        
        <div className="mt-4 flex items-center">
          {metric.trend === 'up' ? (
            <TrendingUp className="w-4 h-4 text-green-500" />
          ) : metric.trend === 'down' ? (
            <TrendingDown className="w-4 h-4 text-red-500" />
          ) : (
            <div className="w-4 h-4" />
          )}
          <span 
            className={`text-sm font-medium ml-1 ${
              metric.trend === 'up' ? 'text-green-500' : 
              metric.trend === 'down' ? 'text-red-500' : 
              'text-gray-500'
            }`}
          >
            {metric.change > 0 ? '+' : ''}{metric.change}%
          </span>
          <span className="text-sm text-muted-foreground ml-2">vs last period</span>
        </div>
      </CardContent>
    </Card>
  )

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Analytics Dashboard</h1>
          <p className="text-muted-foreground">
            Comprehensive insights into your workflow performance
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-[120px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1d">Last 24h</SelectItem>
              <SelectItem value="7d">Last 7 days</SelectItem>
              <SelectItem value="30d">Last 30 days</SelectItem>
              <SelectItem value="90d">Last 90 days</SelectItem>
            </SelectContent>
          </Select>
          
          <Button 
            variant="outline" 
            size="sm" 
            onClick={handleRefresh}
            disabled={refreshing}
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          </Button>
          
          <Button variant="outline" size="sm">
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      {loading ? (
        <div className="flex items-center justify-center py-12 text-muted-foreground">
          <Loader2 className="w-6 h-6 animate-spin mr-2" />
          Loading analytics...
        </div>
      ) : error ? (
        <Card>
          <CardContent className="p-4 text-sm text-destructive flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" />
            {error}
            <Button variant="outline" size="sm" className="ml-auto" onClick={handleRefresh}>
              Retry
            </Button>
          </CardContent>
        </Card>
      ) : (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {metrics.map((metric, index) => (
          <MetricCard key={index} metric={metric} />
        ))}
      </div>
      )}

      {/* Detailed Analytics */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid grid-cols-4 w-full max-w-md">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="errors">Errors</TabsTrigger>
          <TabsTrigger value="usage">Usage</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6 mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Execution Trends */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <BarChart3 className="w-5 h-5" />
                  <span>Execution Trends</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={executionTrendData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Area 
                      type="monotone" 
                      dataKey="success" 
                      stackId="1"
                      stroke="#10b981" 
                      fill="#10b981"
                      fillOpacity={0.6}
                    />
                    <Area 
                      type="monotone" 
                      dataKey="failure" 
                      stackId="1"
                      stroke="#ef4444" 
                      fill="#ef4444"
                      fillOpacity={0.6}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Workflow Distribution */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <PieChartIcon className="w-5 h-5" />
                  <span>Workflow Types</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={workflowDistribution}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {workflowDistribution.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Real-time Activity Feed */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Activity className="w-5 h-5" />
                <span>Recent Activity</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[
                  { time: '2 min ago', event: 'Workflow "Data Processing" completed successfully', status: 'success' },
                  { time: '5 min ago', event: 'API integration workflow started', status: 'info' },
                  { time: '8 min ago', event: 'Error in email notification step', status: 'error' },
                  { time: '12 min ago', event: 'New workflow template created', status: 'success' },
                  { time: '15 min ago', event: 'User authenticated successfully', status: 'info' }
                ].map((activity, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className={`w-2 h-2 rounded-full ${
                        activity.status === 'success' ? 'bg-green-500' :
                        activity.status === 'error' ? 'bg-red-500' :
                        'bg-blue-500'
                      }`} />
                      <span className="text-sm">{activity.event}</span>
                    </div>
                    <span className="text-xs text-muted-foreground">{activity.time}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="performance" className="space-y-6 mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Performance Trends */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Clock className="w-5 h-5" />
                  <span>Execution Duration</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={performanceData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line 
                      type="monotone" 
                      dataKey="duration" 
                      stroke="#3b82f6" 
                      strokeWidth={2}
                      dot={{ fill: '#3b82f6' }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Resource Usage */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Cpu className="w-5 h-5" />
                  <span>Resource Utilization</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={performanceData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="cpu" stroke="#ef4444" name="CPU %" />
                    <Line type="monotone" dataKey="memory" stroke="#10b981" name="Memory %" />
                    <Line type="monotone" dataKey="network" stroke="#f59e0b" name="Network %" />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Performance Insights */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                    <Target className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold">Optimization Score</h3>
                    <p className="text-2xl font-bold text-blue-600">87%</p>
                    <p className="text-sm text-muted-foreground">+5% this week</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                    <Zap className="w-5 h-5 text-green-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold">Throughput</h3>
                    <p className="text-2xl font-bold text-green-600">234/h</p>
                    <p className="text-sm text-muted-foreground">workflows per hour</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                    <HardDrive className="w-5 h-5 text-purple-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold">Cache Hit Rate</h3>
                    <p className="text-2xl font-bold text-purple-600">92%</p>
                    <p className="text-sm text-muted-foreground">Excellent performance</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="errors" className="space-y-6 mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Error Types */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <AlertTriangle className="w-5 h-5" />
                  <span>Error Distribution</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={errorTypes}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value" fill="#ef4444" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Error Timeline */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Clock className="w-5 h-5" />
                  <span>Error Timeline</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {[
                    { time: '10:32 AM', error: 'API timeout in data fetch step', severity: 'high' },
                    { time: '09:15 AM', error: 'Validation failed for user input', severity: 'medium' },
                    { time: '08:45 AM', error: 'Network connectivity issue', severity: 'high' },
                    { time: '07:22 AM', error: 'Authentication token expired', severity: 'low' }
                  ].map((error, index) => (
                    <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center space-x-3">
                        <Badge 
                          variant={error.severity === 'high' ? 'destructive' : 
                                   error.severity === 'medium' ? 'default' : 'secondary'}
                        >
                          {error.severity}
                        </Badge>
                        <span className="text-sm">{error.error}</span>
                      </div>
                      <span className="text-xs text-muted-foreground">{error.time}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="usage" className="space-y-6 mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* User Activity */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Users className="w-5 h-5" />
                  <span>User Activity</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {metrics.length === 0 && !loading ? (
                    <p className="text-sm text-muted-foreground text-center py-6">
                      No user activity data yet.
                    </p>
                  ) : (
                    metrics.slice(0, 4).map((metric, index) => (
                      <div key={index} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                        <div>
                          <h4 className="font-medium">{metric.title}</h4>
                          <p className="text-sm text-muted-foreground">{metric.value}</p>
                        </div>
                        <span className="text-xs text-muted-foreground">
                          {metric.change > 0 ? `+${metric.change}%` : `${metric.change}%`}
                        </span>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>

            {/* API Usage */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Globe className="w-5 h-5" />
                  <span>API Endpoints</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {[
                    { endpoint: '/api/workflows/execute', calls: 1247, avgResponse: '1.2s' },
                    { endpoint: '/api/workflows/save', calls: 342, avgResponse: '0.8s' },
                    { endpoint: '/api/agents/list', calls: 876, avgResponse: '0.3s' },
                    { endpoint: '/api/templates/library', calls: 234, avgResponse: '0.5s' }
                  ].map((api, index) => (
                    <div key={index} className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm font-mono">{api.endpoint}</span>
                        <span className="text-sm text-muted-foreground">{api.avgResponse}</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Progress value={(api.calls / 1247) * 100} className="flex-1 h-2" />
                        <span className="text-sm text-muted-foreground">{api.calls}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default AdvancedAnalyticsDashboard