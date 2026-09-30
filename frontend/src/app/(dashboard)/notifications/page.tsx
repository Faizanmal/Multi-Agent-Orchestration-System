"use client";

import React, { useCallback, useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { formatDistanceToNow } from 'date-fns';
import {
  Bell,
  Check,
  CheckCheck,
  Trash2,
  Settings,
  Search,
  MoreVertical,
  AlertCircle,
  CheckCircle2,
  Info,
  AlertTriangle,
  Bot,
  GitBranch,
  Shield,
  CreditCard,
  Archive,
  Star,
  StarOff,
  Volume2,
  ExternalLink,
  Loader2,
  RefreshCw,
} from 'lucide-react';
import { AppLayout } from '@/components/layout/AppLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { cn } from '@/lib/utils';
import apiClient from '@/lib/api';
import { toast } from 'sonner';

const notificationTypes = {
  success: { icon: CheckCircle2, color: 'text-green-500', bg: 'bg-green-500/10', borderColor: 'border-green-500/20' },
  error: { icon: AlertCircle, color: 'text-red-500', bg: 'bg-red-500/10', borderColor: 'border-red-500/20' },
  warning: { icon: AlertTriangle, color: 'text-yellow-500', bg: 'bg-yellow-500/10', borderColor: 'border-yellow-500/20' },
  info: { icon: Info, color: 'text-blue-500', bg: 'bg-blue-500/10', borderColor: 'border-blue-500/20' },
  agent: { icon: Bot, color: 'text-purple-500', bg: 'bg-purple-500/10', borderColor: 'border-purple-500/20' },
  workflow: { icon: GitBranch, color: 'text-indigo-500', bg: 'bg-indigo-500/10', borderColor: 'border-indigo-500/20' },
  security: { icon: Shield, color: 'text-orange-500', bg: 'bg-orange-500/10', borderColor: 'border-orange-500/20' },
  billing: { icon: CreditCard, color: 'text-cyan-500', bg: 'bg-cyan-500/10', borderColor: 'border-cyan-500/20' },
};

type NotificationTypeKey = keyof typeof notificationTypes;

interface UiNotification {
  id: string;
  type: NotificationTypeKey | string;
  title: string;
  description: string;
  timestamp: string;
  createdAt: string;
  read: boolean;
  starred: boolean;
  source: 'webhook' | 'agent';
  action?: { label: string; href: string };
}

const notificationPreferences = [
  { category: 'Agents', items: ['Agent completed', 'Agent failed', 'Agent started'] },
  { category: 'Workflows', items: ['Workflow completed', 'Workflow failed', 'Workflow scheduled'] },
  { category: 'System', items: ['Errors', 'Warnings', 'Security alerts'] },
  { category: 'Billing', items: ['Payment received', 'Invoice due', 'Usage alerts'] },
];

function formatRelativeTime(value?: string | null): string {
  if (!value) return '';
  try {
    return formatDistanceToNow(new Date(value), { addSuffix: true });
  } catch {
    return value;
  }
}

function mapNotificationType(raw: unknown): string {
  const value = String(raw || 'info').toLowerCase();
  if (value in notificationTypes) return value;
  if (value.startsWith('agent') || value.includes('agent')) return 'agent';
  if (value.startsWith('workflow') || value.includes('workflow')) return 'workflow';
  if (value.includes('error') || value.includes('failed')) return 'error';
  if (value.includes('warn')) return 'warning';
  if (value.includes('security') || value.includes('login')) return 'security';
  if (value.includes('billing') || value.includes('payment') || value.includes('invoice')) return 'billing';
  if (value.includes('success') || value.includes('completed')) return 'success';
  return 'info';
}

function mapRawNotification(raw: Record<string, unknown>, source: 'webhook' | 'agent'): UiNotification {
  const id = String(raw.id ?? '');
  const createdAt = String(raw.created_at ?? raw.timestamp ?? '');
  const read = Boolean(raw.is_read ?? raw.read ?? false);
  const type = mapNotificationType(
    raw.type ?? raw.notification_type ?? raw.event_type ?? 'info'
  );
  const title = String(raw.title ?? 'Notification');
  const description = String(raw.message ?? raw.description ?? '');

  return {
    id,
    type,
    title,
    description,
    timestamp: formatRelativeTime(createdAt),
    createdAt,
    read,
    starred: false,
    source,
  };
}

function extractList(payload: unknown): Record<string, unknown>[] {
  if (Array.isArray(payload)) return payload as Record<string, unknown>[];
  if (payload && typeof payload === 'object') {
    const obj = payload as Record<string, unknown>;
    if (Array.isArray(obj.notifications)) return obj.notifications as Record<string, unknown>[];
    if (Array.isArray(obj.results)) return obj.results as Record<string, unknown>[];
  }
  return [];
}

export default function NotificationsPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [notificationList, setNotificationList] = useState<UiNotification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);

  const loadNotifications = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const [webhookRes, agentRes] = await Promise.allSettled([
        apiClient.getNotifications(),
        apiClient.getAgentNotifications(),
      ]);

      const merged = new Map<string, UiNotification>();

      if (webhookRes.status === 'fulfilled') {
        for (const item of extractList(webhookRes.value.notifications ?? webhookRes.value)) {
          const mapped = mapRawNotification(item, 'webhook');
          if (mapped.id) merged.set(mapped.id, mapped);
        }
      }

      if (agentRes.status === 'fulfilled') {
        for (const item of extractList(agentRes.value.notifications ?? agentRes.value)) {
          const mapped = mapRawNotification(item, 'agent');
          if (mapped.id && !merged.has(mapped.id)) {
            merged.set(mapped.id, mapped);
          }
        }
      }

      if (webhookRes.status === 'rejected' && agentRes.status === 'rejected') {
        throw webhookRes.reason ?? agentRes.reason ?? new Error('Failed to load notifications');
      }

      const sorted = Array.from(merged.values()).sort((a, b) => {
        const aTime = a.createdAt ? new Date(a.createdAt).getTime() : 0;
        const bTime = b.createdAt ? new Date(b.createdAt).getTime() : 0;
        return bTime - aTime;
      });

      setNotificationList((prev) => {
        const starredIds = new Set(prev.filter((n) => n.starred).map((n) => n.id));
        return sorted.map((n) => ({
          ...n,
          starred: starredIds.has(n.id),
        }));
      });
    } catch (err) {
      console.error('Failed to load notifications:', err);
      setError('Failed to load notifications');
      toast.error('Failed to load notifications');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    setTimeout(() => { loadNotifications(); }, 0)
  }, [loadNotifications]);

  const unreadCount = notificationList.filter((n) => !n.read).length;
  const starredCount = notificationList.filter((n) => n.starred).length;

  const matchesSearch = (notification: UiNotification) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      notification.title.toLowerCase().includes(q) ||
      notification.description.toLowerCase().includes(q)
    );
  };

  const filteredNotifications = notificationList.filter(matchesSearch);

  const markAsRead = async (id: string) => {
    const target = notificationList.find((n) => n.id === id);
    if (!target || target.read) return;

    setNotificationList((list) =>
      list.map((n) => (n.id === id ? { ...n, read: true } : n))
    );

    try {
      if (target.source === 'agent') {
        await apiClient.markNotificationAsRead(id);
      } else {
        await apiClient.markNotificationRead(id);
      }
    } catch (err) {
      console.error('Failed to mark notification as read:', err);
      setNotificationList((list) =>
        list.map((n) => (n.id === id ? { ...n, read: false } : n))
      );
      toast.error('Failed to mark as read');
    }
  };

  const markAllAsRead = async () => {
    try {
      setActionLoading(true);
      await apiClient.markAllNotificationsRead();
      setNotificationList((list) => list.map((n) => ({ ...n, read: true })));
      toast.success('All notifications marked as read');
    } catch (err) {
      console.error('Failed to mark all as read:', err);
      toast.error('Failed to mark all as read');
    } finally {
      setActionLoading(false);
    }
  };

  const toggleStarred = (id: string) => {
    setNotificationList((list) =>
      list.map((n) => (n.id === id ? { ...n, starred: !n.starred } : n))
    );
  };

  const deleteNotification = (id: string) => {
    setNotificationList((list) => list.filter((n) => n.id !== id));
  };

  const renderNotificationRow = (
    notification: UiNotification,
    options?: { compact?: boolean; index?: number }
  ) => {
    const typeConfig =
      notificationTypes[notification.type as NotificationTypeKey] || notificationTypes.info;
    const TypeIcon = typeConfig.icon;
    const index = options?.index ?? 0;

    if (options?.compact) {
      return (
        <div
          key={notification.id}
          className={cn(
            'flex items-start gap-4 p-4 hover:bg-muted/50 transition-colors cursor-pointer',
            !notification.read && 'bg-primary/5'
          )}
          onClick={() => markAsRead(notification.id)}
        >
          <div className={cn('flex h-10 w-10 items-center justify-center rounded-full', typeConfig.bg)}>
            <TypeIcon className={cn('h-5 w-5', typeConfig.color)} />
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-medium">{notification.title}</p>
            <p className="text-sm text-muted-foreground mt-0.5">{notification.description}</p>
          </div>
          <span className="text-xs text-muted-foreground">{notification.timestamp}</span>
        </div>
      );
    }

    return (
      <motion.div
        key={notification.id}
        layout
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: 20 }}
        transition={{ delay: index * 0.05 }}
        className={cn(
          'flex items-start gap-4 p-4 hover:bg-muted/50 transition-colors cursor-pointer',
          !notification.read && 'bg-primary/5'
        )}
        onClick={() => markAsRead(notification.id)}
      >
        <div
          className={cn(
            'flex h-10 w-10 items-center justify-center rounded-full shrink-0',
            typeConfig.bg
          )}
        >
          <TypeIcon className={cn('h-5 w-5', typeConfig.color)} />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div>
              <p
                className={cn(
                  'font-medium',
                  !notification.read && 'text-foreground',
                  notification.read && 'text-muted-foreground'
                )}
              >
                {notification.title}
              </p>
              <p className="text-sm text-muted-foreground mt-0.5">{notification.description}</p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground whitespace-nowrap">
                {notification.timestamp}
              </span>
              {!notification.read && <div className="h-2 w-2 rounded-full bg-primary" />}
            </div>
          </div>
          {notification.action && (
            <Button
              variant="link"
              className="h-auto p-0 mt-2 text-primary"
              onClick={(e) => e.stopPropagation()}
            >
              {notification.action.label}
              <ExternalLink className="h-3 w-3 ml-1" />
            </Button>
          )}
        </div>

        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={(e) => {
              e.stopPropagation();
              toggleStarred(notification.id);
            }}
          >
            {notification.starred ? (
              <Star className="h-4 w-4 fill-yellow-500 text-yellow-500" />
            ) : (
              <StarOff className="h-4 w-4 text-muted-foreground" />
            )}
          </Button>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => markAsRead(notification.id)}>
                <Check className="h-4 w-4 mr-2" />
                Mark as read
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => toggleStarred(notification.id)}>
                <Star className="h-4 w-4 mr-2" />
                {notification.starred ? 'Unstar' : 'Star'}
              </DropdownMenuItem>
              <DropdownMenuItem>
                <Archive className="h-4 w-4 mr-2" />
                Archive
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                className="text-destructive"
                onClick={() => deleteNotification(notification.id)}
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </motion.div>
    );
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
              <Bell className="h-8 w-8 text-primary" />
              Notifications
              {unreadCount > 0 && <Badge className="ml-2">{unreadCount} unread</Badge>}
            </h1>
            <p className="text-muted-foreground mt-1">
              Stay updated with your agent activities and system alerts
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="icon" onClick={loadNotifications} disabled={loading}>
              <RefreshCw className={cn('h-4 w-4', loading && 'animate-spin')} />
            </Button>
            <Button
              variant="outline"
              className="gap-2"
              onClick={markAllAsRead}
              disabled={actionLoading || unreadCount === 0}
            >
              {actionLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <CheckCheck className="h-4 w-4" />
              )}
              Mark All Read
            </Button>
            <Button variant="outline" size="icon">
              <Settings className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <Tabs defaultValue="all" className="space-y-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <TabsList>
              <TabsTrigger value="all">All</TabsTrigger>
              <TabsTrigger value="inbox" className="gap-2">
                Inbox
                {unreadCount > 0 && (
                  <Badge variant="secondary" className="h-5 px-1.5">
                    {unreadCount}
                  </Badge>
                )}
              </TabsTrigger>
              <TabsTrigger value="starred" className="gap-2">
                Starred
                {starredCount > 0 && (
                  <Badge variant="secondary" className="h-5 px-1.5">
                    {starredCount}
                  </Badge>
                )}
              </TabsTrigger>
              <TabsTrigger value="settings">Settings</TabsTrigger>
            </TabsList>
            <div className="flex items-center gap-2 sm:ml-auto">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search notifications..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 w-64"
                />
              </div>
            </div>
          </div>

          <TabsContent value="all" className="space-y-4">
            <Card>
              <CardContent className="p-0">
                <div className="divide-y">
                  {loading ? (
                    <div className="flex flex-col items-center justify-center py-12 text-center">
                      <Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
                      <p className="text-sm text-muted-foreground">Loading notifications...</p>
                    </div>
                  ) : error ? (
                    <div className="flex flex-col items-center justify-center py-12 text-center">
                      <AlertCircle className="h-12 w-12 text-destructive mb-4" />
                      <h3 className="font-semibold">{error}</h3>
                      <Button variant="outline" className="mt-4" onClick={loadNotifications}>
                        Try again
                      </Button>
                    </div>
                  ) : (
                    <>
                      <AnimatePresence mode="popLayout">
                        {filteredNotifications.map((notification, index) =>
                          renderNotificationRow(notification, { index })
                        )}
                      </AnimatePresence>

                      {filteredNotifications.length === 0 && (
                        <div className="flex flex-col items-center justify-center py-12 text-center">
                          <Bell className="h-12 w-12 text-muted-foreground mb-4" />
                          <h3 className="font-semibold">No notifications</h3>
                          <p className="text-sm text-muted-foreground">You&apos;re all caught up!</p>
                        </div>
                      )}
                    </>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="inbox" className="space-y-4">
            <Card>
              <CardContent className="p-0">
                <div className="divide-y">
                  {loading ? (
                    <div className="flex flex-col items-center justify-center py-12 text-center">
                      <Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
                      <p className="text-sm text-muted-foreground">Loading notifications...</p>
                    </div>
                  ) : (
                    <>
                      {notificationList
                        .filter((n) => !n.read && matchesSearch(n))
                        .map((notification) =>
                          renderNotificationRow(notification, { compact: true })
                        )}
                      {notificationList.filter((n) => !n.read && matchesSearch(n)).length === 0 && (
                        <div className="flex flex-col items-center justify-center py-12 text-center">
                          <CheckCircle2 className="h-12 w-12 text-green-500 mb-4" />
                          <h3 className="font-semibold">All caught up!</h3>
                          <p className="text-sm text-muted-foreground">No unread notifications</p>
                        </div>
                      )}
                    </>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="starred" className="space-y-4">
            <Card>
              <CardContent className="p-0">
                <div className="divide-y">
                  {notificationList
                    .filter((n) => n.starred && matchesSearch(n))
                    .map((notification) => {
                      const typeConfig =
                        notificationTypes[notification.type as NotificationTypeKey] ||
                        notificationTypes.info;
                      const TypeIcon = typeConfig.icon;

                      return (
                        <div
                          key={notification.id}
                          className="flex items-start gap-4 p-4 hover:bg-muted/50 transition-colors cursor-pointer"
                        >
                          <div
                            className={cn(
                              'flex h-10 w-10 items-center justify-center rounded-full',
                              typeConfig.bg
                            )}
                          >
                            <TypeIcon className={cn('h-5 w-5', typeConfig.color)} />
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="font-medium">{notification.title}</p>
                            <p className="text-sm text-muted-foreground mt-0.5">
                              {notification.description}
                            </p>
                          </div>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8"
                            onClick={() => toggleStarred(notification.id)}
                          >
                            <Star className="h-4 w-4 fill-yellow-500 text-yellow-500" />
                          </Button>
                        </div>
                      );
                    })}
                  {notificationList.filter((n) => n.starred && matchesSearch(n)).length === 0 && (
                    <div className="flex flex-col items-center justify-center py-12 text-center">
                      <Star className="h-12 w-12 text-muted-foreground mb-4" />
                      <h3 className="font-semibold">No starred notifications</h3>
                      <p className="text-sm text-muted-foreground">
                        Star important notifications to find them easily
                      </p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="settings" className="space-y-6">
            {notificationPreferences.map((category) => (
              <Card key={category.category}>
                <CardHeader>
                  <CardTitle className="text-lg">{category.category}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {category.items.map((item, index) => (
                    <React.Fragment key={item}>
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium">{item}</p>
                          <p className="text-sm text-muted-foreground">
                            Receive notifications for {item.toLowerCase()}
                          </p>
                        </div>
                        <div className="flex items-center gap-4">
                          <div className="flex items-center gap-2">
                            <Volume2 className="h-4 w-4 text-muted-foreground" />
                            <Switch defaultChecked />
                          </div>
                        </div>
                      </div>
                      {index < category.items.length - 1 && <Separator />}
                    </React.Fragment>
                  ))}
                </CardContent>
              </Card>
            ))}
          </TabsContent>
        </Tabs>
      </motion.div>
    </AppLayout>
  );
}
