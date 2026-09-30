"use client";

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import {
  BarChart3,
  TrendingUp,
  DollarSign,
  Activity,
  Zap,
  Bot,
  ArrowUp,
  ArrowDown,
  RefreshCw,
  Download,
  Calendar,
  AlertTriangle,
  CheckCircle2,
  Sparkles,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import { AppLayout } from '@/components/layout/AppLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart as RechartsLineChart,
  Line,
  BarChart,
  Bar,
  PieChart as RechartsPieChart,
  Pie,
  Cell,
} from 'recharts';
import { cn } from '@/lib/utils';
import {
  getAnalyticsDashboard,
  getSystemPerformance,
  getAnalyticsInsights,
  getPerformanceMetrics,
  getAnalyticsCostSummary,
  getAnalyticsPredictions,
  getAnalyticsMetricTrends,
} from '@/lib/api';

const MODEL_COLORS = ['#8b5cf6', '#10b981', '#3b82f6', '#6b7280', '#f59e0b', '#06b6d4'];
const AGENT_COLORS = ['#8b5cf6', '#3b82f6', '#10b981', '#f59e0b', '#06b6d4', '#ef4444'];

type StatCard = {
  title: string;
  value: string;
  change: string;
  changeType: 'positive' | 'negative';
  icon: typeof Activity;
  gradient: string;
  description: string;
};

