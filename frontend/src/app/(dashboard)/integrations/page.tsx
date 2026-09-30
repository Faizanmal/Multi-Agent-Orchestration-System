"use client";

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Plug,
  Plus,
  Search,
  MoreVertical,
  Settings,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Globe,
  Zap,
  Database,
  Cloud,
  Bot,
  MessageSquare,
  BarChart3,
  GitBranch,
  Mail,
  Calendar,
  Shield,
  Copy,
  Eye,
  EyeOff,
  TestTube,
  Link2,
  Unlink,
  Clock,
  Activity,
  Trash2,
} from 'lucide-react';
import apiClient from '@/lib/api';
import { toast } from '@/hooks/use-toast';
import type { LucideIcon } from 'lucide-react';
import type { ActivityLogRecord, IntegrationRecord, IntegrationTemplate } from '@/types/api';
import { axiosErrorDetail, errorMessage, integrationListFromResponse, paginatedItems } from '@/types/api';
import { AppLayout } from '@/components/layout/AppLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Switch } from '@/components/ui/switch';
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

type IntegrationUI = IntegrationRecord & {
  icon: LucideIcon;
  category: string;
  status: string;
  lastSync: string;
};

type ActivityLogUI = {
  integration: string;
  event: string;
  status: string;
  time: string;
  details: string;
  integrationName: string;
};

// Integration categories
const categories = [
  { id: 'all', label: 'All', icon: Globe },
  { id: 'ai', label: 'AI & ML', icon: Bot },
  { id: 'communication', label: 'Communication', icon: MessageSquare },
  { id: 'analytics', label: 'Analytics', icon: BarChart3 },
  { id: 'devops', label: 'DevOps', icon: GitBranch },
  { id: 'storage', label: 'Storage', icon: Database },
];

// Icons mapping
const iconMap: Record<string, LucideIcon> = {
  'Globe': Globe,
  'Bot': Bot,
  'MessageSquare': MessageSquare,
  'BarChart3': BarChart3,
  'GitBranch': GitBranch,
  'Database': Database,
  'Cloud': Cloud,
  'Mail': Mail,
  'Calendar': Calendar,
  'Shield': Shield,
  'Zap': Zap,
  'Link2': Link2,
};

// Predefined integration templates
const predefinedTemplates = [
  { id: 'openai', name: 'OpenAI', icon: Bot, type: 'ai' },
  { id: 'anthropic', name: 'Anthropic Claude', icon: Bot, type: 'ai' },
  { id: 'slack', name: 'Slack', icon: MessageSquare, type: 'communication' },
  { id: 'gmail', name: 'Gmail', icon: Mail, type: 'communication' },
  { id: 'outlook', name: 'Microsoft Outlook', icon: Mail, type: 'communication' },
  { id: 'microsoft_teams', name: 'Microsoft Teams', icon: MessageSquare, type: 'communication' },
  { id: 'whatsapp', name: 'WhatsApp', icon: MessageSquare, type: 'communication' },
  { id: 'instagram', name: 'Instagram', icon: MessageSquare, type: 'communication' },
  { id: 'telegram', name: 'Telegram', icon: MessageSquare, type: 'communication' },
  { id: 'discord', name: 'Discord', icon: MessageSquare, type: 'communication' },
  { id: 'twilio', name: 'Twilio', icon: MessageSquare, type: 'communication' },
  { id: 'calendar', name: 'Google Calendar', icon: Calendar, type: 'communication' },
  { id: 'google_drive', name: 'Google Drive', icon: Cloud, type: 'storage' },
  { id: 'onedrive', name: 'OneDrive', icon: Cloud, type: 'storage' },
  { id: 'dropbox', name: 'Dropbox', icon: Cloud, type: 'storage' },
  { id: 'github', name: 'GitHub', icon: GitBranch, type: 'devops' },
  { id: 'jira', name: 'Jira', icon: GitBranch, type: 'devops' },
  { id: 'linear', name: 'Linear', icon: GitBranch, type: 'devops' },
  { id: 'trello', name: 'Trello', icon: GitBranch, type: 'devops' },
  { id: 'aws', name: 'AWS S3', icon: Cloud, type: 'storage' },
  { id: 'supabase', name: 'Supabase', icon: Database, type: 'storage' },
  { id: 'airtable', name: 'Airtable', icon: Database, type: 'storage' },
  { id: 'notion', name: 'Notion', icon: Globe, type: 'ai' },
  { id: 'hubspot', name: 'HubSpot', icon: BarChart3, type: 'analytics' },
  { id: 'stripe', name: 'Stripe', icon: BarChart3, type: 'analytics' },
  { id: 'shopify', name: 'Shopify', icon: Globe, type: 'analytics' },
  { id: 'webhook', name: 'Webhook', icon: Zap, type: 'devops' },
];

