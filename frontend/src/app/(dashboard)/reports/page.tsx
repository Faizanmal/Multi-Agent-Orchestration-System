"use client";

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import {
  FileText,
  Plus,
  Search,
  Download,
  Calendar,
  Clock,
  MoreVertical,
  Eye,
  Trash2,
  Copy,
  Share2,
  Filter,
  TrendingUp,
  PieChart,
  BarChart3,
  LineChart,
  FileSpreadsheet,
  File,
  CheckCircle2,
  RefreshCw,
  Star,
  Users,
  Mail,
  Sparkles,
  Printer,
  Edit,
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
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
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

type ReportUI = {
  id: string;
  name: string;
  template: string;
  status: string;
  generatedAt: string;
  generatedBy: string;
  format: string;
  size: string;
  schedule: string | null;
  error?: string;
  reportType: string;
};

type TemplateUI = {
  id: string;
  name: string;
  description: string;
  icon: LucideIcon;
  category: string;
  popular: boolean;
};

type ScheduledUI = {
  id: string;
  name: string;
  template: string;
  schedule: string;
  recipients: string[];
  enabled: boolean;
  reportId: string;
};

const TEMPLATE_ICONS: Record<string, LucideIcon> = {
  analytics: BarChart3,
  performance: TrendingUp,
  financial: PieChart,
  finance: PieChart,
  operational: LineChart,
  operations: LineChart,
  custom: FileText,
  agent_performance: TrendingUp,
  system_metrics: BarChart3,
  usage_analytics: Users,
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
  if (['completed', 'published', 'ready', 'success'].includes(s)) return 'completed';
  if (['generating', 'processing', 'pending', 'running', 'draft'].includes(s)) return 'generating';
  if (['failed', 'error'].includes(s)) return 'failed';
  return s || 'completed';
}

function formatBytes(n: unknown): string {
  const bytes = typeof n === 'number' ? n : Number(n);
  if (!Number.isFinite(bytes) || bytes <= 0) return '-';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(value: unknown): string {
  if (!value) return '—';
  const d = new Date(String(value));
  return Number.isNaN(d.getTime()) ? String(value) : d.toLocaleString();
}

function mapReport(raw: Record<string, unknown>): ReportUI {
  const config = asRecord(raw.config);
  const schedule =
    str(raw.schedule) ||
    str(config.schedule) ||
    str(config.frequency) ||
    null;
  return {
    id: str(raw.id),
    name: str(raw.name, 'Untitled Report'),
    template: str(raw.template_name || raw.template || raw.report_type, 'Custom'),
    status: mapUiStatus(str(raw.status || raw.generation_status, 'completed')),
    generatedAt: formatDate(raw.last_generated || raw.generated_at || raw.created_at),
    generatedBy: str(raw.generated_by || raw.user_name || raw.username, 'You'),
    format: str(raw.format || config.format || raw.export_format, 'pdf').toLowerCase(),
    size: formatBytes(raw.file_size || raw.size),
    schedule: schedule || null,
    error: str(raw.error || raw.error_message) || undefined,
    reportType: str(raw.report_type, 'custom'),
  };
}

function mapTemplate(raw: Record<string, unknown>): TemplateUI {
  const category = str(raw.category, 'custom').toLowerCase();
  return {
    id: str(raw.id),
    name: str(raw.name, 'Untitled Template'),
    description: str(raw.description, 'No description'),
    icon: TEMPLATE_ICONS[category] || TEMPLATE_ICONS[str(raw.report_type)] || FileText,
    category,
    popular: Boolean(raw.popular || raw.is_official || (Number(raw.usage_count) || 0) > 10),
  };
}

function mapScheduled(raw: Record<string, unknown>, report?: ReportUI): ScheduledUI | null {
  const config = asRecord(raw.config);
  const scheduleConfig = asRecord(raw.schedule_config || config.schedule);
  const frequency =
    str(raw.frequency) ||
    str(scheduleConfig.frequency) ||
    str(config.schedule) ||
    str(config.frequency);
  if (!frequency && !raw.is_scheduled && !scheduleConfig.enabled) return null;

  const recipientsRaw = raw.email_recipients || scheduleConfig.recipients || config.recipients || [];
  const recipients = Array.isArray(recipientsRaw)
    ? recipientsRaw.map((r) => str(r)).filter(Boolean)
    : [];

  return {
    id: str(raw.schedule_id || raw.id),
    name: str(raw.schedule_name || raw.name, report?.name || 'Scheduled Report'),
    template: report?.template || str(raw.report_type || raw.template, 'Custom'),
    schedule: frequency,
    recipients,
    enabled: raw.is_active !== false && scheduleConfig.enabled !== false,
    reportId: str(raw.report || raw.report_id || raw.id),
  };
}

export default function ReportsPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [selectedReport, setSelectedReport] = useState<ReportUI | null>(null);
  const [reports, setReports] = useState<ReportUI[]>([]);
  const [reportTemplates, setReportTemplates] = useState<TemplateUI[]>([]);
  const [scheduledReports, setScheduledReports] = useState<ScheduledUI[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [actionId, setActionId] = useState<string | null>(null);

  const [newName, setNewName] = useState('');
  const [newTemplateId, setNewTemplateId] = useState('');
  const [newDateRange, setNewDateRange] = useState('30d');
  const [newFormat, setNewFormat] = useState('pdf');
  const [newSchedule, setNewSchedule] = useState(false);

  const load = useCallback(async () => {
    setIsLoading(true);
    try {
      const [reportsRes, templatesRes] = await Promise.all([
        apiClient.getReports(),
        apiClient.getReportTemplates().catch(() => ({ templates: [] })),
      ]);

      const reportRows = extractList<Record<string, unknown>>(reportsRes, ['reports', 'results']);
      const mappedReports = reportRows.map(mapReport);
      setReports(mappedReports);

      const templateRows = extractList<Record<string, unknown>>(templatesRes, ['templates', 'results']);
      setReportTemplates(templateRows.map(mapTemplate));

      const scheduled = reportRows
        .map((row) => mapScheduled(row, mappedReports.find((r) => r.id === str(row.id))))
        .filter((s): s is ScheduledUI => Boolean(s));
      setScheduledReports(scheduled);
    } catch (e: unknown) {
      toast({
        title: 'Failed to load reports',
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

  const filteredReports = useMemo(() => {
    return reports.filter((report) => {
      const q = searchQuery.toLowerCase();
      const matchesSearch =
        !q ||
        report.name.toLowerCase().includes(q) ||
        report.template.toLowerCase().includes(q);
      const matchesStatus = statusFilter === 'all' || report.status === statusFilter;
      return matchesSearch && matchesStatus;
    });
  }, [reports, searchQuery, statusFilter]);

  const generatedToday = useMemo(() => {
    const today = new Date().toDateString();
    return reports.filter((r) => {
      const d = new Date(r.generatedAt);
      return !Number.isNaN(d.getTime()) && d.toDateString() === today;
    }).length;
  }, [reports]);

  const stats = [
    { label: 'Total Reports', value: reports.length, icon: FileText, color: 'text-primary' },
    { label: 'Generated Today', value: generatedToday, icon: CheckCircle2, color: 'text-green-500' },
    { label: 'Scheduled', value: scheduledReports.length, icon: Calendar, color: 'text-blue-500' },
    { label: 'Templates', value: reportTemplates.length, icon: Copy, color: 'text-purple-500' },
  ];

  const getFormatIcon = (format: string) => {
    switch (format) {
      case 'pdf':
        return <File className="h-4 w-4 text-red-500" />;
      case 'xlsx':
      case 'excel':
        return <FileSpreadsheet className="h-4 w-4 text-green-500" />;
      default:
        return <FileText className="h-4 w-4" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge className="bg-green-500/10 text-green-500 border-green-500/20">Completed</Badge>;
      case 'generating':
        return <Badge className="bg-blue-500/10 text-blue-500 border-blue-500/20">Generating</Badge>;
      case 'failed':
        return <Badge className="bg-red-500/10 text-red-500 border-red-500/20">Failed</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const handleCreate = async () => {
    if (!newName.trim()) {
      toast({ title: 'Enter a report name', variant: 'destructive' });
      return;
    }
    setIsCreating(true);
    try {
      const template = reportTemplates.find((t) => t.id === newTemplateId);
      const reportType =
        template?.category === 'financial'
          ? 'financial'
          : template?.category === 'performance'
            ? 'agent_performance'
            : template?.category === 'analytics'
              ? 'usage_analytics'
              : newTemplateId === 'custom' || !newTemplateId
                ? 'custom'
                : 'custom';

      const created = await apiClient.createReport({
        name: newName.trim(),
        description: template?.description || '',
        report_type: reportType,
        config: {
          template_id: newTemplateId || null,
          format: newFormat,
          schedule: newSchedule ? 'daily' : null,
        },
        filters: {},
        date_range: { range: newDateRange },
        status: 'draft',
      });

      const createdId = str(asRecord(created).id);
      if (createdId) {
        await apiClient.generateLegacyReport(createdId, { format: newFormat }).catch(() => null);
        if (newSchedule) {
          await apiClient
            .scheduleReport(createdId, {
              frequency: 'daily',
              email_recipients: [],
              is_active: true,
            })
            .catch(() => null);
        }
      }

      setShowCreateDialog(false);
      setNewName('');
      setNewTemplateId('');
      setNewSchedule(false);
      await load();
      toast({ title: 'Report created' });
    } catch (e: unknown) {
      toast({
        title: 'Failed to create report',
        description: axiosErrorDetail(e) || errorMessage(e),
        variant: 'destructive',
      });
    } finally {
      setIsCreating(false);
    }
  };

  const handleDelete = async (id: string) => {
    setActionId(id);
    try {
      await apiClient.deleteReport(id);
      await load();
      toast({ title: 'Report deleted' });
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

  const handleGenerate = async (id: string) => {
    setActionId(id);
    try {
      await apiClient.generateLegacyReport(id);
      await load();
      toast({ title: 'Report generated' });
    } catch {
      try {
        await apiClient.generateReport(id);
        await load();
        toast({ title: 'Report generated' });
      } catch (e2: unknown) {
        toast({
          title: 'Generate failed',
          description: axiosErrorDetail(e2) || errorMessage(e2),
          variant: 'destructive',
        });
      }
    } finally {
      setActionId(null);
    }
  };

  const handleExport = async (id: string, format: string) => {
    setActionId(id);
    try {
      const fmt = format === 'xlsx' ? 'excel' : (format as 'pdf' | 'excel' | 'csv');
      const res = await apiClient.exportReport(id, fmt === 'excel' || fmt === 'pdf' || fmt === 'csv' ? fmt : 'pdf');
      if (res.download_url) {
        window.open(res.download_url, '_blank');
      } else {
        toast({ title: 'Export queued', description: 'Download will be available when storage is configured.' });
      }
    } catch (e: unknown) {
      toast({
        title: 'Export failed',
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
              <FileText className="h-8 w-8 text-primary" />
              Reports
            </h1>
            <p className="text-muted-foreground mt-1">
              Generate and manage analytics reports
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="icon" onClick={load} disabled={isLoading}>
              <RefreshCw className={cn('h-4 w-4', isLoading && 'animate-spin')} />
            </Button>
            <Button onClick={() => setShowCreateDialog(true)} className="gap-2">
              <Plus className="h-4 w-4" />
              Create Report
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

        <Tabs defaultValue="reports" className="space-y-6">
          <TabsList>
            <TabsTrigger value="reports">All Reports</TabsTrigger>
            <TabsTrigger value="templates">Templates</TabsTrigger>
            <TabsTrigger value="scheduled">Scheduled</TabsTrigger>
          </TabsList>

          <TabsContent value="reports" className="space-y-4">
            <div className="flex items-center gap-4">
              <div className="relative flex-1 max-w-md">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search reports..."
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
                  <SelectItem value="completed">Completed</SelectItem>
                  <SelectItem value="generating">Generating</SelectItem>
                  <SelectItem value="failed">Failed</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {isLoading ? (
              <div className="flex items-center justify-center py-16 text-muted-foreground gap-2">
                <RefreshCw className="h-5 w-5 animate-spin" />
                Loading reports…
              </div>
            ) : filteredReports.length === 0 ? (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-16 text-center">
                  <FileText className="h-12 w-12 text-muted-foreground mb-4" />
                  <h3 className="font-semibold">No reports yet</h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    Create your first report from a template
                  </p>
                  <Button onClick={() => setShowCreateDialog(true)} className="gap-2">
                    <Plus className="h-4 w-4" />
                    Create Report
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <div className="grid gap-4">
                {filteredReports.map((report, index) => (
                  <motion.div
                    key={report.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                  >
                    <Card
                      className={cn(
                        'hover:shadow-md transition-shadow',
                        report.status === 'failed' && 'border-red-500/30'
                      )}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-center gap-4">
                          <div
                            className={cn(
                              'flex h-12 w-12 items-center justify-center rounded-xl shrink-0',
                              report.status === 'completed' && 'bg-green-500/10',
                              report.status === 'generating' && 'bg-blue-500/10',
                              report.status === 'failed' && 'bg-red-500/10'
                            )}
                          >
                            {report.status === 'generating' || actionId === report.id ? (
                              <RefreshCw className="h-6 w-6 text-blue-500 animate-spin" />
                            ) : (
                              getFormatIcon(report.format)
                            )}
                          </div>

                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <h3 className="font-semibold truncate">{report.name}</h3>
                              {getStatusBadge(report.status)}
                            </div>
                            <div className="flex items-center gap-4 text-sm text-muted-foreground flex-wrap">
                              <span>Template: {report.template}</span>
                              <span>•</span>
                              <span>{report.generatedAt}</span>
                              {report.schedule && (
                                <>
                                  <span>•</span>
                                  <Badge variant="outline" className="text-xs gap-1">
                                    <Calendar className="h-3 w-3" />
                                    {report.schedule}
                                  </Badge>
                                </>
                              )}
                            </div>
                            {report.error && (
                              <p className="text-sm text-red-500 mt-1">{report.error}</p>
                            )}
                          </div>

                          <div className="hidden sm:flex flex-col items-end gap-1 text-sm text-muted-foreground">
                            <span>By {report.generatedBy}</span>
                            {report.size !== '-' && <span>{report.size}</span>}
                          </div>

                          <div className="flex items-center gap-2">
                            {report.status === 'completed' && (
                              <Button
                                variant="outline"
                                size="icon"
                                onClick={() => handleExport(report.id, report.format)}
                              >
                                <Download className="h-4 w-4" />
                              </Button>
                            )}
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="icon">
                                  <MoreVertical className="h-4 w-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuItem onClick={() => setSelectedReport(report)}>
                                  <Eye className="h-4 w-4 mr-2" />
                                  View Details
                                </DropdownMenuItem>
                                <DropdownMenuItem>
                                  <Share2 className="h-4 w-4 mr-2" />
                                  Share
                                </DropdownMenuItem>
                                <DropdownMenuItem>
                                  <Printer className="h-4 w-4 mr-2" />
                                  Print
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => handleGenerate(report.id)}>
                                  <RefreshCw className="h-4 w-4 mr-2" />
                                  Regenerate
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem
                                  className="text-destructive"
                                  onClick={() => handleDelete(report.id)}
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
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="templates" className="space-y-6">
            {isLoading ? (
              <div className="flex items-center justify-center py-16 text-muted-foreground gap-2">
                <RefreshCw className="h-5 w-5 animate-spin" />
                Loading templates…
              </div>
            ) : reportTemplates.length === 0 ? (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-16 text-center">
                  <Copy className="h-12 w-12 text-muted-foreground mb-4" />
                  <h3 className="font-semibold">No templates available</h3>
                  <p className="text-sm text-muted-foreground">
                    Report templates will appear here when published
                  </p>
                </CardContent>
              </Card>
            ) : (
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {reportTemplates.map((template, index) => (
                  <motion.div
                    key={template.id}
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: index * 0.05 }}
                  >
                    <Card
                      className="hover:shadow-lg transition-all hover:border-primary/50 cursor-pointer group"
                      onClick={() => {
                        setNewTemplateId(template.id);
                        setNewName(template.name);
                        setShowCreateDialog(true);
                      }}
                    >
                      <CardContent className="p-6">
                        <div className="flex items-start justify-between mb-4">
                          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 transition-transform group-hover:scale-110">
                            <template.icon className="h-6 w-6 text-primary" />
                          </div>
                          {template.popular && (
                            <Badge variant="secondary" className="gap-1">
                              <Star className="h-3 w-3 fill-yellow-500 text-yellow-500" />
                              Popular
                            </Badge>
                          )}
                        </div>
                        <h3 className="font-semibold mb-1">{template.name}</h3>
                        <p className="text-sm text-muted-foreground mb-4">{template.description}</p>
                        <Badge variant="outline" className="capitalize">
                          {template.category}
                        </Badge>
                      </CardContent>
                    </Card>
                  </motion.div>
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="scheduled" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Scheduled Reports</CardTitle>
                <CardDescription>Automatically generated reports on a schedule</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {isLoading ? (
                  <div className="flex items-center justify-center py-12 text-muted-foreground gap-2">
                    <RefreshCw className="h-5 w-5 animate-spin" />
                    Loading schedules…
                  </div>
                ) : scheduledReports.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-12 text-center">
                    <Calendar className="h-12 w-12 text-muted-foreground mb-4" />
                    <h3 className="font-semibold">No scheduled reports</h3>
                    <p className="text-sm text-muted-foreground">
                      Enable scheduling when creating a report
                    </p>
                  </div>
                ) : (
                  scheduledReports.map((schedule) => (
                    <div key={schedule.id} className="flex items-center gap-4 p-4 rounded-xl bg-muted/50">
                      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                        <Calendar className="h-5 w-5 text-primary" />
                      </div>
                      <div className="flex-1">
                        <p className="font-medium">{schedule.name}</p>
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <Clock className="h-3 w-3" />
                          {schedule.schedule}
                          <span>•</span>
                          <Mail className="h-3 w-3" />
                          {schedule.recipients.length} recipients
                        </div>
                      </div>
                      <Switch checked={schedule.enabled} disabled />
                      <Button variant="ghost" size="icon">
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="text-destructive"
                        onClick={() => handleDelete(schedule.reportId)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogContent className="max-w-xl">
            <DialogHeader>
              <DialogTitle>Create New Report</DialogTitle>
              <DialogDescription>
                Generate a new report from a template or create a custom one
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">Report Name</Label>
                <Input
                  id="name"
                  placeholder="My Custom Report"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label>Template</Label>
                <Select value={newTemplateId || undefined} onValueChange={setNewTemplateId}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a template" />
                  </SelectTrigger>
                  <SelectContent>
                    {reportTemplates.map((template) => (
                      <SelectItem key={template.id} value={template.id}>
                        {template.name}
                      </SelectItem>
                    ))}
                    <SelectItem value="custom">Custom Report</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Date Range</Label>
                  <Select value={newDateRange} onValueChange={setNewDateRange}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select range" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="today">Today</SelectItem>
                      <SelectItem value="7d">Last 7 Days</SelectItem>
                      <SelectItem value="30d">Last 30 Days</SelectItem>
                      <SelectItem value="90d">Last 90 Days</SelectItem>
                      <SelectItem value="custom">Custom Range</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Format</Label>
                  <Select value={newFormat} onValueChange={setNewFormat}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select format" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="pdf">PDF</SelectItem>
                      <SelectItem value="xlsx">Excel (XLSX)</SelectItem>
                      <SelectItem value="csv">CSV</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Schedule this report</p>
                  <p className="text-sm text-muted-foreground">Automatically generate on a schedule</p>
                </div>
                <Switch checked={newSchedule} onCheckedChange={setNewSchedule} />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                Cancel
              </Button>
              <Button className="gap-2" onClick={handleCreate} disabled={isCreating}>
                {isCreating ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  <Sparkles className="h-4 w-4" />
                )}
                Generate Report
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        <Dialog open={!!selectedReport} onOpenChange={() => setSelectedReport(null)}>
          <DialogContent className="max-w-lg">
            {selectedReport && (
              <>
                <DialogHeader>
                  <DialogTitle className="flex items-center gap-2">
                    {selectedReport.name}
                    {getStatusBadge(selectedReport.status)}
                  </DialogTitle>
                  <DialogDescription>
                    {selectedReport.template} • {selectedReport.generatedAt}
                  </DialogDescription>
                </DialogHeader>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-muted-foreground">Format</p>
                    <p className="font-medium uppercase">{selectedReport.format}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Generated by</p>
                    <p className="font-medium">{selectedReport.generatedBy}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Type</p>
                    <p className="font-medium">{selectedReport.reportType}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Schedule</p>
                    <p className="font-medium">{selectedReport.schedule || 'None'}</p>
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setSelectedReport(null)}>
                    Close
                  </Button>
                  <Button onClick={() => handleGenerate(selectedReport.id)}>
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Regenerate
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
