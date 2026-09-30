"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
import { 
  Play, 
  CheckCircle, 
  XCircle, 
  Clock, 
  Zap,
  BarChart,
  FileText,
  Code,
  Search,
  Bug,
  Sparkles,
  Loader2,
  ArrowRight,
  Network
} from 'lucide-react';
import { toast } from '@/hooks/use-toast';

interface WorkflowTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  step_count: number;
  input_schema: Record<string, string>;
}

interface WorkflowExecution {
  workflow_id: string;
  workflow_name: string;
  status: string;
  success: boolean;
  execution_time: number;
  steps_completed: number;
  steps_failed: number;
  total_steps: number;
  results: unknown;
  step_details: Array<{
    id: string;
    name: string;
    status: string;
    agent: string;
    execution_time: number;
    retry_count: number;
    error?: string;
  }>;
}

const categoryIcons: Record<string, React.ComponentType<React.SVGProps<SVGSVGElement>>> = {
  data_analysis: BarChart,
  customer_support: Sparkles,
  content_creation: FileText,
  code_development: Code,
  research: Search,
  testing: CheckCircle,
  automation: Zap,
  documentation: FileText,
};

const categoryColors: Record<string, string> = {
  data_analysis: 'bg-blue-500',
  customer_support: 'bg-purple-500',
  content_creation: 'bg-green-500',
  code_development: 'bg-orange-500',
  research: 'bg-indigo-500',
  testing: 'bg-red-500',
  automation: 'bg-yellow-500',
  documentation: 'bg-teal-500',
};

const quickStartOptions = [
  {
    id: 'analyze_data',
    title: 'Analyze Data',
    description: 'Upload and analyze data with AI insights',
    icon: BarChart,
    color: 'bg-blue-500',
    placeholder: 'Enter data source path or paste CSV data...'
  },
  {
    id: 'support_ticket',
    title: 'Support Ticket',
    description: 'Handle customer support inquiry',
    icon: Sparkles,
    color: 'bg-purple-500',
    placeholder: 'Describe the customer issue...'
  },
  {
    id: 'code_review',
    title: 'Code Review',
    description: 'Automated code review and analysis',
    icon: Code,
    color: 'bg-orange-500',
    placeholder: 'Enter repository URL or paste code...'
  },
  {
    id: 'research',
    title: 'Research Topic',
    description: 'Deep research with summarization',
    icon: Search,
    color: 'bg-indigo-500',
    placeholder: 'What would you like to research?'
  },
  {
    id: 'create_content',
    title: 'Create Content',
    description: 'Generate articles and content',
    icon: FileText,
    color: 'bg-green-500',
    placeholder: 'Describe the content you want to create...'
  },
  {
    id: 'fix_bug',
    title: 'Fix Bug',
    description: 'Investigate and fix bugs',
    icon: Bug,
    color: 'bg-red-500',
    placeholder: 'Describe the bug and symptoms...'
  },
];

