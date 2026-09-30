'use client'

import React, { useState, useEffect, useCallback } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  Play,
  Pause,
  Square,
  Clock,
  CheckCircle,
  AlertCircle,
  Loader2,
  Activity,
  TrendingUp,
  ChevronDown,
  ChevronRight,
  Timer
} from 'lucide-react'
import apiClient from '@/lib/api'

interface ExecutionStep {
  id: string
  nodeId: string
  nodeName: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped'
  startTime?: number
  endTime?: number
  duration?: number
  progress?: number
  input?: unknown
  output?: unknown
  error?: string
  metrics?: {
    cpuUsage?: number
    memoryUsage?: number
    networkIO?: number
    diskIO?: number
  }
}

interface ExecutionSession {
  id: string
  workflowName: string
  status: 'running' | 'completed' | 'failed' | 'paused' | 'cancelled' | 'queued'
  startTime: number
  endTime?: number
  totalSteps: number
  completedSteps: number
  currentStep?: ExecutionStep
  steps: ExecutionStep[]
  overallProgress: number
  estimatedTimeRemaining?: number
  throughput?: number
  errorCount: number
}

interface RealTimeExecutionMonitorProps {
  workflowId?: string
  executionId?: string
  onPause?: () => void
  onResume?: () => void
  onStop?: () => void
}

function unwrapList(data: unknown): Record<string, unknown>[] {
  if (Array.isArray(data)) return data as Record<string, unknown>[]
  if (data && typeof data === 'object') {
    const obj = data as Record<string, unknown>
    if (Array.isArray(obj.results)) return obj.results as Record<string, unknown>[]
    if (Array.isArray(obj.executions)) return obj.executions as Record<string, unknown>[]
    if (obj.data !== undefined) return unwrapList(obj.data)
  }
  return []
}

function mapStatus(status: string): ExecutionSession['status'] {
  switch (status) {
    case 'running':
    case 'completed':
    case 'failed':
    case 'paused':
    case 'cancelled':
    case 'queued':
      return status
    default:
      return 'queued'
  }
}

function mapStepStatus(status: string): ExecutionStep['status'] {
  switch (status) {
    case 'running':
    case 'completed':
    case 'failed':
    case 'skipped':
    case 'pending':
      return status
    case 'queued':
      return 'pending'
    case 'cancelled':
      return 'failed'
    default:
      return 'pending'
  }
}

function parseTime(value: unknown): number | undefined {
  if (!value) return undefined
  if (typeof value === 'number') return value
  const t = Date.parse(String(value))
  return Number.isNaN(t) ? undefined : t
}

function mapExecution(raw: Record<string, unknown>): ExecutionSession {
  const status = mapStatus(String(raw.status || 'queued'))
  const startTime = parseTime(raw.started_at) || parseTime(raw.created_at) || Date.now()
  const endTime = parseTime(raw.completed_at)
  const nodeResults = (raw.node_results && typeof raw.node_results === 'object'
    ? raw.node_results
    : {}) as Record<string, unknown>

  const steps: ExecutionStep[] = Object.entries(nodeResults).map(([nodeId, result], index) => {
    const r = (result && typeof result === 'object' ? result : {}) as Record<string, unknown>
    const stepStatus = mapStepStatus(String(r.status || (status === 'completed' ? 'completed' : status === 'failed' && index === Object.keys(nodeResults).length - 1 ? 'failed' : status === 'running' ? 'running' : 'pending')))
    const stepStart = parseTime(r.started_at || r.start_time)
    const stepEnd = parseTime(r.completed_at || r.end_time)
    const progress =
      stepStatus === 'completed' ? 100 :
      stepStatus === 'running' ? Number(r.progress ?? 50) :
      stepStatus === 'failed' ? Number(r.progress ?? 0) :
      0

    return {
      id: String(r.id || `step-${nodeId}`),
      nodeId,
      nodeName: String(r.name || r.node_name || nodeId),
      status: stepStatus,
      startTime: stepStart,
      endTime: stepEnd,
      duration: typeof r.duration_ms === 'number' ? r.duration_ms : (stepStart && stepEnd ? stepEnd - stepStart : undefined),
      progress,
      output: r.output ?? r.result,
      error: r.error ? String(r.error) : undefined,
      metrics: r.metrics as ExecutionStep['metrics'],
    }
  })

  // If no node_results, synthesize a single summary step from execution status
  if (steps.length === 0) {
    steps.push({
      id: 'summary',
      nodeId: 'workflow',
      nodeName: String(raw.workflow_name || 'Workflow'),
      status: status === 'completed' ? 'completed' : status === 'failed' ? 'failed' : status === 'running' ? 'running' : 'pending',
      startTime,
      endTime,
      duration: typeof raw.duration_ms === 'number' ? raw.duration_ms : undefined,
      progress: status === 'completed' ? 100 : status === 'running' ? 50 : status === 'failed' ? 0 : 0,
      error: raw.error_message ? String(raw.error_message) : undefined,
    })
  }

  const completedSteps = steps.filter(s => s.status === 'completed').length
  const totalSteps = steps.length
  const overallProgress = totalSteps > 0
    ? steps.reduce((sum, s) => sum + (s.progress ?? 0), 0) / totalSteps
    : (status === 'completed' ? 100 : 0)

  const durationMs = typeof raw.duration_ms === 'number'
    ? raw.duration_ms
    : (endTime ? endTime - startTime : Date.now() - startTime)
  const throughput = durationMs > 0 ? (completedSteps / (durationMs / 60000)) : undefined

  return {
    id: String(raw.id || 'unknown'),
    workflowName: String(raw.workflow_name || raw.workflow || 'Workflow'),
    status,
    startTime,
    endTime,
    totalSteps,
    completedSteps,
    steps,
    overallProgress,
    throughput,
    errorCount: steps.filter(s => s.status === 'failed').length + (raw.error_message ? 1 : 0),
  }
}

