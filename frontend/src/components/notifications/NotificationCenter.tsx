"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Bell,
  Mail,
  Settings,
  Plus,
  Edit,
  Trash2,
  Send,
  Eye,
  Check,
  X,
  Clock,
  User,
  Smartphone,
  Monitor,
  AlertTriangle,
  CheckCircle2,
  Info,
  MessageCircle,
  Calendar,
  Search,
  Archive,
  Download,
  Zap,
  Target,
  Database,
  Workflow,
  Volume2
} from 'lucide-react';

interface Notification {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error' | 'system';
  priority: 'low' | 'medium' | 'high' | 'critical';
  category: string;
  source: {
    type: 'agent' | 'workflow' | 'task' | 'system' | 'user';
    id: string;
    name: string;
  };
  recipient: {
    user_id: string;
    channels: string[];
  };
  status: 'unread' | 'read' | 'archived' | 'deleted';
  actions?: Array<{
    label: string;
    action: string;
    style: 'primary' | 'secondary' | 'destructive';
  }>;
  metadata: Record<string, unknown>;
  created_at: string;
  read_at?: string;
  expires_at?: string;
}

interface EmailTemplate {
  id: string;
  name: string;
  subject: string;
  body_html: string;
  body_text: string;
  recipients: Array<{
    email: string;
    name?: string;
    variables?: Record<string, string>;
  }>;
  status: 'draft' | 'scheduled' | 'sending' | 'sent' | 'cancelled';
  scheduled_at?: string;
  sent_at?: string;
  updated_at: string;
  stats: {
    total: number;
    sent: number;
    delivered: number;
    opened: number;
    clicked: number;
    bounced: number;
    unsubscribed: number;
  };
  created_at: string;
}

interface EmailTemplate {
  id: string;
  name: string;
  subject: string;
  body_html: string;
  body_text: string;
  recipients: Array<{
    email: string;
    name?: string;
    variables?: Record<string, string>;
  }>;
  status: 'draft' | 'scheduled' | 'sending' | 'sent' | 'cancelled';
  scheduled_at?: string;
  sent_at?: string;
  updated_at: string;
  category: string;
  variables: Array<{
    name: string;
    description: string;
    required: boolean;
  }>;
  stats: {
    total: number;
    sent: number;
    delivered: number;
    opened: number;
    clicked: number;
    bounced: number;
    unsubscribed: number;
  };
  created_at: string;
}

interface EmailCampaign {
  id: string;
  name: string;
  description: string;
  subject: string;
  body_html: string;
  body_text: string;
  recipients: Array<{
    email: string;
    name?: string;
    variables?: Record<string, string>;
  }>;
  status: 'draft' | 'scheduled' | 'sending' | 'sent' | 'cancelled';
  scheduled_at?: string;
  sent_at?: string;
  updated_at: string;
  stats: {
    total: number;
    sent: number;
    delivered: number;
    opened: number;
    clicked: number;
    bounced: number;
    unsubscribed: number;
  };
  created_at: string;
}

interface NotificationRule {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  trigger: {
    event_type: string;
    conditions: Array<{
      field: string;
      operator: string;
      value: unknown;
    }>;
  };
  actions: Array<{
    type: 'notification' | 'email' | 'webhook' | 'sms';
    config: Record<string, unknown>;
  }>;
  recipients: Array<{
    type: 'user' | 'role' | 'email';
    value: string;
  }>;
  throttling: {
    enabled: boolean;
    max_per_hour: number;
  };
}

interface NotificationPreferencesType {
  push_notifications: boolean;
  email_notifications: boolean;
  sms_notifications: boolean;
  in_app_notifications: boolean;
  sound_enabled: boolean;
  vibration_enabled: boolean;
  quiet_hours: {
    enabled: boolean;
    start_time: string;
    end_time: string;
  };
  categories: Record<string, {
    push: boolean;
    email: boolean;
    sms: boolean;
    priority: 'low' | 'medium' | 'high';
  }>;
}