type ChartPoint = { name: string; requests: number; latency: number; errors: number };
type CostPoint = { name: string; groq: number; openai: number; anthropic: number; [key: string]: string | number };
type AgentRow = { name: string; tasks: number; success: number; color: string };
type ModelSlice = { name: string; value: number; color: string };
type InsightCard = {
  title: string;
  description: string;
  type: string;
  impact: string;
};

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function num(value: unknown, fallback = 0): number {
  const n = typeof value === 'number' ? value : Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function formatCompact(value: number): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(1)}K`;
  return value.toLocaleString();
}

function derivePerformanceSeries(dashboard: Record<string, unknown>, systemPerf: Record<string, unknown>): ChartPoint[] {
  const trends = asRecord(dashboard.performance_trends);
  const completion = asArray(trends.task_completion_rate);
  const responseTimes = asArray(trends.response_times);
  const errorRates = asArray(trends.error_rates);

  if (completion.length > 0 || responseTimes.length > 0) {
    const len = Math.max(completion.length, responseTimes.length, errorRates.length, 1);
    return Array.from({ length: len }, (_, i) => {
      const c = asRecord(completion[i]);
      const r = asRecord(responseTimes[i]);
      const e = asRecord(errorRates[i]);
      const label =
        String(c.date || c.period || c.label || r.date || r.period || `P${i + 1}`);
      return {
        name: label.length > 12 ? label.slice(5, 10) : label,
        requests: num(c.total ?? c.count ?? c.value, 0),
        latency: num(r.avg_response_time ?? r.value ?? r.latency, 0),
        errors: Math.round(num(e.error_rate ?? e.value, 0) * (num(c.total, 100) || 100)),
      };
    });
  }

  // Derive a minimal series from aggregate system performance when trends are empty
  const overview = asRecord(dashboard.overview);
  const tasks = asRecord(overview.tasks);
  const total = num(tasks.total, num(systemPerf.total_tasks));
  if (total <= 0) return [];

  const latency = num(systemPerf.avg_response_time ?? systemPerf.average_latency, 0);
  const failed = num(asRecord(tasks.by_status).failed, num(systemPerf.failed_tasks));
  return [
    { name: 'Period', requests: total, latency, errors: failed },
  ];
}

function deriveCostSeries(costSummary: Record<string, unknown>): CostPoint[] {
  const byProvider = asRecord(costSummary.by_provider);
  const providers = Object.keys(byProvider);
  if (providers.length === 0) return [];

  const point: CostPoint = { name: 'Current', groq: 0, openai: 0, anthropic: 0 };
  for (const provider of providers) {
    const entry = asRecord(byProvider[provider]);
    const cost = num(entry.cost);
    const key = provider.toLowerCase();
    if (key.includes('groq')) point.groq = cost;
    else if (key.includes('openai') || key.includes('open_ai')) point.openai = cost;
    else if (key.includes('anthropic') || key.includes('claude')) point.anthropic = cost;
    else point[key] = cost;
  }
  return [point];
}

function deriveAgentRows(dashboard: Record<string, unknown>): AgentRow[] {
  const metrics = asRecord(dashboard.agent_metrics);
  const individual = asRecord(metrics.individual_metrics);
  return Object.values(individual).map((raw, index) => {
    const agent = asRecord(raw);
    const info = asRecord(agent.agent_info);
    const tasks = asRecord(agent.tasks);
    const total = num(tasks.total);
    const completed = num(tasks.completed);
    const success = total > 0 ? (completed / total) * 100 : num(agent.efficiency_score) * 100;
    return {
      name: String(info.name || `Agent ${index + 1}`),
      tasks: total,
      success: Math.round(success * 10) / 10,
      color: AGENT_COLORS[index % AGENT_COLORS.length],
    };
  });
}

function deriveModelUsage(dashboard: Record<string, unknown>, costSummary: Record<string, unknown>): ModelSlice[] {
  const byProvider = asRecord(costSummary.by_provider);
  const providers = Object.keys(byProvider);
  if (providers.length > 0) {
    const totalRequests = providers.reduce(
      (sum, p) => sum + num(asRecord(byProvider[p]).requests),
      0
    );
    if (totalRequests > 0) {
      return providers.map((provider, i) => ({
        name: provider,
        value: Math.round((num(asRecord(byProvider[provider]).requests) / totalRequests) * 100),
        color: MODEL_COLORS[i % MODEL_COLORS.length],
      }));
    }
  }

  const taskAnalytics = asRecord(dashboard.task_analytics);
  const typeStats = asArray(taskAnalytics.task_type_distribution ?? taskAnalytics.by_type);
  if (typeStats.length > 0) {
    const total = typeStats.reduce((sum: number, item) => sum + num(asRecord(item).count), 0) || 1;
    return typeStats.slice(0, 6).map((item, i) => {
      const row = asRecord(item);
      return {
        name: String(row.task_type || row.name || `Type ${i + 1}`),
        value: Math.round((num(row.count) / (total as number)) * 100),
        color: MODEL_COLORS[i % MODEL_COLORS.length],
      };
    });
  }

  return [];
}

function deriveInsights(insightsRes: Record<string, unknown>, dashboard: Record<string, unknown>): InsightCard[] {
  const fromApi = asArray(insightsRes.insights ?? insightsRes.recommendations ?? dashboard.insights);
  if (fromApi.length > 0) {
    return fromApi.slice(0, 6).map((item) => {
      const row = asRecord(item);
      return {
        title: String(row.title || row.name || 'Insight'),
        description: String(row.description || row.message || row.suggested_action || ''),
        type: String(row.category || row.type || 'optimization'),
        impact: String(row.impact || 'Medium'),
      };
    });
  }

  const recommendations = asArray(dashboard.recommendations);
  return recommendations.slice(0, 6).map((item) => {
    const row = asRecord(item);
    return {
      title: String(row.title || 'Recommendation'),
      description: String(row.description || ''),
      type: String(row.type || 'optimization'),
      impact: String(row.impact || 'Medium'),
    };
  });
}

function buildStats(
  dashboard: Record<string, unknown>,
  systemPerf: Record<string, unknown>,
  costSummary: Record<string, unknown>,
  perfMetrics: Record<string, unknown>
): StatCard[] {
  const overview = asRecord(dashboard.overview);
  const tasks = asRecord(overview.tasks);
  const messages = asRecord(overview.messages);

  const totalRequests = num(
    messages.total,
    num(tasks.total, num(perfMetrics.total_requests ?? systemPerf.total_tasks))
  );
  const avgLatency = num(
    systemPerf.avg_response_time ?? systemPerf.average_latency ?? perfMetrics.avg_latency,
    0
  );
  const successRate =
    num(tasks.success_rate, num(systemPerf.success_rate, num(perfMetrics.success_rate))) *
    (num(tasks.success_rate) <= 1 || num(systemPerf.success_rate) <= 1 ? 100 : 1);
  const totalCost = num(costSummary.total_cost);

  return [
    {
      title: 'Total Requests',
      value: formatCompact(totalRequests),
      change: totalRequests > 0 ? `${totalRequests}` : '0',
      changeType: 'positive',
      icon: Activity,
      gradient: 'from-indigo-500 to-purple-500',
      description: 'In selected range',
    },
    {
      title: 'Avg Latency',
      value: avgLatency > 0 ? `${avgLatency.toFixed(0)}ms` : '—',
      change: avgLatency > 0 ? 'live' : 'n/a',
      changeType: 'positive',
      icon: Zap,
      gradient: 'from-green-500 to-emerald-500',
      description: 'System average',
    },
    {
      title: 'Success Rate',
      value: `${successRate.toFixed(1)}%`,
      change: successRate >= 95 ? 'Healthy' : 'Watch',
      changeType: successRate >= 90 ? 'positive' : 'negative',
      icon: CheckCircle2,
      gradient: 'from-blue-500 to-cyan-500',
      description: 'Task completion',
    },
    {
      title: 'Total Cost',
      value: totalCost > 0 ? `$${totalCost.toFixed(2)}` : '$0',
      change: `${num(costSummary.total_requests)} req`,
      changeType: 'negative',
      icon: DollarSign,
      gradient: 'from-orange-500 to-amber-500',
      description: 'Provider spend',
    },
  ];
}

export default function AnalyticsPage() {
  const [timeRange, setTimeRange] = useState('7d');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dashboard, setDashboard] = useState<Record<string, unknown>>({});
  const [systemPerf, setSystemPerf] = useState<Record<string, unknown>>({});
  const [insightsRes, setInsightsRes] = useState<Record<string, unknown>>({});
  const [costSummary, setCostSummary] = useState<Record<string, unknown>>({});
  const [perfMetrics, setPerfMetrics] = useState<Record<string, unknown>>({});

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const results = await Promise.allSettled([
        getAnalyticsDashboard(timeRange),
        getSystemPerformance(),
        getAnalyticsInsights(),
        getPerformanceMetrics(),
        getAnalyticsCostSummary({ time_range: timeRange }),
        getAnalyticsPredictions(),
        getAnalyticsMetricTrends({ time_range: timeRange }),
      ]);

      const [dash, sys, insights, perf, costs] = results;

      if (dash.status === 'fulfilled') setDashboard(asRecord(dash.value));
      else setDashboard({});

      if (sys.status === 'fulfilled') setSystemPerf(asRecord(sys.value));
      else setSystemPerf({});

      if (insights.status === 'fulfilled') setInsightsRes(asRecord(insights.value));
      else setInsightsRes({});

      if (perf.status === 'fulfilled') setPerfMetrics(asRecord(perf.value));
      else setPerfMetrics({});

      if (costs.status === 'fulfilled') setCostSummary(asRecord(costs.value.data ?? costs.value));
      else setCostSummary({});

      const criticalFailed = dash.status === 'rejected' && sys.status === 'rejected';
      if (criticalFailed) {
        setError('Failed to load analytics data');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load analytics');
    } finally {
      setLoading(false);
    }
  }, [timeRange]);

  useEffect(() => {
    setTimeout(() => { loadData(); }, 0)
  }, [loadData]);

  const statsCards = useMemo(
    () => buildStats(dashboard, systemPerf, costSummary, perfMetrics),
    [dashboard, systemPerf, costSummary, perfMetrics]
  );
  const performanceData = useMemo(
    () => derivePerformanceSeries(dashboard, systemPerf),
    [dashboard, systemPerf]
  );
  const costData = useMemo(() => deriveCostSeries(costSummary), [costSummary]);
  const agentPerformanceData = useMemo(() => deriveAgentRows(dashboard), [dashboard]);
  const modelUsageData = useMemo(
    () => deriveModelUsage(dashboard, costSummary),
    [dashboard, costSummary]
  );
  const insights = useMemo(
    () => deriveInsights(insightsRes, dashboard),
    [insightsRes, dashboard]
  );

  const requestTrend =
    performanceData.length >= 2
      ? ((performanceData[performanceData.length - 1].requests -
          performanceData[0].requests) /
          Math.max(performanceData[0].requests, 1)) *
        100
      : 0;

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
              <BarChart3 className="h-8 w-8 text-primary" />
              Analytics
            </h1>
            <p className="text-muted-foreground mt-1">
              Monitor performance, costs, and system health
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Select value={timeRange} onValueChange={setTimeRange}>
              <SelectTrigger className="w-[150px]">
                <Calendar className="h-4 w-4 mr-2" />
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="24h">Last 24 hours</SelectItem>
                <SelectItem value="7d">Last 7 days</SelectItem>
                <SelectItem value="30d">Last 30 days</SelectItem>
                <SelectItem value="90d">Last 90 days</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" className="gap-2" onClick={loadData} disabled={loading}>
              <RefreshCw className={cn('h-4 w-4', loading && 'animate-spin')} />
              Refresh
            </Button>
            <Button variant="outline" className="gap-2">
              <Download className="h-4 w-4" />
              Export
            </Button>
          </div>
        </div>

        {error && (
          <Card className="border-destructive/50 bg-destructive/5">
            <CardContent className="flex items-center gap-3 p-4 text-sm text-destructive">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
              <Button variant="outline" size="sm" className="ml-auto" onClick={loadData}>
                Retry
              </Button>
            </CardContent>
          </Card>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-24 text-muted-foreground">
            <Loader2 className="h-8 w-8 animate-spin mr-3" />
            Loading analytics...
          </div>
        ) : (
          <>
            {/* Stats Grid */}
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {statsCards.map((stat, index) => (
                <motion.div
                  key={stat.title}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <Card className="relative overflow-hidden group hover:shadow-lg transition-all duration-300">
                    <div
                      className={cn(
                        'absolute inset-0 opacity-0 group-hover:opacity-5 transition-opacity bg-gradient-to-br',
                        stat.gradient
                      )}
                    />
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between">
                        <div
                          className={cn(
                            'flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br',
                            stat.gradient
                          )}
                        >
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
            </div>

            {/* Charts Grid */}
            <div className="grid gap-6 lg:grid-cols-2">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
              >
                <Card className="h-full">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle>Request Volume</CardTitle>
                        <CardDescription>API requests over time</CardDescription>
                      </div>
                      {performanceData.length > 0 && (
                        <Badge variant="outline" className="gap-1">
                          <TrendingUp className="h-3 w-3 text-green-500" />
                          {requestTrend >= 0 ? '+' : ''}
                          {requestTrend.toFixed(0)}%
                        </Badge>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent>
                    {performanceData.length === 0 ? (
                      <EmptyChart message="No request volume data for this range" />
                    ) : (
                      <ResponsiveContainer width="100%" height={300}>
                        <AreaChart data={performanceData}>
                          <defs>
                            <linearGradient id="colorRequests" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                              <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                          <XAxis dataKey="name" className="text-xs" />
                          <YAxis className="text-xs" />
                          <Tooltip
                            contentStyle={{
                              backgroundColor: 'hsl(var(--background))',
                              border: '1px solid hsl(var(--border))',
                              borderRadius: '8px',
                            }}
                          />
                          <Area
                            type="monotone"
                            dataKey="requests"
                            stroke="#8b5cf6"
                            strokeWidth={2}
                            fillOpacity={1}
                            fill="url(#colorRequests)"
                          />
                        </AreaChart>
                      </ResponsiveContainer>
                    )}
                  </CardContent>
                </Card>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
              >
                <Card className="h-full">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle>Performance Metrics</CardTitle>
                        <CardDescription>Latency and error rates</CardDescription>
                      </div>
                      <div className="flex items-center gap-4 text-sm">
                        <div className="flex items-center gap-2">
                          <div className="h-3 w-3 rounded-full bg-blue-500" />
                          Latency
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="h-3 w-3 rounded-full bg-red-500" />
                          Errors
                        </div>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {performanceData.length === 0 ? (
                      <EmptyChart message="No latency/error series available" />
                    ) : (
                      <ResponsiveContainer width="100%" height={300}>
                        <RechartsLineChart data={performanceData}>
                          <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                          <XAxis dataKey="name" className="text-xs" />
                          <YAxis yAxisId="left" className="text-xs" />
                          <YAxis yAxisId="right" orientation="right" className="text-xs" />
                          <Tooltip
                            contentStyle={{
                              backgroundColor: 'hsl(var(--background))',
                              border: '1px solid hsl(var(--border))',
                              borderRadius: '8px',
                            }}
                          />
                          <Line
                            yAxisId="left"
                            type="monotone"
                            dataKey="latency"
                            stroke="#3b82f6"
                            strokeWidth={2}
                            dot={{ fill: '#3b82f6', strokeWidth: 2 }}
                          />
                          <Line
                            yAxisId="right"
                            type="monotone"
                            dataKey="errors"
                            stroke="#ef4444"
                            strokeWidth={2}
                            dot={{ fill: '#ef4444', strokeWidth: 2 }}
                          />
                        </RechartsLineChart>
                      </ResponsiveContainer>
                    )}
                  </CardContent>
                </Card>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
              >
                <Card className="h-full">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle>Cost by Provider</CardTitle>
                        <CardDescription>Spending breakdown</CardDescription>
                      </div>
                      <div className="flex items-center gap-4 text-sm">
                        <div className="flex items-center gap-2">
                          <div className="h-3 w-3 rounded-full bg-purple-500" />
                          Groq
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="h-3 w-3 rounded-full bg-green-500" />
                          OpenAI
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="h-3 w-3 rounded-full bg-blue-500" />
                          Anthropic
                        </div>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {costData.length === 0 ? (
                      <EmptyChart message="No cost data yet" />
                    ) : (
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={costData}>
                          <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                          <XAxis dataKey="name" className="text-xs" />
                          <YAxis className="text-xs" />
                          <Tooltip
                            contentStyle={{
                              backgroundColor: 'hsl(var(--background))',
                              border: '1px solid hsl(var(--border))',
                              borderRadius: '8px',
                            }}
                          />
                          <Bar dataKey="groq" stackId="a" fill="#8b5cf6" />
                          <Bar dataKey="openai" stackId="a" fill="#10b981" />
                          <Bar dataKey="anthropic" stackId="a" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    )}
                  </CardContent>
                </Card>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
              >
                <Card className="h-full">
                  <CardHeader>
                    <CardTitle>Model Usage Distribution</CardTitle>
                    <CardDescription>Request distribution by model/provider</CardDescription>
                  </CardHeader>
                  <CardContent>
                    {modelUsageData.length === 0 ? (
                      <EmptyChart message="No usage distribution data" />
                    ) : (
                      <div className="flex items-center gap-8">
                        <div className="flex-1">
                          <ResponsiveContainer width="100%" height={250}>
                            <RechartsPieChart>
                              <Pie
                                data={modelUsageData}
                                cx="50%"
                                cy="50%"
                                innerRadius={60}
                                outerRadius={100}
                                paddingAngle={4}
                                dataKey="value"
                              >
                                {modelUsageData.map((entry, index) => (
                                  <Cell key={`cell-${index}`} fill={entry.color} />
                                ))}
                              </Pie>
                              <Tooltip
                                contentStyle={{
                                  backgroundColor: 'hsl(var(--background))',
                                  border: '1px solid hsl(var(--border))',
                                  borderRadius: '8px',
                                }}
                              />
                            </RechartsPieChart>
                          </ResponsiveContainer>
                        </div>
                        <div className="space-y-4">
                          {modelUsageData.map((model) => (
                            <div key={model.name} className="flex items-center gap-3">
                              <div
                                className="h-3 w-3 rounded-full"
                                style={{ backgroundColor: model.color }}
                              />
                              <div className="flex-1">
                                <p className="text-sm font-medium">{model.name}</p>
                              </div>
                              <p className="text-sm font-bold">{model.value}%</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </motion.div>
            </div>

            {/* Agent Performance Table */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6 }}
            >
              <Card>
                <CardHeader>
                  <CardTitle>Agent Performance</CardTitle>
                  <CardDescription>Individual agent metrics and statistics</CardDescription>
                </CardHeader>
                <CardContent>
                  {agentPerformanceData.length === 0 ? (
                    <div className="py-12 text-center text-muted-foreground">
                      <Bot className="h-10 w-10 mx-auto mb-3 opacity-50" />
                      <p>No agent performance data available</p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {agentPerformanceData.map((agent, index) => (
                        <motion.div
                          key={agent.name}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: 0.7 + index * 0.1 }}
                          className="flex items-center gap-4 p-4 rounded-xl bg-muted/50 hover:bg-muted transition-colors"
                        >
                          <div
                            className="flex h-10 w-10 items-center justify-center rounded-lg"
                            style={{ backgroundColor: `${agent.color}20` }}
                          >
                            <Bot className="h-5 w-5" style={{ color: agent.color }} />
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="font-medium">{agent.name}</p>
                            <p className="text-sm text-muted-foreground">
                              {agent.tasks.toLocaleString()} tasks completed
                            </p>
                          </div>
                          <div className="hidden sm:flex items-center gap-8">
                            <div className="text-center">
                              <p className="text-lg font-bold">{agent.success}%</p>
                              <p className="text-xs text-muted-foreground">Success Rate</p>
                            </div>
                            <div className="w-32">
                              <Progress
                                value={agent.success}
                                className="h-2"
                                style={{ backgroundColor: `${agent.color}20` }}
                              />
                            </div>
                          </div>
                          <Badge
                            variant={
                              agent.success >= 98
                                ? 'default'
                                : agent.success >= 95
                                  ? 'secondary'
                                  : 'destructive'
                            }
                          >
                            {agent.success >= 98
                              ? 'Excellent'
                              : agent.success >= 95
                                ? 'Good'
                                : 'Needs Attention'}
                          </Badge>
                        </motion.div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>

            {/* AI Insights */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.8 }}
            >
              <Card className="border-primary/20 bg-gradient-to-br from-primary/5 to-transparent">
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-purple-500">
                      <Sparkles className="h-5 w-5 text-white" />
                    </div>
                    <div>
                      <CardTitle>AI Insights</CardTitle>
                      <CardDescription>Automated optimization recommendations</CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  {insights.length === 0 ? (
                    <div className="py-8 text-center text-muted-foreground text-sm">
                      No insights available yet. Insights appear as the system gathers more data.
                    </div>
                  ) : (
                    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                      {insights.map((insight, index) => (
                        <motion.div
                          key={`${insight.title}-${index}`}
                          initial={{ opacity: 0, scale: 0.95 }}
                          animate={{ opacity: 1, scale: 1 }}
                          transition={{ delay: 0.9 + index * 0.1 }}
                          className="p-4 rounded-xl bg-background border hover:shadow-md transition-all cursor-pointer"
                        >
                          <div className="flex items-center gap-2 mb-2">
                            {(insight.type.includes('cost') || insight.type === 'cost') && (
                              <DollarSign className="h-4 w-4 text-green-500" />
                            )}
                            {(insight.type.includes('alert') ||
                              insight.type.includes('warning') ||
                              insight.type === 'alert') && (
                              <AlertTriangle className="h-4 w-4 text-yellow-500" />
                            )}
                            {!insight.type.includes('cost') &&
                              !insight.type.includes('alert') &&
                              !insight.type.includes('warning') && (
                                <TrendingUp className="h-4 w-4 text-blue-500" />
                              )}
                            <Badge variant="secondary" className="text-xs capitalize">
                              {insight.impact} Impact
                            </Badge>
                          </div>
                          <h4 className="font-medium mb-1">{insight.title}</h4>
                          <p className="text-sm text-muted-foreground">{insight.description}</p>
                        </motion.div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          </>
        )}
      </motion.div>
    </AppLayout>
  );
}

function EmptyChart({ message }: { message: string }) {
  return (
    <div className="flex h-[300px] items-center justify-center text-sm text-muted-foreground">
      {message}
    </div>
  );
}
