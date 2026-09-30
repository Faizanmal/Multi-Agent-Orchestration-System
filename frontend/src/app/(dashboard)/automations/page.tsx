"use client";

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Clock, Mail, MessageSquare, Play, Plus, Zap, Workflow, RefreshCw, Trash2, Pause, PlayCircle } from 'lucide-react';
import apiClient from '@/lib/api';
import { toast } from '@/hooks/use-toast';
import type { AutomationRecord, WorkflowRecord } from '@/types/api';
import { axiosErrorDetail, errorMessage, paginatedItems } from '@/types/api';
import { AppLayout } from '@/components/layout/AppLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select';
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from '@/components/ui/dialog';

const PRESETS = [
  {
    type: 'inbox_digest',
    name: 'Daily Inbox Digest',
    icon: Mail,
    description: 'Read Gmail, summarize with AI, optionally post to Slack',
    defaultConfig: { max_emails: '10', slack_channel: '' },
  },
  {
    type: 'slack_alert',
    name: 'Slack Alert',
    icon: MessageSquare,
    description: 'Send a scheduled message to a Slack channel',
    defaultConfig: { channel: '', message: 'Hello from MultiAgent!' },
  },
  {
    type: 'integration_check',
    name: 'Integration Health Check',
    icon: RefreshCw,
    description: 'Test all integrations and alert Slack on failures',
    defaultConfig: { slack_channel: '' },
  },
  {
    type: 'workflow_run',
    name: 'Run Workflow',
    icon: Workflow,
    description: 'Execute a saved visual workflow on schedule',
    defaultConfig: {},
  },
];

const TYPE_LABELS: Record<string, string> = {
  inbox_digest: 'Inbox Digest',
  slack_alert: 'Slack Alert',
  integration_check: 'Health Check',
  workflow_run: 'Workflow Run',
};