export const NotificationCenter: React.FC = () => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [emailTemplates, setEmailTemplates] = useState<EmailTemplate[]>([]);
  const [emailCampaigns, setEmailCampaigns] = useState<EmailCampaign[]>([]);
  const [notificationRules, setNotificationRules] = useState<NotificationRule[]>([]);
  const [settings, setSettings] = useState<NotificationPreferencesType | null>(null);
  const [activeTab, setActiveTab] = useState('notifications');
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const loadNotificationData = async () => {
    try {
      const [notificationsRes, templatesRes, campaignsRes, rulesRes, settingsRes] = await Promise.all([
        fetch('/api/notifications/'),
        fetch('/api/notifications/email-templates/'),
        fetch('/api/notifications/email-campaigns/'),
        fetch('/api/notifications/rules/'),
        fetch('/api/notifications/settings/')
      ]);

      if (notificationsRes.ok) {
        const data = await notificationsRes.json();
        setNotifications(data);
      }

      if (templatesRes.ok) {
        const data = await templatesRes.json();
        setEmailTemplates(data);
      }

      if (campaignsRes.ok) {
        const data = await campaignsRes.json();
        setEmailCampaigns(data);
      }

      if (rulesRes.ok) {
        const data = await rulesRes.json();
        setNotificationRules(data);
      }

      if (settingsRes.ok) {
        const data = await settingsRes.json();
        setSettings(data);
      }
    } catch (error) {
      console.error('Failed to load notification data:', error);
    }
  };

  const markAsRead = async (notificationId: string) => {
    try {
      const response = await fetch(`/api/notifications/${notificationId}/read/`, {
        method: 'POST'
      });

      if (response.ok) {
        setNotifications(prev => 
          prev.map(n => 
            n.id === notificationId 
              ? { ...n, status: 'read', read_at: new Date().toISOString() }
              : n
          )
        );
      }
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  };

  const archiveNotification = async (notificationId: string) => {
    try {
      const response = await fetch(`/api/notifications/${notificationId}/archive/`, {
        method: 'POST'
      });

      if (response.ok) {
        setNotifications(prev => 
          prev.map(n => 
            n.id === notificationId 
              ? { ...n, status: 'archived' }
              : n
          )
        );
      }
    } catch (error) {
      console.error('Failed to archive notification:', error);
    }
  };

  const deleteNotification = async (notificationId: string) => {
    if (!confirm('Are you sure you want to delete this notification?')) return;

    try {
      const response = await fetch(`/api/notifications/${notificationId}/`, {
        method: 'DELETE'
      });

      if (response.ok) {
        setNotifications(prev => prev.filter(n => n.id !== notificationId));
      }
    } catch (error) {
      console.error('Failed to delete notification:', error);
    }
  };

  const sendEmailCampaign = async (campaignId: string) => {
    try {
      const response = await fetch(`/api/notifications/email-campaigns/${campaignId}/send/`, {
        method: 'POST'
      });

      if (response.ok) {
        const updated = await response.json();
        setEmailCampaigns(prev => 
          prev.map(c => c.id === campaignId ? updated : c)
        );
      }
    } catch (error) {
      console.error('Failed to send email campaign:', error);
    }
  };

  const updateSettings = async (newSettings: Partial<NotificationPreferencesType>) => {
    try {
      const response = await fetch('/api/notifications/settings/', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newSettings)
      });

      if (response.ok) {
        const updated = await response.json();
        setSettings(updated);
      }
    } catch (error) {
      console.error('Failed to update settings:', error);
    }
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'success': return <CheckCircle2 className="w-4 h-4 text-green-500" />;
      case 'warning': return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
      case 'error': return <X className="w-4 h-4 text-red-500" />;
      case 'info': return <Info className="w-4 h-4 text-blue-500" />;
      default: return <Bell className="w-4 h-4 text-gray-500" />;
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'text-red-600 bg-red-50 border-red-200';
      case 'high': return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'medium': return 'text-blue-600 bg-blue-50 border-blue-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const filteredNotifications = notifications.filter(notification => {
    const matchesSearch = notification.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         notification.message.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = filterType === 'all' || notification.type === filterType;
    const matchesStatus = filterStatus === 'all' || notification.status === filterStatus;
    
    return matchesSearch && matchesType && matchesStatus;
  });
    useEffect(() => {
        setTimeout(() => loadNotificationData(), 0);
      }, []);

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Notification & Email Center
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Manage notifications, email campaigns, and communication settings
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm">
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
          <Button>
            <Plus className="w-4 h-4 mr-2" />
            New Campaign
          </Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="notifications" className="flex items-center gap-2">
            <Bell className="w-4 h-4" />
            Notifications
            {notifications.filter(n => n.status === 'unread').length > 0 && (
              <Badge variant="destructive" className="ml-1 px-1 py-0 text-xs">
                {notifications.filter(n => n.status === 'unread').length}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="emails" className="flex items-center gap-2">
            <Mail className="w-4 h-4" />
            Email Campaigns
          </TabsTrigger>
          <TabsTrigger value="templates" className="flex items-center gap-2">
            <MessageCircle className="w-4 h-4" />
            Templates
          </TabsTrigger>
          <TabsTrigger value="rules" className="flex items-center gap-2">
            <Zap className="w-4 h-4" />
            Rules
          </TabsTrigger>
          <TabsTrigger value="settings" className="flex items-center gap-2">
            <Settings className="w-4 h-4" />
            Settings
          </TabsTrigger>
        </TabsList>

        <TabsContent value="notifications" className="space-y-6">
          {/* Filters */}
          <Card>
            <CardContent className="p-4">
              <div className="flex flex-wrap gap-4 items-center">
                <div className="flex-1 min-w-64">
                  <div className="relative">
                    <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                    <Input
                      placeholder="Search notifications..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-10"
                    />
                  </div>
                </div>
                <Select value={filterType} onValueChange={setFilterType}>
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Types</SelectItem>
                    <SelectItem value="info">Info</SelectItem>
                    <SelectItem value="success">Success</SelectItem>
                    <SelectItem value="warning">Warning</SelectItem>
                    <SelectItem value="error">Error</SelectItem>
                  </SelectContent>
                </Select>
                <Select value={filterStatus} onValueChange={setFilterStatus}>
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Status</SelectItem>
                    <SelectItem value="unread">Unread</SelectItem>
                    <SelectItem value="read">Read</SelectItem>
                    <SelectItem value="archived">Archived</SelectItem>
                  </SelectContent>
                </Select>
                <div className="flex gap-2">
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => {
                      notifications.filter(n => n.status === 'unread').forEach(n => markAsRead(n.id));
                    }}
                  >
                    Mark All Read
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Notifications List */}
          <div className="space-y-3">
            {filteredNotifications.length === 0 ? (
              <Card>
                <CardContent className="p-8 text-center">
                  <Bell className="w-16 h-16 mx-auto text-gray-400 mb-4" />
                  <h3 className="text-lg font-semibold mb-2">No Notifications</h3>
                  <p className="text-gray-600 dark:text-gray-400">
                    {searchTerm || filterType !== 'all' || filterStatus !== 'all' 
                      ? 'No notifications match your current filters.'
                      : 'You\'re all caught up! No new notifications.'}
                  </p>
                </CardContent>
              </Card>
            ) : (
              filteredNotifications.map((notification) => (
                <Card 
                  key={notification.id} 
                  className={`transition-colors ${
                    notification.status === 'unread' 
                      ? 'border-blue-200 bg-blue-50/50 dark:bg-blue-900/10' 
                      : ''
                  }`}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start gap-4">
                      <div className="mt-1">
                        {getNotificationIcon(notification.type)}
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <h3 className="font-semibold truncate">{notification.title}</h3>
                            {notification.status === 'unread' && (
                              <div className="w-2 h-2 bg-blue-500 rounded-full flex-shrink-0"></div>
                            )}
                          </div>
                          <div className="flex items-center gap-2 flex-shrink-0">
                            <Badge 
                              variant="outline" 
                              className={getPriorityColor(notification.priority)}
                            >
                              {notification.priority}
                            </Badge>
                            <Badge variant="secondary">{notification.category}</Badge>
                          </div>
                        </div>
                        
                        <p className="text-gray-600 dark:text-gray-400 mb-3">
                          {notification.message}
                        </p>
                        
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-4 text-sm text-gray-500">
                            <div className="flex items-center gap-1">
                              {notification.source.type === 'agent' && <User className="w-4 h-4" />}
                              {notification.source.type === 'workflow' && <Workflow className="w-4 h-4" />}
                              {notification.source.type === 'system' && <Database className="w-4 h-4" />}
                              {notification.source.name}
                            </div>
                            <div className="flex items-center gap-1">
                              <Clock className="w-4 h-4" />
                              {new Date(notification.created_at).toLocaleString()}
                            </div>
                          </div>
                          
                          <div className="flex items-center gap-2">
                            {notification.actions?.map((action) => (
                              <Button 
                                key={action.action}
                                size="sm" 
                                variant={action.style === 'primary' ? 'default' : action.style === 'destructive' ? 'destructive' : 'outline'}
                              >
                                {action.label}
                              </Button>
                            ))}
                            
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => markAsRead(notification.id)}
                              disabled={notification.status === 'read'}
                            >
                              <Check className="w-4 h-4" />
                            </Button>
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => archiveNotification(notification.id)}
                            >
                              <Archive className="w-4 h-4" />
                            </Button>
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => deleteNotification(notification.id)}
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </TabsContent>

        <TabsContent value="emails" className="space-y-6">
          {/* Email Campaigns */}
          <div className="grid gap-4">
            {emailCampaigns.map((campaign) => (
              <Card key={campaign.id}>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="font-semibold text-lg">{campaign.name}</h3>
                      <p className="text-gray-600 dark:text-gray-400">{campaign.description}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge 
                        variant={
                          campaign.status === 'sent' ? 'default' :
                          campaign.status === 'sending' ? 'secondary' :
                          campaign.status === 'scheduled' ? 'outline' :
                          'secondary'
                        }
                      >
                        {campaign.status}
                      </Badge>
                      {campaign.status === 'draft' && (
                        <Button size="sm" onClick={() => sendEmailCampaign(campaign.id)}>
                          <Send className="w-4 h-4 mr-1" />
                          Send
                        </Button>
                      )}
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4 mb-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600">{campaign.stats.total}</div>
                      <div className="text-sm text-gray-600">Total</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-600">{campaign.stats.sent}</div>
                      <div className="text-sm text-gray-600">Sent</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-purple-600">{campaign.stats.delivered}</div>
                      <div className="text-sm text-gray-600">Delivered</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-orange-600">{campaign.stats.opened}</div>
                      <div className="text-sm text-gray-600">Opened</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-indigo-600">{campaign.stats.clicked}</div>
                      <div className="text-sm text-gray-600">Clicked</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-red-600">{campaign.stats.bounced}</div>
                      <div className="text-sm text-gray-600">Bounced</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-gray-600">{campaign.stats.unsubscribed}</div>
                      <div className="text-sm text-gray-600">Unsubscribed</div>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between text-sm text-gray-600">
                    <span>Created: {new Date(campaign.created_at).toLocaleDateString()}</span>
                    {campaign.sent_at && (
                      <span>Sent: {new Date(campaign.sent_at).toLocaleDateString()}</span>
                    )}
                    {campaign.scheduled_at && (
                      <span>Scheduled: {new Date(campaign.scheduled_at).toLocaleDateString()}</span>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="templates" className="space-y-6">
          {/* Email Templates */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {emailTemplates.map((template) => (
              <Card key={template.id} className="cursor-pointer hover:shadow-lg transition-shadow">
                <CardContent className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg flex items-center justify-center">
                      <Mail className="w-6 h-6 text-white" />
                    </div>
                    <Badge variant="outline">{template.category}</Badge>
                  </div>
                  
                  <h3 className="font-semibold text-lg mb-2">{template.name}</h3>
                  <p className="text-gray-600 dark:text-gray-400 mb-4 line-clamp-2">
                    {template.subject}
                  </p>
                  
                  <div className="space-y-2 mb-4">
                    <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                      <Target className="w-4 h-4" />
                      {template.variables.length} variables
                    </div>
                    <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                      <Calendar className="w-4 h-4" />
                      Updated {new Date(template.updated_at).toLocaleDateString()}
                    </div>
                  </div>
                  
                  <div className="flex gap-2">
                    <Button className="flex-1" size="sm">
                      <Eye className="w-4 h-4 mr-1" />
                      Preview
                    </Button>
                    <Button variant="outline" size="sm">
                      <Edit className="w-4 h-4" />
                    </Button>
                    <Button variant="outline" size="sm">
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="rules" className="space-y-6">
          {/* Notification Rules */}
          <div className="space-y-4">
            {notificationRules.map((rule) => (
              <Card key={rule.id}>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="font-semibold text-lg flex items-center gap-2">
                        {rule.name}
                        <Switch 
                          checked={rule.enabled} 
                          onCheckedChange={() => {
                            // Update rule enabled status
                          }} 
                        />
                      </h3>
                      <p className="text-gray-600 dark:text-gray-400">{rule.description}</p>
                    </div>
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm">
                        <Edit className="w-4 h-4" />
                      </Button>
                      <Button variant="outline" size="sm">
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                    <div>
                      <h4 className="font-medium mb-2">{rule.name}</h4>
                      <p className="text-gray-600 dark:text-gray-400">
                        {rule.trigger.event_type}
                      </p>
                      <div className="mt-2">
                        {rule.trigger.conditions.map((condition, index) => (
                          <div key={index} className="text-xs text-gray-500">
                            {condition.field} {condition.operator} {String(condition.value)}
                          </div>
                        ))}
                      </div>
                    </div>
                    
                    <div>
                      <h4 className="font-medium mb-2">Actions</h4>
                      <div className="space-y-1">
                        {rule.actions.map((action, index) => (
                          <Badge key={index} variant="outline" className="text-xs">
                            {action.type}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    
                    <div>
                      <h4 className="font-medium mb-2">Recipients</h4>
                      <div className="space-y-1">
                        {rule.recipients.map((recipient, index) => (
                          <div key={index} className="text-xs text-gray-600">
                            {recipient.type}: {recipient.value}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                  
                  {rule.throttling.enabled && (
                    <Alert className="mt-4">
                      <AlertTriangle className="h-4 w-4" />
                      <AlertDescription>
                        Throttling enabled: Max {rule.throttling.max_per_hour} notifications per hour
                      </AlertDescription>
                    </Alert>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="settings" className="space-y-6">
          {settings && <NotificationSettings settings={settings} onUpdate={updateSettings} />}
        </TabsContent>
      </Tabs>
    </div>
  );
};

const NotificationSettings: React.FC<{
  settings: NotificationPreferencesType;
  onUpdate: (settings: Partial<NotificationPreferencesType>) => void;
}> = ({ settings, onUpdate }) => {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="w-5 h-5" />
            General Settings
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Bell className="w-4 h-4" />
                  <Label>Push Notifications</Label>
                </div>
                <Switch 
                  checked={settings.push_notifications}
                  onCheckedChange={(checked) => onUpdate({ push_notifications: checked })}
                />
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Mail className="w-4 h-4" />
                  <Label>Email Notifications</Label>
                </div>
                <Switch 
                  checked={settings.email_notifications}
                  onCheckedChange={(checked) => onUpdate({ email_notifications: checked })}
                />
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Smartphone className="w-4 h-4" />
                  <Label>SMS Notifications</Label>
                </div>
                <Switch 
                  checked={settings.sms_notifications}
                  onCheckedChange={(checked) => onUpdate({ sms_notifications: checked })}
                />
              </div>
            </div>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Volume2 className="w-4 h-4" />
                  <Label>Sound Enabled</Label>
                </div>
                <Switch 
                  checked={settings.sound_enabled}
                  onCheckedChange={(checked) => onUpdate({ sound_enabled: checked })}
                />
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Smartphone className="w-4 h-4" />
                  <Label>Vibration Enabled</Label>
                </div>
                <Switch 
                  checked={settings.vibration_enabled}
                  onCheckedChange={(checked) => onUpdate({ vibration_enabled: checked })}
                />
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Monitor className="w-4 h-4" />
                  <Label>In-App Notifications</Label>
                </div>
                <Switch 
                  checked={settings.in_app_notifications}
                  onCheckedChange={(checked) => onUpdate({ in_app_notifications: checked })}
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="w-5 h-5" />
            Quiet Hours
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between mb-4">
            <Label>Enable Quiet Hours</Label>
            <Switch 
              checked={settings.quiet_hours.enabled}
              onCheckedChange={(checked) => 
                onUpdate({ quiet_hours: { ...settings.quiet_hours, enabled: checked } })
              }
            />
          </div>
          
          {settings.quiet_hours.enabled && (
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Start Time</Label>
                <Input
                  type="time"
                  value={settings.quiet_hours.start_time}
                  onChange={(e) => 
                    onUpdate({ quiet_hours: { ...settings.quiet_hours, start_time: e.target.value } })
                  }
                />
              </div>
              <div className="space-y-2">
                <Label>End Time</Label>
                <Input
                  type="time"
                  value={settings.quiet_hours.end_time}
                  onChange={(e) => 
                    onUpdate({ quiet_hours: { ...settings.quiet_hours, end_time: e.target.value } })
                  }
                />
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default NotificationCenter;