"use client";

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import {
  GitBranch,
  Plus,
  Search,
  Play,
  Pause,
  MoreVertical,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Database,
  ArrowRight,
  RefreshCw,
  Trash2,
  Copy,
  FileJson,
  Cloud,
  Server,
  Zap,
  Activity,
  TrendingUp,
  Layers,
  Eye,
  Edit,
  Calendar,
  Filter,
  type LucideIcon,
} from 'lucide-react';
import apiClient from '@/lib/api';
import { toast } from '@/hooks/use-toast';
import { axiosErrorDetail, errorMessage, paginatedItems } from '@/types/api';
import { AppLayout } from '@/components/layout/AppLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import { Progress } from '@/components/ui/progress';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { cn } from '@/lib/utils';

type EndpointUI = { type: string; name: string; id?: string };

type PipelineUI = {
  id: string;
  name: string;
  description: string;
  status: string;
  source: EndpointUI;
  destination: EndpointUI;
  schedule: string;
  lastRun: string;
  nextRun: string;
  recordsProcessed: number;
  avgDuration: string;
  successRate: number;
  error?: string;
};

type RunUI = {
  id: string;
  pipeline: string;
  status: string;
  records: number;
  duration: string;
  timestamp: string;
};

type DataSourceUI = {
  id: string;
  name: string;
  source_type: string;
  status: string;
  description: string;
};

const sourceTypes: Record<string, { icon: LucideIcon; color: string; bg: string }> = {
  api: { icon: Cloud, color: 'text-blue-500', bg: 'bg-blue-500/10' },
  database: { icon: Database, color: 'text-green-500', bg: 'bg-green-500/10' },
  stream: { icon: Activity, color: 'text-purple-500', bg: 'bg-purple-500/10' },
  webhook: { icon: Zap, color: 'text-yellow-500', bg: 'bg-yellow-500/10' },
  file: { icon: FileJson, color: 'text-orange-500', bg: 'bg-orange-500/10' },
  cloud_storage: { icon: Cloud, color: 'text-orange-500', bg: 'bg-orange-500/10' },
  warehouse: { icon: Layers, color: 'text-indigo-500', bg: 'bg-indigo-500/10' },
  search: { icon: Server, color: 'text-red-500', bg: 'bg-red-500/10' },
  internal: { icon: GitBranch, color: 'text-cyan-500', bg: 'bg-cyan-500/10' },
  ftp: { icon: Server, color: 'text-muted-foreground', bg: 'bg-muted' },
  email: { icon: Cloud, color: 'text-blue-500', bg: 'bg-blue-500/10' },
};

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function str(value: unknown, fallback = ''): string {
  if (value == null) return fallback;
  return String(value);
}

