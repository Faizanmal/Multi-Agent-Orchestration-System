"use client";

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import Header from '@/components/layout/Header';
import MainWorkspace from '@/components/workspace/MainWorkspace';
import AgentProvider from "@/contexts/AgentContext";
import { WebSocketProvider } from '@/contexts/WebSocketContext';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { EnhancedAgentPanel } from '@/components/agents/EnhancedAgentPanel';
import { OrchestrationPanel } from '@/components/orchestration/OrchestrationPanel';
import { InputBar } from '@/components/input/InputBar';
import { ApiHealthStatus } from '@/components/status/ApiHealthStatus';
import { ApiConnectionTest } from '@/components/test/ApiConnectionTest';
import ProjectOverview from '@/components/project/ProjectOverview';
import APIIntegrationHub from '@/components/integrations/APIIntegrationHub';
import AdvancedReportingDashboard from '@/components/reporting/AdvancedReportingDashboard';
import NotificationCenter from '@/components/notifications/NotificationCenter';
import DataPipelineManager from '@/components/data/DataPipelineManager';
import AgentChatInterface from '@/components/chat/AgentChatInterface';
import AgentPerformanceDashboard from '@/components/performance/AgentPerformanceDashboard';
import PluginHub from '@/components/plugins/PluginHub';
import PWAProvider from '@/contexts/PWAContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { getAgents } from '@/lib/api';
import { Brain, Eye, Cpu, Zap, Activity, Settings, Globe, BarChart3, Bell, Database, MessageSquare, TrendingUp } from 'lucide-react';

interface Agent {
  id: string;
  name: string;
  type: 'orchestrator' | 'vision' | 'reasoning' | 'action' | 'memory' | 'custom';
  status: 'idle' | 'active' | 'processing' | 'error';
  capabilities: string[];
}

const agentTypeIcons = {
  orchestrator: Brain,
  vision: Eye,
  reasoning: Cpu,
  action: Zap,
  memory: Activity,
  custom: Settings,
};

