"use client";

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import {
  Cpu,
  Search,
  Plus,
  Play,
  Settings,
  Code2,
  Terminal,
  Sparkles,
  ChevronRight,
  Clock,
  CheckCircle2,
  XCircle,
  Loader2,
  Copy,
  ExternalLink,
  Zap,
  Database,
  Globe,
  FileCode,
  Layers,
  RefreshCw,
  MoreVertical,
  Trash2,
  Star,
  StarOff,
  AlertCircle,
} from 'lucide-react';
import { AppLayout } from '@/components/layout/AppLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { cn } from '@/lib/utils';
import { getMCPTools, executeMCPTool, type MCPTool } from '@/lib/api';

type CategoryIcon = typeof FileCode;

const CATEGORY_META: Record<string, { icon: CategoryIcon; color: string }> = {
  filesystem: { icon: FileCode, color: 'bg-blue-500' },
  system: { icon: FileCode, color: 'bg-blue-500' },
  database: { icon: Database, color: 'bg-green-500' },
  data: { icon: Layers, color: 'bg-cyan-500' },
  network: { icon: Globe, color: 'bg-purple-500' },
  search: { icon: Globe, color: 'bg-purple-500' },
  execution: { icon: Terminal, color: 'bg-orange-500' },
  computation: { icon: Terminal, color: 'bg-orange-500' },
  ai: { icon: Sparkles, color: 'bg-pink-500' },
  communication: { icon: Globe, color: 'bg-indigo-500' },
  productivity: { icon: Layers, color: 'bg-teal-500' },
  general: { icon: Cpu, color: 'bg-slate-500' },
};

interface DisplayTool {
  id: string;
  name: string;
  description: string;
  category: string;
  icon: CategoryIcon;
  color: string;
  operations: string[];
  isInstalled: boolean;
  isFavorite: boolean;
  lastUsed: string | null;
  usageCount: number;
  successRate: number;
  parametersSchema: Record<string, unknown>;
}

interface ExecutionHistoryItem {
  id: string;
  tool: string;
  operation: string;
  status: 'success' | 'error';
  duration: string;
  timestamp: string;
  input: Record<string, unknown>;
  output: Record<string, unknown>;
}

function mapTool(tool: MCPTool): DisplayTool {
  const category = (tool.category || 'general').toLowerCase();
  const meta = CATEGORY_META[category] ?? CATEGORY_META.general;
  const schemaKeys = Object.keys(tool.parameters_schema || {}).filter((k) => !k.startsWith('_'));
  const operations =
    schemaKeys.length > 0
      ? schemaKeys
      : (tool.capabilities || []).length > 0
        ? tool.capabilities
        : ['execute'];

  return {
    id: tool.id || tool.name,
    name: tool.name,
    description: tool.description || 'No description available',
    category,
    icon: meta.icon,
    color: meta.color,
    operations,
    isInstalled: tool.is_active !== false,
    isFavorite: (tool.usage_count ?? 0) > 100,
    lastUsed: (tool.usage_count ?? 0) > 0 ? 'Recently' : null,
    usageCount: tool.usage_count ?? 0,
    successRate: tool.success_rate ?? 1,
    parametersSchema: tool.parameters_schema || {},
  };
}

function formatRelativeTime(date: Date): string {
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
  if (seconds < 60) return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)} min ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return date.toLocaleString();
}