const INTEGRATION_DEFAULTS: Record<string, {
  endpoint: string;
  authLabel: string;
  placeholder: string;
  hint?: string;
  extraFields?: { key: string; label: string; placeholder: string }[];
}> = {
  gmail: {
    endpoint: 'https://gmail.googleapis.com/gmail/v1',
    authLabel: 'OAuth Credentials JSON',
    placeholder: '{"access_token": "...", "scope": "https://www.googleapis.com/auth/gmail.readonly"}',
    hint: 'Paste OAuth JSON from Google OAuth Playground. access_token works ~1 hour; add refresh_token for permanent access.',
  },
  slack: {
    endpoint: 'https://slack.com/api',
    authLabel: 'Bot Token',
    placeholder: 'xoxb-your-slack-bot-token',
    hint: 'Create a Slack app with channels:read, chat:write scopes. Use the Bot User OAuth Token (xoxb-...).',
  },
  github: {
    endpoint: 'https://api.github.com',
    authLabel: 'Personal Access Token',
    placeholder: 'ghp_your_github_personal_access_token',
    hint: 'GitHub → Settings → Developer settings → Personal access tokens. Needs repo scope for issues/repos.',
  },
  openai: {
    endpoint: 'https://api.openai.com/v1',
    authLabel: 'API Key',
    placeholder: 'sk-...',
  },
  anthropic: {
    endpoint: 'https://api.anthropic.com',
    authLabel: 'API Key',
    placeholder: 'sk-ant-...',
  },
  notion: {
    endpoint: 'https://api.notion.com/v1',
    authLabel: 'Integration Token',
    placeholder: 'secret_...',
    hint: 'Create an internal integration at notion.so/my-integrations and copy the secret token.',
  },
  jira: {
    endpoint: 'https://your-domain.atlassian.net',
    authLabel: 'API Token',
    placeholder: 'your-atlassian-api-token',
    hint: 'Atlassian account → Security → API tokens. Use your Atlassian email + token.',
    extraFields: [{ key: 'email', label: 'Atlassian Email', placeholder: 'you@company.com' }],
  },
  discord: {
    endpoint: 'https://discord.com/api/v10',
    authLabel: 'Bot Token',
    placeholder: 'your-discord-bot-token',
    hint: 'Discord Developer Portal → Bot → Token. Enable Message Content Intent if reading messages.',
    extraFields: [{ key: 'guild_id', label: 'Server (Guild) ID', placeholder: '123456789012345678' }],
  },
  aws: {
    endpoint: 'https://s3.amazonaws.com',
    authLabel: 'AWS Access Key ID',
    placeholder: 'AKIA...',
    hint: 'IAM user with S3 read permissions. Secret key and region below.',
    extraFields: [
      { key: 'secret_access_key', label: 'Secret Access Key', placeholder: 'wJalr...' },
      { key: 'region', label: 'Region', placeholder: 'us-east-1' },
    ],
  },
  telegram: {
    endpoint: 'https://api.telegram.org',
    authLabel: 'Bot Token',
    placeholder: '123456:ABC-DEF...',
    hint: 'Create a bot with @BotFather and paste the token here.',
  },
  whatsapp: {
    endpoint: 'https://graph.facebook.com/v21.0',
    authLabel: 'Meta Access Token',
    placeholder: 'EAAxxxx...',
    hint: 'Meta Developer → WhatsApp → API Setup. Use a permanent System User token in production.',
    extraFields: [
      { key: 'phone_number_id', label: 'Phone Number ID', placeholder: '123456789012345' },
    ],
  },
  instagram: {
    endpoint: 'https://graph.facebook.com/v21.0',
    authLabel: 'Meta Access Token',
    placeholder: 'EAAxxxx...',
    hint: 'Connect an Instagram Business/Creator account via a Meta app with instagram_basic + messaging permissions.',
    extraFields: [
      { key: 'ig_user_id', label: 'Instagram User ID', placeholder: '17841400000000000' },
    ],
  },
  google_drive: {
    endpoint: 'https://www.googleapis.com/drive/v3',
    authLabel: 'OAuth Credentials JSON',
    placeholder: '{"access_token": "...", "scope": "https://www.googleapis.com/auth/drive.readonly"}',
    hint: 'Google OAuth with Drive readonly (or full) scope. Paste access_token JSON.',
  },
  dropbox: {
    endpoint: 'https://api.dropboxapi.com/2',
    authLabel: 'Access Token',
    placeholder: 'sl.Bxxxx...',
    hint: 'Dropbox App Console → Generated access token (or OAuth token).',
  },
  outlook: {
    endpoint: 'https://graph.microsoft.com/v1.0',
    authLabel: 'Microsoft Graph Access Token',
    placeholder: 'eyJ0eXAiOiJKV1QiLCJub...',
    hint: 'Azure app with Mail.Read / Mail.Send delegated permissions. Paste Graph access_token.',
  },
  microsoft_teams: {
    endpoint: 'https://graph.microsoft.com/v1.0',
    authLabel: 'Microsoft Graph Access Token',
    placeholder: 'eyJ0eXAiOiJKV1QiLCJub...',
    hint: 'Azure app with Chat.Read / ChannelMessage.Send permissions.',
  },
  onedrive: {
    endpoint: 'https://graph.microsoft.com/v1.0',
    authLabel: 'Microsoft Graph Access Token',
    placeholder: 'eyJ0eXAiOiJKV1QiLCJub...',
    hint: 'Azure app with Files.Read permission for OneDrive.',
  },
  stripe: {
    endpoint: 'https://api.stripe.com/v1',
    authLabel: 'Secret Key',
    placeholder: 'sk_live_... or sk_test_...',
    hint: 'Stripe Dashboard → Developers → API keys. Use a restricted key in production when possible.',
  },
  supabase: {
    endpoint: 'https://YOUR_PROJECT.supabase.co',
    authLabel: 'Anon or Service Role Key',
    placeholder: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
    hint: 'Set your project URL as endpoint. Prefer anon key + RLS; service_role bypasses RLS.',
  },
  shopify: {
    endpoint: 'https://YOUR_SHOP.myshopify.com/admin/api/2024-10',
    authLabel: 'Admin API Access Token',
    placeholder: 'shpat_...',
    hint: 'Shopify Admin → Apps → Develop apps → API credentials. Or set shop domain below.',
    extraFields: [
      { key: 'shop_domain', label: 'Shop Domain', placeholder: 'my-store.myshopify.com' },
    ],
  },
  trello: {
    endpoint: 'https://api.trello.com/1',
    authLabel: 'API Key',
    placeholder: 'your-trello-api-key',
    hint: 'Get key + token from trello.com/app-key. Token is required below.',
    extraFields: [{ key: 'token', label: 'Trello Token', placeholder: 'your-trello-token' }],
  },
  linear: {
    endpoint: 'https://api.linear.app/graphql',
    authLabel: 'API Key',
    placeholder: 'lin_api_...',
    hint: 'Linear → Settings → API → Personal API keys.',
  },
  hubspot: {
    endpoint: 'https://api.hubapi.com',
    authLabel: 'Private App Token',
    placeholder: 'pat-na1-...',
    hint: 'HubSpot → Settings → Integrations → Private Apps. Needs CRM contacts scopes.',
  },
  twilio: {
    endpoint: 'https://api.twilio.com',
    authLabel: 'Auth Token',
    placeholder: 'your-auth-token',
    hint: 'Twilio Console → Account SID + Auth Token. Optional from_number for SMS.',
    extraFields: [
      { key: 'account_sid', label: 'Account SID', placeholder: 'ACxxxxxxxx' },
      { key: 'from_number', label: 'From Number (E.164)', placeholder: '+15551234567' },
    ],
  },
  airtable: {
    endpoint: 'https://api.airtable.com/v0',
    authLabel: 'Personal Access Token',
    placeholder: 'pat...',
    hint: 'Airtable → Developer hub → Personal access tokens. Optional default base ID.',
    extraFields: [{ key: 'base_id', label: 'Default Base ID', placeholder: 'appXXXXXXXX' }],
  },
  calendar: {
    endpoint: 'https://www.googleapis.com/calendar/v3',
    authLabel: 'OAuth Credentials JSON',
    placeholder: '{"access_token": "...", "scope": "https://www.googleapis.com/auth/calendar"}',
    hint: 'Google OAuth with Calendar scope. Paste access_token JSON (add refresh_token for lasting access).',
  },
  webhook: {
    endpoint: 'https://example.com/webhook',
    authLabel: 'Optional Bearer Token',
    placeholder: 'leave blank if none',
    hint: 'Set the webhook URL as the endpoint. Token is optional Authorization header.',
  },
};

