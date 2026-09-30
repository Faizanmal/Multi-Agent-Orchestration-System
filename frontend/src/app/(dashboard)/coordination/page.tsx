"use client";

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  Network,
  Plus,
  Play,
  Trash2,
  Clock,
  Users,
  Zap,
  Bot,
  Loader2,
  RefreshCw,
  Sparkles,
} from 'lucide-react';
import apiClient from '@/lib/api';
import { toast } from '@/hooks/use-toast';
import type { Agent } from '@/lib/api';
import { axiosErrorDetail, errorMessage } from '@/types/api';
import { AppLayout } from '@/components/layout/AppLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
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
import { cn } from '@/lib/utils';

type Strategy = {
  id: string;
  name: string;
  description: string;
};

type CoordSession = {
  id: string;
  name: string;
  strategy: string;
  is_active: boolean;
  created_at: string;
  interaction_count?: number;
  final_answer?: string;
  task?: string;
};

type RunResult = {
  strategy?: string;
  final_answer?: string;
  agents_involved?: string[];
  duration_ms?: number;
  results?: Record<string, string>;
  model_coordination?: Record<string, unknown>;
  status?: string;
  error?: string;
};

export default function CoordinationPage() {
  const [sessions, setSessions] = useState<CoordSession[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showRun, setShowRun] = useState(false);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<RunResult | null>(null);

  const [name, setName] = useState('Agent Team Run');
  const [strategy, setStrategy] = useState('collaborative');
  const [task, setTask] = useState('');
  const [selectedAgents, setSelectedAgents] = useState<string[]>([]);
  const [useModelCoord, setUseModelCoord] = useState(false);

  const load = async () => {
    setIsLoading(true);
    try {
      const [sessRes, agentRes, stratRes] = await Promise.all([
        apiClient.getCoordinationSessions(),
        apiClient.getAgents(),
        apiClient.getCoordinationStrategies().catch(() => ({ strategies: [] })),
      ]);
      setSessions((sessRes.sessions || []) as CoordSession[]);
      const agentList = (agentRes?.results || []) as Agent[];
      setAgents(agentList);
      setStrategies(stratRes.strategies || []);
      if (!selectedAgents.length && agentList.length) {
        setSelectedAgents(agentList.slice(0, Math.min(3, agentList.length)).map((a) => a.id));
      }
    } catch (e: unknown) {
      toast({
        title: 'Failed to load coordination data',
        description: axiosErrorDetail(e) || errorMessage(e),
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    setTimeout(() => { load(); }, 0)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const toggleAgent = (id: string) => {
    setSelectedAgents((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
  };

  const handleRun = async () => {
    if (!task.trim()) {
      toast({ title: 'Enter a task for the agents', variant: 'destructive' });
      return;
    }
    if (!selectedAgents.length) {
      toast({ title: 'Select at least one agent', variant: 'destructive' });
      return;
    }
    setRunning(true);
    setResult(null);
    try {
      const data = await apiClient.quickCoordinateAgents({
        name: name || `Run: ${strategy}`,
        strategy,
        agent_ids: selectedAgents,
        task: task.trim(),
        use_model_coordination: useModelCoord,
      });
      setResult(data as unknown as RunResult);
      setShowRun(false);
      toast({ title: 'Agents coordinated', description: strategy });
      await load();
    } catch (e: unknown) {
      toast({
        title: 'Coordination failed',
        description: axiosErrorDetail(e) || errorMessage(e),
        variant: 'destructive',
      });
    } finally {
      setRunning(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await apiClient.deleteCoordinationSession(id);
      setSessions((prev) => prev.filter((s) => s.id !== id));
    } catch (e: unknown) {
      toast({
        title: 'Delete failed',
        description: axiosErrorDetail(e) || errorMessage(e),
        variant: 'destructive',
      });
    }
  };

  return (
    <AppLayout>
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-3">
              <Network className="h-8 w-8 text-primary" />
              Agent Coordination
            </h1>
            <p className="text-muted-foreground mt-1">
              Run sequential, parallel, hierarchical, collaborative, or competitive multi-agent strategies
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={load} disabled={isLoading} className="gap-2">
              <RefreshCw className={cn('h-4 w-4', isLoading && 'animate-spin')} />
              Refresh
            </Button>
            <Button onClick={() => setShowRun(true)} className="gap-2">
              <Plus className="h-4 w-4" />
              Run team
            </Button>
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          <Card>
            <CardContent className="p-4 flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Sessions</p>
                <p className="text-2xl font-bold">{sessions.length}</p>
              </div>
              <Users className="h-5 w-5 text-primary" />
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Agents</p>
                <p className="text-2xl font-bold">{agents.length}</p>
              </div>
              <Bot className="h-5 w-5 text-green-500" />
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Strategies</p>
                <p className="text-2xl font-bold">{strategies.length || 5}</p>
              </div>
              <Zap className="h-5 w-5 text-amber-500" />
            </CardContent>
          </Card>
        </div>

        {result && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Latest result</span>
                <Badge variant="outline">{result.strategy}</Badge>
              </CardTitle>
              <CardDescription>
                {(result.agents_involved || []).join(', ')}
                {result.duration_ms != null ? ` · ${result.duration_ms} ms` : ''}
                {result.model_coordination ? ' · refined by model coordination' : ''}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="rounded-lg bg-muted/40 p-4 whitespace-pre-wrap text-sm">
                {result.final_answer || 'No answer'}
              </div>
              {result.results && Object.keys(result.results).length > 0 && (
                <div className="space-y-2">
                  <p className="text-sm font-medium">Per-agent outputs</p>
                  {Object.entries(result.results).map(([agentName, output]) => (
                    <div key={agentName} className="rounded border p-3 text-sm">
                      <p className="font-medium mb-1">{agentName}</p>
                      <p className="text-muted-foreground whitespace-pre-wrap">
                        {typeof output === 'string' ? output.slice(0, 800) : JSON.stringify(output).slice(0, 800)}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}

        <div className="grid gap-4 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Strategies</CardTitle>
              <CardDescription>How agents work together</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {(strategies.length
                ? strategies
                : [
                    { id: 'sequential', name: 'Sequential', description: 'Chain outputs' },
                    { id: 'parallel', name: 'Parallel', description: 'Run together' },
                    { id: 'hierarchical', name: 'Hierarchical', description: 'Orchestrator delegates' },
                    { id: 'collaborative', name: 'Collaborative', description: 'Critique & refine' },
                    { id: 'competitive', name: 'Competitive', description: 'Judge picks winner' },
                  ]
              ).map((s) => (
                <button
                  key={s.id}
                  type="button"
                  onClick={() => {
                    setStrategy(s.id);
                    setShowRun(true);
                  }}
                  className={cn(
                    'w-full text-left rounded-lg border p-3 hover:border-primary/50 transition',
                    strategy === s.id && 'border-primary bg-primary/5',
                  )}
                >
                  <p className="font-medium">{s.name}</p>
                  <p className="text-sm text-muted-foreground">{s.description}</p>
                </button>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Recent sessions</CardTitle>
              <CardDescription>Past coordination runs</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {isLoading ? (
                <div className="flex items-center gap-2 text-muted-foreground py-8 justify-center">
                  <Loader2 className="h-4 w-4 animate-spin" /> Loading…
                </div>
              ) : sessions.length === 0 ? (
                <p className="text-sm text-muted-foreground py-8 text-center">
                  No sessions yet. Run a team to get started.
                </p>
              ) : (
                sessions.slice(0, 12).map((s) => (
                  <div key={s.id} className="rounded-lg border p-3 space-y-2">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <p className="font-medium">{s.name}</p>
                        <p className="text-xs text-muted-foreground flex items-center gap-2 mt-1">
                          <Badge variant="outline">{s.strategy}</Badge>
                          <Clock className="h-3 w-3" />
                          {new Date(s.created_at).toLocaleString()}
                        </p>
                      </div>
                      <Button variant="ghost" size="icon" onClick={() => handleDelete(s.id)}>
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                    {s.task && <p className="text-sm text-muted-foreground line-clamp-2">{s.task}</p>}
                    {s.final_answer && (
                      <p className="text-sm line-clamp-3 bg-muted/40 rounded p-2">{s.final_answer}</p>
                    )}
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>

        <Dialog open={showRun} onOpenChange={setShowRun}>
          <DialogContent className="max-w-xl">
            <DialogHeader>
              <DialogTitle>Coordinate agents</DialogTitle>
              <DialogDescription>
                Select agents and a strategy. Optionally refine the final answer with multi-model coordination.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Session name</Label>
                <Input value={name} onChange={(e) => setName(e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label>Strategy</Label>
                <Select value={strategy} onValueChange={setStrategy}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="sequential">Sequential</SelectItem>
                    <SelectItem value="parallel">Parallel</SelectItem>
                    <SelectItem value="hierarchical">Hierarchical</SelectItem>
                    <SelectItem value="collaborative">Collaborative</SelectItem>
                    <SelectItem value="competitive">Competitive</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Agents</Label>
                <div className="flex flex-wrap gap-2 max-h-40 overflow-y-auto">
                  {agents.map((a) => {
                    const selected = selectedAgents.includes(a.id);
                    return (
                      <Button
                        key={a.id}
                        type="button"
                        size="sm"
                        variant={selected ? 'default' : 'outline'}
                        onClick={() => toggleAgent(a.id)}
                      >
                        {a.name}
                        <span className="ml-1 text-xs opacity-70">{a.type}</span>
                      </Button>
                    );
                  })}
                  {!agents.length && (
                    <p className="text-sm text-muted-foreground">No agents found. Create some on the Agents page.</p>
                  )}
                </div>
              </div>
              <div className="space-y-2">
                <Label>Task</Label>
                <textarea
                  className="flex min-h-[100px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={task}
                  onChange={(e) => setTask(e.target.value)}
                  placeholder="e.g. Draft an onboarding email sequence and critique it for clarity..."
                />
              </div>
              <div className="flex items-center justify-between rounded-lg border p-3">
                <div>
                  <p className="text-sm font-medium flex items-center gap-2">
                    <Sparkles className="h-4 w-4" />
                    Refine with model coordination
                  </p>
                  <p className="text-xs text-muted-foreground">
                    After agents finish, run collaborative multi-model synthesis
                  </p>
                </div>
                <Switch checked={useModelCoord} onCheckedChange={setUseModelCoord} />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowRun(false)} disabled={running}>
                Cancel
              </Button>
              <Button onClick={handleRun} disabled={running} className="gap-2">
                {running ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                {running ? 'Coordinating…' : 'Run'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </motion.div>
    </AppLayout>
  );
}