function num(value: unknown, fallback = 0): number {
  const n = typeof value === 'number' ? value : Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function extractList<T>(data: unknown, keys: string[]): T[] {
  if (Array.isArray(data)) return data as T[];
  if (!data || typeof data !== 'object') return [];
  const obj = data as Record<string, unknown>;
  for (const key of keys) {
    if (Array.isArray(obj[key])) return obj[key] as T[];
  }
  return paginatedItems(data as { results?: T[] });
}

function mapUiStatus(raw: string): string {
  const s = raw.toLowerCase();
  if (['running', 'active', 'in_progress'].includes(s)) return 'running';
  if (['completed', 'success', 'succeeded'].includes(s)) return 'completed';
  if (['failed', 'error'].includes(s)) return 'failed';
  if (['idle', 'paused', 'draft', 'pending', 'archived'].includes(s)) return 'idle';
  return s || 'idle';
}

function formatDuration(seconds: unknown): string {
  const s = num(seconds, 0);
  if (s <= 0) return '—';
  if (s < 60) return `${Math.round(s)}s`;
  const m = Math.floor(s / 60);
  const rem = Math.round(s % 60);
  if (m < 60) return `${m}m ${rem}s`;
  return `${Math.floor(m / 60)}h ${m % 60}m`;
}

function formatRelative(value: unknown): string {
  if (!value) return '—';
  const d = new Date(String(value));
  if (Number.isNaN(d.getTime())) return String(value);
  const diff = Date.now() - d.getTime();
  const abs = Math.abs(diff);
  const mins = Math.round(abs / 60000);
  if (mins < 1) return diff >= 0 ? 'Just now' : 'Soon';
  if (mins < 60) return diff >= 0 ? `${mins} min ago` : `In ${mins} min`;
  const hours = Math.round(mins / 60);
  if (hours < 24) return diff >= 0 ? `${hours} hours ago` : `In ${hours} hours`;
  return d.toLocaleString();
}

function resolveEndpoint(
  value: unknown,
  sourcesById: Map<string, DataSourceUI>,
  fallbackType = 'api'
): EndpointUI {
  if (typeof value === 'string') {
    const src = sourcesById.get(value);
    return src
      ? { type: src.source_type || fallbackType, name: src.name, id: src.id }
      : { type: fallbackType, name: value.slice(0, 8), id: value };
  }
  const obj = asRecord(value);
  if (obj.id || obj.name) {
    const id = str(obj.id);
    const src = id ? sourcesById.get(id) : undefined;
    return {
      id: id || undefined,
      type: str(obj.source_type || obj.type || src?.source_type, fallbackType),
      name: str(obj.name || src?.name, 'Unknown'),
    };
  }
  return { type: fallbackType, name: 'Unknown' };
}

function mapPipeline(raw: Record<string, unknown>, sourcesById: Map<string, DataSourceUI>): PipelineUI {
  const total = num(raw.total_executions);
  const success = num(raw.successful_executions);
  const successRate =
    typeof raw.success_rate === 'number'
      ? raw.success_rate
      : total > 0
        ? (success / total) * 100
        : 100;
  const scheduleConfig = asRecord(raw.schedule_config);
  const schedule =
    str(raw.schedule) ||
    str(scheduleConfig.frequency) ||
    str(raw.trigger_type, 'manual');

  return {
    id: str(raw.id),
    name: str(raw.name, 'Untitled Pipeline'),
    description: str(raw.description, 'No description'),
    status: mapUiStatus(str(raw.status, 'idle')),
    source: resolveEndpoint(raw.source_detail || raw.source, sourcesById, 'api'),
    destination: resolveEndpoint(raw.destination_detail || raw.destination, sourcesById, 'database'),
    schedule,
    lastRun: formatRelative(raw.last_run_at || raw.last_run),
    nextRun: formatRelative(raw.next_run_at || raw.next_run),
    recordsProcessed: num(raw.records_processed || raw.total_records || asRecord(raw.pipeline_config).records),
    avgDuration: formatDuration(raw.average_duration || raw.avg_duration),
    successRate: Math.round(successRate * 10) / 10,
    error: str(raw.error || raw.error_message) || undefined,
  };
}

function mapDataSource(raw: Record<string, unknown>): DataSourceUI {
  return {
    id: str(raw.id),
    name: str(raw.name, 'Unnamed Source'),
    source_type: str(raw.source_type || raw.type, 'api').toLowerCase(),
    status: str(raw.status, 'inactive'),
    description: str(raw.description),
  };
}

export default function PipelinesPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [selectedPipeline, setSelectedPipeline] = useState<PipelineUI | null>(null);
  const [pipelines, setPipelines] = useState<PipelineUI[]>([]);
  const [dataSources, setDataSources] = useState<DataSourceUI[]>([]);
  const [runHistory, setRunHistory] = useState<RunUI[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [actionId, setActionId] = useState<string | null>(null);

  const [newName, setNewName] = useState('');
  const [newDescription, setNewDescription] = useState('');
  const [newSourceId, setNewSourceId] = useState('');
  const [newDestId, setNewDestId] = useState('');
  const [newSchedule, setNewSchedule] = useState('manual');

  const load = useCallback(async () => {
    setIsLoading(true);
    try {
      const [pipelinesRes, sourcesRes] = await Promise.all([
        apiClient.getDataPipelines(),
        apiClient.getDataSources().catch(() => ({ sources: [] })),
      ]);

      const sourceRows = extractList<Record<string, unknown>>(sourcesRes, ['sources', 'results']);
      const mappedSources = sourceRows.map(mapDataSource);
      setDataSources(mappedSources);
      const sourcesById = new Map(mappedSources.map((s) => [s.id, s]));

      const pipelineRows = extractList<Record<string, unknown>>(pipelinesRes, ['pipelines', 'results']);
      const mappedPipelines = pipelineRows.map((row) => mapPipeline(row, sourcesById));
      setPipelines(mappedPipelines);

      const runs: RunUI[] = [];
      await Promise.all(
        mappedPipelines.slice(0, 8).map(async (p) => {
          try {
            const status = await apiClient.getPipelineStatus(p.id);
            runs.push({
              id: `${p.id}-status`,
              pipeline: p.name,
              status: mapUiStatus(str(status.status, p.status)) === 'completed'
                ? 'success'
                : mapUiStatus(str(status.status, p.status)) === 'failed'
                  ? 'failed'
                  : mapUiStatus(str(status.status, p.status)) === 'running'
                    ? 'running'
                    : 'success',
              records: p.recordsProcessed,
              duration: p.avgDuration,
              timestamp: str(asRecord(status).updated_at) || new Date().toLocaleTimeString(),
            });
          } catch {
            /* skip status for this pipeline */
          }
        })
      );
      setRunHistory(
        runs.length > 0
          ? runs
          : mappedPipelines.slice(0, 5).map((p) => ({
              id: p.id,
              pipeline: p.name,
              status: p.status === 'failed' ? 'failed' : p.status === 'running' ? 'running' : 'success',
              records: p.recordsProcessed,
              duration: p.avgDuration,
              timestamp: p.lastRun,
            }))
      );
    } catch (e: unknown) {
      toast({
        title: 'Failed to load pipelines',
        description: axiosErrorDetail(e) || errorMessage(e),
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    setTimeout(() => { load(); }, 0)
  }, [load]);

  const filteredPipelines = useMemo(() => {
    return pipelines.filter((pipeline) => {
      const q = searchQuery.toLowerCase();
      const matchesSearch =
        !q ||
        pipeline.name.toLowerCase().includes(q) ||
        pipeline.description.toLowerCase().includes(q);
      const matchesStatus = statusFilter === 'all' || pipeline.status === statusFilter;
      return matchesSearch && matchesStatus;
    });
  }, [pipelines, searchQuery, statusFilter]);

  const totalRecords = pipelines.reduce((sum, p) => sum + p.recordsProcessed, 0);
  const avgSuccess =
    pipelines.length === 0
      ? 0
      : pipelines.reduce((sum, p) => sum + p.successRate, 0) / pipelines.length;

  const stats = [
    { label: 'Total Pipelines', value: pipelines.length, icon: GitBranch, color: 'text-primary' },
    {
      label: 'Running',
      value: pipelines.filter((p) => p.status === 'running').length,
      icon: Activity,
      color: 'text-green-500',
    },
    {
      label: 'Records Today',
      value: totalRecords >= 1_000_000
        ? `${(totalRecords / 1_000_000).toFixed(1)}M`
        : totalRecords.toLocaleString(),
      icon: Database,
      color: 'text-blue-500',
    },
    {
      label: 'Avg Success Rate',
      value: `${avgSuccess.toFixed(1)}%`,
      icon: TrendingUp,
      color: 'text-purple-500',
    },
  ];

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'running':
        return <Badge className="bg-green-500/10 text-green-500 border-green-500/20">Running</Badge>;
      case 'completed':
        return <Badge className="bg-blue-500/10 text-blue-500 border-blue-500/20">Completed</Badge>;
      case 'failed':
        return <Badge className="bg-red-500/10 text-red-500 border-red-500/20">Failed</Badge>;
      case 'idle':
        return <Badge variant="secondary">Idle</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const typeMeta = (type: string) =>
    sourceTypes[type] || { icon: Database, color: 'text-muted-foreground', bg: 'bg-muted' };

  const handleCreate = async () => {
    if (!newName.trim()) {
      toast({ title: 'Enter a pipeline name', variant: 'destructive' });
      return;
    }
    if (!newSourceId || !newDestId) {
      toast({ title: 'Select source and destination', variant: 'destructive' });
      return;
    }
    setIsCreating(true);
    try {
      await apiClient.createDataPipeline({
        name: newName.trim(),
        description: newDescription.trim(),
        source: newSourceId,
        destination: newDestId,
        trigger_type: newSchedule === 'realtime' ? 'stream' : newSchedule === 'manual' ? 'manual' : 'scheduled',
        schedule_config: { frequency: newSchedule },
        status: 'draft',
        pipeline_config: {},
        steps: [],
      });
      setShowCreateDialog(false);
      setNewName('');
      setNewDescription('');
      setNewSourceId('');
      setNewDestId('');
      await load();
      toast({ title: 'Pipeline created' });
    } catch (e: unknown) {
      toast({
        title: 'Failed to create pipeline',
        description: axiosErrorDetail(e) || errorMessage(e),
        variant: 'destructive',
      });
    } finally {
      setIsCreating(false);
    }
  };

  const handleExecute = async (id: string) => {
    setActionId(id);
    try {
      await apiClient.executePipeline(id);
      await load();
      toast({ title: 'Pipeline started' });
    } catch (e: unknown) {
      toast({
        title: 'Failed to run pipeline',
        description: axiosErrorDetail(e) || errorMessage(e),
        variant: 'destructive',
      });
    } finally {
      setActionId(null);
    }
  };

  const handleStop = async (id: string) => {
    setActionId(id);
    try {
      await apiClient.stopPipeline(id);
      await load();
      toast({ title: 'Pipeline stopped' });
    } catch (e: unknown) {
      toast({
        title: 'Failed to stop pipeline',
        description: axiosErrorDetail(e) || errorMessage(e),
        variant: 'destructive',
      });
    } finally {
      setActionId(null);
    }
  };

  const handleDelete = async (id: string) => {
    setActionId(id);
    try {
      await apiClient.deleteDataPipeline(id);
      setSelectedPipeline(null);
      await load();
      toast({ title: 'Pipeline deleted' });
    } catch (e: unknown) {
      toast({
        title: 'Delete failed',
        description: axiosErrorDetail(e) || errorMessage(e),
        variant: 'destructive',
      });
    } finally {
      setActionId(null);
    }
  };

  return (
    <AppLayout>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-6"
      >
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-3">
              <GitBranch className="h-8 w-8 text-primary" />
              Data Pipelines
            </h1>
            <p className="text-muted-foreground mt-1">
              Manage and monitor your data pipelines
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="icon" onClick={load} disabled={isLoading}>
              <RefreshCw className={cn('h-4 w-4', isLoading && 'animate-spin')} />
            </Button>
            <Button onClick={() => setShowCreateDialog(true)} className="gap-2">
              <Plus className="h-4 w-4" />
              Create Pipeline
            </Button>
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {stats.map((stat, index) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">{stat.label}</p>
                      <p className="text-2xl font-bold">{isLoading ? '—' : stat.value}</p>
                    </div>
                    <div className={cn('p-2 rounded-lg bg-muted/50', stat.color)}>
                      <stat.icon className="h-5 w-5" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>

        <Tabs defaultValue="pipelines" className="space-y-6">
          <TabsList>
            <TabsTrigger value="pipelines">Pipelines</TabsTrigger>
            <TabsTrigger value="runs">Run History</TabsTrigger>
            <TabsTrigger value="sources">Data Sources</TabsTrigger>
          </TabsList>

          <TabsContent value="pipelines" className="space-y-4">
            <div className="flex items-center gap-4">
              <div className="relative flex-1 max-w-md">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search pipelines..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-40">
                  <Filter className="h-4 w-4 mr-2" />
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="running">Running</SelectItem>
                  <SelectItem value="completed">Completed</SelectItem>
                  <SelectItem value="failed">Failed</SelectItem>
                  <SelectItem value="idle">Idle</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {isLoading ? (
              <div className="flex items-center justify-center py-16 text-muted-foreground gap-2">
                <RefreshCw className="h-5 w-5 animate-spin" />
                Loading pipelines…
              </div>
            ) : filteredPipelines.length === 0 ? (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-16 text-center">
                  <GitBranch className="h-12 w-12 text-muted-foreground mb-4" />
                  <h3 className="font-semibold">No pipelines yet</h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    Create a pipeline to sync data between sources
                  </p>
                  <Button onClick={() => setShowCreateDialog(true)} className="gap-2">
                    <Plus className="h-4 w-4" />
                    Create Pipeline
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <div className="grid gap-4">
                {filteredPipelines.map((pipeline, index) => {
                  const sourceType = typeMeta(pipeline.source.type);
                  const destType = typeMeta(pipeline.destination.type);
                  const SourceIcon = sourceType.icon;
                  const DestIcon = destType.icon;

                  return (
                    <motion.div
                      key={pipeline.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.05 }}
                    >
                      <Card
                        className={cn(
                          'hover:shadow-md transition-shadow',
                          pipeline.status === 'failed' && 'border-red-500/30'
                        )}
                      >
                        <CardContent className="p-4">
                          <div className="flex items-start gap-4">
                            <div
                              className={cn(
                                'flex h-12 w-12 items-center justify-center rounded-xl shrink-0',
                                pipeline.status === 'running' && 'bg-green-500/10',
                                pipeline.status === 'completed' && 'bg-blue-500/10',
                                pipeline.status === 'failed' && 'bg-red-500/10',
                                pipeline.status === 'idle' && 'bg-muted'
                              )}
                            >
                              <GitBranch
                                className={cn(
                                  'h-6 w-6',
                                  pipeline.status === 'running' && 'text-green-500',
                                  pipeline.status === 'completed' && 'text-blue-500',
                                  pipeline.status === 'failed' && 'text-red-500',
                                  pipeline.status === 'idle' && 'text-muted-foreground'
                                )}
                              />
                            </div>

                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-1">
                                <h3 className="font-semibold">{pipeline.name}</h3>
                                {getStatusBadge(pipeline.status)}
                                {(pipeline.status === 'running' || actionId === pipeline.id) && (
                                  <RefreshCw className="h-3 w-3 text-green-500 animate-spin" />
                                )}
                              </div>
                              <p className="text-sm text-muted-foreground mb-3">{pipeline.description}</p>

                              <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
                                <div className="flex items-center gap-2">
                                  <div className={cn('p-1.5 rounded', sourceType.bg)}>
                                    <SourceIcon className={cn('h-4 w-4', sourceType.color)} />
                                  </div>
                                  <span className="text-sm font-medium">{pipeline.source.name}</span>
                                </div>
                                <ArrowRight className="h-4 w-4 text-muted-foreground" />
                                <div className="flex items-center gap-2">
                                  <div className={cn('p-1.5 rounded', destType.bg)}>
                                    <DestIcon className={cn('h-4 w-4', destType.color)} />
                                  </div>
                                  <span className="text-sm font-medium">{pipeline.destination.name}</span>
                                </div>
                              </div>

                              {pipeline.error && (
                                <div className="flex items-center gap-2 mt-2 text-sm text-red-500">
                                  <AlertCircle className="h-4 w-4" />
                                  {pipeline.error}
                                </div>
                              )}
                            </div>

                            <div className="hidden lg:flex flex-col items-end gap-2 text-sm min-w-[200px]">
                              <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-right">
                                <span className="text-muted-foreground">Schedule:</span>
                                <span>{pipeline.schedule}</span>
                                <span className="text-muted-foreground">Last Run:</span>
                                <span>{pipeline.lastRun}</span>
                                <span className="text-muted-foreground">Records:</span>
                                <span>{pipeline.recordsProcessed.toLocaleString()}</span>
                                <span className="text-muted-foreground">Success:</span>
                                <span
                                  className={cn(
                                    pipeline.successRate >= 98 ? 'text-green-500' : 'text-yellow-500'
                                  )}
                                >
                                  {pipeline.successRate}%
                                </span>
                              </div>
                            </div>

                            <div className="flex items-center gap-2">
                              {pipeline.status === 'running' ? (
                                <Button
                                  variant="outline"
                                  size="icon"
                                  onClick={() => handleStop(pipeline.id)}
                                >
                                  <Pause className="h-4 w-4" />
                                </Button>
                              ) : (
                                <Button
                                  variant="outline"
                                  size="icon"
                                  onClick={() => handleExecute(pipeline.id)}
                                >
                                  <Play className="h-4 w-4" />
                                </Button>
                              )}
                              <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                  <Button variant="ghost" size="icon">
                                    <MoreVertical className="h-4 w-4" />
                                  </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent align="end">
                                  <DropdownMenuItem onClick={() => setSelectedPipeline(pipeline)}>
                                    <Eye className="h-4 w-4 mr-2" />
                                    View Details
                                  </DropdownMenuItem>
                                  <DropdownMenuItem onClick={() => handleExecute(pipeline.id)}>
                                    <Play className="h-4 w-4 mr-2" />
                                    Run Now
                                  </DropdownMenuItem>
                                  <DropdownMenuItem>
                                    <Edit className="h-4 w-4 mr-2" />
                                    Edit Pipeline
                                  </DropdownMenuItem>
                                  <DropdownMenuItem>
                                    <Copy className="h-4 w-4 mr-2" />
                                    Duplicate
                                  </DropdownMenuItem>
                                  <DropdownMenuItem>
                                    <Calendar className="h-4 w-4 mr-2" />
                                    View Schedule
                                  </DropdownMenuItem>
                                  <DropdownMenuSeparator />
                                  <DropdownMenuItem
                                    className="text-destructive"
                                    onClick={() => handleDelete(pipeline.id)}
                                  >
                                    <Trash2 className="h-4 w-4 mr-2" />
                                    Delete
                                  </DropdownMenuItem>
                                </DropdownMenuContent>
                              </DropdownMenu>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    </motion.div>
                  );
                })}
              </div>
            )}
          </TabsContent>

          <TabsContent value="runs" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Recent Runs</CardTitle>
                <CardDescription>Pipeline execution history</CardDescription>
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <div className="flex items-center justify-center py-12 text-muted-foreground gap-2">
                    <RefreshCw className="h-5 w-5 animate-spin" />
                    Loading runs…
                  </div>
                ) : runHistory.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-12 text-center">
                    <Activity className="h-12 w-12 text-muted-foreground mb-4" />
                    <h3 className="font-semibold">No runs yet</h3>
                    <p className="text-sm text-muted-foreground">Execute a pipeline to see history</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {runHistory.map((run, index) => (
                      <motion.div
                        key={run.id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.05 }}
                        className="flex items-center gap-4 p-3 rounded-lg bg-muted/50"
                      >
                        {run.status === 'success' && <CheckCircle2 className="h-5 w-5 text-green-500" />}
                        {run.status === 'failed' && <XCircle className="h-5 w-5 text-red-500" />}
                        {run.status === 'running' && (
                          <RefreshCw className="h-5 w-5 text-blue-500 animate-spin" />
                        )}

                        <div className="flex-1">
                          <p className="font-medium">{run.pipeline}</p>
                          <p className="text-sm text-muted-foreground">
                            {run.records.toLocaleString()} records • {run.duration}
                          </p>
                        </div>
                        <div className="text-sm text-muted-foreground">{run.timestamp}</div>
                        <Button variant="ghost" size="sm">
                          <Eye className="h-4 w-4" />
                        </Button>
                      </motion.div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="sources" className="space-y-6">
            {isLoading ? (
              <div className="flex items-center justify-center py-16 text-muted-foreground gap-2">
                <RefreshCw className="h-5 w-5 animate-spin" />
                Loading sources…
              </div>
            ) : dataSources.length === 0 ? (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-16 text-center">
                  <Database className="h-12 w-12 text-muted-foreground mb-4" />
                  <h3 className="font-semibold">No data sources</h3>
                  <p className="text-sm text-muted-foreground">
                    Add data sources to connect pipelines
                  </p>
                </CardContent>
              </Card>
            ) : (
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {dataSources.map((source) => {
                  const meta = typeMeta(source.source_type);
                  const Icon = meta.icon;
                  return (
                    <Card key={source.id} className="hover:shadow-md transition-shadow">
                      <CardContent className="p-4 flex items-center gap-4">
                        <div className={cn('p-3 rounded-xl', meta.bg)}>
                          <Icon className={cn('h-6 w-6', meta.color)} />
                        </div>
                        <div className="min-w-0">
                          <p className="font-medium truncate">{source.name}</p>
                          <p className="text-sm text-muted-foreground capitalize">
                            {source.source_type} • {source.status}
                          </p>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            )}
          </TabsContent>
        </Tabs>

        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogContent className="max-w-xl">
            <DialogHeader>
              <DialogTitle>Create Data Pipeline</DialogTitle>
              <DialogDescription>
                Configure a new data pipeline to sync your data
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">Pipeline Name</Label>
                <Input
                  id="name"
                  placeholder="My Data Pipeline"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Input
                  id="description"
                  placeholder="Sync data from source to destination"
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Source</Label>
                  <Select value={newSourceId || undefined} onValueChange={setNewSourceId}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select source" />
                    </SelectTrigger>
                    <SelectContent>
                      {dataSources.map((s) => (
                        <SelectItem key={s.id} value={s.id}>
                          {s.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Destination</Label>
                  <Select value={newDestId || undefined} onValueChange={setNewDestId}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select destination" />
                    </SelectTrigger>
                    <SelectContent>
                      {dataSources.map((s) => (
                        <SelectItem key={s.id} value={s.id}>
                          {s.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              {dataSources.length === 0 && (
                <p className="text-sm text-muted-foreground">
                  Create data sources first before wiring a pipeline.
                </p>
              )}
              <div className="space-y-2">
                <Label>Schedule</Label>
                <Select value={newSchedule} onValueChange={setNewSchedule}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select schedule" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="manual">Manual</SelectItem>
                    <SelectItem value="realtime">Real-time</SelectItem>
                    <SelectItem value="5min">Every 5 minutes</SelectItem>
                    <SelectItem value="15min">Every 15 minutes</SelectItem>
                    <SelectItem value="hourly">Hourly</SelectItem>
                    <SelectItem value="daily">Daily</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                Cancel
              </Button>
              <Button onClick={handleCreate} disabled={isCreating}>
                {isCreating ? <RefreshCw className="h-4 w-4 animate-spin mr-2" /> : null}
                Create Pipeline
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        <Dialog open={!!selectedPipeline} onOpenChange={() => setSelectedPipeline(null)}>
          <DialogContent className="max-w-2xl">
            {selectedPipeline && (
              <>
                <DialogHeader>
                  <DialogTitle className="flex items-center gap-2">
                    {selectedPipeline.name}
                    {getStatusBadge(selectedPipeline.status)}
                  </DialogTitle>
                  <DialogDescription>{selectedPipeline.description}</DialogDescription>
                </DialogHeader>
                <div className="space-y-6">
                  <div className="grid grid-cols-2 gap-4">
                    <Card>
                      <CardContent className="p-4">
                        <p className="text-sm text-muted-foreground mb-1">Records Processed</p>
                        <p className="text-2xl font-bold">
                          {selectedPipeline.recordsProcessed.toLocaleString()}
                        </p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="p-4">
                        <p className="text-sm text-muted-foreground mb-1">Success Rate</p>
                        <p className="text-2xl font-bold">{selectedPipeline.successRate}%</p>
                      </CardContent>
                    </Card>
                  </div>
                  <div>
                    <p className="text-sm font-medium mb-2">Pipeline Health</p>
                    <Progress value={selectedPipeline.successRate} className="h-2" />
                  </div>
                  <Separator />
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-muted-foreground">Schedule</p>
                      <p className="font-medium">{selectedPipeline.schedule}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Avg Duration</p>
                      <p className="font-medium">{selectedPipeline.avgDuration}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Last Run</p>
                      <p className="font-medium">{selectedPipeline.lastRun}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Next Run</p>
                      <p className="font-medium">{selectedPipeline.nextRun}</p>
                    </div>
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setSelectedPipeline(null)}>
                    Close
                  </Button>
                  <Button onClick={() => handleExecute(selectedPipeline.id)}>
                    <Play className="h-4 w-4 mr-2" />
                    Run Now
                  </Button>
                </DialogFooter>
              </>
            )}
          </DialogContent>
        </Dialog>
      </motion.div>
    </AppLayout>
  );
}