const RealTimeExecutionMonitor: React.FC<RealTimeExecutionMonitorProps> = ({
  workflowId,
  executionId,
  onPause,
  onResume,
  onStop
}) => {
  const [execution, setExecution] = useState<ExecutionSession | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set())
  const [autoScroll, setAutoScroll] = useState(true)

  const loadExecution = useCallback(async (silent = false) => {
    if (!silent) {
      setLoading(true)
      setError(null)
    }
    try {
      const res = await apiClient.getWorkflowExecutions()
      const list = unwrapList(res.data ?? res)

      let match: Record<string, unknown> | undefined
      if (executionId) {
        match = list.find(e => String(e.id) === String(executionId))
      } else if (workflowId) {
        match = list.find(e =>
          String(e.workflow) === String(workflowId) ||
          String(e.workflow_id) === String(workflowId)
        )
      } else {
        match = list[0]
      }

      if (match) {
        setExecution(mapExecution(match))
      } else {
        setExecution(null)
      }
    } catch (err) {
      console.error('Failed to load workflow executions', err)
      if (!silent) {
        setError('Failed to load execution data')
        setExecution(null)
      }
    } finally {
      if (!silent) setLoading(false)
    }
  }, [executionId, workflowId])

  useEffect(() => {
    setTimeout(() => { loadExecution() }, 0)
  }, [loadExecution])

  // Poll while running/queued — refresh from API only (no fake progress)
  useEffect(() => {
    if (!execution || (execution.status !== 'running' && execution.status !== 'queued')) {
      return
    }
    const interval = setInterval(() => {
      loadExecution(true)
    }, 3000)
    return () => clearInterval(interval)
  }, [execution, loadExecution])

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running': return <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
      case 'completed': return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'failed': return <AlertCircle className="w-4 h-4 text-red-500" />
      case 'pending': return <Clock className="w-4 h-4 text-gray-400" />
      case 'paused': return <Pause className="w-4 h-4 text-yellow-500" />
      default: return <Clock className="w-4 h-4 text-gray-400" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'bg-blue-500'
      case 'completed': return 'bg-green-500'
      case 'failed': return 'bg-red-500'
      case 'pending':
      case 'queued': return 'bg-gray-400'
      case 'paused': return 'bg-yellow-500'
      default: return 'bg-gray-400'
    }
  }

  const formatDuration = (ms: number) => {
    const seconds = Math.floor(ms / 1000)
    const minutes = Math.floor(seconds / 60)
    const hours = Math.floor(minutes / 60)

    if (hours > 0) {
      return `${hours}h ${minutes % 60}m ${seconds % 60}s`
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`
    } else {
      return `${seconds}s`
    }
  }

  const formatBytes = (bytes: number) => {
    const units = ['B', 'KB', 'MB', 'GB']
    let value = bytes
    let unitIndex = 0

    while (value >= 1024 && unitIndex < units.length - 1) {
      value /= 1024
      unitIndex++
    }

    return `${value.toFixed(1)}${units[unitIndex]}`
  }

  const toggleStepExpansion = (stepId: string) => {
    setExpandedSteps(prev => {
      const newSet = new Set(prev)
      if (newSet.has(stepId)) {
        newSet.delete(stepId)
      } else {
        newSet.add(stepId)
      }
      return newSet
    })
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
        <Loader2 className="w-8 h-8 animate-spin mb-3" />
        <p>Loading execution…</p>
      </div>
    )
  }

  if (error || !execution) {
    return (
      <Card>
        <CardContent className="py-12 text-center text-muted-foreground">
          <Activity className="w-10 h-10 mx-auto mb-3 opacity-50" />
          <p className="font-medium">{error || 'No executions found'}</p>
          <p className="text-sm mt-1">
            Run a workflow to see live execution progress here
          </p>
          <Button variant="outline" size="sm" className="mt-4" onClick={() => loadExecution()}>
            Refresh
          </Button>
        </CardContent>
      </Card>
    )
  }

  const currentRunningTime = (execution.endTime || new Date().getTime()) - execution.startTime

  return (
    <div className="space-y-6">
      {/* Execution Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className={`w-3 h-3 rounded-full ${getStatusColor(execution.status)} ${execution.status === 'running' ? 'animate-pulse' : ''}`} />
              <div>
                <CardTitle className="text-lg">{execution.workflowName}</CardTitle>
                <div className="text-sm text-muted-foreground">
                  Execution ID: {execution.id}
                </div>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <Badge variant="secondary">
                {execution.status.charAt(0).toUpperCase() + execution.status.slice(1)}
              </Badge>
              
              <div className="flex space-x-1">
                {execution.status === 'running' && (
                  <Button size="sm" variant="outline" onClick={onPause}>
                    <Pause className="w-4 h-4" />
                  </Button>
                )}
                {execution.status === 'paused' && (
                  <Button size="sm" variant="outline" onClick={onResume}>
                    <Play className="w-4 h-4" />
                  </Button>
                )}
                <Button size="sm" variant="outline" onClick={onStop}>
                  <Square className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </div>
        </CardHeader>
        
        <CardContent className="space-y-4">
          {/* Overall Progress */}
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Overall Progress</span>
              <span>{execution.overallProgress.toFixed(1)}%</span>
            </div>
            <Progress value={execution.overallProgress} className="h-2" />
          </div>
          
          {/* Execution Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div className="flex items-center space-x-2">
              <Timer className="w-4 h-4 text-blue-500" />
              <div>
                <div className="font-medium">{formatDuration(currentRunningTime)}</div>
                <div className="text-muted-foreground">Running Time</div>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <Activity className="w-4 h-4 text-green-500" />
              <div>
                <div className="font-medium">{execution.completedSteps}/{execution.totalSteps}</div>
                <div className="text-muted-foreground">Steps Complete</div>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <TrendingUp className="w-4 h-4 text-purple-500" />
              <div>
                <div className="font-medium">{execution.throughput != null ? `${execution.throughput.toFixed(1)}/min` : 'N/A'}</div>
                <div className="text-muted-foreground">Throughput</div>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <Clock className="w-4 h-4 text-orange-500" />
              <div>
                <div className="font-medium">
                  {execution.estimatedTimeRemaining ? formatDuration(execution.estimatedTimeRemaining) : 'N/A'}
                </div>
                <div className="text-muted-foreground">ETA</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Step-by-Step Progress */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center space-x-2">
              <Activity className="w-5 h-5" />
              <span>Execution Steps</span>
            </CardTitle>
            
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setAutoScroll(!autoScroll)}
              >
                Auto Scroll: {autoScroll ? 'ON' : 'OFF'}
              </Button>
            </div>
          </div>
        </CardHeader>
        
        <CardContent>
          <ScrollArea className="h-[400px]">
            <div className="space-y-3">
              {execution.steps.map((step, index) => (
                <div key={step.id} className="border rounded-lg p-3">
                  <div 
                    className="flex items-center justify-between cursor-pointer"
                    onClick={() => toggleStepExpansion(step.id)}
                  >
                    <div className="flex items-center space-x-3">
                      <div className="flex items-center space-x-2">
                        {expandedSteps.has(step.id) ? (
                          <ChevronDown className="w-4 h-4" />
                        ) : (
                          <ChevronRight className="w-4 h-4" />
                        )}
                        {getStatusIcon(step.status)}
                      </div>
                      
                      <div>
                        <div className="font-medium text-sm">{step.nodeName}</div>
                        <div className="text-xs text-muted-foreground">
                          Step {index + 1} of {execution.totalSteps}
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-3">
                      {step.progress !== undefined && (
                        <div className="text-sm font-medium">
                          {step.progress.toFixed(0)}%
                        </div>
                      )}
                      
                      {step.duration && (
                        <Badge variant="secondary" className="text-xs">
                          {formatDuration(step.duration)}
                        </Badge>
                      )}
                    </div>
                  </div>
                  
                  {step.progress !== undefined && (
                    <Progress value={step.progress} className="h-1 mt-2" />
                  )}
                  
                  {expandedSteps.has(step.id) && (
                    <div className="mt-3 space-y-3 text-sm">
                      {/* Timing Information */}
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <div className="text-muted-foreground">Start Time</div>
                          <div>{step.startTime ? new Date(step.startTime).toLocaleTimeString() : 'N/A'}</div>
                        </div>
                        <div>
                          <div className="text-muted-foreground">End Time</div>
                          <div>{step.endTime ? new Date(step.endTime).toLocaleTimeString() : 'Running...'}</div>
                        </div>
                      </div>
                      
                      {/* System Metrics */}
                      {step.metrics && (
                        <div>
                          <div className="text-muted-foreground mb-2">Resource Usage</div>
                          <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                              <div className="flex justify-between">
                                <span>CPU Usage:</span>
                                <span>{step.metrics.cpuUsage}%</span>
                              </div>
                              <Progress value={step.metrics.cpuUsage} className="h-1" />
                            </div>
                            <div className="space-y-2">
                              <div className="flex justify-between">
                                <span>Memory:</span>
                                <span>{formatBytes(step.metrics.memoryUsage || 0)}</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      )}
                      
                      {/* Error Information */}
                      {step.error && (
                        <div className="bg-red-50 border border-red-200 rounded p-2">
                          <div className="text-red-800 font-medium">Error:</div>
                          <div className="text-red-700 text-sm">{step.error}</div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  )
}

export default RealTimeExecutionMonitor
