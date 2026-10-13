'use client';

import { useEffect, useState } from 'react';
import apiClient, { type Agent } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { toast } from 'sonner';
import { Loader2, Save, Bot } from 'lucide-react';

const TOOL_CATALOG = [
  { id: 'web_search', label: 'Web Search', description: 'DuckDuckGo live search' },
  { id: 'calculate', label: 'Calculator', description: 'Safe math expressions' },
  { id: 'get_current_datetime', label: 'Date / Time', description: 'Current UTC timestamp' },
  { id: 'fetch_url_content', label: 'Fetch URL', description: 'Fetch and extract page text' },
] as const;

const DEFAULT_PROMPTS: Record<string, string> = {
  orchestrator:
    'You are an Orchestrator Agent. Analyse requests, decompose them into subtasks, coordinate specialists, and synthesise a coherent answer.',
  reasoning:
    'You are a Reasoning Agent. Apply rigorous logical analysis, break problems into clear steps, and justify every conclusion.',
  vision:
    'You are a Vision Agent. Analyse visual content, describe images, extract text, and reason about visual patterns.',
  action:
    'You are an Action Agent. Execute concrete tasks, call external tools, and report results precisely.',
  memory:
    'You are a Memory Agent. Retrieve, store, and organise contextual information. Summarise what you know and flag gaps.',
  custom: 'You are a custom specialised agent. Follow the instructions below carefully.',
};

export function AgentTemplateBuilder() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedId, setSelectedId] = useState<string>('new');
  const [name, setName] = useState('');
  const [type, setType] = useState<Agent['type']>('custom');
  const [systemPrompt, setSystemPrompt] = useState(DEFAULT_PROMPTS.custom);
  const [enabledTools, setEnabledTools] = useState<string[]>(['web_search', 'calculate']);
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const loadAgents = async () => {
    setLoading(true);
    try {
      const res = await apiClient.getAgents();
      const list = res.results || [];
      setAgents(Array.isArray(list) ? list : []);
    } catch {
      toast.error('Failed to load agents');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAgents();
  }, []);

  const resetNew = () => {
    setSelectedId('new');
    setName('');
    setType('custom');
    setSystemPrompt(DEFAULT_PROMPTS.custom);
    setEnabledTools(['web_search', 'calculate']);
    setDescription('');
  };

  const selectAgent = (id: string) => {
    if (id === 'new') {
      resetNew();
      return;
    }
    const agent = agents.find((a) => a.id === id);
    if (!agent) return;
    setSelectedId(id);
    setName(agent.name);
    setType(agent.type);
    const cfg = agent.configuration || {};
    setSystemPrompt(
      (cfg.system_prompt as string) || DEFAULT_PROMPTS[agent.type] || DEFAULT_PROMPTS.custom
    );
    setEnabledTools(
      Array.isArray(cfg.enabled_tools) ? (cfg.enabled_tools as string[]) : ['web_search']
    );
    setDescription((cfg.description as string) || '');
  };

  const toggleTool = (toolId: string, on: boolean) => {
    setEnabledTools((prev) =>
      on ? Array.from(new Set([...prev, toolId])) : prev.filter((t) => t !== toolId)
    );
  };

  const handleSave = async () => {
    if (!name.trim()) {
      toast.error('Name is required');
      return;
    }
    setSaving(true);
    const configuration = {
      description: description.trim(),
      system_prompt: systemPrompt.trim(),
      enabled_tools: enabledTools,
    };
    try {
      if (selectedId === 'new') {
        const created = await apiClient.createAgent({
          name: name.trim(),
          type,
          capabilities: enabledTools,
          configuration,
        } as Partial<Agent>);
        toast.success('Agent template created');
        await loadAgents();
        setSelectedId(created.id);
      } else {
        await apiClient.updateAgent(selectedId, {
          name: name.trim(),
          type,
          capabilities: enabledTools,
          configuration,
        } as Partial<Agent>);
        toast.success('Agent template updated');
        await loadAgents();
      }
    } catch {
      toast.error('Failed to save agent template');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Templates</CardTitle>
          <CardDescription>Select an agent or create a new one</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          <Button
            variant={selectedId === 'new' ? 'default' : 'outline'}
            className="w-full justify-start"
            onClick={resetNew}
          >
            <Bot className="mr-2 h-4 w-4" />
            New template
          </Button>
          {loading ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground py-4">
              <Loader2 className="h-4 w-4 animate-spin" /> Loading…
            </div>
          ) : (
            agents.map((agent) => (
              <button
                key={agent.id}
                type="button"
                onClick={() => selectAgent(agent.id)}
                className={`w-full text-left rounded-md border px-3 py-2 text-sm transition ${
                  selectedId === agent.id
                    ? 'border-primary bg-primary/5'
                    : 'hover:bg-muted/50'
                }`}
              >
                <div className="font-medium truncate">{agent.name}</div>
                <div className="text-xs text-muted-foreground flex items-center gap-2 mt-1">
                  <Badge variant="outline" className="text-[10px]">
                    {agent.type}
                  </Badge>
                  {(agent.configuration?.enabled_tools as string[] | undefined)?.length ?? 0} tools
                </div>
              </button>
            ))
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Agent Template Builder</CardTitle>
          <CardDescription>
            Define system prompts and toggle which external tools this agent may use.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="agent-name">Name</Label>
              <Input
                id="agent-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Support triage agent"
              />
            </div>
            <div className="space-y-2">
              <Label>Type</Label>
              <Select
                value={type}
                onValueChange={(v) => {
                  const next = v as Agent['type'];
                  setType(next);
                  if (!systemPrompt || Object.values(DEFAULT_PROMPTS).includes(systemPrompt)) {
                    setSystemPrompt(DEFAULT_PROMPTS[next] || DEFAULT_PROMPTS.custom);
                  }
                }}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.keys(DEFAULT_PROMPTS).map((t) => (
                    <SelectItem key={t} value={t}>
                      {t}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="agent-desc">Description</Label>
            <Input
              id="agent-desc"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Short summary shown in the agents list"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="system-prompt">System prompt</Label>
            <Textarea
              id="system-prompt"
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              rows={8}
              className="font-mono text-sm"
            />
          </div>

          <div className="space-y-3">
            <Label>External tools</Label>
            <div className="grid gap-3 sm:grid-cols-2">
              {TOOL_CATALOG.map((tool) => {
                const on = enabledTools.includes(tool.id);
                return (
                  <div
                    key={tool.id}
                    className="flex items-start justify-between rounded-md border p-3"
                  >
                    <div className="pr-3">
                      <div className="text-sm font-medium">{tool.label}</div>
                      <div className="text-xs text-muted-foreground">{tool.description}</div>
                    </div>
                    <Switch checked={on} onCheckedChange={(v) => toggleTool(tool.id, v)} />
                  </div>
                );
              })}
            </div>
          </div>

          <div className="flex justify-end">
            <Button onClick={handleSave} disabled={saving}>
              {saving ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Save className="mr-2 h-4 w-4" />
              )}
              Save template
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