export default function AutomationsPage() {
  const [automations, setAutomations] = useState<AutomationRecord[]>([]);
  const [workflows, setWorkflows] = useState<WorkflowRecord[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [preset, setPreset] = useState(PRESETS[0]);
  const [name, setName] = useState('');
  const [frequency, setFrequency] = useState('daily');
  const [config, setConfig] = useState<Record<string, string>>({});
  const [workflowId, setWorkflowId] = useState('');
  const [runningId, setRunningId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);

  const load = async () => {
    setIsLoading(true);
    try {
      const [autoRes, wfRes] = await Promise.all([
        apiClient.getAutomations(),
        apiClient.getWorkflows(),
      ]);
      setAutomations(paginatedItems(autoRes.data as AutomationRecord[] | { results?: AutomationRecord[] }));
      setWorkflows(paginatedItems(wfRes.data as WorkflowRecord[] | { results?: WorkflowRecord[] }));
    } catch (e: unknown) {
      toast({ title: 'Failed to load automations', description: errorMessage(e), variant: 'destructive' });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => { setTimeout(() => { load(); }, 0) }, []);

  const openPreset = (p: typeof PRESETS[0]) => {
    setPreset(p);
    setName(p.name);
    setConfig(Object.fromEntries(Object.entries(p.defaultConfig).map(([k, v]) => [k, String(v)])));
    setWorkflowId('');
    setShowCreate(true);
  };

  const handleCreate = async () => {
    if (preset.type === 'workflow_run' && !workflowId) {
      toast({ title: 'Select a workflow', variant: 'destructive' });
      return;
    }
    setIsCreating(true);
    try {
      await apiClient.createAutomation({
        name,
        automation_type: preset.type,
        frequency,
        is_active: true,
        config: {
          ...config,
          max_emails: config.max_emails ? parseInt(config.max_emails) : 10,
        },
        workflow: preset.type === 'workflow_run' ? workflowId : null,
      });
      setShowCreate(false);
      await load();
      toast({ title: 'Automation created', description: 'It will run on the next scheduler tick.' });
    } catch (e: unknown) {
      toast({ title: 'Failed to create automation', description: axiosErrorDetail(e) || errorMessage(e), variant: 'destructive' });
    } finally {
      setIsCreating(false);
    }
  };

  const handleRun = async (id: string) => {
    setRunningId(id);
    try {
      const res = await apiClient.runAutomation(id);
      const data = res.data as { success?: boolean; result?: { message?: string; summary?: string } };
      await load();
      toast({
        title: data?.success ? 'Automation completed' : 'Automation failed',
        description: data?.result?.message || data?.result?.summary || undefined,
        variant: data?.success ? 'default' : 'destructive',
      });
    } catch (e: unknown) {
      toast({ title: 'Run failed', description: errorMessage(e), variant: 'destructive' });
    } finally {
      setRunningId(null);
    }
  };

  const handleToggle = async (a: AutomationRecord) => {
    try {
      await apiClient.updateAutomation(a.id, { is_active: !a.is_active });
      await load();
      toast({ title: a.is_active ? 'Automation paused' : 'Automation resumed' });
    } catch (e: unknown) {
      toast({ title: 'Update failed', description: errorMessage(e), variant: 'destructive' });
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await apiClient.deleteAutomation(id);
      await load();
      toast({ title: 'Automation deleted' });
    } catch (e: unknown) {
      toast({ title: 'Delete failed', description: errorMessage(e), variant: 'destructive' });
    }
  };

  return (
    <AppLayout>
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-3">
              <Clock className="h-8 w-8 text-primary" />
              Scheduled Automations
            </h1>
            <p className="text-muted-foreground mt-1">Daily digests, Slack alerts, and workflow schedules</p>
          </div>
          <Button onClick={() => openPreset(PRESETS[0])} className="gap-2">
            <Plus className="h-4 w-4" /> New Automation
          </Button>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {PRESETS.map((p) => (
            <Card key={p.type} className="cursor-pointer hover:border-primary/50 transition-colors" onClick={() => openPreset(p)}>
              <CardContent className="p-5">
                <p.icon className="h-8 w-8 text-primary mb-3" />
                <h3 className="font-semibold">{p.name}</h3>
                <p className="text-sm text-muted-foreground mt-1">{p.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Active Automations</CardTitle>
            <CardDescription>Runs automatically via background scheduler (every minute check)</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {isLoading ? (
              <p className="text-sm text-muted-foreground text-center py-8">Loading...</p>
            ) : automations.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-8">No automations yet. Create one above.</p>
            ) : automations.map((a) => (
              <div key={a.id} className="flex items-center gap-4 p-4 rounded-lg border">
                <Zap className="h-5 w-5 text-primary shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="font-medium">{a.name}</p>
                  <p className="text-sm text-muted-foreground">
                    {TYPE_LABELS[a.automation_type] || a.automation_type} • {a.frequency}
                    {a.next_run_at && ` • next: ${new Date(a.next_run_at).toLocaleString()}`}
                  </p>
                  {a.last_result?.message && (
                    <p className="text-xs text-muted-foreground mt-1 truncate">Last: {a.last_result.message}</p>
                  )}
                </div>
                <Badge variant={a.is_active ? 'default' : 'secondary'}>{a.is_active ? 'Active' : 'Paused'}</Badge>
                <Button size="sm" variant="ghost" onClick={() => handleToggle(a)} title={a.is_active ? 'Pause' : 'Resume'}>
                  {a.is_active ? <Pause className="h-4 w-4" /> : <PlayCircle className="h-4 w-4" />}
                </Button>
                <Button size="sm" variant="outline" className="gap-1" disabled={runningId === a.id} onClick={() => handleRun(a.id)}>
                  <Play className="h-3 w-3" />
                  {runningId === a.id ? 'Running...' : 'Run now'}
                </Button>
                <Button size="sm" variant="ghost" className="text-destructive" onClick={() => handleDelete(a.id)}>
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            ))}
          </CardContent>
        </Card>

        <Dialog open={showCreate} onOpenChange={setShowCreate}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create {preset.name}</DialogTitle>
              <DialogDescription>{preset.description}</DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Name</Label>
                <Input value={name} onChange={(e) => setName(e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label>Frequency</Label>
                <Select value={frequency} onValueChange={setFrequency}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="hourly">Hourly</SelectItem>
                    <SelectItem value="daily">Daily</SelectItem>
                    <SelectItem value="weekly">Weekly</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              {preset.type === 'inbox_digest' && (
                <>
                  <div className="space-y-2">
                    <Label>Max emails</Label>
                    <Input value={config.max_emails || '10'} onChange={(e) => setConfig({ ...config, max_emails: e.target.value })} />
                  </div>
                  <div className="space-y-2">
                    <Label>Slack channel (optional)</Label>
                    <Input placeholder="#general" value={config.slack_channel || ''} onChange={(e) => setConfig({ ...config, slack_channel: e.target.value })} />
                  </div>
                </>
              )}
              {preset.type === 'slack_alert' && (
                <>
                  <div className="space-y-2">
                    <Label>Slack channel</Label>
                    <Input placeholder="#alerts" value={config.channel || ''} onChange={(e) => setConfig({ ...config, channel: e.target.value })} />
                  </div>
                  <div className="space-y-2">
                    <Label>Message</Label>
                    <Input value={config.message || ''} onChange={(e) => setConfig({ ...config, message: e.target.value })} />
                  </div>
                </>
              )}
              {preset.type === 'integration_check' && (
                <div className="space-y-2">
                  <Label>Slack channel for failures (optional)</Label>
                  <Input placeholder="#alerts" value={config.slack_channel || ''} onChange={(e) => setConfig({ ...config, slack_channel: e.target.value })} />
                </div>
              )}
              {preset.type === 'workflow_run' && (
                <div className="space-y-2">
                  <Label>Workflow</Label>
                  <Select value={workflowId} onValueChange={setWorkflowId}>
                    <SelectTrigger><SelectValue placeholder="Select workflow" /></SelectTrigger>
                    <SelectContent>
                      {workflows.length === 0 ? (
                        <SelectItem value="_none" disabled>No saved workflows — create one in Workflows</SelectItem>
                      ) : workflows.map((w) => (
                        <SelectItem key={w.id} value={w.id}>{w.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
              <Button onClick={handleCreate} disabled={isCreating || !name.trim()}>
                {isCreating ? 'Creating...' : 'Create'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </motion.div>
    </AppLayout>
  );
}