export default function MCPPage() {
  const [tools, setTools] = useState<DisplayTool[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedToolId, setSelectedToolId] = useState<string>('');
  const [selectedOperation, setSelectedOperation] = useState<string>('');
  const [parametersJson, setParametersJson] = useState('{}');
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState<{
    success: boolean;
    output: Record<string, unknown>;
    duration: string;
  } | null>(null);
  const [executionHistory, setExecutionHistory] = useState<ExecutionHistoryItem[]>([]);
  const [activeTab, setActiveTab] = useState('tools');

  const loadTools = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await getMCPTools();
      const mapped = (res.tools || []).map(mapTool);
      setTools(mapped);
      if (mapped.length > 0 && !selectedToolId) {
        const first = mapped.find((t) => t.isInstalled) || mapped[0];
        setSelectedToolId(first.id);
        setSelectedOperation(first.operations[0] || 'execute');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load MCP tools');
      setTools([]);
    } finally {
      setLoading(false);
    }
  }, [selectedToolId]);

  useEffect(() => {
    setTimeout(() => { loadTools(); }, 0)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const categories = useMemo(() => {
    const cats = new Set(tools.map((t) => t.category));
    return ['all', ...Array.from(cats).sort()];
  }, [tools]);

  const filteredTools = tools.filter((tool) => {
    const matchesSearch =
      tool.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      tool.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || tool.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const selectedTool = tools.find((t) => t.id === selectedToolId) || null;
  const executableTools = tools.filter((t) => t.isInstalled);

  const totalUsage = tools.reduce((sum, t) => sum + t.usageCount, 0);
  const avgSuccessRate =
    tools.length > 0
      ? tools.reduce((sum, t) => sum + t.successRate, 0) / tools.length
      : 0;

  const handleSelectTool = (tool: DisplayTool) => {
    setSelectedToolId(tool.id);
    setSelectedOperation(tool.operations[0] || 'execute');
    setActiveTab('execute');
    setExecutionResult(null);
  };

  const handleExecute = async () => {
    if (!selectedToolId) return;

    let parameters: Record<string, unknown> = {};
    try {
      parameters = parametersJson.trim() ? JSON.parse(parametersJson) : {};
    } catch {
      setExecutionResult({
        success: false,
        output: { error: 'Invalid JSON parameters' },
        duration: '0ms',
      });
      return;
    }

    if (selectedOperation && selectedOperation !== 'execute' && !parameters.operation) {
      parameters = { ...parameters, operation: selectedOperation };
    }

    setIsExecuting(true);
    setExecutionResult(null);
    const started = new Date().getTime();

    try {
      const res = await executeMCPTool(selectedToolId, parameters);
      const durationMs = Math.round((new Date().getTime() - started) * 10) / 10;
      const duration =
        typeof res.result?.execution_time === 'number'
          ? `${Math.round(Number(res.result.execution_time) * 1000)}ms`
          : `${durationMs}ms`;

      const output = (res.result?.result as Record<string, unknown>) || res.result || {};
      setExecutionResult({
        success: res.success,
        output: typeof output === 'object' ? output : { result: output },
        duration,
      });

      setExecutionHistory((prev) => [
        {
          id: res.execution_id || String(Date.now()),
          tool: selectedTool?.name || selectedToolId,
          operation: selectedOperation || 'execute',
          status: res.success ? 'success' : 'error',
          duration,
          timestamp: formatRelativeTime(new Date()),
          input: parameters,
          output: typeof output === 'object' ? output : { result: output },
        },
        ...prev,
      ]);
    } catch (err) {
      const duration = `${new Date().getTime() - started}ms`;
      const message = err instanceof Error ? err.message : 'Execution failed';
      setExecutionResult({
        success: false,
        output: { error: message },
        duration,
      });
      setExecutionHistory((prev) => [
        {
          id: String(Date.now()),
          tool: selectedTool?.name || selectedToolId,
          operation: selectedOperation || 'execute',
          status: 'error',
          duration,
          timestamp: formatRelativeTime(new Date()),
          input: parameters,
          output: { error: message },
        },
        ...prev,
      ]);
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <AppLayout>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-6"
      >
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-3">
              <Cpu className="h-8 w-8 text-primary" />
              MCP Tools
            </h1>
            <p className="text-muted-foreground mt-1">
              Model Context Protocol tools for extended capabilities
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Button variant="outline" className="gap-2" onClick={loadTools} disabled={loading}>
              <RefreshCw className={cn('h-4 w-4', loading && 'animate-spin')} />
              Sync Tools
            </Button>
            <Button className="gap-2 bg-gradient-to-r from-indigo-500 to-purple-500 hover:opacity-90">
              <Plus className="h-4 w-4" />
              Register Tool
            </Button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { label: 'Total Tools', value: tools.length, icon: Cpu, color: 'text-indigo-500' },
            {
              label: 'Installed',
              value: tools.filter((t) => t.isInstalled).length,
              icon: CheckCircle2,
              color: 'text-green-500',
            },
            {
              label: 'Total Executions',
              value: totalUsage.toLocaleString(),
              icon: Zap,
              color: 'text-orange-500',
            },
            {
              label: 'Avg Success',
              value: `${(avgSuccessRate * 100).toFixed(1)}%`,
              icon: Clock,
              color: 'text-blue-500',
            },
          ].map((stat, index) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <Card className="hover:shadow-md transition-shadow">
                <CardContent className="flex items-center gap-4 p-6">
                  <div
                    className={cn(
                      'flex h-12 w-12 items-center justify-center rounded-xl bg-muted',
                      stat.color
                    )}
                  >
                    <stat.icon className="h-6 w-6" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold">{stat.value}</p>
                    <p className="text-sm text-muted-foreground">{stat.label}</p>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>

        {error && (
          <Card className="border-destructive/50 bg-destructive/5">
            <CardContent className="flex items-center gap-3 p-4 text-sm text-destructive">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
              <Button variant="outline" size="sm" className="ml-auto" onClick={loadTools}>
                Retry
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Main Content */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
          <TabsList>
            <TabsTrigger value="tools" className="gap-2">
              <Cpu className="h-4 w-4" />
              Tools
            </TabsTrigger>
            <TabsTrigger value="execute" className="gap-2">
              <Play className="h-4 w-4" />
              Execute
            </TabsTrigger>
            <TabsTrigger value="history" className="gap-2">
              <Clock className="h-4 w-4" />
              History
            </TabsTrigger>
          </TabsList>

          <TabsContent value="tools" className="space-y-4">
            <Card>
              <CardContent className="p-4">
                <div className="flex flex-col sm:flex-row gap-4">
                  <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="Search tools..."
                      className="pl-10"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                  </div>
                  <div className="flex gap-2 flex-wrap">
                    {categories.map((category) => (
                      <Button
                        key={category}
                        variant={selectedCategory === category ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setSelectedCategory(category)}
                        className="capitalize"
                      >
                        {category}
                      </Button>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>

            {loading ? (
              <div className="flex items-center justify-center py-24 text-muted-foreground">
                <Loader2 className="h-8 w-8 animate-spin mr-3" />
                Loading MCP tools...
              </div>
            ) : filteredTools.length === 0 ? (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-16 text-muted-foreground">
                  <Cpu className="h-10 w-10 mb-3 opacity-50" />
                  <p className="font-medium">No tools found</p>
                  <p className="text-sm">Try adjusting filters or sync tools from the registry</p>
                </CardContent>
              </Card>
            ) : (
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {filteredTools.map((tool, index) => {
                  const Icon = tool.icon;
                  return (
                    <motion.div
                      key={tool.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 }}
                    >
                      <Card className="group hover:shadow-lg transition-all duration-300 overflow-hidden">
                        <div className={cn('h-1.5', tool.color)} />
                        <CardHeader className="pb-2">
                          <div className="flex items-start justify-between">
                            <div className="flex items-center gap-3">
                              <div
                                className={cn(
                                  'flex h-10 w-10 items-center justify-center rounded-lg',
                                  tool.color
                                )}
                              >
                                <Icon className="h-5 w-5 text-white" />
                              </div>
                              <div>
                                <CardTitle className="text-lg flex items-center gap-2">
                                  {tool.name}
                                  {tool.isFavorite && (
                                    <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />
                                  )}
                                </CardTitle>
                                <Badge variant="secondary" className="text-xs capitalize mt-1">
                                  {tool.category}
                                </Badge>
                              </div>
                            </div>
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="icon" className="h-8 w-8">
                                  <MoreVertical className="h-4 w-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuItem>
                                  <Settings className="h-4 w-4 mr-2" />
                                  Configure
                                </DropdownMenuItem>
                                <DropdownMenuItem>
                                  <Code2 className="h-4 w-4 mr-2" />
                                  View Schema
                                </DropdownMenuItem>
                                <DropdownMenuItem>
                                  {tool.isFavorite ? (
                                    <>
                                      <StarOff className="h-4 w-4 mr-2" />
                                      Remove from Favorites
                                    </>
                                  ) : (
                                    <>
                                      <Star className="h-4 w-4 mr-2" />
                                      Add to Favorites
                                    </>
                                  )}
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem className="text-destructive">
                                  <Trash2 className="h-4 w-4 mr-2" />
                                  Uninstall
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </div>
                        </CardHeader>
                        <CardContent className="pb-4">
                          <p className="text-sm text-muted-foreground mb-4">{tool.description}</p>

                          <Collapsible>
                            <CollapsibleTrigger asChild>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="w-full justify-between text-muted-foreground"
                              >
                                <span>{tool.operations.length} Operations</span>
                                <ChevronRight className="h-4 w-4" />
                              </Button>
                            </CollapsibleTrigger>
                            <CollapsibleContent className="pt-2">
                              <div className="flex flex-wrap gap-1">
                                {tool.operations.map((op) => (
                                  <Badge key={op} variant="outline" className="text-xs">
                                    {op}
                                  </Badge>
                                ))}
                              </div>
                            </CollapsibleContent>
                          </Collapsible>
                        </CardContent>
                        <CardFooter className="border-t pt-4 flex items-center justify-between">
                          <div className="flex items-center gap-4 text-xs text-muted-foreground">
                            {tool.isInstalled ? (
                              <>
                                <span className="flex items-center gap-1">
                                  <Clock className="h-3 w-3" />
                                  {(tool.successRate * 100).toFixed(0)}% success
                                </span>
                                <span>{tool.usageCount} uses</span>
                              </>
                            ) : (
                              <span>Inactive</span>
                            )}
                          </div>
                          <Button
                            size="sm"
                            variant={tool.isInstalled ? 'outline' : 'default'}
                            className="gap-2"
                            onClick={() => handleSelectTool(tool)}
                          >
                            {tool.isInstalled ? (
                              <>
                                <Play className="h-3 w-3" />
                                Execute
                              </>
                            ) : (
                              <>
                                <Plus className="h-3 w-3" />
                                Install
                              </>
                            )}
                          </Button>
                        </CardFooter>
                      </Card>
                    </motion.div>
                  );
                })}
              </div>
            )}
          </TabsContent>

          <TabsContent value="execute" className="space-y-4">
            <div className="grid gap-6 lg:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle>Execute Tool</CardTitle>
                  <CardDescription>Select a tool and configure parameters</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>Select Tool</Label>
                    <Select
                      value={selectedToolId}
                      onValueChange={(id) => {
                        setSelectedToolId(id);
                        const tool = tools.find((t) => t.id === id);
                        setSelectedOperation(tool?.operations[0] || 'execute');
                        setExecutionResult(null);
                      }}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Choose a tool" />
                      </SelectTrigger>
                      <SelectContent>
                        {executableTools.map((tool) => (
                          <SelectItem key={tool.id} value={tool.id}>
                            <div className="flex items-center gap-2">
                              <tool.icon className="h-4 w-4" />
                              {tool.name}
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>Operation</Label>
                    <Select value={selectedOperation} onValueChange={setSelectedOperation}>
                      <SelectTrigger>
                        <SelectValue placeholder="Choose operation" />
                      </SelectTrigger>
                      <SelectContent>
                        {(selectedTool?.operations || ['execute']).map((op) => (
                          <SelectItem key={op} value={op}>
                            {op}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>Parameters (JSON)</Label>
                    <Textarea
                      placeholder='{"path": "/example/file.txt"}'
                      className="font-mono text-sm min-h-[150px]"
                      value={parametersJson}
                      onChange={(e) => setParametersJson(e.target.value)}
                    />
                  </div>

                  <Button
                    className="w-full gap-2"
                    onClick={handleExecute}
                    disabled={isExecuting || !selectedToolId}
                  >
                    {isExecuting ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Executing...
                      </>
                    ) : (
                      <>
                        <Play className="h-4 w-4" />
                        Execute Tool
                      </>
                    )}
                  </Button>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>Execution Result</CardTitle>
                      <CardDescription>Output from the tool execution</CardDescription>
                    </div>
                    {executionResult && (
                      <Button
                        variant="outline"
                        size="sm"
                        className="gap-2"
                        onClick={() =>
                          navigator.clipboard.writeText(
                            JSON.stringify(executionResult.output, null, 2)
                          )
                        }
                      >
                        <Copy className="h-4 w-4" />
                        Copy
                      </Button>
                    )}
                  </div>
                </CardHeader>
                <CardContent>
                  {isExecuting ? (
                    <div className="flex items-center justify-center h-[250px]">
                      <div className="text-center">
                        <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary mb-4" />
                        <p className="text-muted-foreground">Executing tool...</p>
                      </div>
                    </div>
                  ) : executionResult ? (
                    <div className="space-y-4">
                      <div className="flex items-center gap-2">
                        {executionResult.success ? (
                          <CheckCircle2 className="h-5 w-5 text-green-500" />
                        ) : (
                          <XCircle className="h-5 w-5 text-red-500" />
                        )}
                        <span className="font-medium">
                          {executionResult.success ? 'Success' : 'Failed'}
                        </span>
                        <Badge variant="secondary" className="ml-auto">
                          {executionResult.duration}
                        </Badge>
                      </div>
                      <div className="rounded-lg bg-muted p-4">
                        <pre className="text-sm font-mono whitespace-pre-wrap overflow-x-auto">
                          {JSON.stringify(executionResult.output, null, 2)}
                        </pre>
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-center justify-center h-[250px] text-muted-foreground">
                      <div className="text-center">
                        <Terminal className="h-8 w-8 mx-auto mb-4 opacity-50" />
                        <p>Execute a tool to see results</p>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="history" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Execution History</CardTitle>
                <CardDescription>Recent tool executions and their results</CardDescription>
              </CardHeader>
              <CardContent>
                {executionHistory.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
                    <Clock className="h-10 w-10 mb-3 opacity-50" />
                    <p className="font-medium">No executions yet</p>
                    <p className="text-sm">Run a tool to see history here</p>
                  </div>
                ) : (
                  <ScrollArea className="h-[500px]">
                    <div className="space-y-4">
                      {executionHistory.map((execution, index) => (
                        <motion.div
                          key={execution.id}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: index * 0.05 }}
                          className="flex items-start gap-4 p-4 rounded-xl bg-muted/50 hover:bg-muted transition-colors"
                        >
                          <div
                            className={cn(
                              'flex h-10 w-10 items-center justify-center rounded-lg shrink-0',
                              execution.status === 'success' ? 'bg-green-500/10' : 'bg-red-500/10'
                            )}
                          >
                            {execution.status === 'success' ? (
                              <CheckCircle2 className="h-5 w-5 text-green-500" />
                            ) : (
                              <XCircle className="h-5 w-5 text-red-500" />
                            )}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <span className="font-medium">{execution.tool}</span>
                              <Badge variant="outline" className="text-xs">
                                {execution.operation}
                              </Badge>
                            </div>
                            <div className="flex items-center gap-4 mt-1 text-sm text-muted-foreground">
                              <span className="flex items-center gap-1">
                                <Clock className="h-3 w-3" />
                                {execution.timestamp}
                              </span>
                              <span className="flex items-center gap-1">
                                <Zap className="h-3 w-3" />
                                {execution.duration}
                              </span>
                            </div>
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="gap-2"
                            onClick={() =>
                              setExecutionResult({
                                success: execution.status === 'success',
                                output: execution.output,
                                duration: execution.duration,
                              })
                            }
                          >
                            <ExternalLink className="h-4 w-4" />
                            Details
                          </Button>
                        </motion.div>
                      ))}
                    </div>
                  </ScrollArea>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </motion.div>
    </AppLayout>
  );
}
