"use client";

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import { DatePickerWithRange } from '@/components/ui/date-picker';
import { 
  BarChart, 
  LineChart, 
  PieChart, 
  AreaChart,
  ResponsiveContainer,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  Bar,
  Line,
  Area,
  Pie,
  Cell
} from 'recharts';
import { 
  FileText, 
  Download, 
  Share2, 
  Filter, 
  TrendingUp,
  Clock,
  Settings,
  Eye,
  BarChart3,
  PieChart as PieChartIcon,
  LineChart as LineChartIcon,
  Grid3X3,
  ArrowUp,
  ArrowDown,
  Minus,
  Plus,
  RefreshCw,
  FileSpreadsheet
} from 'lucide-react';

interface ReportMetric {
  id: string;
  name: string;
  value: number | string;
  previous_value?: number | string;
  change_percentage?: number;
  trend: 'up' | 'down' | 'stable';
  format: 'number' | 'percentage' | 'currency' | 'duration';
  category: string;
}

interface ChartData {
  id: string;
  name: string;
  type: 'line' | 'bar' | 'area' | 'pie' | 'donut';
  data: Array<Record<string, unknown>>;
  config: {
    xAxis?: string;
    yAxis?: string | string[];
    colors?: string[];
    title?: string;
    description?: string;
  };
}

interface ReportTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  metrics: string[];
  charts: string[];
  layout: 'dashboard' | 'executive' | 'detailed' | 'custom';
  schedule?: {
    frequency: 'daily' | 'weekly' | 'monthly' | 'quarterly';
    recipients: string[];
    enabled: boolean;
  };
  created_at: string;
  updated_at: string;
}

interface CustomReport {
  id: string;
  name: string;
  description: string;
  template_id?: string;
  filters: Record<string, unknown>;
  date_range: {
    start: string;
    end: string;
  };
  sections: Array<{
    type: 'metric' | 'chart' | 'table' | 'text';
    config: unknown;
    position: { row: number; col: number; width: number; height: number };
  }>;
  export_formats: string[];
  sharing_settings: {
    is_public: boolean;
    allowed_users: string[];
    password_protected: boolean;
  };
}

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#00ff88', '#ff0088'];