export default function WorkspacePage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('chat');

  useEffect(() => {
    let isMounted = true;

    async function loadAgents() {
      try {
        const response = await getAgents();
        if (!isMounted) {
          return;
        }

        setAgents(
          response.results.map((agent) => ({
            id: agent.id,
            name: agent.name,
            type: agent.type,
            status: agent.status,
            capabilities: agent.capabilities,
          }))
        );
      } catch (error) {
        console.error('Failed to load agents for workspace:', error);
        if (isMounted) {
          setAgents([]);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    loadAgents();

    return () => {
      isMounted = false;
    };
  }, []);

  const getStatusColor = (status: Agent['status']) => {
    switch (status) {
      case 'active': return 'bg-green-500';
      case 'processing': return 'bg-blue-500 animate-pulse';
      case 'error': return 'bg-red-500';
      default: return 'bg-gray-400';
    }
  };

  if (isLoading) {
    return (
      <ThemeProvider>
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-lg font-medium">Initializing Multi-Agent System...</p>
            <p className="text-sm text-muted-foreground mt-2">Connecting agents and establishing workflows</p>
          </div>
        </div>
      </ThemeProvider>
    );
  }

  return (
    <PWAProvider>
      <ThemeProvider>
        <AgentProvider>
          <WebSocketProvider>
            <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900">
              <Header />

              <div className="container mx-auto px-4 py-6">
                {/* Hero Section */}
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, ease: "easeOut" }}
                className="mb-12 text-center p-12 rounded-3xl backdrop-blur-xl bg-white/40 dark:bg-slate-900/40 border border-white/40 dark:border-slate-700/50 shadow-[0_8px_32px_0_rgba(31,38,135,0.07)]"
              >
                <motion.div
                  initial={{ scale: 0.9 }}
                  animate={{ scale: 1 }}
                  transition={{ duration: 0.5, delay: 0.2 }}
                >
                  <h1 className="text-6xl font-extrabold mb-6 bg-gradient-to-r from-blue-600 via-indigo-500 to-purple-600 bg-clip-text text-transparent drop-shadow-sm">
                    Beyond Chatbots
                  </h1>
                </motion.div>
                <p className="text-xl text-slate-700 dark:text-slate-300 max-w-3xl mx-auto leading-relaxed">
                  Intelligent agent orchestration with real-time performance, multi-modal intelligence, 
                  and genuine problem-solving capabilities powered by Groq&apos;s lightning-fast inference.
                </p>
                <motion.div 
                  className="mt-8 flex justify-center gap-4"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.6 }}
                >
                  <button className="px-8 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-full font-semibold shadow-lg hover:shadow-xl hover:scale-105 transition-all">
                    Start Orchestrating
                  </button>
                  <button className="px-8 py-3 bg-white/50 dark:bg-black/30 backdrop-blur-md text-slate-900 dark:text-white rounded-full font-semibold shadow-sm border border-white/20 hover:bg-white/60 dark:hover:bg-black/40 transition-all">
                    View Pricing
                  </button>
                </motion.div>
              </motion.div>

            {/* Main Interface */}
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="grid w-full grid-cols-10 mb-8">
                <TabsTrigger value="project" className="flex items-center gap-2">
                  <Zap className="h-4 w-4" />
                  Project
                </TabsTrigger>
                    <TabsTrigger value="chat" className="flex items-center gap-2">
                      <MessageSquare className="h-4 w-4" />
                      Chat
                    </TabsTrigger>
                    <TabsTrigger value="integrations" className="flex items-center gap-2">
                      <Globe className="h-4 w-4" />
                      APIs
                    </TabsTrigger>
                    <TabsTrigger value="reporting" className="flex items-center gap-2">
                      <BarChart3 className="h-4 w-4" />
                      Reports
                    </TabsTrigger>
                    <TabsTrigger value="notifications" className="flex items-center gap-2">
                      <Bell className="h-4 w-4" />
                      Notifications
                    </TabsTrigger>
                    <TabsTrigger value="data" className="flex items-center gap-2">
                      <Database className="h-4 w-4" />
                      Pipelines
                    </TabsTrigger>
                    <TabsTrigger value="agents" className="flex items-center gap-2">
                      <Brain className="h-4 w-4" />
                      Agents
                    </TabsTrigger>
                    <TabsTrigger value="orchestration" className="flex items-center gap-2">
                      <Settings className="h-4 w-4" />
                      Orchestration
                    </TabsTrigger>
                    <TabsTrigger value="performance" className="flex items-center gap-2">
                      <TrendingUp className="h-4 w-4" />
                      Performance
                    </TabsTrigger>
                    <TabsTrigger value="plugins" className="flex items-center gap-2">
                      <Settings className="h-4 w-4" />
                      Plugins
                    </TabsTrigger>
                    <TabsTrigger value="test" className="flex items-center gap-2">
                      <Settings className="h-4 w-4" />
                      API Test
                    </TabsTrigger>
                  </TabsList>

                  <TabsContent value="integrations" className="mt-6">
                    <APIIntegrationHub />
                  </TabsContent>

                  <TabsContent value="reporting" className="mt-6">
                    <AdvancedReportingDashboard />
                  </TabsContent>

                  <TabsContent value="notifications" className="mt-6">
                    <NotificationCenter />
                  </TabsContent>

                  <TabsContent value="data" className="mt-6">
                    <DataPipelineManager />
                  </TabsContent>

                  <TabsContent value="project" className="mt-6">
                    <ProjectOverview />
                  </TabsContent>

                  <TabsContent value="chat" className="mt-6">
                    <AgentChatInterface />
                  </TabsContent>

                  <TabsContent value="dashboard" className="mt-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
                      {/* API Health Status */}
                      <ApiHealthStatus />

                      {/* System Status */}
                      <Card className="hover:shadow-lg transition-shadow">
                        <CardHeader>
                          <CardTitle className="flex items-center gap-2">
                            <Activity className="h-5 w-5 text-green-500" />
                            System Health
                          </CardTitle>
                          <CardDescription>Real-time system performance metrics</CardDescription>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-4">
                            <div className="flex justify-between items-center">
                              <span>Active Agents</span>
                              <Badge variant="secondary" className="bg-green-100 text-green-800">
                                {agents.filter(a => a.status === 'active').length} / {agents.length}
                              </Badge>
                            </div>
                            <div className="flex justify-between items-center">
                              <span>Processing Tasks</span>
                              <Badge variant="secondary">
                                {agents.filter(a => a.status === 'processing').length}
                              </Badge>
                            </div>
                            <div className="flex justify-between items-center">
                              <span>Avg Response Time</span>
                              <Badge variant="outline" className="text-blue-600">~185ms</Badge>
                            </div>
                            <div className="flex justify-between items-center">
                              <span>Groq Inference</span>
                              <Badge variant="outline" className="text-purple-600">Ultra-Fast</Badge>
                            </div>
                          </div>
                        </CardContent>
                      </Card>

                      {/* Active Agents Overview */}
                      <Card className="hover:shadow-lg transition-shadow">
                        <CardHeader>
                          <CardTitle className="flex items-center gap-2">
                            <Brain className="h-5 w-5 text-blue-500" />
                            Agent Network
                          </CardTitle>
                          <CardDescription>Specialized agents in coordination</CardDescription>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-3">
                            {agents.map(agent => {
                              const IconComponent = agentTypeIcons[agent.type];
                              return (
                                <div key={agent.id} className="flex items-center gap-3 p-2 rounded-lg bg-muted/30">
                                  <IconComponent className="h-4 w-4 text-muted-foreground" />
                                  <div className="flex-1 min-w-0">
                                    <p className="text-sm font-medium truncate">{agent.name}</p>
                                    <p className="text-xs text-muted-foreground capitalize">{agent.type}</p>
                                  </div>
                                  <div className={`w-2 h-2 rounded-full ${getStatusColor(agent.status)}`} />
                                </div>
                              );
                            })}
                          </div>
                        </CardContent>
                      </Card>

                      {/* Capabilities Overview */}
                      <Card className="hover:shadow-lg transition-shadow">
                        <CardHeader>
                          <CardTitle className="flex items-center gap-2">
                            <Zap className="h-5 w-5 text-purple-500" />
                            Multi-Modal Intelligence
                          </CardTitle>
                          <CardDescription>Integrated processing capabilities</CardDescription>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-3">
                            <div className="flex items-center gap-2">
                              <Eye className="h-4 w-4" />
                              <span className="text-sm">Vision Processing</span>
                              <Badge variant="outline">Ready</Badge>
                            </div>
                            <div className="flex items-center gap-2">
                              <Brain className="h-4 w-4" />
                              <span className="text-sm">Natural Language</span>
                              <Badge variant="outline">Active</Badge>
                            </div>
                            <div className="flex items-center gap-2">
                              <Cpu className="h-4 w-4" />
                              <span className="text-sm">Reasoning Engine</span>
                              <Badge variant="outline">Online</Badge>
                            </div>
                            <div className="flex items-center gap-2">
                              <Activity className="h-4 w-4" />
                              <span className="text-sm">Real-time Sync</span>
                              <Badge variant="outline">Connected</Badge>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    </div>

                    {/* Recent Activity */}
                    <Card className="hover:shadow-lg transition-shadow">
                      <CardHeader>
                        <CardTitle>System Activity</CardTitle>
                        <CardDescription>Latest agent interactions and workflow events</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-4">
                          <div className="flex items-start gap-3 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                            <Brain className="h-5 w-5 mt-1 text-blue-600" />
                            <div>
                              <p className="text-sm font-medium">Master Orchestrator initialized workflow coordination</p>
                              <p className="text-xs text-muted-foreground">System ready for multi-agent collaboration • Just now</p>
                            </div>
                          </div>
                          <div className="flex items-start gap-3 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                            <Activity className="h-5 w-5 mt-1 text-green-600" />
                            <div>
                              <p className="text-sm font-medium">Memory Keeper established context synchronization</p>
                              <p className="text-xs text-muted-foreground">All agents connected to shared knowledge base • 2 min ago</p>
                            </div>
                          </div>
                          <div className="flex items-start gap-3 p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                            <Eye className="h-5 w-5 mt-1 text-purple-600" />
                            <div>
                              <p className="text-sm font-medium">Vision Analyst calibrated for multi-modal processing</p>
                              <p className="text-xs text-muted-foreground">Image, video, and document analysis ready • 5 min ago</p>
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </TabsContent>

                  <TabsContent value="agents" className="mt-6">
                    <EnhancedAgentPanel />
                  </TabsContent>

                  <TabsContent value="orchestration" className="mt-6">
                    <OrchestrationPanel />
                  </TabsContent>

                  <TabsContent value="performance" className="mt-6">
                    <AgentPerformanceDashboard />
                  </TabsContent>

                  <TabsContent value="workspace" className="mt-6">
                    <MainWorkspace />
                  </TabsContent>

                  <TabsContent value="plugins" className="mt-6">
                    <PluginHub />
                  </TabsContent>
                  <TabsContent value="test" className="mt-6">
                    <ApiConnectionTest />
                  </TabsContent>
                </Tabs>
              </div>

              {/* Smart Input Interface - Always accessible */}
              <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2 w-full max-w-6xl px-4 z-50">
                <InputBar onSend={(message: string) => console.log('Message sent:', message)} />
              </div>
            </div>
          </WebSocketProvider>
        </AgentProvider>
      </ThemeProvider>
    </PWAProvider>
  );
}
