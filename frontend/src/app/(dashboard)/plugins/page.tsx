"use client";

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Puzzle,
  Search,
  Grid3X3,
  List,
  Star,
  Download,
  Settings,
  Trash2,
  CheckCircle2,
  Shield,
  Database,
  MessageSquare,
  BarChart3,
  Globe,
  Bot,
  Sparkles,
  Filter,
  RefreshCw,
  type LucideIcon,
} from 'lucide-react';
import apiClient from '@/lib/api';
import { toast } from '@/hooks/use-toast';
import { axiosErrorDetail, errorMessage, paginatedItems } from '@/types/api';
import { AppLayout } from '@/components/layout/AppLayout';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
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
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import { cn } from '@/lib/utils';

const categories = [
  { id: 'all', label: 'All Plugins', icon: Grid3X3 },
  { id: 'ai', label: 'AI & ML', icon: Bot },
  { id: 'custom_agent', label: 'Custom Agents', icon: Bot },
  { id: 'integration', label: 'Integrations', icon: Globe },
  { id: 'integrations', label: 'Integrations', icon: Globe },
  { id: 'analytics', label: 'Analytics', icon: BarChart3 },
  { id: 'security', label: 'Security', icon: Shield },
  { id: 'data', label: 'Data', icon: Database },
  { id: 'data_source', label: 'Data Sources', icon: Database },
  { id: 'communication', label: 'Communication', icon: MessageSquare },
  { id: 'notification', label: 'Notifications', icon: MessageSquare },
  { id: 'tool', label: 'Tools', icon: Puzzle },
];

const CATEGORY_ICONS: Record<string, LucideIcon> = {
  ai: Bot,
  custom_agent: Bot,
  integration: Globe,
  integrations: Globe,
  analytics: BarChart3,
  security: Shield,
  data: Database,
  data_source: Database,
  communication: MessageSquare,
  notification: MessageSquare,
  tool: Puzzle,
};

type PluginUI = {
  id: string;
  name: string;
  description: string;
  icon: LucideIcon;
  category: string;
  rating: number;
  downloads: number;
  installed: boolean;
  enabled: boolean;
  verified: boolean;
  author: string;
  version: string;
  tags: string[];
  installationId?: string;
};

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function str(value: unknown, fallback = ''): string {
  if (value == null) return fallback;
  return String(value);
}

