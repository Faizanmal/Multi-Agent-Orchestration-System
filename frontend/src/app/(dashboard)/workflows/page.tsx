"use client";

import React, { useState, useCallback, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  MarkerType,
  Panel,
  NodeTypes,
  Handle,
  Position,
} from 'reactflow';
import 'reactflow/dist/style.css';
import {
  Workflow,
  Play,
  Save,
  Download,
  Upload,
  Undo,
  Redo,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Bot,
  GitBranch,
  Timer,
  ArrowRight,
  Trash2,
  Copy,
  Layers,
  ChevronRight,
  Zap,
  Filter,
  Globe,
} from 'lucide-react';
import { AppLayout } from '@/components/layout/AppLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { ScrollArea } from '@/components/ui/scroll-area';
import apiClient from '@/lib/api';
import { toast } from '@/hooks/use-toast';
import type { IntegrationTool, WorkflowRecord } from '@/types/api';
import { axiosErrorDetail, errorMessage, paginatedItems } from '@/types/api';
import { cn } from '@/lib/utils';

// Node types configuration
const nodeTypesConfig = {
  trigger: { icon: Zap, color: 'bg-green-500', label: 'Trigger' },
  agent: { icon: Bot, color: 'bg-indigo-500', label: 'Agent' },
  condition: { icon: GitBranch, color: 'bg-yellow-500', label: 'Condition' },
  action: { icon: ArrowRight, color: 'bg-blue-500', label: 'Action' },
  transform: { icon: Filter, color: 'bg-purple-500', label: 'Transform' },
  integration: { icon: Globe, color: 'bg-cyan-500', label: 'Integration' },
  delay: { icon: Timer, color: 'bg-orange-500', label: 'Delay' },
  loop: { icon: Layers, color: 'bg-pink-500', label: 'Loop' },
};

// Custom Node Component
const CustomNode = ({ data, selected }: { data: { nodeType: string; label: string; description?: string; [key: string]: unknown }; selected: boolean }) => {
  const config = nodeTypesConfig[data.nodeType as keyof typeof nodeTypesConfig] || nodeTypesConfig.action;
  const Icon = config.icon;

  return (
    <div className={cn(
      "relative rounded-xl border-2 bg-background shadow-lg transition-all duration-200 min-w-[200px]",
      selected ? "border-primary ring-4 ring-primary/20" : "border-border hover:border-primary/50"
    )}>
      {/* Input Handle */}
      {data.nodeType !== 'trigger' && (
        <Handle
          type="target"
          position={Position.Top}
          className="!w-3 !h-3 !bg-primary !border-2 !border-background"
        />
      )}

      {/* Node Header */}
      <div className={cn("flex items-center gap-2 p-3 rounded-t-lg", config.color)}>
        <Icon className="h-4 w-4 text-white" />
        <span className="text-sm font-medium text-white">{config.label}</span>
      </div>

      {/* Node Content */}
      <div className="p-3">
        <h4 className="font-medium text-sm mb-1">{data.label}</h4>
        {data.nodeType === 'integration' && !!data.tool_name && (
          <p className="text-xs font-mono text-cyan-600 dark:text-cyan-400">{String(data.tool_name)}</p>
        )}
        {data.description && (
          <p className="text-xs text-muted-foreground">{data.description}</p>
        )}
      </div>

      {/* Output Handle */}
      <Handle
        type="source"
        position={Position.Bottom}
        className="!w-3 !h-3 !bg-primary !border-2 !border-background"
      />

      {/* Multiple outputs for condition nodes */}
      {data.nodeType === 'condition' && (
        <>
          <Handle
            type="source"
            position={Position.Right}
            id="true"
            className="!w-3 !h-3 !bg-green-500 !border-2 !border-background"
            style={{ top: '50%' }}
          />
          <Handle
            type="source"
            position={Position.Left}
            id="false"
            className="!w-3 !h-3 !bg-red-500 !border-2 !border-background"
            style={{ top: '50%' }}
          />
        </>
      )}
    </div>
  );
};

const nodeTypes: NodeTypes = {
  custom: CustomNode,
};

