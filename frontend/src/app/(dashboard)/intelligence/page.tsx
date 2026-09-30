"use client";

import React, { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import {
  Brain,
  Plus,
  Search,
  MoreVertical,
  Trash2,
  Settings,
  Clock,
  Zap,
  Activity,
  Sparkles,
  TrendingUp,
  MessageSquare,
  Image,
  Mic,
  RefreshCw,
  Loader2,
} from 'lucide-react';
import apiClient from '@/lib/api';
import { toast } from '@/hooks/use-toast';
import type { AIModelRecord, ModelCoordinationMode, ModelCoordinationResult } from '@/types/api';
import { axiosErrorDetail, errorMessage } from '@/types/api';
import { AppLayout } from '@/components/layout/AppLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
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

const PROVIDER_MODELS: Record<string, { id: string; label: string; type: string; capabilities: string[] }[]> = {
  groq: [
    { id: 'llama-3.3-70b-versatile', label: 'Llama 3.3 70B', type: 'text', capabilities: ['reasoning', 'coding', 'fast'] },
    { id: 'llama-3.1-8b-instant', label: 'Llama 3.1 8B Instant', type: 'text', capabilities: ['fast', 'chat'] },
    { id: 'mixtral-8x7b-32768', label: 'Mixtral 8x7B', type: 'text', capabilities: ['coding', 'reasoning'] },
  ],
  openai: [
    { id: 'gpt-4o', label: 'GPT-4o', type: 'multimodal', capabilities: ['reasoning', 'vision', 'coding'] },
    { id: 'gpt-4o-mini', label: 'GPT-4o Mini', type: 'multimodal', capabilities: ['fast', 'cheap'] },
    { id: 'whisper-1', label: 'Whisper', type: 'audio', capabilities: ['transcription'] },
  ],
  anthropic: [
    { id: 'claude-3-5-sonnet-latest', label: 'Claude 3.5 Sonnet', type: 'text', capabilities: ['reasoning', 'writing'] },
    { id: 'claude-3-opus-latest', label: 'Claude 3 Opus', type: 'text', capabilities: ['reasoning', 'analysis'] },
  ],
  google: [
    { id: 'gemini-1.5-pro', label: 'Gemini 1.5 Pro', type: 'multimodal', capabilities: ['vision', 'reasoning'] },
    { id: 'gemini-1.5-flash', label: 'Gemini 1.5 Flash', type: 'multimodal', capabilities: ['fast', 'vision'] },
  ],
  mistral: [
    { id: 'mistral-large-latest', label: 'Mistral Large', type: 'text', capabilities: ['reasoning', 'coding'] },
  ],
  custom: [
    { id: 'custom', label: 'Custom model', type: 'text', capabilities: ['custom'] },
  ],
};

function providerIcon(provider: string, modelType: string) {
  if (modelType === 'audio') return Mic;
  if (modelType === 'vision' || modelType === 'image') return Image;
  if (provider === 'groq') return Zap;
  if (provider === 'anthropic') return Brain;
  if (provider === 'google') return Sparkles;
  return MessageSquare;
}

export default function IntelligencePage() {
  const [models, setModels] = useState<AIModelRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [showAddModelDialog, setShowAddModelDialog] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [provider, setProvider] = useState('groq');
  const [modelId, setModelId] = useState('llama-3.3-70b-versatile');
  const [alias, setAlias] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [modelType, setModelType] = useState('text');
  const [coordMode, setCoordMode] = useState<ModelCoordinationMode>('collaborative');
  const [coordPrompt, setCoordPrompt] = useState('');
  const [selectedModelIds, setSelectedModelIds] = useState<string[]>([]);
  const [coordRunning, setCoordRunning] = useState(false);
  const [coordResult, setCoordResult] = useState<ModelCoordinationResult | null>(null);
  const [coordRounds, setCoordRounds] = useState('2');

  const loadModels = async () => {
    setIsLoading(true);
    try {
      let res = await apiClient.getAIModels();
      if (!res.models?.length) {
        await apiClient.seedDefaultAIModels();
        res = await apiClient.getAIModels();
      }
      setModels(res.models || []);
    } catch (e: unknown) {
      toast({
        title: 'Failed to load models',
        description: axiosErrorDetail(e) || errorMessage(e),
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    setTimeout(() => { loadModels(); }, 0)
  }, []);

  useEffect(() => {
    const options = PROVIDER_MODELS[provider] || [];
    if (options.length) {
      setTimeout(() => { setModelId(options[0].id); }, 0)
      setTimeout(() => {
          setModelType(options[0].type);
        }, 0)
      if (!alias) setTimeout(() => setAlias(options[0].label), 0);
    }
  }, [provider]); // eslint-disable-line react-hooks/exhaustive-deps

  const filtered = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) return models;
    return models.filter(
      (m) =>
        m.name.toLowerCase().includes(q) ||
        m.provider.toLowerCase().includes(q) ||
        m.model_id.toLowerCase().includes(q),
    );
  }, [models, searchQuery]);

  const stats = [
    { label: 'Active Models', value: models.filter((m) => m.is_active).length, icon: Brain, color: 'text-primary' },
    { label: 'Providers', value: new Set(models.map((m) => m.provider)).size, icon: Activity, color: 'text-green-500' },
    { label: 'Defaults', value: models.filter((m) => m.is_default).length, icon: Sparkles, color: 'text-blue-500' },
    { label: 'Total', value: models.length, icon: TrendingUp, color: 'text-yellow-500' },
  ];

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'text': return 'bg-blue-500/10 text-blue-500';
      case 'multimodal': return 'bg-purple-500/10 text-purple-500';
      case 'vision':
      case 'image': return 'bg-pink-500/10 text-pink-500';
      case 'audio': return 'bg-green-500/10 text-green-500';
      default: return 'bg-muted text-muted-foreground';
    }
  };

  const handleAddModel = async () => {
    const option = (PROVIDER_MODELS[provider] || []).find((o) => o.id === modelId);
    const name = alias.trim() || option?.label || modelId;
    if (!provider || !modelId) {
      toast({ title: 'Provider and model are required', variant: 'destructive' });
      return;
    }
    setIsSaving(true);
    try {
      await apiClient.createAIModel({
        name,
        provider,
        model_id: modelId === 'custom' ? (alias.trim() || 'custom-model') : modelId,
        model_type: option?.type || modelType || 'text',
        capabilities: option?.capabilities || [],
        api_key: apiKey || undefined,
      });
      setShowAddModelDialog(false);
      setApiKey('');
      setAlias('');
      toast({ title: 'Model added', description: `${name} is ready to use.` });
      await loadModels();
    } catch (e: unknown) {
      toast({
        title: 'Could not add model',
        description: axiosErrorDetail(e) || errorMessage(e),
        variant: 'destructive',
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async (id: string, name: string) => {
    try {
      await apiClient.deleteAIModel(id);
      toast({ title: 'Model removed', description: name });
      setModels((prev) => prev.filter((m) => m.id !== id));
    } catch (e: unknown) {
      toast({
        title: 'Delete failed',
        description: axiosErrorDetail(e) || errorMessage(e),
        variant: 'destructive',
      });
    }
  };

  const handleToggleActive = async (model: AIModelRecord) => {
    try {
      const updated = await apiClient.updateAIModel(model.id, { is_active: !model.is_active });
      setModels((prev) => prev.map((m) => (m.id === model.id ? { ...m, ...updated } : m)));
    } catch (e: unknown) {
      toast({
        title: 'Update failed',
        description: axiosErrorDetail(e) || errorMessage(e),
        variant: 'destructive',
      });
    }
  };

  const toggleCoordModel = (id: string) => {
    setSelectedModelIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
  };

  const handleCoordinate = async () => {
    if (!coordPrompt.trim()) {
      toast({ title: 'Enter a task/prompt for the models', variant: 'destructive' });
      return;
    }
    setCoordRunning(true);
    setCoordResult(null);
    try {
      const data = await apiClient.coordinateModels({
        prompt: coordPrompt.trim(),
        mode: coordMode,
        model_ids: selectedModelIds.length ? selectedModelIds : undefined,
        options: {
          rounds: Number(coordRounds) || 2,
          priority: 'balanced',
        },
      });
      setCoordResult(data as unknown as ModelCoordinationResult);
      toast({ title: 'Coordination complete', description: `${coordMode} finished` });
    } catch (e: unknown) {
      toast({
        title: 'Coordination failed',
        description: axiosErrorDetail(e) || errorMessage(e),
        variant: 'destructive',
      });
    } finally {
      setCoordRunning(false);
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
              <Brain className="h-8 w-8 text-primary" />
              Multi-Model Intelligence
            </h1>
            <p className="text-muted-foreground mt-1">
              Manage and orchestrate multiple AI models for optimal performance
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={loadModels} disabled={isLoading} className="gap-2">
              <RefreshCw className={cn('h-4 w-4', isLoading && 'animate-spin')} />
              Refresh
            </Button>
            <Button onClick={() => setShowAddModelDialog(true)} className="gap-2">
              <Plus className="h-4 w-4" />
              Add Model
            </Button>
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {stats.map((stat) => (
            <Card key={stat.label}>
              <CardContent className="p-4 flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">{stat.label}</p>
                  <p className="text-2xl font-bold">{stat.value}</p>
                </div>
                <div className={cn('p-2 rounded-lg bg-muted/50', stat.color)}>
                  <stat.icon className="h-5 w-5" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        <Tabs defaultValue="models" className="space-y-6">
          <TabsList>
            <TabsTrigger value="models">AI Models</TabsTrigger>
            <TabsTrigger value="coordinate">Coordinate Models</TabsTrigger>
          </TabsList>

          <TabsContent value="models" className="space-y-4">
            <div className="relative max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search models..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>

            {isLoading ? (
              <div className="flex items-center justify-center py-16 text-muted-foreground gap-2">
                <Loader2 className="h-5 w-5 animate-spin" />
                Loading models...
              </div>
            ) : filtered.length === 0 ? (
              <Card>
                <CardContent className="py-12 text-center space-y-3">
                  <p className="text-muted-foreground">No models yet. Add one or seed defaults.</p>
                  <Button
                    variant="outline"
                    onClick={async () => {
                      await apiClient.seedDefaultAIModels();
                      await loadModels();
                    }}
                  >
                    Seed default models
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {filtered.map((model, index) => {
                  const Icon = providerIcon(model.provider, model.model_type);
                  return (
                    <motion.div
                      key={model.id}
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: index * 0.05 }}
                    >
                      <Card className="hover:shadow-lg transition-all hover:border-primary/50">
                        <CardContent className="p-4">
                          <div className="flex items-start justify-between mb-4">
                            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
                              <Icon className="h-6 w-6 text-primary" />
                            </div>
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="icon" className="h-8 w-8">
                                  <MoreVertical className="h-4 w-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuItem onClick={() => handleToggleActive(model)}>
                                  <Settings className="h-4 w-4 mr-2" />
                                  {model.is_active ? 'Deactivate' : 'Activate'}
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem
                                  className="text-destructive"
                                  onClick={() => handleDelete(model.id, model.name)}
                                >
                                  <Trash2 className="h-4 w-4 mr-2" />
                                  Remove
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </div>

                          <div className="space-y-2">
                            <div className="flex items-center gap-2 flex-wrap">
                              <h3 className="font-semibold">{model.name}</h3>
                              <Badge variant="outline" className={getTypeColor(model.model_type)}>
                                {model.model_type}
                              </Badge>
                              {model.is_default && <Badge>Default</Badge>}
                              {!model.is_active && <Badge variant="secondary">Inactive</Badge>}
                            </div>
                            <p className="text-sm text-muted-foreground capitalize">
                              {model.provider} · <span className="font-mono text-xs">{model.model_id}</span>
                            </p>
                          </div>

                          <div className="flex flex-wrap gap-1 mt-3">
                            {(model.capabilities || []).slice(0, 4).map((cap) => (
                              <Badge key={cap} variant="secondary" className="text-xs">
                                {cap}
                              </Badge>
                            ))}
                          </div>

                          <Separator className="my-4" />
                          <div className="flex justify-between text-sm text-muted-foreground">
                            <span className="flex items-center gap-1">
                              <Clock className="h-3 w-3" />
                              {model.updated_at ? new Date(model.updated_at).toLocaleDateString() : '—'}
                            </span>
                            <span className={model.is_active ? 'text-green-600' : ''}>
                              {model.is_active ? 'Active' : 'Off'}
                            </span>
                          </div>
                        </CardContent>
                      </Card>
                    </motion.div>
                  );
                })}
              </div>
            )}
          </TabsContent>

          <TabsContent value="coordinate" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Models coordinating with each other</CardTitle>
                <CardDescription>
                  Run smart routing, collaborative refinement, debate/consensus, or a sequential pipeline across your registered models.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label>Coordination mode</Label>
                    <Select value={coordMode} onValueChange={(v) => setCoordMode(v as ModelCoordinationMode)}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="route">Smart Route (pick best + failover)</SelectItem>
                        <SelectItem value="collaborative">Collaborative (propose → refine → synthesize)</SelectItem>
                        <SelectItem value="debate">Debate / Consensus (critique + judge)</SelectItem>
                        <SelectItem value="pipeline">Sequential Pipeline (stage by stage)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Rounds (collaborative / debate)</Label>
                    <Select value={coordRounds} onValueChange={setCoordRounds}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="1">1</SelectItem>
                        <SelectItem value="2">2</SelectItem>
                        <SelectItem value="3">3</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Models in this run (optional — leave empty to use all active)</Label>
                  <div className="flex flex-wrap gap-2">
                    {models.filter((m) => m.is_active).map((m) => {
                      const selected = selectedModelIds.includes(m.id);
                      return (
                        <Button
                          key={m.id}
                          type="button"
                          size="sm"
                          variant={selected ? 'default' : 'outline'}
                          onClick={() => toggleCoordModel(m.id)}
                        >
                          {m.name}
                        </Button>
                      );
                    })}
                    {!models.some((m) => m.is_active) && (
                      <p className="text-sm text-muted-foreground">No active models. Add or activate models first.</p>
                    )}
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="coordPrompt">Shared task</Label>
                  <textarea
                    id="coordPrompt"
                    className="flex min-h-[120px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    placeholder="e.g. Design a go-to-market plan for an AI agent platform targeting startups..."
                    value={coordPrompt}
                    onChange={(e) => setCoordPrompt(e.target.value)}
                  />
                </div>

                <Button onClick={handleCoordinate} disabled={coordRunning} className="gap-2">
                  {coordRunning ? <Loader2 className="h-4 w-4 animate-spin" /> : <Zap className="h-4 w-4" />}
                  {coordRunning ? 'Models coordinating…' : 'Run coordination'}
                </Button>
              </CardContent>
            </Card>

            {coordResult && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between gap-2">
                    <span>Result</span>
                    <Badge variant="outline">{coordResult.mode}</Badge>
                  </CardTitle>
                  <CardDescription>
                    {coordResult.duration_ms != null ? `${coordResult.duration_ms} ms` : ''}
                    {coordResult.models_used?.length
                      ? ` · ${coordResult.models_used.map((m) => m.name).join(', ')}`
                      : ''}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {coordResult.verdict && (
                    <div className="rounded-lg border p-3 text-sm space-y-1">
                      <p className="font-medium">Judge verdict</p>
                      <p className="text-muted-foreground">{coordResult.verdict.reason}</p>
                      {coordResult.verdict.confidence != null && (
                        <p>Confidence: {(coordResult.verdict.confidence * 100).toFixed(0)}%</p>
                      )}
                    </div>
                  )}
                  {coordResult.selected && (
                    <p className="text-sm text-muted-foreground">
                      Selected: <span className="font-medium text-foreground">{coordResult.selected.name}</span>
                      {' '}({coordResult.selected.provider}/{coordResult.selected.model_id})
                    </p>
                  )}
                  <div className="rounded-lg bg-muted/40 p-4 whitespace-pre-wrap text-sm">
                    {coordResult.final_answer || 'No answer returned.'}
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>

        <Dialog open={showAddModelDialog} onOpenChange={setShowAddModelDialog}>
          <DialogContent className="max-w-xl">
            <DialogHeader>
              <DialogTitle>Add AI Model</DialogTitle>
              <DialogDescription>
                Connect a new AI model to your multi-model intelligence system
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Provider</Label>
                <Select value={provider} onValueChange={setProvider}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select provider" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="groq">Groq</SelectItem>
                    <SelectItem value="openai">OpenAI</SelectItem>
                    <SelectItem value="anthropic">Anthropic</SelectItem>
                    <SelectItem value="google">Google</SelectItem>
                    <SelectItem value="mistral">Mistral</SelectItem>
                    <SelectItem value="custom">Custom / Self-hosted</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Model</Label>
                <Select
                  value={modelId}
                  onValueChange={(v) => {
                    setModelId(v);
                    const opt = (PROVIDER_MODELS[provider] || []).find((o) => o.id === v);
                    if (opt) {
                      setModelType(opt.type);
                      setAlias(opt.label);
                    }
                  }}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select model" />
                  </SelectTrigger>
                  <SelectContent>
                    {(PROVIDER_MODELS[provider] || []).map((opt) => (
                      <SelectItem key={opt.id} value={opt.id}>
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="apiKey">API Key (optional)</Label>
                <Input
                  id="apiKey"
                  type="password"
                  placeholder="sk-... / gsk_..."
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="alias">Model Alias</Label>
                <Input
                  id="alias"
                  placeholder="My GPT-4 Instance"
                  value={alias}
                  onChange={(e) => setAlias(e.target.value)}
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowAddModelDialog(false)} disabled={isSaving}>
                Cancel
              </Button>
              <Button onClick={handleAddModel} disabled={isSaving}>
                {isSaving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                Add Model
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </motion.div>
    </AppLayout>
  );
}
