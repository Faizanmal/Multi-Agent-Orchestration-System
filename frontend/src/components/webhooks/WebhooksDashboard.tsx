'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Webhook, 
  Bell, 
  Check, 
  X, 
  Clock, 
  AlertCircle,
  Send,
  RefreshCw,
  Trash2,
  Plus
} from 'lucide-react';
import { 
  getWebhooks, 
  createWebhook, 
  deleteWebhook,
  getWebhookDeliveries,
  testWebhook,
  getNotifications,
  markNotificationRead
} from '@/lib/api';
import { toast } from 'sonner';

interface WebhookType {
  id: string;
  name: string;
  url: string;
  event_type: string;
  is_active: boolean;
  secret_key?: string;
  retry_count: number;
  timeout_seconds: number;
  created_at: string;
}

interface WebhookDelivery {
  id: string;
  webhook: { id: string; name: string };
  payload: Record<string, unknown>;
  response_status: number | null;
  response_body: string;
  delivery_attempts: number;
  status: 'pending' | 'success' | 'failed';
  error_message: string;
  delivered_at: string | null;
  created_at: string;
}

interface Notification {
  id: string;
  title: string;
  message: string;
  notification_type: string;
  channel: string;
  is_read: boolean;
  created_at: string;
}

export default function WebhooksDashboard() {
  const [webhooks, setWebhooks] = useState<WebhookType[]>([]);
  const [deliveries, setDeliveries] = useState<WebhookDelivery[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [newWebhook, setNewWebhook] = useState({
    name: '',
    url: '',
    event_type: 'task_completed',
    retry_count: 3,
    timeout_seconds: 30
  });

  async function loadData() {
    try {
      setLoading(true);
      const [webhooksRes, notificationsRes] = await Promise.all([
        getWebhooks(),
        getNotifications({ is_read: false })
      ]);

      setWebhooks(webhooksRes.data.results || webhooksRes.data);
      setNotifications(notificationsRes.notifications as Notification[]);
      
      // Get deliveries for all webhooks
      const allDeliveries: WebhookDelivery[] = [];
      const webhooksData = webhooksRes.data.results || webhooksRes.data;
      for (const webhook of webhooksData.slice(0, 5)) { // Limit to first 5 to avoid too many requests
        try {
          const deliveriesRes = await getWebhookDeliveries(webhook.id);
          allDeliveries.push(...(deliveriesRes.data.results || deliveriesRes.data || []));
        } catch (err) {
          console.error(`Error loading deliveries for webhook ${webhook.id}:`, err);
        }
      }
      setDeliveries(allDeliveries);
    } catch (error) {
      console.error('Error loading data:', error);
      toast.error('Failed to load webhooks data');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateWebhook = async () => {
    try {
      await createWebhook({
        name: newWebhook.name,
        url: newWebhook.url,
        subscribed_events: [newWebhook.event_type],
        secret_key: Math.random().toString(36).substring(7)
      });
      toast.success('Webhook created successfully');
      setCreateDialogOpen(false);
      setNewWebhook({
        name: '',
        url: '',
        event_type: 'task_completed',
        retry_count: 3,
        timeout_seconds: 30
      });
      loadData();
    } catch {
      toast.error('Failed to create webhook');
    }
  };

  const handleDeleteWebhook = async (id: string) => {
    try {
      await deleteWebhook(id);
      toast.success('Webhook deleted successfully');
      loadData();
    } catch {
      toast.error('Failed to delete webhook');
    }
  };

  const handleTestWebhook = async (id: string) => {
    try {
      await testWebhook(id);
      toast.success('Test webhook sent successfully');
      loadData();
    } catch {
      toast.error('Failed to test webhook');
    }
  };

  const handleMarkRead = async (id: string) => {
    try {
      await markNotificationRead(id);
      loadData();
    } catch {
      toast.error('Failed to mark notification as read');
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <Check className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <X className="h-4 w-4 text-red-500" />;
      case 'pending':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      default:
        return <AlertCircle className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  useEffect(() => { setTimeout(() => loadData(), 0); }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <Webhook className="h-12 w-12 animate-pulse text-blue-500 mx-auto mb-4" />
          <p className="text-gray-600">Loading webhooks...</p>
        </div>
      </div>
    );
  }


  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Webhook className="h-8 w-8 text-blue-500" />
            Webhooks & Notifications
          </h1>
          <p className="text-gray-600 mt-2">
            Manage webhook endpoints and notification channels
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={loadData} variant="outline">
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          <Button onClick={() => setCreateDialogOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            New Webhook
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Total Webhooks</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{webhooks.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Active</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">
              {webhooks.filter(w => w.is_active).length}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Recent Deliveries</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{deliveries.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Unread Notifications</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-orange-600">{notifications.length}</div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="webhooks" className="space-y-4">
        <TabsList>
          <TabsTrigger value="webhooks">Webhooks ({webhooks.length})</TabsTrigger>
          <TabsTrigger value="deliveries">Delivery History ({deliveries.length})</TabsTrigger>
          <TabsTrigger value="notifications">
            Notifications
            {notifications.length > 0 && (
              <Badge variant="destructive" className="ml-2">
                {notifications.length}
              </Badge>
            )}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="webhooks" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {webhooks.map((webhook) => (
              <Card key={webhook.id}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-lg flex items-center gap-2">
                        <Webhook className="h-4 w-4" />
                        {webhook.name}
                        {webhook.is_active ? (
                          <Badge variant="default" className="bg-green-500">Active</Badge>
                        ) : (
                          <Badge variant="secondary">Inactive</Badge>
                        )}
                      </CardTitle>
                      <CardDescription className="mt-1 break-all">
                        {webhook.url}
                      </CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Event Type</span>
                      <Badge variant="outline">{webhook.event_type}</Badge>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Retry Count</span>
                      <span className="font-medium">{webhook.retry_count}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Timeout</span>
                      <span className="font-medium">{webhook.timeout_seconds}s</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Created</span>
                      <span className="font-medium">
                        {new Date(webhook.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>

                  <div className="flex gap-2 pt-2 border-t">
                    <Button size="sm" variant="outline" className="flex-1" onClick={() => handleTestWebhook(webhook.id)}>
                      <Send className="mr-1 h-3 w-3" />
                      Test
                    </Button>
                    <Button size="sm" variant="destructive" onClick={() => handleDeleteWebhook(webhook.id)}>
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
            {webhooks.length === 0 && (
              <Card className="col-span-full">
                <CardContent className="text-center py-12">
                  <Webhook className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600">No webhooks configured</p>
                  <p className="text-sm text-gray-500 mt-2">Create your first webhook to get started</p>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        <TabsContent value="deliveries" className="space-y-4">
          <div className="space-y-4">
            {deliveries.map((delivery) => (
              <Card key={delivery.id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(delivery.status)}
                      <CardTitle className="text-lg">{delivery.webhook.name}</CardTitle>
                      <Badge className={getStatusColor(delivery.status)}>
                        {delivery.status}
                      </Badge>
                    </div>
                    <div className="text-sm text-gray-500">
                      {delivery.delivered_at 
                        ? new Date(delivery.delivered_at).toLocaleString()
                        : new Date(delivery.created_at).toLocaleString()}
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Response Status</span>
                    <span className="font-mono font-medium">
                      {delivery.response_status || 'N/A'}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Attempts</span>
                    <span className="font-medium">{delivery.delivery_attempts}</span>
                  </div>
                  {delivery.error_message && (
                    <div className="pt-2 border-t">
                      <p className="text-sm text-gray-600 mb-1">Error Message</p>
                      <p className="text-sm text-red-600 font-mono bg-red-50 p-2 rounded">
                        {delivery.error_message}
                      </p>
                    </div>
                  )}
                  {delivery.response_body && (
                    <details className="pt-2 border-t">
                      <summary className="text-sm text-gray-600 cursor-pointer mb-2">
                        Response Body
                      </summary>
                      <pre className="text-xs bg-gray-50 p-2 rounded overflow-x-auto">
                        {delivery.response_body}
                      </pre>
                    </details>
                  )}
                </CardContent>
              </Card>
            ))}
            {deliveries.length === 0 && (
              <Card>
                <CardContent className="text-center py-12">
                  <Send className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600">No webhook deliveries yet</p>
                  <p className="text-sm text-gray-500 mt-2">Deliveries will appear here once webhooks are triggered</p>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        <TabsContent value="notifications" className="space-y-4">
          <div className="space-y-4">
            {notifications.map((notification) => (
              <Card key={notification.id} className={!notification.is_read ? 'border-l-4 border-l-blue-500' : ''}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <Bell className="h-4 w-4 text-blue-500" />
                        <CardTitle className="text-lg">{notification.title}</CardTitle>
                        {!notification.is_read && (
                          <Badge variant="default">New</Badge>
                        )}
                      </div>
                      <CardDescription className="mt-2">
                        {notification.message}
                      </CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4 text-sm text-gray-600">
                      <Badge variant="outline">{notification.notification_type}</Badge>
                      <Badge variant="secondary">{notification.channel}</Badge>
                      <span>{new Date(notification.created_at).toLocaleString()}</span>
                    </div>
                    {!notification.is_read && (
                      <Button size="sm" variant="outline" onClick={() => handleMarkRead(notification.id)}>
                        <Check className="mr-1 h-3 w-3" />
                        Mark Read
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
            {notifications.length === 0 && (
              <Card>
                <CardContent className="text-center py-12">
                  <Bell className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600">No unread notifications</p>
                  <p className="text-sm text-gray-500 mt-2">You&apos;re all caught up!</p>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>
      </Tabs>

      {/* Create Webhook Dialog */}
      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Create New Webhook</DialogTitle>
            <DialogDescription>Configure a webhook endpoint to receive event notifications</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                value={newWebhook.name}
                onChange={(e) => setNewWebhook({ ...newWebhook, name: e.target.value })}
                placeholder="My Webhook"
              />
            </div>
            <div>
              <Label htmlFor="url">URL</Label>
              <Input
                id="url"
                value={newWebhook.url}
                onChange={(e) => setNewWebhook({ ...newWebhook, url: e.target.value })}
                placeholder="https://example.com/webhook"
              />
            </div>
            <div>
              <Label htmlFor="event_type">Event Type</Label>
              <Select value={newWebhook.event_type} onValueChange={(value) => setNewWebhook({ ...newWebhook, event_type: value })}>
                <SelectTrigger id="event_type">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="task_completed">Task Completed</SelectItem>
                  <SelectItem value="task_failed">Task Failed</SelectItem>
                  <SelectItem value="session_started">Session Started</SelectItem>
                  <SelectItem value="session_completed">Session Completed</SelectItem>
                  <SelectItem value="agent_error">Agent Error</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="retry_count">Retry Count</Label>
                <Input
                  id="retry_count"
                  type="number"
                  value={newWebhook.retry_count}
                  onChange={(e) => setNewWebhook({ ...newWebhook, retry_count: parseInt(e.target.value) })}
                  min="0"
                  max="10"
                />
              </div>
              <div>
                <Label htmlFor="timeout">Timeout (seconds)</Label>
                <Input
                  id="timeout"
                  type="number"
                  value={newWebhook.timeout_seconds}
                  onChange={(e) => setNewWebhook({ ...newWebhook, timeout_seconds: parseInt(e.target.value) })}
                  min="1"
                  max="300"
                />
              </div>
            </div>
            <div className="flex gap-2 pt-4">
              <Button onClick={handleCreateWebhook} className="flex-1">
                Create Webhook
              </Button>
              <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>
                Cancel
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
