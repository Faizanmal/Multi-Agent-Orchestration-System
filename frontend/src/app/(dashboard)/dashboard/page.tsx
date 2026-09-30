"use client";

/* eslint-disable @typescript-eslint/no-explicit-any */

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion, type Variants } from 'framer-motion';
import {
  Bot,
  Workflow,
  Activity,
  Zap,
  ArrowUp,
  ArrowDown,
  Clock,
  CheckCircle2,
  MessageSquare,
  Sparkles,
  Play,
  Pause,
  RefreshCw,
  Plus,
  ChevronRight,
  Brain,
  Eye,
  Cpu,
  Database,
} from 'lucide-react';
import apiClient, { type Agent } from '@/lib/api';
import { AppLayout } from '@/components/layout/AppLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { cn } from '@/lib/utils';
import { GettingStartedCard } from '@/components/onboarding/GettingStartedCard';
import { useAuth } from '@/contexts/AuthContext';

// Animation variants
const containerVariants: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
};

const itemVariants: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.5,
      ease: [0.42, 0, 0.58, 1],
    },
  },
};

// Agent types with icons
const agentTypes = [
  { type: 'orchestrator', icon: Brain, color: 'text-purple-500', bg: 'bg-purple-500/10' },
  { type: 'vision', icon: Eye, color: 'text-blue-500', bg: 'bg-blue-500/10' },
  { type: 'reasoning', icon: Cpu, color: 'text-green-500', bg: 'bg-green-500/10' },
  { type: 'action', icon: Zap, color: 'text-orange-500', bg: 'bg-orange-500/10' },
  { type: 'memory', icon: Database, color: 'text-cyan-500', bg: 'bg-cyan-500/10' },
  { type: 'custom', icon: Cpu, color: 'text-gray-500', bg: 'bg-gray-500/10' },
];

// Quick actions
const quickActions = [
  { title: 'Create Agent', icon: Bot, href: '/agents', gradient: 'from-indigo-500 to-purple-500' },
  { title: 'Build Workflow', icon: Workflow, href: '/workflows', gradient: 'from-blue-500 to-cyan-500' },
  { title: 'Start Chat', icon: MessageSquare, href: '/chat', gradient: 'from-green-500 to-emerald-500' },
  { title: 'Connect Apps', icon: Database, href: '/integrations', gradient: 'from-orange-500 to-amber-500' },
];

type DashboardAgent = Agent & { tasks?: number };

