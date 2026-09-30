'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  LineChart, 
  Line, 
  BarChart, 
  Bar, 
  AreaChart,
  Area,
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts';
import { 
  TrendingUp, 
  Activity, 
  BarChart3, 
  Clock,
  AlertCircle,
  RefreshCw,
  Download,
  Target,
  Zap
} from 'lucide-react';
import { 
  getPerformanceMetrics,
  getPerformanceTrends,
  getPredictiveInsights,
  generateReport
} from '@/lib/api';
import { toast } from 'sonner';

interface PerformanceMetric {
  id: string;
  metric_name: string;
  metric_type: string;
  metric_value: number;
  timestamp: string;
  agent?: { id: string; name: string };
  session?: { id: string };
}

interface PerformanceTrend {
  period: string;
  avg_success_rate: number;
  total_tasks: number;
  avg_response_time: number;
}

interface PredictiveInsight {
  id: string;
  insight_type: string;
  prediction: Record<string, unknown>;
  confidence_score: number;
  created_at: string;
}

export default function EnhancedAnalyticsDashboard() {
  const [metrics, setMetrics] = useState<PerformanceMetric[]>([]);
  const [trends, setTrends] = useState<PerformanceTrend[]>([]);
  const [insights, setInsights] = useState<PredictiveInsight[]>([]);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('7d');
  const [metricType, setMetricType] = useState('all');
  const loadData = async () => {
    try {
      setLoading(true);

      const [metricsRes, trendsRes, insightsRes] = await Promise.all([
        getPerformanceMetrics(),
        getPerformanceTrends({ time_range: timeRange }),
        getPredictiveInsights()
      ]);

      const metricsData: Record<string, unknown> = metricsRes as unknown as Record<string, unknown>;
      const trendsData = trendsRes.data as { results?: PerformanceTrend[] } | PerformanceTrend[];
      const insightsData = insightsRes.data as { results?: PredictiveInsight[] } | PredictiveInsight[];
      
      setMetrics(Array.isArray(metricsData) ? metricsData as PerformanceMetric[] : []);
      setTrends(Array.isArray(trendsData) ? trendsData : trendsData.results || []);
      setInsights(Array.isArray(insightsData) ? insightsData : insightsData.results || []);
    } catch {
      toast.error('Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateReport = async () => {
    try {
      const response = await generateReport('performance-report');
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([JSON.stringify(response.report_data, null, 2)]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `analytics-report-${new Date().toISOString()}.json`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      toast.success('Report generated successfully');
    } catch {
      toast.error('Failed to generate report');
    }
  };

  const calculateStats = () => {
    const totalMetrics = metrics.length;
    const avgValue = metrics.length > 0 
      ? metrics.reduce((sum, m) => sum + m.metric_value, 0) / metrics.length 
      : 0;
    
    const successRate = metrics.filter(m => m.metric_name.includes('success')).length > 0
      ? metrics.filter(m => m.metric_name.includes('success')).reduce((sum, m) => sum + m.metric_value, 0) / 
        metrics.filter(m => m.metric_name.includes('success')).length
      : 0;

    return { totalMetrics, avgValue, successRate };
  };

  const stats = calculateStats();

  const getInsightIcon = (type: string) => {
    switch (type) {
      case 'performance_prediction':
        return <TrendingUp className="h-5 w-5 text-green-500" />;
      case 'resource_optimization':
        return <Target className="h-5 w-5 text-blue-500" />;
      case 'anomaly_detection':
        return <AlertCircle className="h-5 w-5 text-yellow-500" />;
      default:
        return <Activity className="h-5 w-5 text-gray-500" />;
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  useEffect(() => {
    setTimeout(() => {
      loadData();
    }, 0);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [timeRange, metricType]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <BarChart3 className="h-12 w-12 animate-pulse text-blue-500 mx-auto mb-4" />
          <p className="text-gray-600">Loading analytics...</p>
        </div>
      </div>
    );
  }


  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <BarChart3 className="h-8 w-8 text-blue-500" />
            Advanced Analytics
          </h1>
          <p className="text-gray-600 mt-2">
            Performance metrics and predictive insights
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={loadData} variant="outline">
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          <Button onClick={handleGenerateReport}>
            <Download className="mr-2 h-4 w-4" />
            Generate Report
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <Select value={timeRange} onValueChange={setTimeRange}>
          <SelectTrigger className="w-[200px]">
            <Clock className="mr-2 h-4 w-4" />
            <SelectValue placeholder="Time Range" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="24h">Last 24 Hours</SelectItem>
            <SelectItem value="7d">Last 7 Days</SelectItem>
            <SelectItem value="30d">Last 30 Days</SelectItem>
            <SelectItem value="90d">Last 90 Days</SelectItem>
          </SelectContent>
        </Select>

        <Select value={metricType} onValueChange={setMetricType}>
          <SelectTrigger className="w-[200px]">
            <Activity className="mr-2 h-4 w-4" />
            <SelectValue placeholder="Metric Type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Metrics</SelectItem>
            <SelectItem value="response_time">Response Time</SelectItem>
            <SelectItem value="success_rate">Success Rate</SelectItem>
            <SelectItem value="task_count">Task Count</SelectItem>
            <SelectItem value="resource_usage">Resource Usage</SelectItem>
            <SelectItem value="error_rate">Error Rate</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Key Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Total Metrics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{stats.totalMetrics}</div>
            <p className="text-xs text-gray-500 mt-1">Collected data points</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Avg Success Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">
              {(stats.successRate * 100).toFixed(1)}%
            </div>
            <p className="text-xs text-gray-500 mt-1 flex items-center gap-1">
              <TrendingUp className="h-3 w-3" />
              +5.2% from last period
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Active Insights</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-600">{insights.length}</div>
            <p className="text-xs text-gray-500 mt-1">Predictive insights</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Avg Metric Value</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{stats.avgValue.toFixed(2)}</div>
            <p className="text-xs text-gray-500 mt-1">Across all metrics</p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="trends">Trends</TabsTrigger>
          <TabsTrigger value="insights">Insights ({insights.length})</TabsTrigger>
          <TabsTrigger value="details">Detailed Metrics</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Performance Trends</CardTitle>
              <CardDescription>Key performance indicators over time</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={trends}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="period" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Area type="monotone" dataKey="avg_success_rate" stackId="1" stroke="#10b981" fill="#10b981" fillOpacity={0.6} name="Success Rate" />
                  <Area type="monotone" dataKey="total_tasks" stackId="2" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.6} name="Total Tasks" />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Metric Distribution</CardTitle>
                <CardDescription>Breakdown by metric type</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={Object.entries(
                    metrics.reduce((acc, m) => {
                      acc[m.metric_type] = (acc[m.metric_type] || 0) + 1;
                      return acc;
                    }, {} as Record<string, number>)
                  ).map(([name, value]) => ({ name, value }))}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value" fill="#3b82f6" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Response Time Trends</CardTitle>
                <CardDescription>Average response times</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                  <LineChart data={trends}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="period" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="avg_response_time" stroke="#f59e0b" strokeWidth={2} name="Avg Response Time (ms)" />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="trends" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Comprehensive Trends Analysis</CardTitle>
              <CardDescription>Detailed view of all performance trends</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={trends}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="period" />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip />
                  <Legend />
                  <Line yAxisId="left" type="monotone" dataKey="avg_success_rate" stroke="#10b981" strokeWidth={2} name="Success Rate" />
                  <Line yAxisId="right" type="monotone" dataKey="total_tasks" stroke="#3b82f6" strokeWidth={2} name="Total Tasks" />
                  <Line yAxisId="right" type="monotone" dataKey="avg_response_time" stroke="#f59e0b" strokeWidth={2} name="Response Time" />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {trends.map((trend, idx) => (
              <Card key={idx}>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">{trend.period}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Success Rate</span>
                    <span className="font-semibold text-green-600">
                      {(trend.avg_success_rate * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Total Tasks</span>
                    <span className="font-semibold">{trend.total_tasks}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Avg Response</span>
                    <span className="font-semibold text-blue-600">
                      {trend.avg_response_time.toFixed(0)}ms
                    </span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="insights" className="space-y-4">
          <div className="space-y-4">
            {insights.map((insight) => (
              <Card key={insight.id}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      {getInsightIcon(insight.insight_type)}
                      <div>
                        <CardTitle className="text-lg">
                          {insight.insight_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </CardTitle>
                        <CardDescription>
                          Confidence: <span className={getConfidenceColor(insight.confidence_score)}>
                            {(insight.confidence_score * 100).toFixed(1)}%
                          </span>
                        </CardDescription>
                      </div>
                    </div>
                    <Badge variant={insight.confidence_score >= 0.7 ? 'default' : 'secondary'}>
                      {insight.confidence_score >= 0.8 ? 'High' : insight.confidence_score >= 0.6 ? 'Medium' : 'Low'} Confidence
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <pre className="text-sm whitespace-pre-wrap">
                      {JSON.stringify(insight.prediction, null, 2)}
                    </pre>
                  </div>
                  <div className="mt-3 text-xs text-gray-500">
                    Generated: {new Date(insight.created_at).toLocaleString()}
                  </div>
                </CardContent>
              </Card>
            ))}
            {insights.length === 0 && (
              <Card>
                <CardContent className="text-center py-12">
                  <Target className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600">No predictive insights available yet</p>
                  <p className="text-sm text-gray-500 mt-2">Insights will be generated as more data is collected</p>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        <TabsContent value="details" className="space-y-4">
          <div className="space-y-4">
            {metrics.slice(0, 50).map((metric) => (
              <Card key={metric.id}>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <Zap className="h-4 w-4 text-blue-500" />
                        <span className="font-semibold">{metric.metric_name}</span>
                        <Badge variant="outline">{metric.metric_type}</Badge>
                      </div>
                      {metric.agent && (
                        <p className="text-sm text-gray-600">Agent: {metric.agent.name}</p>
                      )}
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-blue-600">{metric.metric_value.toFixed(2)}</div>
                      <p className="text-xs text-gray-500">{new Date(metric.timestamp).toLocaleString()}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
            {metrics.length === 0 && (
              <Card>
                <CardContent className="text-center py-12">
                  <Activity className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600">No metrics recorded yet</p>
                  <p className="text-sm text-gray-500 mt-2">Metrics will appear here as agents perform tasks</p>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
