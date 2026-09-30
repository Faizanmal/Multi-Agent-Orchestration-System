"use client";

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { formatDistanceToNow } from 'date-fns';
import {
  Webhook,
  Plus,
  Search,
  MoreVertical,
  Copy,
  Trash2,
  Settings,
  Play,
  Pause,
  CheckCircle2,
  XCircle,
  Clock,
  Activity,
  RefreshCw,
  Zap,
  Globe,
  Eye,
  EyeOff,
  RotateCcw,
  Send,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import { AppLayout } from '@/components/layout/AppLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { cn } from '@/lib/utils';
import apiClient from '@/lib/api';
import { toast } from 'sonner';

interface UiWebhook {
  id: string;
  name: string;
  url: string;
  events: string[];
  status: 'active' | 'paused';
  lastTriggered: string;
  successRate: number;
  totalDeliveries: number;
  isActive: boolean;
}

interface UiDeliveryLog {
  id: string;
  webhook: string;
  event: string;
  status: 'success' | 'failed' | 'pending';
  statusCode: number | null;
  timestamp: string;
  duration: string;
}

const availableEvents = [
  {
    category: 'Session',
    events: ['session.created', 'session.completed', 'session.failed'],
  },
  {
    category: 'Task',
    events: ['task.created', 'task.completed', 'task.failed'],
  },
  {
    category: 'Agent',
    events: ['agent.response'],
  },
  {
    category: 'Workflow',
    events: ['workflow.started', 'workflow.completed'],
  },
  {
    category: 'System',
    events: ['error.occurred'],
  },
];

function formatRelativeTime(value?: string | null): string {
  if (!value) return 'Never';
  try {
    return formatDistanceToNow(new Date(value), { addSuffix: true });
  } catch {
    return value;
  }
}

function formatTimestamp(value?: string | null): string {
  if (!value) return '—';
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
}

function toPercent(rate: unknown, successful?: unknown, total?: unknown): number {
  if (typeof rate === 'number') {
    return rate <= 1 ? Math.round(rate * 1000) / 10 : Math.round(rate * 10) / 10;
  }
  const ok = Number(successful ?? 0);
  const all = Number(total ?? 0);
  if (!all) return 0;
  return Math.round((ok / all) * 1000) / 10;
}

function extractList(payload: unknown): Record<string, unknown>[] {
  if (Array.isArray(payload)) return payload as Record<string, unknown>[];
  if (payload && typeof payload === 'object') {
    const obj = payload as Record<string, unknown>;
    if (Array.isArray(obj.results)) return obj.results as Record<string, unknown>[];
    if (Array.isArray(obj.webhooks)) return obj.webhooks as Record<string, unknown>[];
    if (Array.isArray(obj.deliveries)) return obj.deliveries as Record<string, unknown>[];
  }
  return [];
}

function mapWebhook(raw: Record<string, unknown>): UiWebhook {
  const isActive = Boolean(raw.is_active ?? raw.status === 'active');
  const eventsRaw = raw.subscribed_events ?? raw.events ?? raw.event_type;
  const events = Array.isArray(eventsRaw)
    ? eventsRaw.map(String)
    : eventsRaw
      ? [String(eventsRaw)]
      : [];

  return {
    id: String(raw.id ?? ''),
    name: String(raw.name ?? 'Webhook'),
    url: String(raw.url ?? ''),
    events,
    status: isActive ? 'active' : 'paused',
    lastTriggered: formatRelativeTime(
      (raw.last_triggered as string) ?? (raw.updated_at as string) ?? null
    ),
    successRate: toPercent(raw.success_rate, raw.successful_deliveries, raw.total_deliveries),
    totalDeliveries: Number(raw.total_deliveries ?? 0),
    isActive,
  };
}

function mapDelivery(
  raw: Record<string, unknown>,
  webhookNameFallback?: string
): UiDeliveryLog {
  const success = raw.success;
  const statusField = String(raw.status ?? '');
  let status: UiDeliveryLog['status'] = 'pending';
  if (typeof success === 'boolean') {
    status = success ? 'success' : 'failed';
  } else if (statusField === 'success' || statusField === 'failed' || statusField === 'pending') {
    status = statusField;
  } else if (raw.status_code != null || raw.response_status != null) {
    const code = Number(raw.status_code ?? raw.response_status);
    status = code >= 200 && code < 300 ? 'success' : 'failed';
  }

  const durationMs = Number(raw.duration_ms ?? 0);
  const webhookObj = raw.webhook;
  const webhookName =
    String(
      raw.webhook_name ??
        (webhookObj && typeof webhookObj === 'object'
          ? (webhookObj as Record<string, unknown>).name
          : '') ??
        webhookNameFallback ??
        'Webhook'
    ) || 'Webhook';

  return {
    id: String(raw.id ?? crypto.randomUUID()),
    webhook: webhookName,
    event: String(raw.event_type ?? raw.event ?? '—'),
    status,
    statusCode:
      raw.status_code != null
        ? Number(raw.status_code)
        : raw.response_status != null
          ? Number(raw.response_status)
          : null,
    timestamp: formatTimestamp(
      (raw.delivered_at as string) ?? (raw.created_at as string) ?? null
    ),
    duration: durationMs > 0 ? `${durationMs}ms` : '—',
  };
}

export default function WebhooksPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [deliverySearch, setDeliverySearch] = useState('');
  const [deliveryStatusFilter, setDeliveryStatusFilter] = useState('all');
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [selectedWebhook, setSelectedWebhook] = useState<UiWebhook | null>(null);
  const [showSecret, setShowSecret] = useState(false);
  const [webhooks, setWebhooks] = useState<UiWebhook[]>([]);
  const [deliveryLogs, setDeliveryLogs] = useState<UiDeliveryLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [deliveriesLoading, setDeliveriesLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [activeWebhookId, setActiveWebhookId] = useState<string | null>(null);

  const [createForm, setCreateForm] = useState({
    name: '',
    url: '',
    event: 'task.completed',
    secret: '',
  });

  const loadDeliveries = useCallback(async (webhookId: string, webhookName?: string) => {
    try {
      setDeliveriesLoading(true);
      const res = await apiClient.getWebhookDeliveries(webhookId);
      const list = extractList(res.data).map((item) => mapDelivery(item, webhookName));
      setDeliveryLogs(list);
      setActiveWebhookId(webhookId);
    } catch (err) {
      console.error('Failed to load deliveries:', err);
      setDeliveryLogs([]);
      toast.error('Failed to load delivery logs');
    } finally {
      setDeliveriesLoading(false);
    }
  }, []);

  const loadWebhooks = useCallback(async (preferredId?: string | null) => {
    try {
      setLoading(true);
      setError(null);
      const res = await apiClient.getWebhooks();
      const mapped = extractList(res.data).map(mapWebhook).filter((w) => w.id);
      setWebhooks(mapped);

      if (mapped.length > 0) {
        const preferred =
          mapped.find((w) => w.id === preferredId) ?? mapped[0];
        await loadDeliveries(preferred.id, preferred.name);
      } else {
        setDeliveryLogs([]);
        setActiveWebhookId(null);
      }
    } catch (err) {
      console.error('Failed to load webhooks:', err);
      setError('Failed to load webhooks');
      toast.error('Failed to load webhooks');
    } finally {
      setLoading(false);
    }
  }, [loadDeliveries]);

  useEffect(() => {
    setTimeout(() => { loadWebhooks(); }, 0)
  }, [loadWebhooks]);

  const filteredWebhooks = useMemo(() => {
    if (!searchQuery.trim()) return webhooks;
    const q = searchQuery.toLowerCase();
    return webhooks.filter(
      (w) =>
        w.name.toLowerCase().includes(q) ||
        w.url.toLowerCase().includes(q) ||
        w.events.some((e) => e.toLowerCase().includes(q))
    );
  }, [webhooks, searchQuery]);

  const filteredDeliveries = useMemo(() => {
    return deliveryLogs.filter((log) => {
      if (deliveryStatusFilter !== 'all' && log.status !== deliveryStatusFilter) return false;
      if (!deliverySearch.trim()) return true;
      const q = deliverySearch.toLowerCase();
      return (
        log.webhook.toLowerCase().includes(q) ||
        log.event.toLowerCase().includes(q) ||
        String(log.statusCode ?? '').includes(q)
      );
    });
  }, [deliveryLogs, deliverySearch, deliveryStatusFilter]);

  const totalDeliveries = webhooks.reduce((sum, w) => sum + w.totalDeliveries, 0);
  const avgSuccessRate =
    webhooks.length === 0
      ? 0
      : Math.round(
          (webhooks.reduce((sum, w) => sum + w.successRate, 0) / webhooks.length) * 10
        ) / 10;

  const stats = [
    { label: 'Total Webhooks', value: webhooks.length, icon: Webhook, color: 'text-primary' },
    {
      label: 'Active',
      value: webhooks.filter((w) => w.status === 'active').length,
      icon: CheckCircle2,
      color: 'text-green-500',
    },
    {
      label: 'Total Deliveries',
      value: totalDeliveries >= 1000 ? `${(totalDeliveries / 1000).toFixed(1)}K` : String(totalDeliveries),
      icon: Send,
      color: 'text-blue-500',
    },
    {
      label: 'Success Rate',
      value: `${avgSuccessRate}%`,
      icon: Activity,
      color: 'text-purple-500',
    },
  ];

  const handleCreateWebhook = async () => {
    if (!createForm.name.trim() || !createForm.url.trim()) {
      toast.error('Name and URL are required');
      return;
    }

    try {
      setCreating(true);
      await apiClient.createWebhook({
        name: createForm.name.trim(),
        url: createForm.url.trim(),
        subscribed_events: [createForm.event],
        secret_key:
          createForm.secret.trim() ||
          `whsec_${Math.random().toString(36).slice(2)}${Date.now().toString(36)}`,
      });
      toast.success('Webhook created successfully');
      setShowCreateDialog(false);
      setCreateForm({ name: '', url: '', event: 'task.completed', secret: '' });
      await loadWebhooks(activeWebhookId);
    } catch (err) {
      console.error('Failed to create webhook:', err);
      toast.error('Failed to create webhook');
    } finally {
      setCreating(false);
    }
  };

  const handleTestWebhook = async (id: string) => {
    try {
      await apiClient.testWebhook(id);
      toast.success('Test webhook sent');
      const webhook = webhooks.find((w) => w.id === id);
      await loadDeliveries(id, webhook?.name);
    } catch (err) {
      console.error('Failed to test webhook:', err);
      toast.error('Failed to send test webhook');
    }
  };

  const handleDeleteWebhook = async (id: string) => {
    try {
      await apiClient.deleteWebhook(id);
      toast.success('Webhook deleted');
      if (selectedWebhook?.id === id) setSelectedWebhook(null);
      const nextPreferred = activeWebhookId === id ? null : activeWebhookId;
      await loadWebhooks(nextPreferred);
    } catch (err) {
      console.error('Failed to delete webhook:', err);
      toast.error('Failed to delete webhook');
    }
  };

  const copyUrl = async (url: string) => {
    try {
      await navigator.clipboard.writeText(url);
      toast.success('URL copied');
    } catch {
      toast.error('Failed to copy URL');
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
              <Webhook className="h-8 w-8 text-primary" />
              Webhooks
            </h1>
            <p className="text-muted-foreground mt-1">
              Manage webhook endpoints and event subscriptions
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="icon" onClick={() => loadWebhooks()} disabled={loading}>
              <RefreshCw className={cn('h-4 w-4', loading && 'animate-spin')} />
            </Button>
            <Button onClick={() => setShowCreateDialog(true)} className="gap-2">
              <Plus className="h-4 w-4" />
              Create Webhook
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
                      <p className="text-2xl font-bold">{stat.value}</p>
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

        <Tabs defaultValue="endpoints" className="space-y-6">
          <TabsList>
            <TabsTrigger value="endpoints">Endpoints</TabsTrigger>
            <TabsTrigger value="deliveries">Delivery Logs</TabsTrigger>
            <TabsTrigger value="events">Event Types</TabsTrigger>
          </TabsList>

          <TabsContent value="endpoints" className="space-y-4">
            <div className="flex items-center gap-4">
              <div className="relative flex-1 max-w-md">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search webhooks..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>

            {loading ? (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-12 text-center">
                  <Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
                  <p className="text-sm text-muted-foreground">Loading webhooks...</p>
                </CardContent>
              </Card>
            ) : error ? (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-12 text-center">
                  <AlertCircle className="h-12 w-12 text-destructive mb-4" />
                  <h3 className="font-semibold">{error}</h3>
                  <Button variant="outline" className="mt-4" onClick={() => loadWebhooks()}>
                    Try again
                  </Button>
                </CardContent>
              </Card>
            ) : filteredWebhooks.length === 0 ? (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-12 text-center">
                  <Webhook className="h-12 w-12 text-muted-foreground mb-4" />
                  <h3 className="font-semibold">No webhooks</h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    Create your first webhook endpoint to get started
                  </p>
                  <Button onClick={() => setShowCreateDialog(true)} className="gap-2">
                    <Plus className="h-4 w-4" />
                    Create Webhook
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <div className="grid gap-4">
                {filteredWebhooks.map((webhook, index) => (
                  <motion.div
                    key={webhook.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                  >
                    <Card
                      className={cn(
                        'hover:shadow-md transition-shadow cursor-pointer',
                        activeWebhookId === webhook.id && 'ring-1 ring-primary/40'
                      )}
                      onClick={() => loadDeliveries(webhook.id, webhook.name)}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-start gap-4">
                          <div
                            className={cn(
                              'flex h-12 w-12 items-center justify-center rounded-xl shrink-0',
                              webhook.status === 'active' ? 'bg-green-500/10' : 'bg-muted'
                            )}
                          >
                            <Webhook
                              className={cn(
                                'h-6 w-6',
                                webhook.status === 'active'
                                  ? 'text-green-500'
                                  : 'text-muted-foreground'
                              )}
                            />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <h3 className="font-semibold">{webhook.name}</h3>
                              <Badge
                                variant={webhook.status === 'active' ? 'default' : 'secondary'}
                              >
                                {webhook.status}
                              </Badge>
                            </div>
                            <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
                              <Globe className="h-3 w-3" />
                              <code className="text-xs bg-muted px-2 py-0.5 rounded truncate max-w-md">
                                {webhook.url}
                              </code>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-6 w-6"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  copyUrl(webhook.url);
                                }}
                              >
                                <Copy className="h-3 w-3" />
                              </Button>
                            </div>
                            <div className="flex flex-wrap gap-1">
                              {webhook.events.map((event) => (
                                <Badge key={event} variant="outline" className="text-xs">
                                  {event}
                                </Badge>
                              ))}
                            </div>
                          </div>
                          <div className="hidden sm:flex flex-col items-end gap-1 text-sm">
                            <div className="flex items-center gap-2 text-muted-foreground">
                              <Clock className="h-3 w-3" />
                              Last triggered: {webhook.lastTriggered}
                            </div>
                            <div className="flex items-center gap-4">
                              <span className="text-muted-foreground">
                                {webhook.totalDeliveries} deliveries
                              </span>
                              <span
                                className={cn(
                                  'font-medium',
                                  webhook.successRate >= 98
                                    ? 'text-green-500'
                                    : 'text-yellow-500'
                                )}
                              >
                                {webhook.successRate}% success
                              </span>
                            </div>
                          </div>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={(e) => e.stopPropagation()}
                              >
                                <MoreVertical className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setSelectedWebhook(webhook);
                                }}
                              >
                                <Settings className="h-4 w-4 mr-2" />
                                Configure
                              </DropdownMenuItem>
                              <DropdownMenuItem
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleTestWebhook(webhook.id);
                                }}
                              >
                                <Send className="h-4 w-4 mr-2" />
                                Send Test
                              </DropdownMenuItem>
                              <DropdownMenuItem disabled>
                                {webhook.status === 'active' ? (
                                  <>
                                    <Pause className="h-4 w-4 mr-2" />
                                    Pause
                                  </>
                                ) : (
                                  <>
                                    <Play className="h-4 w-4 mr-2" />
                                    Resume
                                  </>
                                )}
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem
                                className="text-destructive"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleDeleteWebhook(webhook.id);
                                }}
                              >
                                <Trash2 className="h-4 w-4 mr-2" />
                                Delete
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="deliveries" className="space-y-4">
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4">
              <div className="relative flex-1 max-w-md">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search logs..."
                  className="pl-10"
                  value={deliverySearch}
                  onChange={(e) => setDeliverySearch(e.target.value)}
                />
              </div>
              {webhooks.length > 0 && (
                <Select
                  value={activeWebhookId ?? webhooks[0]?.id}
                  onValueChange={(id) => {
                    const webhook = webhooks.find((w) => w.id === id);
                    loadDeliveries(id, webhook?.name);
                  }}
                >
                  <SelectTrigger className="w-56">
                    <SelectValue placeholder="Select webhook" />
                  </SelectTrigger>
                  <SelectContent>
                    {webhooks.map((w) => (
                      <SelectItem key={w.id} value={w.id}>
                        {w.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
              <Select value={deliveryStatusFilter} onValueChange={setDeliveryStatusFilter}>
                <SelectTrigger className="w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="success">Success</SelectItem>
                  <SelectItem value="failed">Failed</SelectItem>
                </SelectContent>
              </Select>
              <Button
                variant="outline"
                className="gap-2"
                onClick={() => {
                  if (activeWebhookId) {
                    const webhook = webhooks.find((w) => w.id === activeWebhookId);
                    loadDeliveries(activeWebhookId, webhook?.name);
                  } else {
                    loadWebhooks();
                  }
                }}
                disabled={deliveriesLoading}
              >
                <RefreshCw className={cn('h-4 w-4', deliveriesLoading && 'animate-spin')} />
                Refresh
              </Button>
            </div>

            <Card>
              {deliveriesLoading ? (
                <CardContent className="flex flex-col items-center justify-center py-12 text-center">
                  <Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
                  <p className="text-sm text-muted-foreground">Loading delivery logs...</p>
                </CardContent>
              ) : filteredDeliveries.length === 0 ? (
                <CardContent className="flex flex-col items-center justify-center py-12 text-center">
                  <Send className="h-12 w-12 text-muted-foreground mb-4" />
                  <h3 className="font-semibold">No delivery logs</h3>
                  <p className="text-sm text-muted-foreground">
                    {webhooks.length === 0
                      ? 'Create a webhook to see delivery history'
                      : 'Deliveries will appear here once webhooks are triggered'}
                  </p>
                </CardContent>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Status</TableHead>
                      <TableHead>Webhook</TableHead>
                      <TableHead>Event</TableHead>
                      <TableHead>Response</TableHead>
                      <TableHead>Duration</TableHead>
                      <TableHead>Timestamp</TableHead>
                      <TableHead></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredDeliveries.map((log) => (
                      <TableRow key={log.id}>
                        <TableCell>
                          {log.status === 'success' ? (
                            <CheckCircle2 className="h-4 w-4 text-green-500" />
                          ) : log.status === 'pending' ? (
                            <Clock className="h-4 w-4 text-yellow-500" />
                          ) : (
                            <XCircle className="h-4 w-4 text-red-500" />
                          )}
                        </TableCell>
                        <TableCell className="font-medium">{log.webhook}</TableCell>
                        <TableCell>
                          <Badge variant="outline" className="text-xs">
                            {log.event}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {log.statusCode != null ? (
                            <Badge
                              variant={
                                log.statusCode >= 200 && log.statusCode < 300
                                  ? 'default'
                                  : 'destructive'
                              }
                            >
                              {log.statusCode}
                            </Badge>
                          ) : (
                            <span className="text-muted-foreground text-sm">—</span>
                          )}
                        </TableCell>
                        <TableCell className="text-muted-foreground">{log.duration}</TableCell>
                        <TableCell className="text-muted-foreground">{log.timestamp}</TableCell>
                        <TableCell>
                          <Button variant="ghost" size="icon" className="h-8 w-8">
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="icon" className="h-8 w-8">
                            <RotateCcw className="h-4 w-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </Card>
          </TabsContent>

          <TabsContent value="events" className="space-y-6">
            {availableEvents.map((category) => (
              <Card key={category.category}>
                <CardHeader>
                  <CardTitle className="text-lg">{category.category} Events</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {category.events.map((event) => (
                      <Badge key={event} variant="secondary" className="py-1.5 px-3">
                        <Zap className="h-3 w-3 mr-2" />
                        {event}
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </TabsContent>
        </Tabs>

        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogContent className="max-w-xl">
            <DialogHeader>
              <DialogTitle>Create Webhook</DialogTitle>
              <DialogDescription>
                Configure a new webhook endpoint to receive event notifications
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">Name</Label>
                <Input
                  id="name"
                  placeholder="My Webhook"
                  value={createForm.name}
                  onChange={(e) => setCreateForm((f) => ({ ...f, name: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="url">Endpoint URL</Label>
                <Input
                  id="url"
                  placeholder="https://api.example.com/webhooks"
                  value={createForm.url}
                  onChange={(e) => setCreateForm((f) => ({ ...f, url: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label>Events</Label>
                <Select
                  value={createForm.event}
                  onValueChange={(event) => setCreateForm((f) => ({ ...f, event }))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select events" />
                  </SelectTrigger>
                  <SelectContent>
                    {availableEvents.flatMap((cat) => cat.events).map((event) => (
                      <SelectItem key={event} value={event}>
                        {event}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="secret">Secret (optional)</Label>
                <div className="relative">
                  <Input
                    id="secret"
                    type={showSecret ? 'text' : 'password'}
                    placeholder="whsec_..."
                    value={createForm.secret}
                    onChange={(e) => setCreateForm((f) => ({ ...f, secret: e.target.value }))}
                  />
                  <Button
                    variant="ghost"
                    size="icon"
                    className="absolute right-2 top-1/2 -translate-y-1/2 h-6 w-6"
                    onClick={() => setShowSecret(!showSecret)}
                  >
                    {showSecret ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </Button>
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                Cancel
              </Button>
              <Button onClick={handleCreateWebhook} disabled={creating}>
                {creating ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                Create Webhook
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        <Dialog open={!!selectedWebhook} onOpenChange={() => setSelectedWebhook(null)}>
          <DialogContent className="max-w-xl">
            {selectedWebhook && (
              <>
                <DialogHeader>
                  <DialogTitle>Configure Webhook</DialogTitle>
                  <DialogDescription>
                    Update settings for {selectedWebhook.name}
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label>Name</Label>
                    <Input defaultValue={selectedWebhook.name} />
                  </div>
                  <div className="space-y-2">
                    <Label>Endpoint URL</Label>
                    <Input defaultValue={selectedWebhook.url} />
                  </div>
                  <div className="space-y-2">
                    <Label>Subscribed Events</Label>
                    <div className="flex flex-wrap gap-2">
                      {selectedWebhook.events.map((event) => (
                        <Badge key={event} variant="secondary" className="gap-1">
                          {event}
                          <XCircle className="h-3 w-3 cursor-pointer" />
                        </Badge>
                      ))}
                      <Button variant="ghost" size="sm">
                        <Plus className="h-4 w-4 mr-1" />
                        Add
                      </Button>
                    </div>
                  </div>
                  <Separator />
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Enable Webhook</p>
                      <p className="text-sm text-muted-foreground">Receive event notifications</p>
                    </div>
                    <Switch defaultChecked={selectedWebhook.status === 'active'} />
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setSelectedWebhook(null)}>
                    Cancel
                  </Button>
                  <Button onClick={() => setSelectedWebhook(null)}>
                    Save Changes
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