// Initial nodes
const initialNodes: Node[] = [
  {
    id: '1',
    type: 'custom',
    position: { x: 400, y: 50 },
    data: { label: 'Webhook Trigger', nodeType: 'trigger', description: 'Starts when webhook is received' },
  },
  {
    id: '2',
    type: 'custom',
    position: { x: 400, y: 180 },
    data: { label: 'Orchestrator Agent', nodeType: 'agent', description: 'Routes to appropriate agent' },
  },
  {
    id: '3',
    type: 'custom',
    position: { x: 400, y: 310 },
    data: { label: 'Check Intent', nodeType: 'condition', description: 'Analyze user intent' },
  },
  {
    id: '4',
    type: 'custom',
    position: { x: 200, y: 440 },
    data: { label: 'Vision Agent', nodeType: 'agent', description: 'Process visual content' },
  },
  {
    id: '5',
    type: 'custom',
    position: { x: 600, y: 440 },
    data: { label: 'Reasoning Agent', nodeType: 'agent', description: 'Handle text queries' },
  },
];

const initialEdges: Edge[] = [
  { id: 'e1-2', source: '1', target: '2', markerEnd: { type: MarkerType.ArrowClosed } },
  { id: 'e2-3', source: '2', target: '3', markerEnd: { type: MarkerType.ArrowClosed } },
  { id: 'e3-4', source: '3', sourceHandle: 'false', target: '4', markerEnd: { type: MarkerType.ArrowClosed }, label: 'Image' },
  { id: 'e3-5', source: '3', sourceHandle: 'true', target: '5', markerEnd: { type: MarkerType.ArrowClosed }, label: 'Text' },
];

// Fallback templates when API has none
const fallbackWorkflowTemplates: WorkflowRecord[] = [
  { id: '1', name: 'Integration Pipeline', category: 'integration', workflow_definition: { nodes: [], edges: [] } },
  { id: '2', name: 'Gmail → Slack Alert', category: 'automation', workflow_definition: { nodes: [], edges: [] } },
];