function num(value: unknown, fallback = 0): number {
  const n = typeof value === 'number' ? value : Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function extractList<T>(data: unknown, keys: string[]): T[] {
  if (Array.isArray(data)) return data as T[];
  if (!data || typeof data !== 'object') return [];
  const obj = data as Record<string, unknown>;
  for (const key of keys) {
    if (Array.isArray(obj[key])) return obj[key] as T[];
  }
  return paginatedItems(data as { results?: T[] });
}

function normalizeCategory(raw: string): string {
  const c = raw.toLowerCase().replace(/-/g, '_');
  if (c === 'integrations') return 'integration';
  if (c === 'ml' || c === 'ai_ml') return 'ai';
  return c;
}

function mapPlugin(
  raw: Record<string, unknown>,
  installedIds: Set<string>,
  enabledIds: Set<string>,
  installationByPlugin: Map<string, string>
): PluginUI {
  const category = normalizeCategory(str(raw.category, 'tool'));
  const tagsRaw = raw.tags || asRecord(raw.manifest).tags || [];
  const tags = Array.isArray(tagsRaw)
    ? tagsRaw.map((t) => str(t)).filter(Boolean)
    : [];
  const id = str(raw.id);

  return {
    id,
    name: str(raw.name, 'Untitled Plugin'),
    description: str(raw.description, 'No description'),
    icon: CATEGORY_ICONS[category] || Puzzle,
    category,
    rating: num(raw.rating ?? raw.avg_rating, 0),
    downloads: num(raw.download_count ?? raw.downloads ?? raw.installations_count, 0),
    installed: installedIds.has(id) || Boolean(raw.is_installed),
    enabled: enabledIds.has(id) || Boolean(raw.is_active),
    verified: Boolean(raw.is_verified ?? raw.verified),
    author: str(raw.author, 'Unknown'),
    version: str(raw.version, '1.0.0'),
    tags: tags.length > 0 ? tags : [category],
    installationId: installationByPlugin.get(id),
  };
}

export default function PluginsPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [category, setCategory] = useState('all');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [selectedPlugin, setSelectedPlugin] = useState<PluginUI | null>(null);
  const [plugins, setPlugins] = useState<PluginUI[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [actionId, setActionId] = useState<string | null>(null);

  const categoryOptions = useMemo(() => {
    const seen = new Set<string>();
    return categories.filter((c) => {
      if (c.id === 'all') return true;
      if (seen.has(c.label)) return false;
      seen.add(c.label);
      return true;
    });
  }, []);

  const load = useCallback(async () => {
    setIsLoading(true);
    try {
      const [pluginsRes, installationsRes] = await Promise.all([
        apiClient.getPlugins(),
        apiClient.getPluginInstallations().catch(() => ({ data: { results: [] } })),
      ]);

      const pluginRows = extractList<Record<string, unknown>>(pluginsRes.data, [
        'results',
        'plugins',
      ]);
      const installationRows = extractList<Record<string, unknown>>(
        installationsRes.data,
        ['results', 'installations']
      );

      const installedIds = new Set<string>();
      const enabledIds = new Set<string>();
      const installationByPlugin = new Map<string, string>();

      for (const inst of installationRows) {
        const pluginId = str(
          typeof inst.plugin === 'object'
            ? asRecord(inst.plugin).id
            : inst.plugin || inst.plugin_id
        );
        if (!pluginId) continue;
        installedIds.add(pluginId);
        installationByPlugin.set(pluginId, str(inst.id));
        if (inst.is_enabled !== false) enabledIds.add(pluginId);
      }

      setPlugins(
        pluginRows.map((row) =>
          mapPlugin(row, installedIds, enabledIds, installationByPlugin)
        )
      );
    } catch (e: unknown) {
      toast({
        title: 'Failed to load plugins',
        description: axiosErrorDetail(e) || errorMessage(e),
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    setTimeout(() => { load(); }, 0)
  }, [load]);

  const installedPlugins = useMemo(
    () => plugins.filter((p) => p.installed).map((p) => p.id),
    [plugins]
  );
  const enabledPlugins = useMemo(
    () => plugins.filter((p) => p.enabled).map((p) => p.id),
    [plugins]
  );

  const filteredPlugins = plugins.filter((plugin) => {
    const matchesSearch =
      plugin.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      plugin.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory =
      category === 'all' ||
      plugin.category === category ||
      (category === 'integrations' && plugin.category === 'integration') ||
      (category === 'integration' && plugin.category === 'integrations');
    return matchesSearch && matchesCategory;
  });

  const featuredPlugins = useMemo(
    () =>
      [...plugins]
        .sort((a, b) => b.rating - a.rating || b.downloads - a.downloads)
        .slice(0, 3),
    [plugins]
  );

  const toggleInstall = async (plugin: PluginUI) => {
    setActionId(plugin.id);
    try {
      if (plugin.installed) {
        await apiClient.uninstallPlugin(plugin.id);
        toast({ title: 'Plugin uninstalled' });
      } else {
        await apiClient.installPlugin(plugin.id);
        toast({ title: 'Plugin installed' });
      }
      await load();
      if (selectedPlugin?.id === plugin.id) {
        setSelectedPlugin(null);
      }
    } catch (e: unknown) {
      toast({
        title: plugin.installed ? 'Uninstall failed' : 'Install failed',
        description: axiosErrorDetail(e) || errorMessage(e),
        variant: 'destructive',
      });
    } finally {
      setActionId(null);
    }
  };

  const toggleEnabled = (plugin: PluginUI) => {
    if (!plugin.installed) return;
    setPlugins((prev) =>
      prev.map((p) => (p.id === plugin.id ? { ...p, enabled: !p.enabled } : p))
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
              <Puzzle className="h-8 w-8 text-primary" />
              Plugin Marketplace
            </h1>
            <p className="text-muted-foreground mt-1">
              Extend your agents with powerful plugins
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="icon" onClick={load} disabled={isLoading}>
              <RefreshCw className={cn('h-4 w-4', isLoading && 'animate-spin')} />
            </Button>
            <Badge variant="secondary" className="gap-1">
              <Download className="h-3 w-3" />
              {installedPlugins.length} Installed
            </Badge>
          </div>
        </div>

        <Tabs defaultValue="browse" className="space-y-6">
          <TabsList>
            <TabsTrigger value="browse">Browse</TabsTrigger>
            <TabsTrigger value="installed">Installed ({installedPlugins.length})</TabsTrigger>
            <TabsTrigger value="updates">Updates</TabsTrigger>
          </TabsList>

          <TabsContent value="browse" className="space-y-6">
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search plugins..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
              <Select value={category} onValueChange={setCategory}>
                <SelectTrigger className="w-full sm:w-48">
                  <Filter className="h-4 w-4 mr-2" />
                  <SelectValue placeholder="Category" />
                </SelectTrigger>
                <SelectContent>
                  {categoryOptions.map((cat) => (
                    <SelectItem key={cat.id} value={cat.id}>
                      <div className="flex items-center gap-2">
                        <cat.icon className="h-4 w-4" />
                        {cat.label}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <div className="flex items-center gap-1 border rounded-lg p-1">
                <Button
                  variant={viewMode === 'grid' ? 'secondary' : 'ghost'}
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => setViewMode('grid')}
                >
                  <Grid3X3 className="h-4 w-4" />
                </Button>
                <Button
                  variant={viewMode === 'list' ? 'secondary' : 'ghost'}
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => setViewMode('list')}
                >
                  <List className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {isLoading ? (
              <div className="flex items-center justify-center py-16 text-muted-foreground gap-2">
                <RefreshCw className="h-5 w-5 animate-spin" />
                Loading marketplace…
              </div>
            ) : plugins.length === 0 ? (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-16 text-center">
                  <Puzzle className="h-12 w-12 text-muted-foreground mb-4" />
                  <h3 className="font-semibold">No plugins available</h3>
                  <p className="text-sm text-muted-foreground">
                    The marketplace is empty right now
                  </p>
                </CardContent>
              </Card>
            ) : (
              <>
                {featuredPlugins.length > 0 && (
                  <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-indigo-500/20 via-purple-500/20 to-pink-500/20 p-6 border">
                    <div className="flex items-center gap-2 mb-4">
                      <Sparkles className="h-5 w-5 text-yellow-500" />
                      <span className="font-semibold">Featured Plugins</span>
                    </div>
                    <div className="grid gap-4 md:grid-cols-3">
                      {featuredPlugins.map((plugin) => {
                        const Icon = plugin.icon;
                        return (
                          <div
                            key={plugin.id}
                            className="bg-background/80 backdrop-blur-sm rounded-xl p-4 border cursor-pointer hover:border-primary/50 transition-colors"
                            onClick={() => setSelectedPlugin(plugin)}
                          >
                            <div className="flex items-center gap-3 mb-2">
                              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                                <Icon className="h-5 w-5 text-primary" />
                              </div>
                              <div>
                                <p className="font-medium">{plugin.name}</p>
                                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                                  <Star className="h-3 w-3 fill-yellow-500 text-yellow-500" />
                                  {plugin.rating.toFixed(1)}
                                </div>
                              </div>
                            </div>
                            <p className="text-sm text-muted-foreground line-clamp-2">
                              {plugin.description}
                            </p>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                <div
                  className={cn(
                    viewMode === 'grid'
                      ? 'grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4'
                      : 'space-y-4'
                  )}
                >
                  <AnimatePresence mode="popLayout">
                    {filteredPlugins.length === 0 ? (
                      <div className="col-span-full flex flex-col items-center justify-center py-12 text-center">
                        <Search className="h-10 w-10 text-muted-foreground mb-3" />
                        <h3 className="font-semibold">No matching plugins</h3>
                        <p className="text-sm text-muted-foreground">Try a different search or category</p>
                      </div>
                    ) : (
                      filteredPlugins.map((plugin, index) => {
                        const Icon = plugin.icon;
                        return (
                          <motion.div
                            key={plugin.id}
                            layout
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.9 }}
                            transition={{ delay: index * 0.03 }}
                          >
                            <Card
                              className={cn(
                                'group cursor-pointer transition-all hover:shadow-lg hover:border-primary/50',
                                viewMode === 'list' && 'flex'
                              )}
                              onClick={() => setSelectedPlugin(plugin)}
                            >
                              <CardContent
                                className={cn(
                                  'p-4',
                                  viewMode === 'list' && 'flex items-center gap-4 flex-1'
                                )}
                              >
                                <div
                                  className={cn(
                                    'flex items-start gap-3',
                                    viewMode === 'list' && 'flex-1'
                                  )}
                                >
                                  <div
                                    className={cn(
                                      'flex items-center justify-center rounded-xl bg-gradient-to-br transition-transform group-hover:scale-110',
                                      viewMode === 'grid' ? 'h-12 w-12' : 'h-10 w-10',
                                      plugin.category === 'ai' && 'from-purple-500/20 to-pink-500/20',
                                      (plugin.category === 'integration' ||
                                        plugin.category === 'integrations') &&
                                        'from-blue-500/20 to-cyan-500/20',
                                      plugin.category === 'analytics' &&
                                        'from-green-500/20 to-emerald-500/20',
                                      plugin.category === 'security' &&
                                        'from-red-500/20 to-orange-500/20',
                                      (plugin.category === 'data' ||
                                        plugin.category === 'data_source') &&
                                        'from-yellow-500/20 to-amber-500/20',
                                      (plugin.category === 'communication' ||
                                        plugin.category === 'notification') &&
                                        'from-indigo-500/20 to-violet-500/20'
                                    )}
                                  >
                                    <Icon
                                      className={cn(
                                        'text-primary',
                                        viewMode === 'grid' ? 'h-6 w-6' : 'h-5 w-5'
                                      )}
                                    />
                                  </div>
                                  <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2">
                                      <p className="font-semibold truncate">{plugin.name}</p>
                                      {plugin.verified && (
                                        <CheckCircle2 className="h-4 w-4 text-blue-500 shrink-0" />
                                      )}
                                    </div>
                                    <p
                                      className={cn(
                                        'text-sm text-muted-foreground',
                                        viewMode === 'grid' ? 'line-clamp-2 mt-1' : 'line-clamp-1'
                                      )}
                                    >
                                      {plugin.description}
                                    </p>
                                    {viewMode === 'grid' && (
                                      <div className="flex flex-wrap gap-1 mt-2">
                                        {plugin.tags.slice(0, 2).map((tag) => (
                                          <Badge key={tag} variant="secondary" className="text-xs">
                                            {tag}
                                          </Badge>
                                        ))}
                                      </div>
                                    )}
                                  </div>
                                </div>
                                <div
                                  className={cn(
                                    'flex items-center justify-between',
                                    viewMode === 'grid' ? 'mt-4' : 'gap-4'
                                  )}
                                >
                                  <div className="flex items-center gap-3 text-sm text-muted-foreground">
                                    <span className="flex items-center gap-1">
                                      <Star className="h-3 w-3 fill-yellow-500 text-yellow-500" />
                                      {plugin.rating.toFixed(1)}
                                    </span>
                                    <span className="flex items-center gap-1">
                                      <Download className="h-3 w-3" />
                                      {plugin.downloads >= 1000
                                        ? `${(plugin.downloads / 1000).toFixed(0)}k`
                                        : plugin.downloads}
                                    </span>
                                  </div>
                                  <Button
                                    size="sm"
                                    variant={
                                      installedPlugins.includes(plugin.id) ? 'secondary' : 'default'
                                    }
                                    disabled={actionId === plugin.id}
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      toggleInstall(plugin);
                                    }}
                                  >
                                    {actionId === plugin.id ? (
                                      <RefreshCw className="h-4 w-4 animate-spin" />
                                    ) : installedPlugins.includes(plugin.id) ? (
                                      <>
                                        <CheckCircle2 className="h-4 w-4 mr-1" />
                                        Installed
                                      </>
                                    ) : (
                                      <>
                                        <Download className="h-4 w-4 mr-1" />
                                        Install
                                      </>
                                    )}
                                  </Button>
                                </div>
                              </CardContent>
                            </Card>
                          </motion.div>
                        );
                      })
                    )}
                  </AnimatePresence>
                </div>
              </>
            )}
          </TabsContent>

          <TabsContent value="installed" className="space-y-6">
            <div className="grid gap-4">
              {isLoading ? (
                <div className="flex items-center justify-center py-16 text-muted-foreground gap-2">
                  <RefreshCw className="h-5 w-5 animate-spin" />
                  Loading installations…
                </div>
              ) : (
                plugins
                  .filter((p) => installedPlugins.includes(p.id))
                  .map((plugin) => {
                    const Icon = plugin.icon;
                    return (
                      <Card key={plugin.id}>
                        <CardContent className="flex items-center gap-4 p-4">
                          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
                            <Icon className="h-6 w-6 text-primary" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <p className="font-semibold">{plugin.name}</p>
                              <Badge variant="outline" className="text-xs">
                                v{plugin.version}
                              </Badge>
                              {plugin.verified && (
                                <CheckCircle2 className="h-4 w-4 text-blue-500" />
                              )}
                            </div>
                            <p className="text-sm text-muted-foreground">{plugin.description}</p>
                          </div>
                          <div className="flex items-center gap-4">
                            <div className="flex items-center gap-2">
                              <span className="text-sm text-muted-foreground">Enabled</span>
                              <Switch
                                checked={enabledPlugins.includes(plugin.id)}
                                onCheckedChange={() => toggleEnabled(plugin)}
                              />
                            </div>
                            <Button variant="ghost" size="icon">
                              <Settings className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="text-destructive"
                              disabled={actionId === plugin.id}
                              onClick={() => toggleInstall(plugin)}
                            >
                              {actionId === plugin.id ? (
                                <RefreshCw className="h-4 w-4 animate-spin" />
                              ) : (
                                <Trash2 className="h-4 w-4" />
                              )}
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    );
                  })
              )}
              {!isLoading && installedPlugins.length === 0 && (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <Puzzle className="h-12 w-12 text-muted-foreground mb-4" />
                  <h3 className="font-semibold">No plugins installed</h3>
                  <p className="text-sm text-muted-foreground">
                    Browse the marketplace to find plugins
                  </p>
                </div>
              )}
            </div>
          </TabsContent>

          <TabsContent value="updates" className="space-y-6">
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12 text-center">
                <CheckCircle2 className="h-12 w-12 text-green-500 mb-4" />
                <h3 className="font-semibold">All plugins are up to date</h3>
                <p className="text-sm text-muted-foreground">
                  Your installed plugins are running the latest versions
                </p>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        <Dialog open={!!selectedPlugin} onOpenChange={() => setSelectedPlugin(null)}>
          <DialogContent className="max-w-2xl">
            {selectedPlugin && (
              <>
                <DialogHeader>
                  <div className="flex items-start gap-4">
                    <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10">
                      <selectedPlugin.icon className="h-8 w-8 text-primary" />
                    </div>
                    <div>
                      <DialogTitle className="flex items-center gap-2">
                        {selectedPlugin.name}
                        {selectedPlugin.verified && (
                          <CheckCircle2 className="h-5 w-5 text-blue-500" />
                        )}
                      </DialogTitle>
                      <DialogDescription>By {selectedPlugin.author}</DialogDescription>
                      <div className="flex items-center gap-4 mt-2">
                        <span className="flex items-center gap-1 text-sm">
                          <Star className="h-4 w-4 fill-yellow-500 text-yellow-500" />
                          {selectedPlugin.rating.toFixed(1)}
                        </span>
                        <span className="flex items-center gap-1 text-sm text-muted-foreground">
                          <Download className="h-4 w-4" />
                          {selectedPlugin.downloads.toLocaleString()} downloads
                        </span>
                        <Badge variant="outline">v{selectedPlugin.version}</Badge>
                      </div>
                    </div>
                  </div>
                </DialogHeader>
                <Separator />
                <div className="space-y-4">
                  <p className="text-muted-foreground">{selectedPlugin.description}</p>
                  <div className="flex flex-wrap gap-2">
                    {selectedPlugin.tags.map((tag) => (
                      <Badge key={tag} variant="secondary">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setSelectedPlugin(null)}>
                    Close
                  </Button>
                  <Button
                    disabled={actionId === selectedPlugin.id}
                    onClick={() => toggleInstall(selectedPlugin)}
                  >
                    {actionId === selectedPlugin.id ? (
                      <RefreshCw className="h-4 w-4 animate-spin mr-2" />
                    ) : installedPlugins.includes(selectedPlugin.id) ? (
                      <>
                        <Trash2 className="h-4 w-4 mr-2" />
                        Uninstall
                      </>
                    ) : (
                      <>
                        <Download className="h-4 w-4 mr-2" />
                        Install
                      </>
                    )}
                  </Button>
                </DialogFooter>
              </>
            )}
          </DialogContent>
        </Dialog>
      </motion.div>
    </AppLayout>
  );
}
