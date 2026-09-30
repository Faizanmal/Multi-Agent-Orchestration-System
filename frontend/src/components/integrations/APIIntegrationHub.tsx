"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Separator } from '@/components/ui/separator';
import { 
  Globe, 
  Plus, 
  Settings, 
  Play, 
  Trash2, 
  CheckCircle, 
  XCircle, 
  AlertCircle,
  Zap,
  Database,
  Cloud,
  Monitor,
  BarChart3,
  Clock,
  Activity,
  Shield,
  Link,
  Search,
  RefreshCw
} from 'lucide-react';

interface APIIntegration {
  id: string;
  name: string;
  description: string;
  type: 'REST' | 'GraphQL' | 'WebSocket' | 'Webhook';
  category: 'Database' | 'Cloud' | 'Payment' | 'Analytics' | 'Social' | 'AI/ML' | 'Other';
  endpoint: string;
  method: string;
  headers: Record<string, string>;
  authentication: {
    type: 'none' | 'api_key' | 'bearer' | 'basic' | 'oauth2';
    credentials: Record<string, string>;
  };
  parameters: Array<{
    name: string;
    type: string;
    required: boolean;
    description: string;
    default?: string;
  }>;
  rate_limit: {
    enabled: boolean;
    requests_per_minute: number;
    burst_limit: number;
  };
  retry_policy: {
    enabled: boolean;
    max_retries: number;
    backoff_strategy: 'linear' | 'exponential';
  };
  timeout: number;
  status: 'active' | 'inactive' | 'error';
  last_tested: string;
  success_rate: number;
  total_calls: number;
  avg_response_time: number;
  created_at: string;
  updated_at: string;
}

interface APICallResult {
  id: string;
  integration_id: string;
  status: 'success' | 'error' | 'timeout';
  response_data: unknown;
  response_time: number;
  error_message?: string;
  timestamp: string;
}

interface APITemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  provider: string;
  tags: string[];
  popularity: number;
  config_template: Partial<APIIntegration>;
}