export default function IntegrationsPage() {
  const [integrations, setIntegrations] = React.useState<IntegrationUI[]>([]);
  const [apiTemplates, setApiTemplates] = React.useState<IntegrationTemplate[]>([]);
  const [isLoading, setIsLoading] = React.useState(true);
  
  const [searchQuery, setSearchQuery] = useState('');
  const [category, setCategory] = useState('all');
  const [showConnectDialog, setShowConnectDialog] = useState(false);
  const [selectedIntegration, setSelectedIntegration] = useState<IntegrationUI | null>(null);
  
  // New Integration Form State
  const [newIntegrationType, setNewIntegrationType] = useState('');
  const [newIntegrationKey, setNewIntegrationKey] = useState('');
  const [newIntegrationName, setNewIntegrationName] = useState('');
  const [newIntegrationEndpoint, setNewIntegrationEndpoint] = useState('');
  const [newIntegrationExtra, setNewIntegrationExtra] = useState<Record<string, string>>({});
  const [isCreating, setIsCreating] = useState(false);
  
  const [showApiKey, setShowApiKey] = useState(false);
  const [activityLogs, setActivityLogs] = React.useState<ActivityLogUI[]>([]);
  const [testingId, setTestingId] = React.useState<string | null>(null);

  const loadIntegrations = async () => {
    setIsLoading(true);
    try {
      const [integrationsRes, templatesRes, activityRes] = await Promise.all([
        apiClient.getAPIIntegrations(),
        apiClient.getIntegrationTemplates(),
        apiClient.getIntegrationActivity().catch(() => ({ results: [] })),
      ]);
      
      const integrationList = integrationListFromResponse(
        integrationsRes as unknown as Parameters<typeof integrationListFromResponse>[0],
      );
      const mappedIntegrations: IntegrationUI[] = integrationList.map((item) => {
        const templateId = item.description || item.name?.toLowerCase() || '';
        let matchedIcon = Globe;
        if (templateId.includes('gmail') || templateId.includes('mail') || templateId.includes('outlook')) matchedIcon = Mail;
        else if (templateId.includes('open') || templateId.includes('anthropic') || templateId.includes('ai')) matchedIcon = Bot;
        else if (templateId.includes('telegram') || templateId.includes('slack') || templateId.includes('discord') || templateId.includes('twilio') || templateId.includes('whatsapp') || templateId.includes('instagram') || templateId.includes('insta') || templateId.includes('teams')) matchedIcon = MessageSquare;
        else if (templateId.includes('github') || templateId.includes('jira') || templateId.includes('linear') || templateId.includes('trello')) matchedIcon = GitBranch;
        else if (templateId.includes('notion') || templateId.includes('webhook') || templateId.includes('shopify')) matchedIcon = templateId.includes('webhook') ? Zap : Globe;
        else if (templateId.includes('aws') || templateId.includes('s3') || templateId.includes('cloud') || templateId.includes('drive') || templateId.includes('dropbox') || templateId.includes('onedrive')) matchedIcon = Cloud;
        else if (templateId.includes('airtable') || templateId.includes('supabase')) matchedIcon = Database;
        else if (templateId.includes('hubspot') || templateId.includes('analytic') || templateId.includes('stripe')) matchedIcon = BarChart3;
        else if (templateId.includes('calendar')) matchedIcon = Calendar;
        
        return {
          ...item,
          icon: matchedIcon,
          category: item.category || 'ai',
          status: item.status === 'active' ? 'connected' : (item.status || 'disconnected'),
          lastSync: item.last_sync || 'Just now'
        };
      });
      setIntegrations(mappedIntegrations);
      
      const templatesData = templatesRes as unknown as { results?: IntegrationTemplate[]; templates?: IntegrationTemplate[] };
      const dbTemplates = paginatedItems(templatesData).concat(templatesData.templates ?? []);
      setApiTemplates(dbTemplates.length > 0 ? dbTemplates : predefinedTemplates.map(t => ({
        id: t.id,
        name: t.name,
        description: `${t.type} integration`,
        provider: t.id,
        config_template: { provider_key: t.id, auth_type: t.id === 'gmail' ? 'oauth' : 'api_key' },
      })));
      setActivityLogs(((activityRes.results as ActivityLogRecord[]) || []).map((log) => ({
        integration: log.integration,
        event: log.request_data?.tool || 'API call',
        status: log.status === 'success' ? 'success' : 'failed',
        time: new Date(log.timestamp).toLocaleString(),
        details: log.error_message || JSON.stringify(log.response_data || {}).slice(0, 80),
        integrationName:
          log.integration_name ||
          mappedIntegrations.find((i) => i.id === log.integration)?.name ||
          'Integration',
      })));
    } catch (error) {
      console.error('Failed to load integrations:', error);
    } finally {
      setIsLoading(false);
    }
  };

  React.useEffect(() => {
    setTimeout(() => { loadIntegrations(); }, 0)
  }, []);

  const filteredIntegrations = integrations.filter(integration => {
    const matchesSearch = integration.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (integration.description || '').toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = category === 'all' || integration.category === category;
    return matchesSearch && matchesCategory;
  });

  const totalApiCalls = integrations.reduce((sum, i) => sum + (i.total_calls || 0), 0);

  const stats = [
    { label: 'Total Integrations', value: integrations.length, icon: Plug, color: 'text-primary' },
    { label: 'Connected', value: integrations.filter(i => i.status === 'connected').length, icon: CheckCircle2, color: 'text-green-500' },
    { label: 'Errors', value: integrations.filter(i => i.status === 'error').length, icon: XCircle, color: 'text-red-500' },
    { label: 'Total API Calls', value: totalApiCalls.toLocaleString(), icon: Activity, color: 'text-blue-500' },
  ];

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'connected':
        return <Badge className="bg-green-500/10 text-green-500 border-green-500/20">Connected</Badge>;
      case 'disconnected':
        return <Badge variant="secondary">Disconnected</Badge>;
      case 'error':
        return <Badge className="bg-red-500/10 text-red-500 border-red-500/20">Error</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const handleTestIntegration = async (id: string) => {
    setTestingId(id);
    try {
      const res = await apiClient.testAPIIntegration(id);
      await loadIntegrations();
      toast({
        title: res.success ? 'Connection successful' : 'Test failed',
        description: res.message || res.error || undefined,
        variant: res.success ? 'default' : 'destructive',
      });
    } catch (error: unknown) {
      toast({ title: 'Connection test failed', description: errorMessage(error), variant: 'destructive' });
    } finally {
      setTestingId(null);
    }
  };

  const handleDeleteIntegration = async (id: string) => {
    try {
      await apiClient.deleteAPIIntegration(id);
      setIntegrations(prev => prev.filter(i => i.id !== id));
      toast({ title: 'Integration removed' });
    } catch (error: unknown) {
      toast({ title: 'Failed to delete integration', description: errorMessage(error), variant: 'destructive' });
    }
  };

  const resetConnectForm = () => {
    setNewIntegrationType('');
    setNewIntegrationKey('');
    setNewIntegrationName('');
    setNewIntegrationEndpoint('');
    setNewIntegrationExtra({});
  };

  const canConnect = () => {
    if (!newIntegrationType) return false;
    if (newIntegrationType === 'webhook') {
      return Boolean(newIntegrationEndpoint || INTEGRATION_DEFAULTS.webhook?.endpoint);
    }
    if (!newIntegrationKey) return false;
    if (newIntegrationType === 'jira' && !newIntegrationExtra.email) return false;
    if (newIntegrationType === 'discord' && !newIntegrationExtra.guild_id) return false;
    if (newIntegrationType === 'aws' && !newIntegrationExtra.secret_access_key) return false;
    if (newIntegrationType === 'trello' && !newIntegrationExtra.token) return false;
    if (newIntegrationType === 'twilio' && !newIntegrationExtra.account_sid) return false;
    if (newIntegrationType === 'whatsapp' && !newIntegrationExtra.phone_number_id) return false;
    if (newIntegrationType === 'instagram' && !newIntegrationExtra.ig_user_id) return false;
    if (newIntegrationType === 'shopify') {
      const endpoint = newIntegrationEndpoint || '';
      if (!newIntegrationExtra.shop_domain && !endpoint.includes('myshopify.com')) return false;
    }
    if (newIntegrationType === 'supabase') {
      const endpoint = newIntegrationEndpoint || '';
      if (!endpoint || endpoint.includes('YOUR_PROJECT')) return false;
    }
    return true;
  };

  return (
    <AppLayout>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-6"
      >
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-3">
              <Plug className="h-8 w-8 text-primary" />
              API Integrations
            </h1>
            <p className="text-muted-foreground mt-1">
              Connect your agents to external services and APIs
            </p>
          </div>
          <Button onClick={() => {
            resetConnectForm();
            setShowConnectDialog(true);
          }} className="gap-2">
            <Plus className="h-4 w-4" />
            Add Integration
          </Button>
        </div>

        {/* Stats */}
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
                    <div className={cn("p-2 rounded-lg bg-muted/50", stat.color)}>
                      <stat.icon className="h-5 w-5" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>

        <Tabs defaultValue="integrations" className="space-y-6">
          <TabsList>
            <TabsTrigger value="integrations">Integrations</TabsTrigger>
            <TabsTrigger value="templates">API Templates</TabsTrigger>
            <TabsTrigger value="logs">Activity Logs</TabsTrigger>
          </TabsList>

          {/* Integrations Tab */}
          <TabsContent value="integrations" className="space-y-4">
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="relative flex-1 max-w-md">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search integrations..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
              <Select value={category} onValueChange={setCategory}>
                <SelectTrigger className="w-full sm:w-48">
                  <SelectValue placeholder="Category" />
                </SelectTrigger>
                <SelectContent>
                  {categories.map(cat => (
                    <SelectItem key={cat.id} value={cat.id}>
                      <div className="flex items-center gap-2">
                        <cat.icon className="h-4 w-4" />
                        {cat.label}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {isLoading ? (
                <p className="text-sm text-muted-foreground col-span-full text-center py-12">Loading integrations...</p>
              ) : (
              <AnimatePresence mode="popLayout">
                {filteredIntegrations.map((integration, index) => (
                  <motion.div
                    key={integration.id}
                    layout
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    transition={{ delay: index * 0.05 }}
                  >
                    <Card className={cn(
                      "hover:shadow-lg transition-all cursor-pointer group",
                      integration.status === 'connected' && "border-green-500/20",
                      integration.status === 'error' && "border-red-500/20"
                    )}>
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between mb-4">
                          <div className={cn(
                            "flex h-12 w-12 items-center justify-center rounded-xl transition-transform group-hover:scale-110",
                            integration.status === 'connected' && "bg-green-500/10",
                            integration.status === 'disconnected' && "bg-muted",
                            integration.status === 'error' && "bg-red-500/10"
                          )}>
                            <integration.icon className={cn(
                              "h-6 w-6",
                              integration.status === 'connected' && "text-green-500",
                              integration.status === 'disconnected' && "text-muted-foreground",
                              integration.status === 'error' && "text-red-500"
                            )} />
                          </div>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="icon" className="h-8 w-8">
                                <MoreVertical className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem onClick={() => setSelectedIntegration(integration)}>
                                <Settings className="h-4 w-4 mr-2" />
                                Configure
                              </DropdownMenuItem>
                              <DropdownMenuItem onClick={() => handleTestIntegration(integration.id)} disabled={testingId === integration.id}>
                                <TestTube className="h-4 w-4 mr-2" />
                                {testingId === integration.id ? 'Testing...' : 'Test Connection'}
                              </DropdownMenuItem>
                              <DropdownMenuItem onClick={() => loadIntegrations()}>
                                <RefreshCw className="h-4 w-4 mr-2" />
                                Refresh
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem className="text-destructive" onClick={() => handleDeleteIntegration(integration.id)}>
                                <Unlink className="h-4 w-4 mr-2" />
                                Disconnect
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </div>

                        <div className="space-y-2">
                          <div className="flex items-center gap-2">
                            <h3 className="font-semibold">{integration.name}</h3>
                            {getStatusBadge(integration.status)}
                          </div>
                          <p className="text-sm text-muted-foreground line-clamp-2">
                            {integration.description}
                          </p>
                        </div>

                        {integration.error && (
                          <div className="flex items-center gap-2 mt-3 text-sm text-red-500">
                            <XCircle className="h-4 w-4" />
                            {integration.error}
                          </div>
                        )}

                        {integration.usage && integration.status === 'connected' && (
                          <div className="mt-4 space-y-2">
                            <div className="flex justify-between text-xs">
                              <span className="text-muted-foreground">Usage</span>
                              <span>
                                {typeof integration.usage === 'object' && 'requests' in integration.usage && integration.usage.requests !== undefined &&
                                  `${(integration.usage.requests / 1000).toFixed(1)}k / ${(integration.usage.limit / 1000).toFixed(0)}k`
                                }
                                {typeof integration.usage === 'object' && 'messages' in integration.usage && integration.usage.messages !== undefined &&
                                  `${integration.usage.messages.toLocaleString()} / ${integration.usage.limit.toLocaleString()}`
                                }
                                {typeof integration.usage === 'object' && 'events' in integration.usage && integration.usage.events !== undefined &&
                                  `${(integration.usage.events / 1000).toFixed(0)}k / ${(integration.usage.limit / 1000).toFixed(0)}k`
                                }
                                {typeof integration.usage === 'object' && 'storage' in integration.usage && integration.usage.storage !== undefined &&
                                  `${integration.usage.storage}GB / ${integration.usage.limit}GB`
                                }
                              </span>
                            </div>
                            <Progress 
                              value={
                                typeof integration.usage === 'object' && 'requests' in integration.usage && integration.usage.requests !== undefined
                                  ? (integration.usage.requests / integration.usage.limit) * 100
                                  : typeof integration.usage === 'object' && 'messages' in integration.usage && integration.usage.messages !== undefined
                                  ? (integration.usage.messages / integration.usage.limit) * 100
                                  : typeof integration.usage === 'object' && 'events' in integration.usage && integration.usage.events !== undefined
                                  ? (integration.usage.events / integration.usage.limit) * 100
                                  : typeof integration.usage === 'object' && 'storage' in integration.usage && integration.usage.storage !== undefined
                                  ? (integration.usage.storage / integration.usage.limit) * 100
                                  : 0
                              } 
                              className="h-1.5" 
                            />
                          </div>
                        )}

                        {integration.lastSync && (
                          <div className="flex items-center gap-2 mt-3 text-xs text-muted-foreground">
                            <Clock className="h-3 w-3" />
                            Last sync: {integration.lastSync}
                          </div>
                        )}
                      </CardContent>
                      <CardFooter className="p-4 pt-0">
                        <div className="flex w-full gap-2">
                          {integration.status === 'disconnected' ? (
                            <Button className="flex-1" variant="outline" onClick={() => {
                              setNewIntegrationType(integration.description || integration.type || '');
                              setShowConnectDialog(true);
                            }}>
                              Connect
                            </Button>
                          ) : integration.status === 'error' ? (
                            <Button className="flex-1" variant="outline" onClick={() => setSelectedIntegration(integration)}>
                              Reconnect
                            </Button>
                          ) : (
                            <Button className="flex-1" variant="outline" onClick={() => setSelectedIntegration(integration)}>
                              Sync Now
                            </Button>
                          )}
                          <Button 
                            variant="outline" 
                            className="px-3 border-destructive/20 text-destructive hover:bg-destructive/10 hover:text-destructive"
                            onClick={() => handleDeleteIntegration(integration.id)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </CardFooter>
                    </Card>
                  </motion.div>
                ))}
              </AnimatePresence>
              )}
            </div>
          </TabsContent>

          {/* API Templates Tab */}
          <TabsContent value="templates" className="space-y-6">
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {apiTemplates.map((template, index) => {
                const providerKey = template.provider || template.config_template?.provider_key || '';
                const iconKey = typeof template.icon === 'string' ? template.icon : providerKey;
                const IconComp = (typeof template.icon === 'function' ? template.icon : iconMap[iconKey]) || (
                  providerKey.includes('gmail') ? Mail :
                  providerKey.includes('slack') ? MessageSquare :
                  providerKey.includes('github') ? GitBranch :
                  providerKey.includes('openai') || providerKey.includes('anthropic') ? Bot :
                  Globe
                );
                return (
                <motion.div
                  key={template.id || index}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <Card
                    className="hover:shadow-lg transition-all cursor-pointer group hover:border-primary/50"
                    onClick={() => {
                      setNewIntegrationType(providerKey || template.id);
                      setShowConnectDialog(true);
                    }}
                  >
                    <CardContent className="p-6 text-center">
                      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 mx-auto mb-4 transition-transform group-hover:scale-110">
                        {typeof IconComp === 'function' ? <IconComp className="h-7 w-7 text-primary" /> : <Globe className="h-7 w-7 text-primary" />}
                      </div>
                      <h3 className="font-semibold mb-1">{template.name}</h3>
                      <p className="text-sm text-muted-foreground">{template.description}</p>
                      {template.config_template?.tools && (
                        <p className="text-xs text-muted-foreground mt-2">
                          {(template.config_template?.tools ?? []).length} tools • {(template.config_template?.sub_agents ?? []).length || 3} sub-agents
                        </p>
                      )}
                    </CardContent>
                  </Card>
                </motion.div>
              );})}
            </div>
          </TabsContent>

          {/* Activity Logs Tab */}
          <TabsContent value="logs" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
                <CardDescription>API calls and integration events</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {activityLogs.length === 0 ? (
                    <p className="text-sm text-muted-foreground text-center py-8">
                      No API activity yet. Connect an integration and use it from chat.
                    </p>
                  ) : activityLogs.map((log, index) => (
                    <div key={index} className="flex items-center gap-4 p-3 rounded-lg bg-muted/50">
                      {log.status === 'success' ? (
                        <CheckCircle2 className="h-5 w-5 text-green-500" />
                      ) : (
                        <XCircle className="h-5 w-5 text-red-500" />
                      )}
                      <div className="flex-1">
                        <p className="font-medium">{log.integrationName || log.integration}</p>
                        <p className="text-sm text-muted-foreground">
                          {log.event} • {log.details}
                        </p>
                      </div>
                      <span className="text-sm text-muted-foreground">{log.time}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Add Integration Dialog */}
        <Dialog open={showConnectDialog} onOpenChange={setShowConnectDialog}>
          <DialogContent className="max-w-xl">
            <DialogHeader>
              <DialogTitle>Add Integration</DialogTitle>
              <DialogDescription>
                Connect a new service to your agent platform
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Select Integration</Label>
                <Select value={newIntegrationType} onValueChange={(v) => {
                  setNewIntegrationType(v);
                  const defaults = INTEGRATION_DEFAULTS[v];
                  setNewIntegrationEndpoint(defaults?.endpoint || '');
                  setNewIntegrationExtra({});
                  setNewIntegrationKey('');
                }}>
                  <SelectTrigger>
                    <SelectValue placeholder="Choose an integration" />
                  </SelectTrigger>
                  <SelectContent>
                    {predefinedTemplates.map(template => (
                      <SelectItem key={template.id} value={template.id}>
                        <div className="flex items-center gap-2">
                          <template.icon className="h-4 w-4" />
                          {template.name}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              {newIntegrationType && INTEGRATION_DEFAULTS[newIntegrationType] && (
                <div className="space-y-2">
                  <Label htmlFor="endpoint">Endpoint</Label>
                  <Input
                    id="endpoint"
                    placeholder={INTEGRATION_DEFAULTS[newIntegrationType].endpoint}
                    value={newIntegrationEndpoint}
                    onChange={(e) => setNewIntegrationEndpoint(e.target.value)}
                  />
                </div>
              )}
              {newIntegrationType && INTEGRATION_DEFAULTS[newIntegrationType]?.extraFields?.map((field) => (
                <div key={field.key} className="space-y-2">
                  <Label htmlFor={field.key}>{field.label}</Label>
                  <Input
                    id={field.key}
                    type={field.key.includes('secret') || field.key.includes('token') ? (showApiKey ? 'text' : 'password') : 'text'}
                    placeholder={field.placeholder}
                    value={newIntegrationExtra[field.key] || ''}
                    onChange={(e) => setNewIntegrationExtra((prev) => ({ ...prev, [field.key]: e.target.value }))}
                  />
                </div>
              ))}
              <div className="space-y-2">
                <Label htmlFor="apiKey">
                  {INTEGRATION_DEFAULTS[newIntegrationType]?.authLabel || (newIntegrationType === 'gmail' ? 'OAuth Credentials JSON' : 'API Key')}
                </Label>
                <div className="relative">
                  <Input
                    id="apiKey"
                    type={showApiKey ? 'text' : 'password'}
                    placeholder={
                      INTEGRATION_DEFAULTS[newIntegrationType]?.placeholder ||
                      (newIntegrationType === 'gmail'
                        ? '{"access_token": "...", "scope": "https://www.googleapis.com/auth/gmail.readonly"}'
                        : 'sk-...')
                    }
                    value={newIntegrationKey}
                    onChange={(e) => setNewIntegrationKey(e.target.value)}
                  />
                  <Button
                    variant="ghost"
                    size="icon"
                    className="absolute right-2 top-1/2 -translate-y-1/2 h-6 w-6"
                    onClick={() => setShowApiKey(!showApiKey)}
                  >
                    {showApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </Button>
                </div>
                {INTEGRATION_DEFAULTS[newIntegrationType]?.hint && (
                  <p className="text-xs text-muted-foreground">
                    {INTEGRATION_DEFAULTS[newIntegrationType].hint}
                  </p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="name">Connection Name (optional)</Label>
                <Input 
                  id="name" 
                  placeholder="My API Connection" 
                  value={newIntegrationName}
                  onChange={(e) => setNewIntegrationName(e.target.value)}
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowConnectDialog(false)} disabled={isCreating}>
                Cancel
              </Button>
              <Button 
                className="gap-2" 
                disabled={!canConnect() || isCreating}
                onClick={async () => {
                  setIsCreating(true);
                  try {
                    const template = predefinedTemplates.find(t => t.id === newIntegrationType);
                    const defaults = INTEGRATION_DEFAULTS[newIntegrationType];
                    let authentication: Record<string, string> = { api_key: newIntegrationKey };
                    if (newIntegrationType === 'jira') {
                      authentication = { email: newIntegrationExtra.email || '', api_key: newIntegrationKey };
                    } else if (newIntegrationType === 'discord') {
                      authentication = { api_key: newIntegrationKey, guild_id: newIntegrationExtra.guild_id || '' };
                    } else if (newIntegrationType === 'aws') {
                      authentication = {
                        access_key_id: newIntegrationKey,
                        secret_access_key: newIntegrationExtra.secret_access_key || '',
                        region: newIntegrationExtra.region || 'us-east-1',
                      };
                    } else if (newIntegrationType === 'trello') {
                      authentication = { api_key: newIntegrationKey, token: newIntegrationExtra.token || '' };
                    } else if (newIntegrationType === 'twilio') {
                      authentication = {
                        auth_token: newIntegrationKey,
                        account_sid: newIntegrationExtra.account_sid || '',
                        from_number: newIntegrationExtra.from_number || '',
                      };
                    } else if (newIntegrationType === 'whatsapp') {
                      authentication = {
                        access_token: newIntegrationKey,
                        phone_number_id: newIntegrationExtra.phone_number_id || '',
                      };
                    } else if (newIntegrationType === 'instagram') {
                      authentication = {
                        access_token: newIntegrationKey,
                        ig_user_id: newIntegrationExtra.ig_user_id || '',
                      };
                    } else if (newIntegrationType === 'shopify') {
                      authentication = {
                        api_key: newIntegrationKey,
                        shop_domain: newIntegrationExtra.shop_domain || '',
                      };
                    } else if (
                      ['gmail', 'calendar', 'google_drive', 'outlook', 'microsoft_teams', 'onedrive'].includes(newIntegrationType) &&
                      newIntegrationKey.trim().startsWith('{')
                    ) {
                      try { authentication = JSON.parse(newIntegrationKey); } catch { /* keep api_key */ }
                    } else if (
                      ['outlook', 'microsoft_teams', 'onedrive', 'google_drive'].includes(newIntegrationType) &&
                      !newIntegrationKey.trim().startsWith('{')
                    ) {
                      authentication = { access_token: newIntegrationKey };
                    } else if (newIntegrationType === 'airtable') {
                      authentication = {
                        api_key: newIntegrationKey,
                        base_id: newIntegrationExtra.base_id || '',
                      };
                    } else if (newIntegrationType === 'webhook' && !newIntegrationKey.trim()) {
                      authentication = {};
                    }
                    const categoryMap: Record<string, string> = {
                      ai: 'AI/ML',
                      communication: 'Social',
                      devops: 'Cloud',
                      analytics: 'Analytics',
                      storage: 'Cloud',
                    };
                    const descriptionMap: Record<string, string> = {
                      aws: 'aws s3',
                      webhook: 'webhook',
                      google_drive: 'google drive',
                      microsoft_teams: 'microsoft teams',
                      onedrive: 'onedrive',
                      stripe: 'stripe',
                      supabase: 'supabase',
                      shopify: 'shopify',
                      outlook: 'outlook',
                      dropbox: 'dropbox',
                    };
                    await apiClient.createAPIIntegration({
                      name: newIntegrationName || template?.name || 'New Integration',
                      type: newIntegrationType === 'webhook' ? 'Webhook' : 'REST',
                      category: categoryMap[template?.type || ''] || 'Other',
                      endpoint: newIntegrationEndpoint || defaults?.endpoint || 'https://api.example.com',
                      description: descriptionMap[newIntegrationType] || newIntegrationType,
                      authentication,
                      status: 'active',
                    });
                    setShowConnectDialog(false);
                    resetConnectForm();
                    await loadIntegrations();
                    toast({ title: 'Integration connected', description: `${template?.name || 'Service'} is ready to use.` });
                  } catch (error: unknown) {
                    toast({ title: 'Failed to connect', description: axiosErrorDetail(error) || errorMessage(error), variant: 'destructive' });
                  } finally {
                    setIsCreating(false);
                  }
                }}
              >
                {isCreating ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Link2 className="h-4 w-4" />}
                Connect
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Configure Integration Dialog */}
        <Dialog open={!!selectedIntegration} onOpenChange={() => setSelectedIntegration(null)}>
          <DialogContent className="max-w-xl">
            {selectedIntegration && (
              <>
                <DialogHeader>
                  <DialogTitle className="flex items-center gap-2">
                    <selectedIntegration.icon className="h-5 w-5" />
                    {selectedIntegration.name} Settings
                  </DialogTitle>
                  <DialogDescription>
                    Configure your {selectedIntegration.name} integration
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 rounded-lg bg-muted/50">
                    <div>
                      <p className="font-medium">Connection Status</p>
                      <p className="text-sm text-muted-foreground">
                        {selectedIntegration.lastSync ? `Last synced ${selectedIntegration.lastSync}` : 'Not connected'}
                      </p>
                    </div>
                    {getStatusBadge(selectedIntegration.status)}
                  </div>
                  {selectedIntegration.apiKey && (
                    <div className="space-y-2">
                      <Label>API Key</Label>
                      <div className="flex items-center gap-2">
                        <Input
                          type={showApiKey ? 'text' : 'password'}
                          value={selectedIntegration.apiKey}
                          readOnly
                          className="font-mono"
                        />
                        <Button variant="outline" size="icon" onClick={() => setShowApiKey(!showApiKey)}>
                          {showApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        </Button>
                        <Button variant="outline" size="icon">
                          <Copy className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  )}
                  <Separator />
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Auto-sync</p>
                      <p className="text-sm text-muted-foreground">Automatically sync data</p>
                    </div>
                    <Switch defaultChecked />
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setSelectedIntegration(null)}>
                    Close
                  </Button>
                  <Button>Save Changes</Button>
                </DialogFooter>
              </>
            )}
          </DialogContent>
        </Dialog>
      </motion.div>
    </AppLayout>
  );
}
