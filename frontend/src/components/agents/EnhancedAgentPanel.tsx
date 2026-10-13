/**
 * Enhanced Agent Panel with API integration
 * Manages agents with full CRUD operations and real-time status
 */

"use client";

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  useAgents, 
  useAgent, 
  useCreateAgent, 
  useUpdateAgent, 
  useDeleteAgent, 
  useActivateAgent, 
  useDeactivateAgent,
  useAgentPerformance
} from '@/hooks/useApi';
import { Agent } from '@/lib/api';
import { 
  Brain, 
  Eye, 
  Cpu, 
  Zap, 
  Database, 
  Plus, 
  Edit, 
  Trash2, 
  Play, 
  Pause,

  Clock,
  Target,
  BarChart3,
  Loader2,
  AlertCircle,
  Settings,
} from 'lucide-react';
import { toast } from '@/hooks/use-toast';

const agentTypeIcons = {
  orchestrator: Brain,
  vision: Eye,
  reasoning: Cpu,
  action: Zap,
  memory: Database,
  custom: Settings,
} as const;

const agentTypeColors = {
  orchestrator: 'bg-blue-500',
  vision: 'bg-purple-500',
  reasoning: 'bg-green-500',
  action: 'bg-orange-500',
  memory: 'bg-indigo-500',
  custom: 'bg-gray-500',
} as const;

interface CreateAgentFormData {
  name: string;
  type: Agent['type'];
  capabilities: string[];
}