export default function WorkflowDashboard() {
  const [templates, setTemplates] = useState<WorkflowTemplate[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<WorkflowTemplate | null>(null);
  const [loading, setLoading] = useState(false);
  const [execution, setExecution] = useState<WorkflowExecution | null>(null);
  const [quickStartInput, setQuickStartInput] = useState('');
  const [selectedQuickStart, setSelectedQuickStart] = useState<string | null>(null);
  const [inputData, setInputData] = useState<Record<string, unknown>>({});
  const [activeTab, setActiveTab] = useState('quick-start');

  async function loadTemplates() {
    try {
      const response = await fetch('http://localhost:8000/api/agents/api/workflows/templates/');
      const data = await response.json();
      setTemplates(data.templates || []);
    } catch (error) {
      console.error('Error loading templates:', error);
      toast({
        title: 'Error',
        description: 'Failed to load workflow templates',
        variant: 'destructive',
      });
    }
  };

  const executeQuickStart = async (useCase: string, input: string) => {
    if (!input.trim()) {
      toast({
        title: 'Input Required',
        description: 'Please provide input for the workflow',
        variant: 'destructive',
      });
      return;
    }

    setLoading(true);
    setExecution(null);

    try {
      const response = await fetch('http://localhost:8000/api/agents/api/workflows/quick_start/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          use_case: useCase,
          input: input,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to execute workflow');
      }

      const data = await response.json();
      setExecution(data.result);

      toast({
        title: 'Workflow Complete',
        description: `${data.result.workflow_name} completed successfully!`,
      });
    } catch (error) {
      console.error('Error executing workflow:', error);
      toast({
        title: 'Execution Failed',
        description: 'Failed to execute workflow. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const executeWorkflow = async (workflowId: string, inputs: Record<string, unknown>) => {
    setLoading(true);
    setExecution(null);

    try {
      const response = await fetch('http://localhost:8000/api/agents/api/workflows/execute/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          workflow_id: workflowId,
          input_data: inputs,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to execute workflow');
      }

      const data = await response.json();
      setExecution(data);

      toast({
        title: 'Workflow Complete',
        description: `Workflow completed successfully!`,
      });
    } catch (error) {
      console.error('Error executing workflow:', error);
      toast({
        title: 'Execution Failed',
        description: 'Failed to execute workflow. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-500" />;
      case 'running':
        return <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />;
      case 'pending':
        return <Clock className="h-5 w-5 text-gray-400" />;
      default:
        return <Clock className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'running':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };
    useEffect(() => {
        setTimeout(() => loadTemplates(), 0);
      }, []);

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Workflow Automation</h1>
          <p className="text-gray-600 mt-2">
            Multi-agent workflows for real-world tasks
          </p>
        </div>
        <Network className="h-12 w-12 text-blue-500" />
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="quick-start">Quick Start</TabsTrigger>
          <TabsTrigger value="templates">Templates</TabsTrigger>
          <TabsTrigger value="results">Results</TabsTrigger>
        </TabsList>

        <TabsContent value="quick-start" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Quick Start Workflows</CardTitle>
              <CardDescription>
                Get started quickly with common workflow patterns
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
                {quickStartOptions.map((option) => {
                  const Icon = option.icon;
                  return (
                    <Card
                      key={option.id}
                      className={`cursor-pointer transition-all hover:shadow-lg ${
                        selectedQuickStart === option.id ? 'ring-2 ring-blue-500' : ''
                      }`}
                      onClick={() => setSelectedQuickStart(option.id)}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-start space-x-3">
                          <div className={`p-2 rounded-lg ${option.color}`}>
                            <Icon className="h-6 w-6 text-white" />
                          </div>
                          <div className="flex-1">
                            <h3 className="font-semibold">{option.title}</h3>
                            <p className="text-sm text-gray-600 mt-1">
                              {option.description}
                            </p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>

              {selectedQuickStart && (
                <div className="space-y-4">
                  <div>
                    <Label>Input</Label>
                    <Textarea
                      placeholder={
                        quickStartOptions.find((o) => o.id === selectedQuickStart)
                          ?.placeholder
                      }
                      value={quickStartInput}
                      onChange={(e) => setQuickStartInput(e.target.value)}
                      rows={4}
                      className="mt-2"
                    />
                  </div>
                  <Button
                    onClick={() => executeQuickStart(selectedQuickStart, quickStartInput)}
                    disabled={loading || !quickStartInput.trim()}
                    className="w-full"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Executing Workflow...
                      </>
                    ) : (
                      <>
                        <Play className="mr-2 h-4 w-4" />
                        Start Workflow
                      </>
                    )}
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="templates" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Workflow Templates</CardTitle>
              <CardDescription>
                Browse and execute predefined workflow templates
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[500px]">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {templates.map((template) => {
                    const Icon = categoryIcons[template.category] || FileText;
                    const colorClass = categoryColors[template.category] || 'bg-gray-500';
                    
                    return (
                      <Card
                        key={template.id}
                        className="cursor-pointer hover:shadow-lg transition-all"
                        onClick={() => setSelectedTemplate(template)}
                      >
                        <CardContent className="p-4">
                          <div className="flex items-start space-x-3">
                            <div className={`p-2 rounded-lg ${colorClass}`}>
                              <Icon className="h-6 w-6 text-white" />
                            </div>
                            <div className="flex-1">
                              <h3 className="font-semibold">{template.name}</h3>
                              <p className="text-sm text-gray-600 mt-1">
                                {template.description}
                              </p>
                              <div className="flex items-center mt-2 space-x-2">
                                <Badge variant="secondary" className="text-xs">
                                  {template.step_count} steps
                                </Badge>
                                <Badge variant="outline" className="text-xs">
                                  {template.category.replace('_', ' ')}
                                </Badge>
                              </div>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              </ScrollArea>

              {selectedTemplate && (
                <div className="mt-6 p-4 border rounded-lg space-y-4">
                  <h3 className="font-semibold text-lg">{selectedTemplate.name}</h3>
                  <p className="text-sm text-gray-600">{selectedTemplate.description}</p>
                  
                  <div className="space-y-3">
                    {Object.entries(selectedTemplate.input_schema || {}).map(([key]) => (
                      <div key={key}>
                        <Label>{key.replace('_', ' ').toUpperCase()}</Label>
                        <Input
                          placeholder={`Enter ${key}...`}
                          value={String(inputData[key] || '')}
                          onChange={(e) =>
                            setInputData({ ...inputData, [key]: e.target.value })
                          }
                          className="mt-1"
                        />
                      </div>
                    ))}
                  </div>

                  <Button
                    onClick={() => executeWorkflow(selectedTemplate.id, inputData)}
                    disabled={loading}
                    className="w-full"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Executing...
                      </>
                    ) : (
                      <>
                        <Play className="mr-2 h-4 w-4" />
                        Execute Workflow
                      </>
                    )}
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="results" className="space-y-4">
          {!execution ? (
            <Card>
              <CardContent className="p-12 text-center">
                <Network className="h-16 w-16 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500">No workflow results yet</p>
                <p className="text-sm text-gray-400 mt-2">
                  Execute a workflow to see results here
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>{execution.workflow_name}</CardTitle>
                      <CardDescription>
                        Executed in {execution.execution_time.toFixed(2)}s
                      </CardDescription>
                    </div>
                    <Badge className={getStatusColor(execution.status)}>
                      {execution.status}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Progress</span>
                      <span className="text-sm font-medium">
                        {execution.steps_completed} / {execution.total_steps} steps
                      </span>
                    </div>
                    <Progress
                      value={(execution.steps_completed / execution.total_steps) * 100}
                    />

                    <div className="grid grid-cols-3 gap-4 pt-4">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-green-600">
                          {execution.steps_completed}
                        </div>
                        <div className="text-xs text-gray-600">Completed</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-red-600">
                          {execution.steps_failed}
                        </div>
                        <div className="text-xs text-gray-600">Failed</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-blue-600">
                          {execution.total_steps}
                        </div>
                        <div className="text-xs text-gray-600">Total</div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Step Details</CardTitle>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-[400px]">
                    <div className="space-y-3">
                      {execution.step_details.map((step, index) => (
                        <div
                          key={step.id}
                          className="flex items-start space-x-3 p-3 border rounded-lg"
                        >
                          <div className="mt-1">{getStatusIcon(step.status)}</div>
                          <div className="flex-1">
                            <div className="flex items-center justify-between">
                              <h4 className="font-medium">{step.name}</h4>
                              <Badge variant="outline" className="text-xs">
                                {step.execution_time.toFixed(2)}s
                              </Badge>
                            </div>
                            <p className="text-sm text-gray-600 mt-1">
                              Agent: {step.agent || 'Not assigned'}
                            </p>
                            {step.retry_count > 0 && (
                              <p className="text-xs text-orange-600 mt-1">
                                Retried {step.retry_count} times
                              </p>
                            )}
                            {step.error && (
                              <p className="text-xs text-red-600 mt-1">
                                Error: {step.error}
                              </p>
                            )}
                          </div>
                          {index < execution.step_details.length - 1 && (
                            <ArrowRight className="h-4 w-4 text-gray-400 mt-1" />
                          )}
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>

              {execution.results && typeof execution.results === 'object' && Object.keys(execution.results as Record<string, unknown>).length > 0 ? (
                <Card>
                  <CardHeader>
                    <CardTitle>Results</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ScrollArea className="h-[300px]">
                      <pre className="text-xs bg-gray-50 p-4 rounded-lg overflow-auto">
                        {JSON.stringify(execution.results, null, 2)}
                      </pre>
                    </ScrollArea>
                  </CardContent>
                </Card>
              ) : null}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