export const AdvancedReportingDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<ReportMetric[]>([]);
  const [charts, setCharts] = useState<ChartData[]>([]);
  const [templates, setTemplates] = useState<ReportTemplate[]>([]);
  const [reports, setReports] = useState<CustomReport[]>([]);
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedTemplate, setSelectedTemplate] = useState<ReportTemplate | null>(null);
  const [selectedReport, setSelectedReport] = useState<CustomReport | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [dateRange, setDateRange] = useState({
    from: new Date(new Date().getTime() - 30 * 24 * 60 * 60 * 1000), // 30 days ago
    to: new Date()
  });
  const [filters, setFilters] = useState({
    category: 'all',
    agent_type: 'all',
    status: 'all'
  });

  const loadDashboardData = useCallback(async () => {
    try {
      setIsLoading(true);
      const [metricsRes, chartsRes, templatesRes, reportsRes] = await Promise.all([
        fetch(`/api/reports/metrics/?from=${dateRange.from.toISOString()}&to=${dateRange.to.toISOString()}`),
        fetch(`/api/reports/charts/?from=${dateRange.from.toISOString()}&to=${dateRange.to.toISOString()}`),
        fetch('/api/reports/templates/'),
        fetch('/api/reports/custom/')
      ]);

      if (metricsRes.ok) {
        const metricsData = await metricsRes.json();
        setMetrics(metricsData);
      }

      if (chartsRes.ok) {
        const chartsData = await chartsRes.json();
        setCharts(chartsData);
      }

      if (templatesRes.ok) {
        const templatesData = await templatesRes.json();
        setTemplates(templatesData);
      }

      if (reportsRes.ok) {
        const reportsData = await reportsRes.json();
        setReports(reportsData);
      }
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setIsLoading(false);
    }
  }, [dateRange]);

  useEffect(() => {
    setTimeout(() => { loadDashboardData(); }, 0)
  }, [dateRange, filters, loadDashboardData]);

  const generateReport = async (templateId: string) => {
    try {
      setIsLoading(true);
      const response = await fetch(`/api/reports/generate/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          template_id: templateId,
          date_range: dateRange,
          filters
        })
      });

      if (response.ok) {
        const report = await response.json();
        setReports(prev => [...prev, report]);
        setSelectedReport(report);
        setActiveTab('custom');
      }
    } catch (error) {
      console.error('Failed to generate report:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const exportReport = async (reportId: string, format: string) => {
    try {
      const response = await fetch(`/api/reports/${reportId}/export/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ format })
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `report-${reportId}.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  const formatMetricValue = (value: number | string, format: string) => {
    if (typeof value === 'string') return value;
    
    switch (format) {
      case 'percentage':
        return `${value.toFixed(1)}%`;
      case 'currency':
        return `$${value.toLocaleString()}`;
      case 'duration':
        return `${value}ms`;
      default:
        return value.toLocaleString();
    }
  };

  const getTrendIcon = (trend: string, change?: number) => {
    if (trend === 'up' || (change && change > 0)) {
      return <ArrowUp className="w-4 h-4 text-green-500" />;
    } else if (trend === 'down' || (change && change < 0)) {
      return <ArrowDown className="w-4 h-4 text-red-500" />;
    } else {
      return <Minus className="w-4 h-4 text-gray-500" />;
    }
  };

  const renderChart = (chart: ChartData) => {
    const { type, data, config } = chart;
    
    switch (type) {
      case 'line':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={config.xAxis || 'name'} />
              <YAxis />
              <Tooltip />
              <Legend />
              {(config.yAxis as string[])?.map((key, index) => (
                <Line 
                  key={key} 
                  type="monotone" 
                  dataKey={key} 
                  stroke={config.colors?.[index] || COLORS[index]} 
                  strokeWidth={2}
                />
              )) || <Line type="monotone" dataKey="value" stroke="#8884d8" strokeWidth={2} />}
            </LineChart>
          </ResponsiveContainer>
        );

      case 'bar':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={config.xAxis || 'name'} />
              <YAxis />
              <Tooltip />
              <Legend />
              {(config.yAxis as string[])?.map((key, index) => (
                <Bar 
                  key={key} 
                  dataKey={key} 
                  fill={config.colors?.[index] || COLORS[index]} 
                />
              )) || <Bar dataKey="value" fill="#8884d8" />}
            </BarChart>
          </ResponsiveContainer>
        );

      case 'area':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={config.xAxis || 'name'} />
              <YAxis />
              <Tooltip />
              <Legend />
              {(config.yAxis as string[])?.map((key, index) => (
                <Area 
                  key={key} 
                  type="monotone" 
                  dataKey={key} 
                  stackId="1" 
                  stroke={config.colors?.[index] || COLORS[index]} 
                  fill={config.colors?.[index] || COLORS[index]} 
                />
              )) || <Area type="monotone" dataKey="value" stackId="1" stroke="#8884d8" fill="#8884d8" />}
            </AreaChart>
          </ResponsiveContainer>
        );

      case 'pie':
      case 'donut':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={type === 'donut' ? 60 : 0}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
                label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`}
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        );

      default:
        return <div>Unsupported chart type</div>;
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Advanced Reporting & BI Dashboard
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Generate comprehensive reports and business intelligence insights
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={loadDashboardData} variant="outline" size="sm">
            <RefreshCw className="w-4 h-4" />
          </Button>
          <Button variant="outline">
            <Plus className="w-4 h-4 mr-2" />
            New Report
          </Button>
        </div>
      </div>

      {/* Selected template/report quick info */}
      {(selectedTemplate || selectedReport) && (
        <div className="flex items-center gap-4">
          {selectedTemplate && (
            <div className="text-sm text-muted-foreground">Selected template: <strong className="text-slate-800">{selectedTemplate.name}</strong></div>
          )}
          {selectedReport && (
            <div className="text-sm text-muted-foreground">Selected report: <strong className="text-slate-800">{selectedReport.name}</strong></div>
          )}
        </div>
      )}

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-4 items-end">
            <div className="space-y-2">
              <Label>Date Range</Label>
              <DatePickerWithRange 
                date={{ from: dateRange.from, to: dateRange.to }}
                onDateChange={(range) => {
                  if (range?.from && range?.to) {
                    setDateRange({ from: range.from, to: range.to });
                  }
                }}
              />
            </div>
            
            <div className="space-y-2">
              <Label>Category</Label>
              <Select value={filters.category} onValueChange={(value) => setFilters({...filters, category: value})}>
                <SelectTrigger className="w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Categories</SelectItem>
                  <SelectItem value="agents">Agents</SelectItem>
                  <SelectItem value="workflows">Workflows</SelectItem>
                  <SelectItem value="tasks">Tasks</SelectItem>
                  <SelectItem value="performance">Performance</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Status</Label>
              <Select value={filters.status} onValueChange={(value) => setFilters({...filters, status: value})}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="completed">Completed</SelectItem>
                  <SelectItem value="failed">Failed</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Button onClick={loadDashboardData} disabled={isLoading}>
              <Filter className="w-4 h-4 mr-2" />
              Apply Filters
            </Button>
          </div>
        </CardContent>
      </Card>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview" className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="metrics" className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4" />
            Metrics
          </TabsTrigger>
          <TabsTrigger value="charts" className="flex items-center gap-2">
            <LineChartIcon className="w-4 h-4" />
            Charts
          </TabsTrigger>
          <TabsTrigger value="templates" className="flex items-center gap-2">
            <FileText className="w-4 h-4" />
            Templates
          </TabsTrigger>
          <TabsTrigger value="custom" className="flex items-center gap-2">
            <Settings className="w-4 h-4" />
            Custom Reports
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Key Metrics Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {metrics.slice(0, 8).map((metric) => (
              <Card key={metric.id}>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                        {metric.name}
                      </p>
                      <p className="text-2xl font-bold">
                        {formatMetricValue(metric.value, metric.format)}
                      </p>
                      {metric.change_percentage && (
                        <div className="flex items-center gap-1 mt-1">
                          {getTrendIcon(metric.trend, metric.change_percentage)}
                          <span className={`text-sm ${
                            metric.change_percentage > 0 ? 'text-green-600' : 
                            metric.change_percentage < 0 ? 'text-red-600' : 'text-gray-600'
                          }`}>
                            {Math.abs(metric.change_percentage).toFixed(1)}%
                          </span>
                        </div>
                      )}
                    </div>
                    <Badge variant="outline">{metric.category}</Badge>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Quick Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {charts.slice(0, 4).map((chart) => (
              <Card key={chart.id}>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    {chart.type === 'line' && <LineChartIcon className="w-5 h-5" />}
                    {chart.type === 'bar' && <BarChart3 className="w-5 h-5" />}
                    {chart.type === 'pie' && <PieChartIcon className="w-5 h-5" />}
                    {chart.config.title || chart.name}
                  </CardTitle>
                  {chart.config.description && (
                    <CardDescription>{chart.config.description}</CardDescription>
                  )}
                </CardHeader>
                <CardContent>
                  {renderChart(chart)}
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="metrics" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {metrics.map((metric) => (
              <Card key={metric.id}>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <Badge variant="outline">{metric.category}</Badge>
                    {getTrendIcon(metric.trend, metric.change_percentage)}
                  </div>
                  
                  <h3 className="font-semibold text-lg mb-2">{metric.name}</h3>
                  
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600 dark:text-gray-400">Current</span>
                      <span className="text-2xl font-bold">
                        {formatMetricValue(metric.value, metric.format)}
                      </span>
                    </div>
                    
                    {metric.previous_value && (
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600 dark:text-gray-400">Previous</span>
                        <span className="text-sm">
                          {formatMetricValue(metric.previous_value, metric.format)}
                        </span>
                      </div>
                    )}
                    
                    {metric.change_percentage && (
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600 dark:text-gray-400">Change</span>
                        <div className="flex items-center gap-1">
                          {getTrendIcon(metric.trend, metric.change_percentage)}
                          <span className={`text-sm font-medium ${
                            metric.change_percentage > 0 ? 'text-green-600' : 
                            metric.change_percentage < 0 ? 'text-red-600' : 'text-gray-600'
                          }`}>
                            {metric.change_percentage > 0 ? '+' : ''}{metric.change_percentage.toFixed(1)}%
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="charts" className="space-y-6">
          <div className="grid gap-6">
            {charts.map((chart) => (
              <Card key={chart.id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        {chart.type === 'line' && <LineChartIcon className="w-5 h-5" />}
                        {chart.type === 'bar' && <BarChart3 className="w-5 h-5" />}
                        {chart.type === 'area' && <BarChart3 className="w-5 h-5" />}
                        {chart.type === 'pie' && <PieChartIcon className="w-5 h-5" />}
                        {chart.config.title || chart.name}
                      </CardTitle>
                      {chart.config.description && (
                        <CardDescription>{chart.config.description}</CardDescription>
                      )}
                    </div>
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm">
                        <Download className="w-4 h-4 mr-1" />
                        Export
                      </Button>
                      <Button variant="outline" size="sm">
                        <Share2 className="w-4 h-4 mr-1" />
                        Share
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  {renderChart(chart)}
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="templates" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {templates.map((template) => (
              <Card key={template.id} className="cursor-pointer hover:shadow-lg transition-shadow">
                <CardContent className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg flex items-center justify-center">
                      <FileText className="w-6 h-6 text-white" />
                    </div>
                    <Badge variant="outline">{template.category}</Badge>
                  </div>
                  
                  <h3 className="font-semibold text-lg mb-2">{template.name}</h3>
                  <p className="text-gray-600 dark:text-gray-400 mb-4">{template.description}</p>
                  
                  <div className="space-y-2 mb-4">
                    <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                      <BarChart3 className="w-4 h-4" />
                      {template.metrics.length} metrics
                    </div>
                    <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                      <PieChartIcon className="w-4 h-4" />
                      {template.charts.length} charts
                    </div>
                    <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                      <Grid3X3 className="w-4 h-4" />
                      {template.layout} layout
                    </div>
                  </div>

                  {template.schedule?.enabled && (
                    <div className="mb-4">
                      <Badge variant="secondary" className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        Auto-scheduled {template.schedule.frequency}
                      </Badge>
                    </div>
                  )}
                  
                  <div className="flex gap-2">
                    <Button 
                      className="flex-1" 
                      onClick={() => generateReport(template.id)}
                      disabled={isLoading}
                    >
                      Generate Report
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => setSelectedTemplate(template)}>
                      <Eye className="w-4 h-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="custom" className="space-y-6">
          <div className="grid gap-4">
            {reports.map((report) => (
              <Card key={report.id}>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-semibold text-lg">{report.name}</h3>
                      <p className="text-gray-600 dark:text-gray-400">{report.description}</p>
                      <div className="flex items-center gap-4 mt-2">
                        <span className="text-sm text-gray-500">
                          {new Date(report.date_range.start).toLocaleDateString()} - {new Date(report.date_range.end).toLocaleDateString()}
                        </span>
                        <Badge variant="outline">
                          {report.sections.length} sections
                        </Badge>
                        {report.sharing_settings.is_public && (
                          <Badge variant="secondary">Public</Badge>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => exportReport(report.id, 'pdf')}
                      >
                        <FileText className="w-4 h-4 mr-1" />
                        PDF
                      </Button>
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => exportReport(report.id, 'xlsx')}
                      >
                        <FileSpreadsheet className="w-4 h-4 mr-1" />
                        Excel
                      </Button>
                      <Button 
                        variant="outline" 
                        size="sm"
                      >
                        <Share2 className="w-4 h-4 mr-1" />
                        Share
                      </Button>
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => setSelectedReport(report)}
                      >
                        <Eye className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AdvancedReportingDashboard;