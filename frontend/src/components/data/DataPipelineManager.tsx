"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Plus,
  Edit,
  Play,
  Pause,
  Square,
  Search,
  Activity,
  Clock,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Cloud,
  Server,
  FileText,
  Shield,
  RefreshCw,
  Monitor,
  Network,
  Cpu,
  HardDrive,
  MemoryStick,
  Globe,
  Database,
  Eye
} from 'lucide-react';interface DataPipeline {
  id: string;
  name: string;
  description: string;
  status: 'draft' | 'active' | 'paused' | 'error' | 'completed';
  type: 'batch' | 'streaming' | 'hybrid';
  schedule: {
    enabled: boolean;
    cron: string;
    timezone: string;
    next_run?: string;
  };
  source: {
    type: 'database' | 'api' | 'file' | 'stream' | 'webhook';
    config: Record<string, unknown>;
    connection_id?: string;
  };
  destinations: Array<{
    type: 'database' | 'api' | 'file' | 'stream' | 'warehouse';
    config: Record<string, unknown>;
    connection_id?: string;
  }>;
  transformations: Array<{
    id: string;
    name: string;
    type: 'filter' | 'map' | 'aggregate' | 'join' | 'custom';
    config: Record<string, unknown>;
    order: number;
  }>;
  monitoring: {
    health_checks: boolean;
    alerting: boolean;
    metrics_enabled: boolean;
    log_level: 'debug' | 'info' | 'warn' | 'error';
  };
  performance: {
    throughput: number;
    latency: number;
    success_rate: number;
    error_rate: number;
  };
  resource_usage: {
    cpu_percent: number;
    memory_mb: number;
    storage_gb: number;
    network_mbps: number;
  };
  last_run?: {
    records_processed: number;
    error_message?: string;
    timestamp: string;
  };
  created_at: string;
  updated_at: string;
  created_by: string;
}

interface DataConnection {
  id: string;
  name: string;
  type: 'postgresql' | 'mysql' | 'mongodb' | 'redis' | 'elasticsearch' | 's3' | 'bigquery' | 'snowflake';
  host: string;
  port: number;
  database?: string;
  username: string;
  ssl_enabled: boolean;
  connection_pool: {
    min_connections: number;
    max_connections: number;
    timeout_seconds: number;
  };
  status: 'connected' | 'disconnected' | 'error';
  last_tested: string;
  created_at: string;
}

interface PipelineExecution {
  id: string;
  pipeline_id: string;
  status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
  started_at: string;
  completed_at?: string;
  duration_seconds?: number;
  records_processed: number;
  records_failed: number;
  logs: Array<{
    timestamp: string;
    level: 'info' | 'warn' | 'error' | 'debug';
    message: string;
    component?: string;
  }>;
  metrics: {
    throughput_per_second: number;
    memory_peak_mb: number;
    cpu_peak_percent: number;
    network_bytes: number;
  };
  error_details?: {
    error_type: string;
    error_message: string;
    stack_trace?: string;
    failed_records: number;
  };
}

interface DataQualityRule {
  id: string;
  name: string;
  pipeline_id: string;
  rule_type: 'not_null' | 'unique' | 'range' | 'regex' | 'custom';
  field: string;
  config: Record<string, unknown>;
  severity: 'low' | 'medium' | 'high' | 'critical';
  enabled: boolean;
  last_check: {
    timestamp: string;
    passed: boolean;
    violations: number;
    details?: string;
  };
}

interface PipelineTemplate {
  id: string;
  name: string;
  description: string;
  category: 'etl' | 'streaming' | 'ml_pipeline' | 'analytics' | 'integration';
  template_config: Partial<DataPipeline>;
  popularity: number;
  tags: string[];
  created_by: string;
}

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'success':
    case 'completed':
      return <CheckCircle2 className="w-4 h-4 text-green-500" />;
    case 'error':
    case 'failed':
    case 'disconnected':
      return <XCircle className="w-4 h-4 text-red-500" />;
    case 'paused':
    case 'cancelled':
      return <Pause className="w-4 h-4 text-yellow-500" />;
    case 'running':
    case 'queued':
      return <Clock className="w-4 h-4 text-blue-500" />;
    case 'draft':
      return <Edit className="w-4 h-4 text-gray-500" />;
    default:
      return <Clock className="w-4 h-4 text-gray-500" />;
  }
};