export default function DashboardPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [agents, setAgents] = useState<DashboardAgent[]>([]);
  const [dashboardData, setDashboardData] = useState<Record<string, unknown> | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [agentsRes, dashboardRes] = await Promise.all([
        apiClient.getAgents(),
        apiClient.getAnalyticsDashboard()
      ]);
      setAgents((agentsRes.results || agentsRes || []) as DashboardAgent[]);
      setDashboardData(dashboardRes as unknown as Record<string, unknown>);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    setTimeout(() => { loadData(); }, 0)
  }, []);

  const stats = dashboardData ? [
    {
      title: 'Active Agents',
      value: String((dashboardData.overview as Record<string, any>)?.agents?.by_status?.active || 0),
      change: `Total ${(dashboardData.overview as Record<string, any>)?.agents?.total || 0}`,
      changeType: 'positive' as const,
      icon: Bot,
      gradient: 'from-indigo-500 to-purple-500',
      description: 'Running workflows',
    },
    {
      title: 'Tasks Completed',
      value: String((dashboardData.overview as Record<string, any>)?.tasks?.by_status?.completed || 0),
      change: `${(((dashboardData.overview as Record<string, any>)?.tasks?.success_rate || 0) * 100).toFixed(1)}%`,
      changeType: 'positive' as const,
      icon: CheckCircle2,
      gradient: 'from-green-500 to-emerald-500',
      description: 'Success rate',
    },
    {
      title: 'Total Tasks',
      value: String((dashboardData.overview as Record<string, any>)?.tasks?.total || 0),
      change: 'Active',
      changeType: 'positive' as const,
      icon: Zap,
      gradient: 'from-orange-500 to-amber-500',
      description: 'All tasks',
    },
    {
      title: 'Total Messages',
      value: String((dashboardData.overview as Record<string, any>)?.messages?.total || 0),
      change: 'Activity',
      changeType: 'positive' as const,
      icon: Activity,
      gradient: 'from-blue-500 to-cyan-500',
      description: 'In sessions',
    },
  ] : [
    { title: 'Active Agents', value: '-', change: '-', changeType: 'positive' as const, icon: Bot, gradient: 'from-indigo-500 to-purple-500', description: 'Loading...' },
    { title: 'Tasks Completed', value: '-', change: '-', changeType: 'positive' as const, icon: CheckCircle2, gradient: 'from-green-500 to-emerald-500', description: 'Loading...' },
    { title: 'Total Tasks', value: '-', change: '-', changeType: 'positive' as const, icon: Zap, gradient: 'from-orange-500 to-amber-500', description: 'Loading...' },
    { title: 'Total Messages', value: '-', change: '-', changeType: 'positive' as const, icon: Activity, gradient: 'from-blue-500 to-cyan-500', description: 'Loading...' },
  ];

  const getAgentTypeInfo = (type: string) => {
    return agentTypes.find(t => t.type === type) || agentTypes[0];
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-500';
      case 'processing': return 'bg-blue-500 animate-pulse';
      case 'error': return 'bg-red-500';
      default: return 'bg-slate-400';
    }
  };

  return (
    <AppLayout>
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="space-y-6"
      >
        {/* Header */}
        <motion.div variants={itemVariants} className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-3">
              <Sparkles className="h-8 w-8 text-primary" />
              Welcome back{user?.first_name || user?.display_name || user?.username ? `, ${user.first_name || user.display_name || user.username}` : ''}
            </h1>
            <p className="text-muted-foreground mt-1">
              Here&apos;s what&apos;s happening with your AI agents today.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Button variant="outline" className="gap-2" onClick={loadData}>
              <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button 
              className="gap-2 bg-gradient-to-r from-indigo-500 to-purple-500 hover:opacity-90"
              onClick={() => router.push('/agents')}
            >
              <Plus className="h-4 w-4" />
              New Agent
            </Button>
          </div>
        </motion.div>

        <motion.div variants={itemVariants}>
          <GettingStartedCard
            hasAgents={agents.length > 0}
            hasMessages={Number((dashboardData?.overview as Record<string, any>)?.messages?.total || 0) > 0}
          />
        </motion.div>

        {/* Stats Grid */}
        <motion.div variants={itemVariants} className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {stats.map((stat, index) => (
            <motion.div
              key={stat.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <Card className="relative overflow-hidden group hover:shadow-lg transition-all duration-300">
                {/* Gradient Background */}
                <div className={cn(
                  "absolute inset-0 opacity-0 group-hover:opacity-5 transition-opacity bg-gradient-to-br",
                  stat.gradient
                )} />
                
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div className={cn(
                      "flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br",
                      stat.gradient
                    )}>
                      <stat.icon className="h-6 w-6 text-white" />
                    </div>
                    <Badge 
                      variant={stat.changeType === 'positive' ? 'default' : 'destructive'}
                      className="flex items-center gap-1"
                    >
                      {stat.changeType === 'positive' ? (
                        <ArrowUp className="h-3 w-3" />
                      ) : (
                        <ArrowDown className="h-3 w-3" />
                      )}
                      {stat.change}
                    </Badge>
                  </div>
                  <div className="mt-4">
                    <h3 className="text-3xl font-bold">{stat.value}</h3>
                    <p className="text-sm text-muted-foreground">{stat.title}</p>
                    <p className="text-xs text-muted-foreground mt-1">{stat.description}</p>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </motion.div>

        {/* Quick Actions */}
        <motion.div variants={itemVariants}>
          <h2 className="text-lg font-semibold mb-4">Quick Actions</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {quickActions.map((action, index) => (
              <motion.a
                key={action.title}
                href={action.href}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.3 + index * 0.1 }}
                whileHover={{ scale: 1.02, y: -2 }}
                whileTap={{ scale: 0.98 }}
                className="group"
              >
                <Card className="relative overflow-hidden cursor-pointer hover:shadow-lg transition-all duration-300 border-dashed">
                  <div className={cn(
                    "absolute inset-0 opacity-0 group-hover:opacity-10 transition-opacity bg-gradient-to-br",
                    action.gradient
                  )} />
                  <CardContent className="flex items-center gap-4 p-4">
                    <div className={cn(
                      "flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br",
                      action.gradient
                    )}>
                      <action.icon className="h-5 w-5 text-white" />
                    </div>
                    <span className="font-medium">{action.title}</span>
                    <ChevronRight className="h-4 w-4 ml-auto text-muted-foreground group-hover:translate-x-1 transition-transform" />
                  </CardContent>
                </Card>
              </motion.a>
            ))}
          </div>
        </motion.div>

        {/* Main Content Grid */}
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Active Agents */}
          <motion.div variants={itemVariants} className="lg:col-span-2">
            <Card className="h-full">
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>Active Agents</CardTitle>
                  <CardDescription>Monitor and manage your AI agents</CardDescription>
                </div>
                <Button variant="ghost" size="sm" className="gap-2">
                  View All
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {agents.map((agent, index) => {
                    const typeInfo = getAgentTypeInfo(agent.type);
                    const Icon = typeInfo.icon;
                    
                    return (
                      <motion.div
                        key={agent.id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.4 + index * 0.1 }}
                        className="flex items-center gap-4 p-4 rounded-xl bg-muted/50 hover:bg-muted transition-colors group"
                      >
                        <div className={cn("flex h-10 w-10 items-center justify-center rounded-lg", typeInfo.bg)}>
                          <Icon className={cn("h-5 w-5", typeInfo.color)} />
                        </div>
                        
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="font-medium truncate">{agent.name}</span>
                            <span className={cn("h-2 w-2 rounded-full", getStatusColor(agent.status))} />
                          </div>
                          <div className="flex items-center gap-4 text-sm text-muted-foreground">
                            <span className="capitalize">{agent.type}</span>
                            <span>{agent.tasks} tasks</span>
                          </div>
                        </div>

                        <div className="hidden sm:flex items-center gap-4">
                          <div className="text-right">
                            <div className="text-sm font-medium">{agent.tasks || 0} tasks</div>
                            <div className="text-xs text-muted-foreground">Processed</div>
                          </div>
                          <Progress value={agent.performance_metrics?.accuracy ?? 100} className="w-20 h-2" />
                        </div>

                        <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                          {agent.status === 'active' ? (
                            <Button variant="ghost" size="icon" className="h-8 w-8">
                              <Pause className="h-4 w-4" />
                            </Button>
                          ) : (
                            <Button variant="ghost" size="icon" className="h-8 w-8">
                              <Play className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      </motion.div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Recent Activity */}
          <motion.div variants={itemVariants}>
            <Card className="h-full">
              <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
                <CardDescription>Latest updates from your agents</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {((dashboardData?.recent_activities as Array<Record<string, unknown>>) || []).map((activity, index: number) => (
                    <motion.div
                      key={String(activity.id ?? index)}
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.5 + index * 0.1 }}
                      className="flex items-start gap-3"
                    >
                      <div className={cn(
                        "mt-1 h-2 w-2 rounded-full shrink-0",
                        activity.status === 'success' && "bg-green-500",
                        activity.status === 'warning' && "bg-yellow-500",
                        activity.status === 'info' && "bg-blue-500",
                        activity.status === 'error' && "bg-red-500"
                      )} />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium">{String(activity.action ?? '')}</p>
                        <p className="text-xs text-muted-foreground truncate">{String(activity.agent ?? '')}</p>
                      </div>
                      <div className="flex items-center gap-1 text-xs text-muted-foreground">
                        <Clock className="h-3 w-3" />
                        {String(activity.time ?? '')}
                      </div>
                    </motion.div>
                  ))}
                  {(!dashboardData?.recent_activities || (dashboardData.recent_activities as unknown[]).length === 0) && (
                    <div className="text-center text-muted-foreground text-sm py-4">
                      No recent activity.
                    </div>
                  )}
                </div>

                <Button variant="ghost" className="w-full mt-4 text-muted-foreground">
                  View All Activity
                  <ChevronRight className="h-4 w-4 ml-2" />
                </Button>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Performance Overview */}
        <motion.div variants={itemVariants}>
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Performance Overview</CardTitle>
                  <CardDescription>System metrics and health status</CardDescription>
                </div>
                <Tabs defaultValue="24h" className="w-auto">
                  <TabsList>
                    <TabsTrigger value="24h">24h</TabsTrigger>
                    <TabsTrigger value="7d">7d</TabsTrigger>
                    <TabsTrigger value="30d">30d</TabsTrigger>
                  </TabsList>
                </Tabs>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
                {[
                  { label: 'CPU Usage', value: 45, color: 'bg-blue-500' },
                  { label: 'Memory', value: 62, color: 'bg-purple-500' },
                  { label: 'API Quota', value: 78, color: 'bg-green-500' },
                  { label: 'Storage', value: 34, color: 'bg-orange-500' },
                ].map((metric, index) => (
                  <motion.div
                    key={metric.label}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.6 + index * 0.1 }}
                    className="space-y-2"
                  >
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">{metric.label}</span>
                      <span className="font-medium">{metric.value}%</span>
                    </div>
                    <div className="h-2 rounded-full bg-muted overflow-hidden">
                      <motion.div
                        className={cn("h-full rounded-full", metric.color)}
                        initial={{ width: 0 }}
                        animate={{ width: `${metric.value}%` }}
                        transition={{ duration: 1, delay: 0.8 + index * 0.1 }}
                      />
                    </div>
                  </motion.div>
                ))}
              </div>

              {/* System Status */}
              <div className="mt-6 pt-6 border-t">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="relative flex h-3 w-3">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
                    </span>
                    <span className="text-sm font-medium">All Systems Operational</span>
                  </div>
                  <Button variant="outline" size="sm">
                    View Status Page
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </motion.div>
    </AppLayout>
  );
}