export default function WorkflowsPage() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [isPanelOpen, setIsPanelOpen] = useState(false);
  const [workflowName, setWorkflowName] = useState('My Workflow');
  const [workflowId, setWorkflowId] = useState<string | null>(null);
  const [savedWorkflows, setSavedWorkflows] = useState<WorkflowRecord[]>([]);
  const [workflowTemplates, setWorkflowTemplates] = useState<WorkflowRecord[]>(fallbackWorkflowTemplates);
  const [integrationTools, setIntegrationTools] = useState<IntegrationTool[]>([]);
  const [isSaving, setIsSaving] = useState(false);
  const [isExecuting, setIsExecuting] = useState(false);
  const [paramsJson, setParamsJson] = useState('{}');
  const reactFlowWrapper = useRef<HTMLDivElement>(null);

  const loadSavedWorkflows = async () => {
    try {
      const res = await apiClient.getWorkflows();
      setSavedWorkflows(paginatedItems(res.data as WorkflowRecord[] | { results?: WorkflowRecord[] }));
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    setTimeout(() => { loadSavedWorkflows(); }, 0)
    apiClient.getWorkflowTemplates().then((res) => {
      const list = paginatedItems(res.data as WorkflowRecord[] | { results?: WorkflowRecord[] });
      if (list.length > 0) setWorkflowTemplates(list);
    }).catch(console.error);
    apiClient.getIntegrationTools().then((res) => {
      setIntegrationTools(paginatedItems(res.data as IntegrationTool[] | { results?: IntegrationTool[] }));
    }).catch(console.error);
  }, []);

  const onConnect = useCallback(
    (params: Connection) => {
      setEdges((eds) => addEdge({ ...params, markerEnd: { type: MarkerType.ArrowClosed } }, eds));
    },
    [setEdges]
  );

  const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
    setIsPanelOpen(true);
    if (node.data?.nodeType === 'integration') {
      setParamsJson(JSON.stringify(node.data.params || {}, null, 2));
    }
  }, []);

  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
    setIsPanelOpen(false);
  }, []);

  useEffect(() => {
    if (!selectedNode) {
      return;
    }

    const nextSelectedNode = nodes.find((node) => node.id === selectedNode.id) ?? null;

    if (nextSelectedNode !== selectedNode) {
      setTimeout(() => { setSelectedNode(nextSelectedNode); }, 0)
    }
  }, [nodes, selectedNode]);

  const updateSelectedNodeData = useCallback(
    (field: 'label' | 'description' | 'nodeType', value: string) => {
      if (!selectedNode) {
        return;
      }

      setNodes((currentNodes) =>
        currentNodes.map((node) => {
          if (node.id !== selectedNode.id) {
            return node;
          }

          const updatedNode = {
            ...node,
            data: {
              ...node.data,
              [field]: value,
            },
          };
          return updatedNode;
        })
      );
    },
    [selectedNode, setNodes]
  );

  const addNode = (nodeType: keyof typeof nodeTypesConfig) => {
    const newNode: Node = {
      id: `node-${new Date().getTime()}`,
      type: 'custom',
      position: { x: 400, y: 100 + nodes.length * 50 },
      data: {
        label: `New ${nodeTypesConfig[nodeType].label}`,
        nodeType,
        description: 'Configure this node',
      },
    };
    setNodes((nds) => [...nds, newNode]);
  };

  const serializeNodes = () => nodes.map((n) => ({
    id: n.id,
    type: n.type,
    position: n.position,
    data: n.data,
  }));

  const loadWorkflow = async (id: string) => {
    try {
      const res = await apiClient.getWorkflow(id);
      const wf = res.data as WorkflowRecord;
      setWorkflowId(wf.id);
      setWorkflowName(wf.name);
      setNodes(wf.nodes?.length ? (wf.nodes as Node[]) : initialNodes);
      setEdges(wf.edges?.length ? (wf.edges as Edge[]) : []);
      toast({ title: 'Workflow loaded', description: wf.name });
    } catch (e: unknown) {
      toast({ title: 'Failed to load workflow', description: errorMessage(e), variant: 'destructive' });
    }
  };

  const handleNewWorkflow = () => {
    setWorkflowId(null);
    setWorkflowName('My Workflow');
    setNodes(initialNodes);
    setEdges(initialEdges);
    setSelectedNode(null);
    setIsPanelOpen(false);
  };

  const applyTemplate = async (template: WorkflowRecord) => {
    if (template.workflow_definition) {
      const def = template.workflow_definition;
      setWorkflowId(null);
      setWorkflowName(template.name);
      setNodes((def.nodes as Node[]) || initialNodes);
      setEdges((def.edges as Edge[]) || []);
      toast({ title: 'Template applied', description: template.name });
      return;
    }
    try {
      const res = await apiClient.cloneWorkflowTemplate(template.id);
      const wf = (res.data as { workflow?: WorkflowRecord })?.workflow ?? (res.data as WorkflowRecord);
      if (wf?.id) {
        await loadWorkflow(wf.id);
      }
    } catch {
      toast({ title: 'Template loaded', description: 'Start from scratch and add integration nodes.' });
      setWorkflowId(null);
      setWorkflowName(template.name);
      setNodes([{
        id: 'node-trigger',
        type: 'custom',
        position: { x: 250, y: 50 },
        data: { label: 'Start', nodeType: 'trigger', description: 'Workflow entry point' },
      }]);
      setEdges([]);
    }
  };

  const deleteSelectedNode = () => {
    if (!selectedNode) return;
    setNodes((nds) => nds.filter((n) => n.id !== selectedNode.id));
    setEdges((eds) => eds.filter((e) => e.source !== selectedNode.id && e.target !== selectedNode.id));
    setSelectedNode(null);
    setIsPanelOpen(false);
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const payload = {
        name: workflowName,
        description: 'Visual integration workflow',
        nodes: serializeNodes(),
        edges,
        status: 'active',
      };
      if (workflowId) {
        await apiClient.updateWorkflow(workflowId, payload);
      } else {
        const res = await apiClient.createWorkflow(payload);
        setWorkflowId((res.data as WorkflowRecord).id);
      }
      await loadSavedWorkflows();
      toast({ title: 'Workflow saved' });
    } catch (e: unknown) {
      toast({ title: 'Failed to save workflow', description: errorMessage(e), variant: 'destructive' });
    } finally {
      setIsSaving(false);
    }
  };

  const handleExecute = async () => {
    setIsExecuting(true);
    try {
      let id = workflowId;
      if (!id) {
        const res = await apiClient.createWorkflow({
          name: workflowName,
          nodes: serializeNodes(),
          edges,
          status: 'active',
        });
        id = (res.data as WorkflowRecord).id;
        setWorkflowId(id);
      }
      const execRes = await apiClient.executeWorkflow(id!, { input_data: {} });
      const exec = execRes.data as { status?: string; error_message?: string };
      toast({
        title: exec.status === 'completed' ? 'Workflow completed' : 'Workflow finished',
        description: exec.error_message || `Status: ${exec.status}`,
        variant: exec.status === 'failed' ? 'destructive' : 'default',
      });
    } catch (e: unknown) {
      toast({ title: 'Workflow execution failed', description: axiosErrorDetail(e) || errorMessage(e), variant: 'destructive' });
    } finally {
      setIsExecuting(false);
    }
  };

  const addIntegrationNode = (tool: IntegrationTool) => {
    const newNode: Node = {
      id: `node-${new Date().getTime()}`,
      type: 'custom',
      position: { x: 400, y: 100 + nodes.length * 50 },
      data: {
        label: tool.name,
        nodeType: 'integration',
        description: tool.description,
        tool_name: tool.name,
        params: {},
      },
    };
    setNodes((nds) => [...nds, newNode]);
  };

  return (
    <AppLayout>
      <div className="h-[calc(100vh-7rem)] flex flex-col">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between mb-4"
        >
          <div className="flex items-center gap-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-purple-500">
              <Workflow className="h-5 w-5 text-white" />
            </div>
            <div>
              <Input
                value={workflowName}
                onChange={(e) => setWorkflowName(e.target.value)}
                className="text-lg font-semibold bg-transparent border-none p-0 h-auto focus-visible:ring-0"
              />
              <p className="text-sm text-muted-foreground">Visual Workflow Builder</p>
            </div>
            <Badge variant="secondary">{workflowId ? 'Saved' : 'Draft'}</Badge>
            {savedWorkflows.length > 0 && (
              <Select value={workflowId || ''} onValueChange={(v) => v && loadWorkflow(v)}>
                <SelectTrigger className="w-48 h-8">
                  <SelectValue placeholder="Open workflow..." />
                </SelectTrigger>
                <SelectContent>
                  {savedWorkflows.map((w) => (
                    <SelectItem key={w.id} value={w.id}>{w.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
            <Button variant="ghost" size="sm" onClick={handleNewWorkflow}>New</Button>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" className="gap-2">
              <Undo className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="sm" className="gap-2">
              <Redo className="h-4 w-4" />
            </Button>
            <div className="w-px h-6 bg-border mx-2" />
            <Button variant="outline" size="sm" className="gap-2">
              <Upload className="h-4 w-4" />
              Import
            </Button>
            <Button variant="outline" size="sm" className="gap-2">
              <Download className="h-4 w-4" />
              Export
            </Button>
            <Button variant="outline" size="sm" className="gap-2" onClick={handleSave} disabled={isSaving}>
              <Save className="h-4 w-4" />
              {isSaving ? 'Saving...' : 'Save'}
            </Button>
            <Button className="gap-2 bg-gradient-to-r from-green-500 to-emerald-500 hover:opacity-90" onClick={handleExecute} disabled={isExecuting}>
              <Play className="h-4 w-4" />
              {isExecuting ? 'Running...' : 'Execute'}
            </Button>
          </div>
        </motion.div>

        {/* Main Content */}
        <div className="flex-1 flex gap-4 overflow-hidden">
          {/* Node Palette */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="w-64 shrink-0"
          >
            <Card className="h-full">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">Node Palette</CardTitle>
                <CardDescription className="text-xs">Drag to add nodes</CardDescription>
              </CardHeader>
              <CardContent className="p-2">
                <Tabs defaultValue="nodes">
                  <TabsList className="w-full grid grid-cols-3">
                    <TabsTrigger value="nodes" className="text-xs">Nodes</TabsTrigger>
                    <TabsTrigger value="integrations" className="text-xs">Integrations</TabsTrigger>
                    <TabsTrigger value="templates" className="text-xs">Templates</TabsTrigger>
                  </TabsList>
                  
                  <TabsContent value="nodes" className="mt-2">
                    <ScrollArea className="h-[calc(100vh-22rem)]">
                      <div className="space-y-2 pr-4">
                        {Object.entries(nodeTypesConfig).map(([key, config]) => {
                          const Icon = config.icon;
                          return (
                            <motion.button
                              key={key}
                              whileHover={{ scale: 1.02 }}
                              whileTap={{ scale: 0.98 }}
                              onClick={() => addNode(key as keyof typeof nodeTypesConfig)}
                              className="w-full flex items-center gap-3 p-3 rounded-lg border border-dashed hover:border-primary hover:bg-primary/5 transition-colors text-left"
                            >
                              <div className={cn("flex h-8 w-8 items-center justify-center rounded-lg", config.color)}>
                                <Icon className="h-4 w-4 text-white" />
                              </div>
                              <div>
                                <p className="text-sm font-medium">{config.label}</p>
                                <p className="text-xs text-muted-foreground">Click to add</p>
                              </div>
                            </motion.button>
                          );
                        })}
                      </div>
                    </ScrollArea>
                  </TabsContent>

                  <TabsContent value="integrations" className="mt-2">
                    <ScrollArea className="h-[calc(100vh-22rem)]">
                      <div className="space-y-2 pr-4">
                        {integrationTools.length === 0 ? (
                          <p className="text-xs text-muted-foreground p-2">Connect integrations first, then add tools here.</p>
                        ) : integrationTools.map((tool) => (
                          <motion.button
                            key={`${tool.integration_id}-${tool.name}`}
                            whileHover={{ scale: 1.02 }}
                            onClick={() => addIntegrationNode(tool)}
                            className="w-full flex flex-col gap-1 p-3 rounded-lg border border-dashed hover:border-cyan-500 hover:bg-cyan-500/5 text-left"
                          >
                            <span className="text-sm font-medium">{tool.name}</span>
                            <span className="text-xs text-muted-foreground">{tool.integration_name}</span>
                          </motion.button>
                        ))}
                      </div>
                    </ScrollArea>
                  </TabsContent>

                  <TabsContent value="templates" className="mt-2">
                    <ScrollArea className="h-[calc(100vh-22rem)]">
                      <div className="space-y-2 pr-4">
                        {workflowTemplates.map((template) => (
                          <motion.button
                            key={template.id}
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                            onClick={() => applyTemplate(template)}
                            className="w-full flex items-center justify-between p-3 rounded-lg border hover:border-primary hover:bg-primary/5 transition-colors text-left"
                          >
                            <div>
                              <p className="text-sm font-medium">{template.name}</p>
                              <p className="text-xs text-muted-foreground">
                                {template.category || 'template'}
                                {template.workflow_definition?.nodes?.length
                                  ? ` • ${template.workflow_definition.nodes.length} nodes`
                                  : ''}
                              </p>
                            </div>
                            <ChevronRight className="h-4 w-4 text-muted-foreground" />
                          </motion.button>
                        ))}
                      </div>
                    </ScrollArea>
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          </motion.div>

          {/* Canvas */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex-1 rounded-xl border bg-muted/30 overflow-hidden"
            ref={reactFlowWrapper}
          >
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onNodeClick={onNodeClick}
              onPaneClick={onPaneClick}
              nodeTypes={nodeTypes}
              fitView
              snapToGrid
              snapGrid={[15, 15]}
              className="bg-dots-pattern"
            >
              <Background gap={20} size={1} color="hsl(var(--muted-foreground) / 0.1)" />
              <Controls className="!bg-background !border !shadow-lg !rounded-xl" />
              <MiniMap
                className="!bg-background !border !shadow-lg !rounded-xl"
                nodeColor={(node) => {
                  const config = nodeTypesConfig[node.data?.nodeType as keyof typeof nodeTypesConfig];
                  return config ? config.color.replace('bg-', '') : '#6366f1';
                }}
              />
              
              <Panel position="top-right" className="flex gap-2">
                <Button variant="outline" size="icon" className="bg-background">
                  <ZoomIn className="h-4 w-4" />
                </Button>
                <Button variant="outline" size="icon" className="bg-background">
                  <ZoomOut className="h-4 w-4" />
                </Button>
                <Button variant="outline" size="icon" className="bg-background">
                  <Maximize2 className="h-4 w-4" />
                </Button>
              </Panel>
            </ReactFlow>
          </motion.div>

          {/* Properties Panel */}
          <Sheet open={isPanelOpen} onOpenChange={setIsPanelOpen}>
            <SheetContent className="w-80">
              <SheetHeader>
                <SheetTitle>Node Properties</SheetTitle>
                <SheetDescription>
                  Configure the selected node
                </SheetDescription>
              </SheetHeader>
              {selectedNode && (
                <div className="space-y-4 mt-4">
                  <div className="space-y-2">
                    <Label>Node Name</Label>
                    <Input
                      value={String(selectedNode.data.label ?? '')}
                      onChange={(event) => updateSelectedNodeData('label', event.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Description</Label>
                    <Textarea
                      value={String(selectedNode.data.description ?? '')}
                      onChange={(event) => updateSelectedNodeData('description', event.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Type</Label>
                    <Select
                      value={String(selectedNode.data.nodeType ?? 'action')}
                      onValueChange={(value) => updateSelectedNodeData('nodeType', value)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {Object.entries(nodeTypesConfig).map(([key, config]) => (
                          <SelectItem key={key} value={key}>
                            <div className="flex items-center gap-2">
                              <config.icon className="h-4 w-4" />
                              {config.label}
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  {selectedNode.data.nodeType === 'integration' && (
                    <>
                      <div className="space-y-2">
                        <Label>Integration Tool</Label>
                        <Select
                          value={String(selectedNode.data.tool_name ?? '')}
                          onValueChange={(value) => {
                            const tool = integrationTools.find((t) => t.name === value);
                            setNodes((current) => current.map((node) => node.id === selectedNode.id
                              ? { ...node, data: { ...node.data, tool_name: value, label: value, description: tool?.description || '' } }
                              : node));
                          }}
                        >
                          <SelectTrigger><SelectValue placeholder="Select tool" /></SelectTrigger>
                          <SelectContent>
                            {integrationTools.map((t) => (
                              <SelectItem key={t.name} value={t.name}>{t.name}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <Label>Tool Parameters (JSON)</Label>
                        <Textarea
                          className="font-mono text-xs"
                          rows={5}
                          value={paramsJson}
                          onChange={(e) => {
                            setParamsJson(e.target.value);
                            try {
                              const parsed = JSON.parse(e.target.value || '{}');
                              setNodes((current) => current.map((node) => node.id === selectedNode.id
                                ? { ...node, data: { ...node.data, params: parsed } }
                                : node));
                            } catch { /* invalid json while typing */ }
                          }}
                        />
                      </div>
                    </>
                  )}

                  <div className="pt-4 border-t flex gap-2">
                    <Button variant="outline" size="sm" className="flex-1 gap-2" onClick={() => {
                      if (!selectedNode) return;
                      const copy: Node = {
                        ...selectedNode,
                        id: `node-${Date.now()}`,
                        position: { x: selectedNode.position.x + 40, y: selectedNode.position.y + 40 },
                      };
                      setNodes((nds) => [...nds, copy]);
                    }}>
                      <Copy className="h-4 w-4" />
                      Duplicate
                    </Button>
                    <Button variant="destructive" size="sm" className="flex-1 gap-2" onClick={deleteSelectedNode}>
                      <Trash2 className="h-4 w-4" />
                      Delete
                    </Button>
                  </div>
                </div>
              )}
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </AppLayout>
  );
}