const getConnectionIcon = (type: string) => {
  switch (type) {
    case 'postgresql':
    case 'mysql':
    case 'mongodb':
      return <Database className="w-4 h-4" />;
    case 'api':
    case 'webhook':
      return <Globe className="w-4 h-4" />;
    case 'file':
      return <FileText className="w-4 h-4" />;
    case 's3':
    case 'bigquery':
    case 'snowflake':
      return <Cloud className="w-4 h-4" />;
    case 'redis':
    case 'elasticsearch':
      return <Server className="w-4 h-4" />;
    default:
      return <Database className="w-4 h-4" />;
  }
};

export const DataPipelineManager: React.FC = () => {
  const [pipelines, setPipelines] = useState<DataPipeline[]>([]);
  const [connections, setConnections] = useState<DataConnection[]>([]);
  const [executions, setExecutions] = useState<PipelineExecution[]>([]);
  const [qualityRules, setQualityRules] = useState<DataQualityRule[]>([]);
  const [templates, setTemplates] = useState<PipelineTemplate[]>([]);
  const [selectedPipeline, setSelectedPipeline] = useState<DataPipeline | null>(null);
  const [activeTab, setActiveTab] = useState('pipelines');
  const [isLoading, setIsLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const loadPipelineData = async () => {
    try {
      setIsLoading(true);
      const [pipelinesRes, connectionsRes, executionsRes, qualityRes, templatesRes] = await Promise.all([
        fetch('/api/data-pipelines/'),
        fetch('/api/data-connections/'),
        fetch('/api/data-pipeline-executions/'),
        fetch('/api/data-quality-rules/'),
        fetch('/api/data-pipeline-templates/')
      ]);

      if (pipelinesRes.ok) {
        const data = await pipelinesRes.json();
        setPipelines(data);
      }

      if (connectionsRes.ok) {
        const data = await connectionsRes.json();
        setConnections(data);
      }

      if (executionsRes.ok) {
        const data = await executionsRes.json();
        setExecutions(data);
      }

      if (qualityRes.ok) {
        const data = await qualityRes.json();
        setQualityRules(data);
      }

      if (templatesRes.ok) {
        const data = await templatesRes.json();
        setTemplates(data);
      }
    } catch (error) {
      console.error('Failed to load pipeline data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const runPipeline = async (pipelineId: string) => {
    try {
      setIsLoading(true);
      const response = await fetch(`/api/data-pipelines/${pipelineId}/run/`, {
        method: 'POST'
      });

      if (response.ok) {
        const execution = await response.json();
        setExecutions(prev => [execution, ...prev]);
        
        // Update pipeline status
        setPipelines(prev => 
          prev.map(p => 
            p.id === pipelineId 
              ? { ...p, status: 'active' as const }
              : p
          )
        );
      }
    } catch (error) {
      console.error('Failed to run pipeline:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const pausePipeline = async (pipelineId: string) => {
    try {
      const response = await fetch(`/api/data-pipelines/${pipelineId}/pause/`, {
        method: 'POST'
      });

      if (response.ok) {
        setPipelines(prev => 
          prev.map(p => 
            p.id === pipelineId 
              ? { ...p, status: 'paused' as const }
              : p
          )
        );
      }
    } catch (error) {
      console.error('Failed to pause pipeline:', error);
    }
  };

  const stopPipeline = async (pipelineId: string) => {
    try {
      const response = await fetch(`/api/data-pipelines/${pipelineId}/stop/`, {
        method: 'POST'
      });

      if (response.ok) {
        setPipelines(prev => 
          prev.map(p => 
            p.id === pipelineId 
              ? { ...p, status: 'draft' as const }
              : p
          )
        );
      }
    } catch (error) {
      console.error('Failed to stop pipeline:', error);
    }
  };

  const testConnection = async (connectionId: string) => {
    try {
      const response = await fetch(`/api/data-connections/${connectionId}/test/`, {
        method: 'POST'
      });

      if (response.ok) {
        const result = await response.json();
        setConnections(prev => 
          prev.map(c => 
            c.id === connectionId 
              ? { 
                  ...c, 
                  status: result.success ? 'connected' as const : 'error' as const,
                  last_tested: new Date().toISOString()
                }
              : c
          )
        );
      }
    } catch (error) {
      console.error('Failed to test connection:', error);
    }
  };

  const createFromTemplate = async (template: PipelineTemplate) => {
    try {
      const newPipeline = {
        ...template.template_config,
        name: `${template.name} - Copy`,
        description: template.description
      };
      
      const response = await fetch('/api/data-pipelines/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newPipeline)
      });

      if (response.ok) {
        const created = await response.json();
        setPipelines(prev => [...prev, created]);
        setSelectedPipeline(created);
        setActiveTab('configure');
      }
    } catch (error) {
      console.error('Failed to create pipeline from template:', error);
    }
  };

  const filteredPipelines = pipelines.filter(pipeline => {
    const matchesSearch = pipeline.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         pipeline.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || pipeline.status === statusFilter;
    const matchesType = typeFilter === 'all' || pipeline.type === typeFilter;
    
    return matchesSearch && matchesStatus && matchesType;
  });
    useEffect(() => {
        setTimeout(() => loadPipelineData(), 0);
      }, []);

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Data Pipeline Manager
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Build, manage, and monitor data processing pipelines
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={loadPipelineData} variant="outline" size="sm">
            <RefreshCw className="w-4 h-4" />
          </Button>
          <Button>
            <Plus className="w-4 h-4 mr-2" />
            New Pipeline
          </Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="pipelines" className="flex items-center gap-2">
            <Database className="w-4 h-4" />
            Pipelines
          </TabsTrigger>
          <TabsTrigger value="executions" className="flex items-center gap-2">
            <Activity className="w-4 h-4" />
            Executions
          </TabsTrigger>
          <TabsTrigger value="connections" className="flex items-center gap-2">
            <Network className="w-4 h-4" />
            Connections
          </TabsTrigger>
          <TabsTrigger value="quality" className="flex items-center gap-2">
            <Shield className="w-4 h-4" />
            Data Quality
          </TabsTrigger>
          <TabsTrigger value="templates" className="flex items-center gap-2">
            <FileText className="w-4 h-4" />
            Templates
          </TabsTrigger>
          <TabsTrigger value="monitoring" className="flex items-center gap-2">
            <Monitor className="w-4 h-4" />
            Monitoring
          </TabsTrigger>
        </TabsList>

        <TabsContent value="pipelines" className="space-y-6">
          {/* Filters */}
          <Card>
            <CardContent className="p-4">
              <div className="flex flex-wrap gap-4 items-center">
                <div className="flex-1 min-w-64">
                  <div className="relative">
                    <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                    <Input
                      placeholder="Search pipelines..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-10"
                    />
                  </div>
                </div>
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Status</SelectItem>
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="paused">Paused</SelectItem>
                    <SelectItem value="draft">Draft</SelectItem>
                    <SelectItem value="error">Error</SelectItem>
                  </SelectContent>
                </Select>
                <Select value={typeFilter} onValueChange={setTypeFilter}>
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Types</SelectItem>
                    <SelectItem value="batch">Batch</SelectItem>
                    <SelectItem value="streaming">Streaming</SelectItem>
                    <SelectItem value="hybrid">Hybrid</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          {/* Pipelines List */}
          <div className="space-y-4">
            {filteredPipelines.map((pipeline) => (
              <Card key={pipeline.id} className="hover:shadow-lg transition-shadow">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg flex items-center justify-center">
                        <Database className="w-6 h-6 text-white" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-lg flex items-center gap-2">
                          {pipeline.name}
                          {getStatusIcon(pipeline.status)}
                        </h3>
                        <p className="text-gray-600 dark:text-gray-400">{pipeline.description}</p>
                        <div className="flex items-center gap-4 mt-2">
                          <Badge variant="outline">{pipeline.type}</Badge>
                          <Badge variant="outline">{pipeline.status}</Badge>
                          {pipeline.schedule.enabled && (
                            <Badge variant="secondary">Scheduled</Badge>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {pipeline.status === 'draft' || pipeline.status === 'paused' ? (
                        <Button 
                          size="sm" 
                          onClick={() => runPipeline(pipeline.id)}
                          disabled={isLoading}
                        >
                          <Play className="w-4 h-4 mr-1" />
                          Run
                        </Button>
                      ) : pipeline.status === 'active' ? (
                        <>
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={() => pausePipeline(pipeline.id)}
                          >
                            <Pause className="w-4 h-4 mr-1" />
                            Pause
                          </Button>
                          <Button 
                            variant="destructive" 
                            size="sm"
                            onClick={() => stopPipeline(pipeline.id)}
                          >
                            <Square className="w-4 h-4 mr-1" />
                            Stop
                          </Button>
                        </>
                      ) : null}
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => {
                          setSelectedPipeline(pipeline);
                          setActiveTab('monitoring');
                        }}
                      >
                        <Eye className="w-4 h-4 mr-1" />
                        Monitor
                      </Button>
                      <Button variant="outline" size="sm">
                        <Edit className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                  
                  {/* Pipeline Metrics */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600">
                        {pipeline.performance.throughput.toLocaleString()}
                      </div>
                      <div className="text-sm text-gray-600">Records/sec</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-600">
                        {pipeline.performance.success_rate.toFixed(1)}%
                      </div>
                      <div className="text-sm text-gray-600">Success Rate</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-orange-600">
                        {pipeline.performance.latency}ms
                      </div>
                      <div className="text-sm text-gray-600">Avg Latency</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-purple-600">
                        {pipeline.last_run?.records_processed.toLocaleString() ?? 'N/A'}
                      </div>
                      <div className="text-sm text-gray-600">Last Run</div>
                    </div>
                  </div>

                  {/* Resource Usage */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="flex items-center gap-2 text-sm">
                      <Cpu className="w-4 h-4 text-blue-500" />
                      <span>CPU: {pipeline.resource_usage.cpu_percent}%</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <MemoryStick className="w-4 h-4 text-green-500" />
                      <span>RAM: {pipeline.resource_usage.memory_mb}MB</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <HardDrive className="w-4 h-4 text-orange-500" />
                      <span>Storage: {pipeline.resource_usage.storage_gb}GB</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <Network className="w-4 h-4 text-purple-500" />
                      <span>Network: {pipeline.resource_usage.network_mbps}Mbps</span>
                    </div>
                  </div>

                  {pipeline.last_run?.error_message && (
                    <Alert className="mt-4">
                      <AlertTriangle className="h-4 w-4" />
                      <AlertDescription>
                        Last run failed: {pipeline.last_run.error_message}
                      </AlertDescription>
                    </Alert>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="executions" className="space-y-6">
          <ExecutionHistory executions={executions} pipelines={pipelines} />
        </TabsContent>

        <TabsContent value="connections" className="space-y-6">
          <ConnectionManager connections={connections} onTestConnection={testConnection} />
        </TabsContent>

        <TabsContent value="quality" className="space-y-6">
          <DataQualityManager rules={qualityRules} pipelines={pipelines} />
        </TabsContent>

        <TabsContent value="templates" className="space-y-6">
          <TemplateLibrary templates={templates} onCreateFromTemplate={createFromTemplate} />
        </TabsContent>

        <TabsContent value="monitoring" className="space-y-6">
          {selectedPipeline ? (
            <PipelineMonitoring pipeline={selectedPipeline} executions={executions} />
          ) : (
            <Card>
              <CardContent className="p-8 text-center">
                <Monitor className="w-16 h-16 mx-auto text-gray-400 mb-4" />
                <h3 className="text-lg font-semibold mb-2">No Pipeline Selected</h3>
                <p className="text-gray-600 dark:text-gray-400">
                  Select a pipeline from the pipelines tab to view its monitoring dashboard.
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

const ExecutionHistory: React.FC<{
  executions: PipelineExecution[];
  pipelines: DataPipeline[];
}> = ({ executions, pipelines }) => {
  return (
    <div className="space-y-4">
      {executions.map((execution) => {
        const pipeline = pipelines.find(p => p.id === execution.pipeline_id);
        return (
          <Card key={execution.id}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="font-semibold text-lg flex items-center gap-2">
                    {pipeline?.name || 'Unknown Pipeline'}
                    {getStatusIcon(execution.status)}
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400">
                    Started: {new Date(execution.started_at).toLocaleString()}
                  </p>
                </div>
                <Badge 
                  variant={
                    execution.status === 'completed' ? 'default' :
                    execution.status === 'failed' ? 'destructive' :
                    execution.status === 'running' ? 'secondary' :
                    'outline'
                  }
                >
                  {execution.status}
                </Badge>
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <div>
                  <div className="text-sm text-gray-600">Duration</div>
                  <div className="text-lg font-semibold">
                    {execution.duration_seconds ? `${execution.duration_seconds}s` : 'Running...'}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-600">Records Processed</div>
                  <div className="text-lg font-semibold text-green-600">
                    {execution.records_processed.toLocaleString()}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-600">Records Failed</div>
                  <div className="text-lg font-semibold text-red-600">
                    {execution.records_failed.toLocaleString()}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-600">Throughput</div>
                  <div className="text-lg font-semibold text-blue-600">
                    {execution.metrics.throughput_per_second.toFixed(1)}/sec
                  </div>
                </div>
              </div>

              {execution.error_details && (
                <Alert>
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    {execution.error_details.error_message}
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
};

const ConnectionManager: React.FC<{
  connections: DataConnection[];
  onTestConnection: (id: string) => void;
}> = ({ connections, onTestConnection }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {connections.map((connection) => (
        <Card key={connection.id}>
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg flex items-center justify-center">
                  {getConnectionIcon(connection.type)}
                </div>
                <div>
                  <h3 className="font-semibold">{connection.name}</h3>
                  <p className="text-sm text-gray-600">{connection.type}</p>
                </div>
              </div>
              <Badge 
                variant={
                  connection.status === 'connected' ? 'default' :
                  connection.status === 'error' ? 'destructive' :
                  'secondary'
                }
              >
                {connection.status}
              </Badge>
            </div>
            
            <div className="space-y-2 mb-4 text-sm">
              <div>Host: {connection.host}:{connection.port}</div>
              {connection.database && <div>Database: {connection.database}</div>}
              <div>SSL: {connection.ssl_enabled ? 'Enabled' : 'Disabled'}</div>
              <div>Pool: {connection.connection_pool.min_connections}-{connection.connection_pool.max_connections}</div>
            </div>
            
            <div className="flex gap-2">
              <Button 
                size="sm" 
                className="flex-1"
                onClick={() => onTestConnection(connection.id)}
              >
                Test Connection
              </Button>
              <Button variant="outline" size="sm">
                <Edit className="w-4 h-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};

const DataQualityManager: React.FC<{
  rules: DataQualityRule[];
  pipelines: DataPipeline[];
}> = ({ rules, pipelines }) => {
  return (
    <div className="space-y-4">
      {rules.map((rule) => {
        const pipeline = pipelines.find(p => p.id === rule.pipeline_id);
        return (
          <Card key={rule.id}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="font-semibold text-lg flex items-center gap-2">
                    {rule.name}
                    <Switch checked={rule.enabled} />
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400">
                    {pipeline?.name} → {rule.field}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge 
                    variant={
                      rule.severity === 'critical' ? 'destructive' :
                      rule.severity === 'high' ? 'destructive' :
                      rule.severity === 'medium' ? 'secondary' :
                      'outline'
                    }
                  >
                    {rule.severity}
                  </Badge>
                  <Badge variant="outline">{rule.rule_type}</Badge>
                </div>
              </div>
              
              {rule.last_check && (
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {rule.last_check.passed ? (
                      <CheckCircle2 className="w-4 h-4 text-green-500" />
                    ) : (
                      <XCircle className="w-4 h-4 text-red-500" />
                    )}
                    <span className="text-sm">
                      Last check: {new Date(rule.last_check.timestamp).toLocaleString()}
                    </span>
                  </div>
                  {rule.last_check.violations > 0 && (
                    <Badge variant="destructive">
                      {rule.last_check.violations} violations
                    </Badge>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
};

const TemplateLibrary: React.FC<{
  templates: PipelineTemplate[];
  onCreateFromTemplate: (template: PipelineTemplate) => void;
}> = ({ templates, onCreateFromTemplate }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {templates.map((template) => (
        <Card key={template.id} className="cursor-pointer hover:shadow-lg transition-shadow">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-blue-500 rounded-lg flex items-center justify-center">
                <FileText className="w-6 h-6 text-white" />
              </div>
              <Badge variant="outline">{template.category}</Badge>
            </div>
            
            <h3 className="font-semibold text-lg mb-2">{template.name}</h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">{template.description}</p>
            
            <div className="flex flex-wrap gap-2 mb-4">
              {template.tags.map((tag) => (
                <Badge key={tag} variant="secondary" className="text-xs">
                  {tag}
                </Badge>
              ))}
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-500">
                ⭐ {template.popularity} uses
              </span>
              <Button 
                size="sm" 
                onClick={() => onCreateFromTemplate(template)}
              >
                <Plus className="w-4 h-4 mr-1" />
                Use Template
              </Button>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};

const PipelineMonitoring: React.FC<{
  pipeline: DataPipeline;
  executions: PipelineExecution[];
}> = ({ pipeline, executions }) => {
  const pipelineExecutions = executions.filter(e => e.pipeline_id === pipeline.id);
  
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Monitor className="w-5 h-5" />
            {pipeline.name} - Live Monitoring
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600">
                {pipeline.performance.success_rate.toFixed(1)}%
              </div>
              <div className="text-sm text-gray-600">Success Rate</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600">
                {pipeline.performance.throughput}
              </div>
              <div className="text-sm text-gray-600">Records/sec</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-orange-600">
                {pipeline.performance.latency}ms
              </div>
              <div className="text-sm text-gray-600">Avg Latency</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-red-600">
                {pipeline.performance.error_rate.toFixed(2)}%
              </div>
              <div className="text-sm text-gray-600">Error Rate</div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Recent Executions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {pipelineExecutions.slice(0, 5).map((execution) => (
              <div key={execution.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div className="flex items-center gap-3">
                  {getStatusIcon(execution.status)}
                  <div>
                    <p className="font-medium">{execution.status}</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {new Date(execution.started_at).toLocaleString()}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-medium">{execution.records_processed.toLocaleString()}</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">records</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default DataPipelineManager;

