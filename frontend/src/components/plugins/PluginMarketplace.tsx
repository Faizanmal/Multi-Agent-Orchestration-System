'use client';

import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Search,
  Download,
  Star,
  Package,
  TrendingUp,
  Verified,
  X,
  Check,
  Filter,
} from 'lucide-react';
// using sonnerToast for notifications in this component
import { 
  getPlugins, 
  installPlugin as apiInstallPlugin, 
  uninstallPlugin as apiUninstallPlugin,
  getPluginInstallations,
  submitPluginReview,
  getCustomAgents
} from '@/lib/api';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { toast as sonnerToast } from 'sonner';

interface PluginType {
  id: string;
  name: string;
  slug: string;
  description: string;
  version: string;
  category: string;
  type?: 'agent_extension' | 'workflow_node' | 'integration' | 'tool' | 'custom';
  status?: 'active' | 'inactive' | 'pending' | 'rejected';
  author: string | {
    id: string;
    username: string;
  };
  repository_url?: string;
  documentation_url?: string;
  configuration_schema?: Record<string, unknown>;
  permissions_required?: string[];
  dependencies?: string[];
  tags?: string[];
  is_public?: boolean;
  is_verified?: boolean;
  download_count: number;
  rating: number;
  rating_count: number;
  created_at?: string;
  updated_at?: string;
  is_installed?: boolean;
}

interface PluginInstallation {
  id: string;
  plugin: PluginType;
  is_enabled: boolean;
  usage_count: number;
  installed_at: string;
}
interface CustomAgent {
  id: string;
  agent?: { id?: string; name?: string } | null;
  total_invocations?: number;
  success_rate?: number; // 0..1
  capabilities?: string[];
}