export const APIIntegrationHub: React.FC = () => {
  const [integrations, setIntegrations] = useState<APIIntegration[]>([]);
  const [templates, setTemplates] = useState<APITemplate[]>([]);
  const [callHistory, setCallHistory] = useState<APICallResult[]>([]);
  const [selectedIntegration, setSelectedIntegration] = useState<APIIntegration | null>(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [isLoading, setIsLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [error, setError] = useState<string | null>(null);
  const loadIntegrations = async () => {
    try {
      setIsLoading(true);
      const response = await fetch('/api/integrations/');
      if (response.ok) {
        const data = await response.json();
        setIntegrations(data);
      }
    } catch (err) {
      console.error('Failed to load integrations:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const loadTemplates = async () => {
    try {
      const response = await fetch('/api/integrations/templates/');
      if (response.ok) {
        const data = await response.json();
        setTemplates(data);
      }
    } catch (error) {
      console.error('Failed to load templates:', error);
    }
  };

  const loadCallHistory = async () => {
    try {
      const response = await fetch('/api/integrations/calls/');
      if (response.ok) {
        const data = await response.json();
        setCallHistory(data);
      }
    } catch (error) {
      console.error('Failed to load call history:', error);
    }
  };

  const testIntegration = async (integration: APIIntegration) => {
    try {
      setIsLoading(true);
      const response = await fetch(`/api/integrations/${integration.id}/test/`, {
        method: 'POST',
      });
      
      if (response.ok) {
        const result = await response.json();
        // Update integration status
        setIntegrations(prev => 
          prev.map(int => 
            int.id === integration.id 
              ? { ...int, status: result.success ? 'active' : 'error', last_tested: new Date().toISOString() }
              : int
          )
        );
      }
    } catch (err) {
      console.error('Test failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const createFromTemplate = async (template: APITemplate) => {
    try {
      const newIntegration = {
        ...template.config_template,
        name: `${template.name} Integration`,
        description: template.description
      };
      
      const response = await fetch('/api/integrations/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newIntegration)
      });

      if (response.ok) {
        const created = await response.json();
        setIntegrations(prev => [...prev, created]);
        setSelectedIntegration(created);
        setActiveTab('configure');
      }
    } catch (error) {
      console.error('Failed to create integration:', error);
    }
  };

  const deleteIntegration = async (id: string) => {
    if (!confirm('Are you sure you want to delete this integration?')) return;

    try {
      const response = await fetch(`/api/integrations/${id}/`, {
        method: 'DELETE'
      });

      if (response.ok) {
        setIntegrations(prev => prev.filter(int => int.id !== id));
        if (selectedIntegration?.id === id) {
          setSelectedIntegration(null);
        }
      }
    } catch (err) {
      console.error('Failed to delete integration:', err);
      setError('Failed to delete integration');
    }
  };

  const filteredIntegrations = integrations.filter(integration => {
    const matchesSearch = integration.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         integration.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = categoryFilter === 'all' || integration.category === categoryFilter;
    const matchesStatus = statusFilter === 'all' || integration.status === statusFilter;
    
    return matchesSearch && matchesCategory && matchesStatus;
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'error': return <XCircle className="w-4 h-4 text-red-500" />;
      case 'inactive': return <AlertCircle className="w-4 h-4 text-yellow-500" />;
      default: return <AlertCircle className="w-4 h-4 text-gray-500" />;
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'Database': return <Database className="w-4 h-4" />;
      case 'Cloud': return <Cloud className="w-4 h-4" />;
      case 'Analytics': return <BarChart3 className="w-4 h-4" />;
      case 'AI/ML': return <Zap className="w-4 h-4" />;
      default: return <Globe className="w-4 h-4" />;
    }
  };
    useEffect(() => {
        setTimeout(() => {
          loadIntegrations();
          loadTemplates();
          loadCallHistory();
        }, 0);
      }, []);

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            API Integration Hub
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Connect your workflows with external APIs and services
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => setActiveTab('templates')} variant="outline">
            <Plus className="w-4 h-4 mr-2" />
            Add Integration
          </Button>
          <Button onClick={loadIntegrations} variant="outline" size="sm">
            <RefreshCw className="w-4 h-4" />
          </Button>
        </div>
      </div>
      {error && (
        <div className="p-2 text-sm text-red-600">{error}</div>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview" className="flex items-center gap-2">
            <Activity className="w-4 h-4" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="integrations" className="flex items-center gap-2">
            <Link className="w-4 h-4" />
            Integrations
          </TabsTrigger>
          <TabsTrigger value="templates" className="flex items-center gap-2">
            <Globe className="w-4 h-4" />
            Templates
          </TabsTrigger>
          <TabsTrigger value="configure" className="flex items-center gap-2">
            <Settings className="w-4 h-4" />
            Configure
          </TabsTrigger>
          <TabsTrigger value="monitoring" className="flex items-center gap-2">
            <Monitor className="w-4 h-4" />
            Monitoring
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                      Total Integrations
                    </p>
                    <p className="text-2xl font-bold">{integrations.length}</p>
                  </div>
                  <Link className="w-8 h-8 text-blue-500" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                      Active APIs
                    </p>
                    <p className="text-2xl font-bold text-green-600">
                      {integrations.filter(i => i.status === 'active').length}
                    </p>
                  </div>
                  <CheckCircle className="w-8 h-8 text-green-500" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                      Total API Calls
                    </p>
                    <p className="text-2xl font-bold">
                      {integrations.reduce((sum, int) => sum + int.total_calls, 0).toLocaleString()}
                    </p>
                  </div>
                  <Activity className="w-8 h-8 text-purple-500" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                      Avg Response Time
                    </p>
                    <p className="text-2xl font-bold">
                      {integrations.length > 0 ? Math.round(
                        integrations.reduce((sum, int) => sum + int.avg_response_time, 0) / integrations.length
                      ) : 0}ms
                    </p>
                  </div>
                  <Clock className="w-8 h-8 text-orange-500" />
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="w-5 h-5" />
                Recent API Activity
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {callHistory.slice(0, 5).map((call) => {
                  const integration = integrations.find(i => i.id === call.integration_id);
                  return (
                    <div key={call.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                      <div className="flex items-center gap-3">
                        {getStatusIcon(call.status)}
                        <div>
                          <p className="font-medium">{integration?.name || 'Unknown'}</p>
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            {new Date(call.timestamp).toLocaleString()}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <Badge variant={call.status === 'success' ? 'default' : 'destructive'}>
                          {call.status}
                        </Badge>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                          {call.response_time}ms
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="integrations" className="space-y-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                <Input
                  placeholder="Search integrations..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
              <SelectTrigger className="w-full md:w-48">
                <SelectValue placeholder="Filter by category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                <SelectItem value="Database">Database</SelectItem>
                <SelectItem value="Cloud">Cloud</SelectItem>
                <SelectItem value="Analytics">Analytics</SelectItem>
                <SelectItem value="AI/ML">AI/ML</SelectItem>
                <SelectItem value="Other">Other</SelectItem>
              </SelectContent>
            </Select>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-full md:w-32">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="inactive">Inactive</SelectItem>
                <SelectItem value="error">Error</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="grid gap-4">
            {filteredIntegrations.map((integration) => (
              <Card key={integration.id} className="cursor-pointer hover:shadow-lg transition-shadow">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg flex items-center justify-center">
                        {getCategoryIcon(integration.category)}
                      </div>
                      <div>
                        <h3 className="font-semibold text-lg flex items-center gap-2">
                          {integration.name}
                          {getStatusIcon(integration.status)}
                        </h3>
                        <p className="text-gray-600 dark:text-gray-400">{integration.description}</p>
                        <div className="flex items-center gap-4 mt-2">
                          <Badge variant="outline">{integration.type}</Badge>
                          <Badge variant="outline">{integration.category}</Badge>
                          <span className="text-sm text-gray-500">
                            {integration.total_calls} calls • {integration.success_rate}% success
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => testIntegration(integration)}
                        disabled={isLoading}
                      >
                        <Play className="w-4 h-4 mr-1" />
                        Test
                      </Button>
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => {
                          setSelectedIntegration(integration);
                          setActiveTab('configure');
                        }}
                      >
                        <Settings className="w-4 h-4 mr-1" />
                        Configure
                      </Button>
                      <Button 
                        variant="destructive" 
                        size="sm"
                        onClick={() => deleteIntegration(integration.id)}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="templates" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {templates.map((template) => (
              <Card key={template.id} className="cursor-pointer hover:shadow-lg transition-shadow">
                <CardContent className="p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-blue-500 rounded-lg flex items-center justify-center">
                      {getCategoryIcon(template.category)}
                    </div>
                    <div>
                      <h3 className="font-semibold">{template.name}</h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400">{template.provider}</p>
                    </div>
                  </div>
                  <p className="text-gray-600 dark:text-gray-400 mb-4">{template.description}</p>
                  <div className="flex flex-wrap gap-2 mb-4">
                    {template.tags.map((tag: string) => (
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
                      onClick={() => createFromTemplate(template)}
                    >
                      <Plus className="w-4 h-4 mr-1" />
                      Use Template
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="configure" className="space-y-6">
          {selectedIntegration ? (
            <ConfigurationPanel 
              integration={selectedIntegration}
              onUpdate={(updated) => {
                setIntegrations(prev => 
                  prev.map(int => int.id === updated.id ? updated : int)
                );
                setSelectedIntegration(updated);
              }}
            />
          ) : (
            <Card>
              <CardContent className="p-8 text-center">
                <Settings className="w-16 h-16 mx-auto text-gray-400 mb-4" />
                <h3 className="text-lg font-semibold mb-2">No Integration Selected</h3>
                <p className="text-gray-600 dark:text-gray-400">
                  Select an integration from the integrations tab to configure it here.
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="monitoring" className="space-y-6">
          <MonitoringDashboard integrations={integrations} callHistory={callHistory} />
        </TabsContent>
      </Tabs>
    </div>
  );
};

const ConfigurationPanel: React.FC<{
  integration: APIIntegration;
  onUpdate: (integration: APIIntegration) => void;
}> = ({ integration, onUpdate }) => {
  const [formData, setFormData] = useState<APIIntegration>(integration);
  const [isSaving, setIsSaving] = useState(false);

  const handleSave = async () => {
    try {
      setIsSaving(true);
      const response = await fetch(`/api/integrations/${integration.id}/`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        const updated = await response.json();
        onUpdate(updated);
      }
    } catch (error) {
      console.error('Save failed:', error);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Settings className="w-5 h-5" />
          Configure {integration.name}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="name">Integration Name</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="endpoint">API Endpoint</Label>
            <Input
              id="endpoint"
              value={formData.endpoint}
              onChange={(e) => setFormData({ ...formData, endpoint: e.target.value })}
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="description">Description</Label>
          <Textarea
            id="description"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          />
        </div>

        <Separator />

        <div className="space-y-4">
          <h4 className="font-semibold flex items-center gap-2">
            <Shield className="w-4 h-4" />
            Authentication
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="auth_type">Authentication Type</Label>
              <Select
                value={formData.authentication.type}
                onValueChange={(value: string) => 
                  setFormData({ 
                    ...formData, 
                    authentication: { ...formData.authentication, type: value as 'none' | 'api_key' | 'bearer' | 'basic' | 'oauth2' }
                  })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">None</SelectItem>
                  <SelectItem value="api_key">API Key</SelectItem>
                  <SelectItem value="bearer">Bearer Token</SelectItem>
                  <SelectItem value="basic">Basic Auth</SelectItem>
                  <SelectItem value="oauth2">OAuth 2.0</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="timeout">Timeout (ms)</Label>
              <Input
                id="timeout"
                type="number"
                value={formData.timeout}
                onChange={(e) => setFormData({ ...formData, timeout: parseInt(e.target.value) })}
              />
            </div>
          </div>
        </div>

        <div className="flex justify-end gap-2">
          <Button variant="outline">Cancel</Button>
          <Button onClick={handleSave} disabled={isSaving}>
            {isSaving ? (
              <>
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              'Save Configuration'
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

const MonitoringDashboard: React.FC<{
  integrations: APIIntegration[];
  callHistory: APICallResult[];
}> = ({ integrations, callHistory }) => {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="text-center">
              <h3 className="text-lg font-semibold">Success Rate</h3>
              <div className="text-3xl font-bold text-green-600 mt-2">
                {integrations.length > 0 ? Math.round(
                  integrations.reduce((sum, int) => sum + int.success_rate, 0) / integrations.length
                ) : 0}%
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="text-center">
              <h3 className="text-lg font-semibold">Avg Response</h3>
              <div className="text-3xl font-bold text-blue-600 mt-2">
                {integrations.length > 0 ? Math.round(
                  integrations.reduce((sum, int) => sum + int.avg_response_time, 0) / integrations.length
                ) : 0}ms
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="text-center">
              <h3 className="text-lg font-semibold">Total Calls</h3>
              <div className="text-3xl font-bold text-purple-600 mt-2">
                {integrations.reduce((sum, int) => sum + int.total_calls, 0).toLocaleString()}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="w-5 h-5" />
            API Call History
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2">Integration</th>
                  <th className="text-left py-2">Status</th>
                  <th className="text-left py-2">Response Time</th>
                  <th className="text-left py-2">Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {callHistory.slice(0, 10).map((call) => {
                  const integration = integrations.find(i => i.id === call.integration_id);
                  return (
                    <tr key={call.id} className="border-b">
                      <td className="py-2">{integration?.name || 'Unknown'}</td>
                      <td className="py-2">
                        <Badge variant={call.status === 'success' ? 'default' : 'destructive'}>
                          {call.status}
                        </Badge>
                      </td>
                      <td className="py-2">{call.response_time}ms</td>
                      <td className="py-2">{new Date(call.timestamp).toLocaleString()}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default APIIntegrationHub;