export function EnhancedAgentPanel() {
  const [selectedAgentId, setSelectedAgentId] = useState<string>('');
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [editingAgent, setEditingAgent] = useState<Agent | null>(null);

  // API hooks
  const { data: agentsResponse, isLoading: isLoadingAgents, error: agentsError } = useAgents();
  const { data: selectedAgent } = useAgent(selectedAgentId);
  useAgentPerformance(selectedAgentId);
  
  const createAgentMutation = useCreateAgent();
  const updateAgentMutation = useUpdateAgent();
  const deleteAgentMutation = useDeleteAgent();
  const activateAgentMutation = useActivateAgent();
  const deactivateAgentMutation = useDeactivateAgent();

  const agents = agentsResponse?.results || [];

  const [formData, setFormData] = useState<CreateAgentFormData>({
    name: '',
    type: 'reasoning',
    capabilities: [],
  });

  const getStatusColor = (status: Agent['status']) => {
    switch (status) {
      case 'active': return 'bg-green-500';
      case 'processing': return 'bg-blue-500 animate-pulse';
      case 'error': return 'bg-red-500';
      default: return 'bg-gray-400';
    }
  };

  const handleCreateAgent = async () => {
    if (!formData.name.trim()) {
      toast({
        title: 'Error',
        description: 'Agent name is required',
        variant: 'destructive',
      });
      return;
    }

    try {
      await createAgentMutation.mutateAsync({
        name: formData.name,
        type: formData.type,
        capabilities: formData.capabilities,
        status: 'idle',
      });
      
      setIsCreateDialogOpen(false);
      setFormData({ name: '', type: 'reasoning', capabilities: [] });
    } catch (error) {
      console.error('Failed to create agent:', error);
    }
  };

  const handleEditAgent = (agent: Agent) => {
    setEditingAgent(agent);
    setFormData({
      name: agent.name,
      type: agent.type,
      capabilities: agent.capabilities,
    });
    setIsEditDialogOpen(true);
  };

  const handleUpdateAgent = async () => {
    if (!editingAgent || !formData.name.trim()) return;

    try {
      await updateAgentMutation.mutateAsync({
        id: editingAgent.id,
        data: {
          name: formData.name,
          type: formData.type,
          capabilities: formData.capabilities,
        },
      });
      
      setIsEditDialogOpen(false);
      setEditingAgent(null);
      setFormData({ name: '', type: 'reasoning', capabilities: [] });
    } catch (error) {
      console.error('Failed to update agent:', error);
    }
  };

  const handleDeleteAgent = async (agentId: string) => {
    if (window.confirm('Are you sure you want to delete this agent?')) {
      try {
        await deleteAgentMutation.mutateAsync(agentId);
        toast({
          title: 'Agent Deleted',
          description: 'The agent has been successfully deleted.',
        });
      } catch (error) {
        console.error('Failed to delete agent:', error);
        toast({
          title: 'Error Deleting Agent',
          description: 'There was a problem deleting the agent. Please try again.',
          variant: 'destructive',
        });
      }
    }
  };

  const handleToggleAgent = async (agent: Agent) => {
    try {
      if (agent.status === 'active') {
        await deactivateAgentMutation.mutateAsync(agent.id);
      } else {
        await activateAgentMutation.mutateAsync(agent.id);
      }
    } catch (error) {
      console.error('Failed to toggle agent status:', error);
    }
  };

  const addCapability = (capability: string) => {
    if (capability.trim() && !formData.capabilities.includes(capability.trim())) {
      setFormData(prev => ({
        ...prev,
        capabilities: [...prev.capabilities, capability.trim()],
      }));
    }
  };

  const removeCapability = (capability: string) => {
    setFormData(prev => ({
      ...prev,
      capabilities: prev.capabilities.filter(c => c !== capability),
    }));
  };

  if (isLoadingAgents) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin" />
        <span className="ml-2">Loading agents...</span>
      </div>
    );
  }

  if (agentsError) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center h-64">
          <div className="text-center">
            <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <p className="text-lg font-medium">Failed to load agents</p>
            <p className="text-sm text-muted-foreground">Please check your connection and try again</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold">Agent Management</h2>
          <p className="text-muted-foreground">Manage and monitor your AI agents</p>
        </div>
        
        <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Create Agent
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle>Create New Agent</DialogTitle>
              <DialogDescription>
                Create a specialized AI agent for your workflow
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label htmlFor="name">Agent Name</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="Enter agent name..."
                />
              </div>
              <div>
                <Label htmlFor="type">Agent Type</Label>
                <Select value={formData.type} onValueChange={(value: Agent['type']) => setFormData(prev => ({ ...prev, type: value }))}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="orchestrator">Orchestrator</SelectItem>
                    <SelectItem value="vision">Vision</SelectItem>
                    <SelectItem value="reasoning">Reasoning</SelectItem>
                    <SelectItem value="action">Action</SelectItem>
                    <SelectItem value="memory">Memory</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Capabilities</Label>
                <div className="flex flex-wrap gap-2 mb-2">
                  {formData.capabilities.map((capability, index) => (
                    <Badge key={index} variant="secondary" className="cursor-pointer" onClick={() => removeCapability(capability)}>
                      {capability} ×
                    </Badge>
                  ))}
                </div>
                <Input
                  placeholder="Add capability and press Enter..."
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      addCapability(e.currentTarget.value);
                      e.currentTarget.value = '';
                    }
                  }}
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleCreateAgent} disabled={createAgentMutation.isPending}>
                {createAgentMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Creating...
                  </>
                ) : (
                  'Create Agent'
                )}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Agents Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {agents.map((agent) => {
          const IconComponent = agentTypeIcons[agent.type];
          return (
            <Card key={agent.id} className="hover:shadow-lg transition-shadow cursor-pointer" onClick={() => setSelectedAgentId(agent.id)}>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${agentTypeColors[agent.type]}`}>
                      <IconComponent className="h-5 w-5 text-white" />
                    </div>
                    <div>
                      <CardTitle className="text-lg">{agent.name}</CardTitle>
                      <CardDescription className="capitalize">{agent.type}</CardDescription>
                    </div>
                  </div>
                  <div className={`w-3 h-3 rounded-full ${getStatusColor(agent.status)}`} />
                </div>
              </CardHeader>
              
              <CardContent className="space-y-4">
                <div>
                  <Label className="text-xs text-muted-foreground">STATUS</Label>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge variant={agent.status === 'active' ? 'default' : 'secondary'} className="capitalize">
                      {agent.status}
                    </Badge>
                    {agent.performance_metrics && (
                      <Badge variant="outline" className="text-xs">
                        {agent.performance_metrics.accuracy}% acc
                      </Badge>
                    )}
                  </div>
                </div>

                <div>
                  <Label className="text-xs text-muted-foreground">CAPABILITIES</Label>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {agent.capabilities.slice(0, 3).map((capability, index) => (
                      <Badge key={index} variant="outline" className="text-xs">
                        {capability}
                      </Badge>
                    ))}
                    {agent.capabilities.length > 3 && (
                      <Badge variant="outline" className="text-xs">
                        +{agent.capabilities.length - 3}
                      </Badge>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2 pt-2">
                  <Button
                    size="sm"
                    variant={agent.status === 'active' ? 'outline' : 'default'}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleToggleAgent(agent);
                    }}
                    disabled={activateAgentMutation.isPending || deactivateAgentMutation.isPending}
                  >
                    {agent.status === 'active' ? (
                      <>
                        <Pause className="h-3 w-3 mr-1" />
                        Stop
                      </>
                    ) : (
                      <>
                        <Play className="h-3 w-3 mr-1" />
                        Start
                      </>
                    )}
                  </Button>
                  
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleEditAgent(agent);
                    }}
                  >
                    <Edit className="h-3 w-3" />
                  </Button>
                  
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteAgent(agent.id);
                    }}
                    disabled={deleteAgentMutation.isPending}
                  >
                    <Trash2 className="h-3 w-3" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Agent Details Modal */}
      {selectedAgent && (
        <Dialog open={!!selectedAgentId} onOpenChange={() => setSelectedAgentId('')}>
          <DialogContent className="sm:max-w-2xl">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                {React.createElement(agentTypeIcons[selectedAgent.type], { className: "h-5 w-5" })}
                {selectedAgent.name}
              </DialogTitle>
              <DialogDescription>
                Detailed information and performance metrics
              </DialogDescription>
            </DialogHeader>
            
            <Tabs defaultValue="overview" className="w-full">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="overview">Overview</TabsTrigger>
                <TabsTrigger value="performance">Performance</TabsTrigger>
                <TabsTrigger value="capabilities">Capabilities</TabsTrigger>
              </TabsList>
              
              <TabsContent value="overview" className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-sm text-muted-foreground">Type</Label>
                    <p className="font-medium capitalize">{selectedAgent.type}</p>
                  </div>
                  <div>
                    <Label className="text-sm text-muted-foreground">Status</Label>
                    <Badge variant={selectedAgent.status === 'active' ? 'default' : 'secondary'} className="capitalize">
                      {selectedAgent.status}
                    </Badge>
                  </div>
                  <div>
                    <Label className="text-sm text-muted-foreground">Created</Label>
                    <p className="font-medium">{new Date(selectedAgent.created_at).toLocaleDateString()}</p>
                  </div>
                  <div>
                    <Label className="text-sm text-muted-foreground">Last Updated</Label>
                    <p className="font-medium">{new Date(selectedAgent.updated_at).toLocaleDateString()}</p>
                  </div>
                </div>
              </TabsContent>
              
              <TabsContent value="performance" className="space-y-4">
                {selectedAgent.performance_metrics ? (
                  <div className="grid grid-cols-3 gap-4">
                    <div className="text-center">
                      <Target className="h-8 w-8 mx-auto mb-2 text-blue-500" />
                      <p className="text-2xl font-bold">{selectedAgent.performance_metrics.accuracy}%</p>
                      <p className="text-sm text-muted-foreground">Accuracy</p>
                    </div>
                    <div className="text-center">
                      <Clock className="h-8 w-8 mx-auto mb-2 text-green-500" />
                      <p className="text-2xl font-bold">{selectedAgent.performance_metrics.speed}%</p>
                      <p className="text-sm text-muted-foreground">Speed</p>
                    </div>
                    <div className="text-center">
                      <BarChart3 className="h-8 w-8 mx-auto mb-2 text-purple-500" />
                      <p className="text-2xl font-bold">{selectedAgent.performance_metrics.reliability}%</p>
                      <p className="text-sm text-muted-foreground">Reliability</p>
                    </div>
                  </div>
                ) : (
                  <p className="text-center text-muted-foreground">No performance data available</p>
                )}
              </TabsContent>
              
              <TabsContent value="capabilities" className="space-y-4">
                <div className="flex flex-wrap gap-2">
                  {selectedAgent.capabilities.map((capability, index) => (
                    <Badge key={index} variant="outline">
                      {capability}
                    </Badge>
                  ))}
                </div>
              </TabsContent>
            </Tabs>
          </DialogContent>
        </Dialog>
      )}

      {/* Edit Agent Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Edit Agent</DialogTitle>
            <DialogDescription>
              Update agent information and capabilities
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="edit-name">Agent Name</Label>
              <Input
                id="edit-name"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                placeholder="Enter agent name..."
              />
            </div>
            <div>
              <Label htmlFor="edit-type">Agent Type</Label>
              <Select value={formData.type} onValueChange={(value: Agent['type']) => setFormData(prev => ({ ...prev, type: value }))}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="orchestrator">Orchestrator</SelectItem>
                  <SelectItem value="vision">Vision</SelectItem>
                  <SelectItem value="reasoning">Reasoning</SelectItem>
                  <SelectItem value="action">Action</SelectItem>
                  <SelectItem value="memory">Memory</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Capabilities</Label>
              <div className="flex flex-wrap gap-2 mb-2">
                {formData.capabilities.map((capability, index) => (
                  <Badge key={index} variant="secondary" className="cursor-pointer" onClick={() => removeCapability(capability)}>
                    {capability} ×
                  </Badge>
                ))}
              </div>
              <Input
                placeholder="Add capability and press Enter..."
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    addCapability(e.currentTarget.value);
                    e.currentTarget.value = '';
                  }
                }}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleUpdateAgent} disabled={updateAgentMutation.isPending}>
              {updateAgentMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Updating...
                </>
              ) : (
                'Update Agent'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}