const PluginMarketplace: React.FC = () => {
  const [plugins, setPlugins] = useState<PluginType[]>([]);
  const [installations, setInstallations] = useState<PluginInstallation[]>([]);
  const [customAgents, setCustomAgents] = useState<CustomAgent[]>([]);
  const [filteredPlugins, setFilteredPlugins] = useState<PluginType[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [sortOption, setSortOption] = useState('popular');
  const [selectedPlugin, setSelectedPlugin] = useState<PluginType | null>(null);
  const [reviewDialogOpen, setReviewDialogOpen] = useState(false);
  const [reviewRating, setReviewRating] = useState(5);
  const [reviewText, setReviewText] = useState('');

  // Using sonnerToast for visible notifications in this component

  const loadPlugins = React.useCallback(async () => {
    try {
      setIsLoading(true);
      const params = categoryFilter !== 'all' ? { category: categoryFilter } : undefined;
      
      const [pluginsRes, installationsRes, customAgentsRes] = await Promise.all([
        getPlugins(params),
        getPluginInstallations(),
        getCustomAgents()
      ]);

      const pluginsData = pluginsRes.data.results || pluginsRes.data;
      const installationsData = installationsRes.data.results || installationsRes.data;
      
      // Mark installed plugins
      const installedIds = new Set(installationsData.map((i: PluginInstallation) => i.plugin.id));
      const pluginsWithInstallStatus = pluginsData.map((p: PluginType) => ({
        ...p,
        is_installed: installedIds.has(p.id)
      }));

      setPlugins(pluginsWithInstallStatus);
      setInstallations(installationsData);
      setCustomAgents(customAgentsRes.data.results || customAgentsRes.data);
    } catch (error) {
      console.error('Failed to load plugins:', error);
      sonnerToast.error('Failed to load plugins from marketplace');
    } finally {
      setIsLoading(false);
    }
  }, [categoryFilter]);

  useEffect(() => {
    setTimeout(() => { loadPlugins(); }, 0)
  }, [categoryFilter, loadPlugins]);

  useEffect(() => {
    let result = [...plugins];
    
    // Apply search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      result = result.filter(plugin => 
        plugin.name.toLowerCase().includes(term) ||
        plugin.description.toLowerCase().includes(term)
      );
    }
    
    // Apply sorting
    switch (sortOption) {
      case 'popular':
        result.sort((a, b) => b.download_count - a.download_count);
        break;
      case 'rating':
        result.sort((a, b) => b.rating - a.rating);
        break;
      case 'newest':
        result.sort((a, b) => {
          if (!a.created_at || !b.created_at) return 0;
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        });
        break;
      case 'updated':
        result.sort((a, b) => {
          if (!a.updated_at || !b.updated_at) return 0;
          return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
        });
        break;
      default:
        break;
    }
    
    setTimeout(() => { setFilteredPlugins(result); }, 0)
  }, [plugins, searchTerm, sortOption]);

  const installPlugin = async (pluginId: string) => {
    try {
      await apiInstallPlugin(pluginId, {});
      sonnerToast.success('Plugin installed successfully');
      loadPlugins();
    } catch (error) {
      console.error('Failed to install plugin:', error);
      sonnerToast.error('Failed to install plugin');
    }
  };

  const uninstallPlugin = async (pluginId: string) => {
    try {
      await apiUninstallPlugin(pluginId);
      sonnerToast.success('Plugin uninstalled successfully');
      loadPlugins();
    } catch (error) {
      console.error('Failed to uninstall plugin:', error);
      sonnerToast.error('Failed to uninstall plugin');
    }
  };

  const handleSubmitReview = async () => {
    if (!selectedPlugin) return;
    
    try {
      await submitPluginReview(selectedPlugin.id, {
        rating: reviewRating,
        review_text: reviewText
      });
      sonnerToast.success('Review submitted successfully');
      setReviewDialogOpen(false);
      setReviewText('');
      setReviewRating(5);
      loadPlugins();
    } catch (err) {
      console.error('Failed to submit review:', err);
      sonnerToast.error('Failed to submit review');
    }
  };

  const getAuthorName = (author: string | { id: string; username: string }) => {
    return typeof author === 'string' ? author : author.username;
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Package className="h-8 w-8 text-blue-500" />
            Plugin Marketplace
          </h1>
          <p className="text-gray-600 mt-2">
            Extend your multi-agent system with powerful plugins
          </p>
        </div>
        <Button onClick={loadPlugins}>
          <Download className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Available Plugins</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{plugins.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Installed</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">{installations.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Custom Agents</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-purple-600">{customAgents.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Verified</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-600">
              {plugins.filter(p => p.is_verified).length}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search and Filters */}
      <div className="flex gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Search plugins..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select value={categoryFilter} onValueChange={setCategoryFilter}>
          <SelectTrigger className="w-[200px]">
            <Filter className="mr-2 h-4 w-4" />
            <SelectValue placeholder="Category" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">ALL</SelectItem>
            <SelectItem value="integration">INTEGRATION</SelectItem>
            <SelectItem value="tool">TOOL</SelectItem>
            <SelectItem value="data_source">DATA SOURCE</SelectItem>
            <SelectItem value="notification">NOTIFICATION</SelectItem>
            <SelectItem value="analytics">ANALYTICS</SelectItem>
            <SelectItem value="custom_agent">CUSTOM AGENT</SelectItem>
          </SelectContent>
        </Select>
        <Select value={sortOption} onValueChange={setSortOption}>
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="Sort by" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="popular">Most Popular</SelectItem>
            <SelectItem value="rating">Highest Rated</SelectItem>
            <SelectItem value="newest">Newest</SelectItem>
            <SelectItem value="updated">Recently Updated</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Package className="h-12 w-12 animate-pulse text-blue-500 mx-auto mb-4" />
          <p className="text-gray-600">Loading plugin marketplace...</p>
        </div>
      ) : (
        <Tabs defaultValue="marketplace" className="space-y-4">
          <TabsList>
            <TabsTrigger value="marketplace">Marketplace</TabsTrigger>
            <TabsTrigger value="installed">Installed ({installations.length})</TabsTrigger>
            <TabsTrigger value="custom-agents">Custom Agents ({customAgents.length})</TabsTrigger>
          </TabsList>

          <TabsContent value="marketplace" className="space-y-4">
            {filteredPlugins.length === 0 ? (
              <Card>
                <CardContent className="p-8 text-center">
                  <Search className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <h3 className="text-lg font-semibold mb-2">No Plugins Found</h3>
                  <p className="text-muted-foreground">
                    No plugins match your search criteria. Try adjusting your filters.
                  </p>
                </CardContent>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredPlugins.map((plugin) => (
                  <Card key={plugin.id} className="hover:shadow-lg transition-shadow">
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <CardTitle className="text-lg flex items-center gap-2">
                            {plugin.name}
                            {plugin.is_verified && (
                              <Verified className="h-4 w-4 text-blue-500" />
                            )}
                          </CardTitle>
                          <CardDescription className="line-clamp-2 mt-1">
                            {plugin.description}
                          </CardDescription>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <div className="flex items-center gap-4 text-sm text-gray-600">
                        <span className="flex items-center gap-1">
                          <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                          {plugin.rating.toFixed(1)} ({plugin.rating_count})
                        </span>
                        <span className="flex items-center gap-1">
                          <Download className="h-4 w-4" />
                          {plugin.download_count}
                        </span>
                      </div>

                      <div className="flex items-center gap-2">
                        <Badge variant="outline">{plugin.category}</Badge>
                        <Badge variant="secondary">v{plugin.version}</Badge>
                      </div>

                      <div className="text-xs text-gray-500">
                        by {getAuthorName(plugin.author)}
                      </div>

                      <div className="flex gap-2 pt-2">
                        {plugin.is_installed ? (
                          <>
                            <Button 
                              size="sm" 
                              variant="outline" 
                              className="flex-1"
                              onClick={() => uninstallPlugin(plugin.id)}
                            >
                              <X className="mr-1 h-3 w-3" />
                              Uninstall
                            </Button>
                            <Button 
                              size="sm" 
                              variant="outline"
                              onClick={() => {
                                setSelectedPlugin(plugin);
                                setReviewDialogOpen(true);
                              }}
                            >
                              <Star className="mr-1 h-3 w-3" />
                              Review
                            </Button>
                          </>
                        ) : (
                          <Button 
                            size="sm" 
                            className="flex-1"
                            onClick={() => installPlugin(plugin.id)}
                          >
                            <Download className="mr-1 h-3 w-3" />
                            Install
                          </Button>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="installed" className="space-y-4">
            <div className="space-y-4">
              {installations.map((installation) => (
                <Card key={installation.id}>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle className="flex items-center gap-2">
                          {installation.plugin.name}
                          {installation.is_enabled && (
                            <Badge variant="default">
                              <Check className="h-3 w-3 mr-1" />
                              Enabled
                            </Badge>
                          )}
                        </CardTitle>
                        <CardDescription>{installation.plugin.description}</CardDescription>
                      </div>
                      <Button 
                        variant="destructive" 
                        size="sm"
                        onClick={() => uninstallPlugin(installation.plugin.id)}
                      >
                        Uninstall
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="flex gap-6 text-sm text-gray-600">
                      <span>Version: {installation.plugin.version}</span>
                      <span>Used: {installation.usage_count} times</span>
                      <span>Installed: {new Date(installation.installed_at).toLocaleDateString()}</span>
                    </div>
                  </CardContent>
                </Card>
              ))}
              {installations.length === 0 && (
                <Card>
                  <CardContent className="text-center py-12">
                    <Package className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-600">No plugins installed yet</p>
                    <p className="text-sm text-gray-500 mt-2">Browse the marketplace to get started</p>
                  </CardContent>
                </Card>
              )}
            </div>
          </TabsContent>

          <TabsContent value="custom-agents" className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {customAgents.map((agent) => (
                <Card key={agent.id}>
                  <CardHeader>
                    <CardTitle>{agent.agent?.name || 'Custom Agent'}</CardTitle>
                    <CardDescription>Plugin-based agent</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Invocations</span>
                      <span className="font-semibold">{agent.total_invocations}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Success Rate</span>
                      <span className="font-semibold">
                        {typeof agent.success_rate === 'number' ? `${Math.round(agent.success_rate * 100)}%` : 'N/A'}
                      </span>
                    </div>
                    {agent.capabilities && agent.capabilities.length > 0 && (
                      <div className="pt-2 border-t">
                        <p className="text-xs text-gray-500 mb-2">Capabilities</p>
                        <div className="flex flex-wrap gap-1">
                          {agent.capabilities.map((cap: string, idx: number) => (
                            <Badge key={idx} variant="secondary" className="text-xs">
                              {cap}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
              {customAgents.length === 0 && (
                <Card className="col-span-full">
                  <CardContent className="text-center py-12">
                    <TrendingUp className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-600">No custom agents created yet</p>
                    <p className="text-sm text-gray-500 mt-2">Install plugins to create custom agents</p>
                  </CardContent>
                </Card>
              )}
            </div>
          </TabsContent>
        </Tabs>
      )}

      {/* Review Dialog */}
      <Dialog open={reviewDialogOpen} onOpenChange={setReviewDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Review {selectedPlugin?.name}</DialogTitle>
            <DialogDescription>Share your experience with this plugin</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Rating</Label>
              <div className="flex gap-2 mt-2">
                {[1, 2, 3, 4, 5].map((rating) => (
                  <button
                    key={rating}
                    onClick={() => setReviewRating(rating)}
                    className="focus:outline-none"
                  >
                    <Star
                      className={`h-8 w-8 ${
                        rating <= reviewRating
                          ? 'fill-yellow-400 text-yellow-400'
                          : 'text-gray-300'
                      }`}
                    />
                  </button>
                ))}
              </div>
            </div>
            <div>
              <Label htmlFor="review">Review</Label>
              <Textarea
                id="review"
                value={reviewText}
                onChange={(e) => setReviewText(e.target.value)}
                placeholder="Share your thoughts about this plugin..."
                rows={4}
              />
            </div>
            <div className="flex gap-2">
              <Button onClick={handleSubmitReview} className="flex-1">
                Submit Review
              </Button>
              <Button variant="outline" onClick={() => setReviewDialogOpen(false)}>
                Cancel
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default PluginMarketplace;