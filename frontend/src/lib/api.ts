/**
 * API Client for Multi-Agent System
 * Handles all HTTP requests to Django backend
 */

import axios, { AxiosInstance, AxiosResponse } from 'axios';

// Types for API responses
export interface Agent {
  id: string;
  name: string;
  type: 'orchestrator' | 'vision' | 'reasoning' | 'action' | 'memory';
  status: 'idle' | 'active' | 'processing' | 'error';
  capabilities: string[];
  created_at: string;
  updated_at: string;
  performance_metrics?: {
    accuracy: number;
    speed: number;
    reliability: number;
  };
}

export interface Session {
  id: string;
  name: string;
  created_by: number;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  agents: Agent[];
}

export interface Message {
  id: string;
  session: string;
  sender: number | null;
  sender_agent: string | null;
  content: string;
  message_type: 'text' | 'image' | 'file' | 'command';
  created_at: string;
  metadata: Record<string, unknown>;
}

export interface Task {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  assigned_agent: string | null;
  priority: number;
  created_at: string;
  completed_at: string | null;
}

// Workflow interfaces
export interface WorkflowDefinition {
  id: string;
  name: string;
  description: string;
  steps: WorkflowStep[];
  metadata: Record<string, unknown>;
}

export interface WorkflowStep {
  id: string;
  type: string;
  config: Record<string, unknown>;
  dependencies?: string[];
  position: { x: number; y: number };
}

export interface WorkflowExecution {
  workflow_id: string;
  success: boolean;
  results: Record<string, unknown>;
  execution_time: number;
  steps_executed: number;
  total_steps: number;
  error?: string;
}

export interface WorkflowTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  tags: string[];
  usage_count: number;
  average_rating: number;
  is_public: boolean;
  created_at: string;
}

// Analytics interfaces
export interface AnalyticsData {
  overview: Record<string, unknown>;
  performance: Record<string, unknown>;
  errors: Record<string, unknown>;
  usage: Record<string, unknown>;
}

// Automation interfaces
export interface AutomationRule {
  id: string;
  name: string;
  type: 'schedule' | 'trigger' | 'condition' | 'optimization';
  enabled: boolean;
  config: Record<string, unknown>;
  last_run?: string;
  next_run?: string;
  success: boolean;
  description: string;
}

// Version control interfaces
export interface WorkflowVersion {
  id: string;
  version: string;
  branch: string;
  author: string;
  timestamp: string;
  message: string;
  changes: {
    added: number;
    modified: number;
    removed: number;
  };
  status: 'draft' | 'published' | 'archived';
  tags: string[];
}

// Collaboration interfaces
export interface TeamMember {
  id: string;
  name: string;
  email: string;
  role: 'owner' | 'editor' | 'viewer';
  status: 'online' | 'offline' | 'away';
  last_active: string;
  permissions: string[];
}

export interface Comment {
  id: string;
  author_id: string;
  author_name: string;
  content: string;
  timestamp: string;
  resolved: boolean;
  node_id?: string;
}

// Smart Agents interfaces
export interface SmartAgentSelection {
  recommended_agents: Agent[];
  selection_criteria: Record<string, unknown>;
  confidence_score: number;
}

// MCP Integration interfaces
export interface MCPTool {
  id: string;
  name: string;
  description: string;
  category: string;
  version: string;
  parameters_schema: Record<string, unknown>;
  capabilities: string[];
  is_active: boolean;
  usage_count: number;
  success_rate: number;
}

export interface MCPToolConfig {
  tool_name: string;
  parameters: Record<string, unknown>;
  critical?: boolean;
}

export interface MCPToolExecution {
  execution_id: string;
  result: Record<string, unknown>;
  success: boolean;
  execution_time: number;
  tool_name: string;
}

export interface MCPSession {
  session_id: string;
  name: string;
  enabled_tools: string[];
  context_data: Record<string, unknown>;
  created_at: string;
}

export interface MCPToolRecommendation {
  tool: MCPTool;
  score: number;
  reason: string;
}

// Collaboration interfaces
export interface CollaborationSession {
  session_id: string;
  name: string;
  description: string;
  is_public: boolean;
  created_at: string;
}

export interface CollaborationUser {
  id: number;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
}

export interface Activity {
  id: string;
  action: string;
  details: Record<string, unknown>;
  user: CollaborationUser;
  timestamp: string;
}

export interface NotificationData {
  id: string;
  type: string;
  title: string;
  message: string;
  read: boolean;
  data: Record<string, unknown>;
  created_at: string;
}

export interface ApiResponse<T = unknown> {
  data: T;
  message?: string;
  status: 'success' | 'error';
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// Multi-Agent Coordination interfaces
export interface CoordinationSession {
  id: string;
  name: string;
  strategy: 'sequential' | 'parallel' | 'hierarchical' | 'collaborative';
  is_active: boolean;
  created_at: string;
  interaction_count: number;
  metrics_count: number;
}

export interface AgentInteraction {
  id: string;
  source_agent_id: string;
  target_agent_id: string;
  interaction_type: string;
  content: Record<string, unknown>;
  created_at: string;
  processed: boolean;
}

export interface CoordinationResult {
  strategy: string;
  results: Array<{
    agent_id: string;
    agent_name: string;
    agent_type: string;
    output: string;
    timestamp: string;
  }>;
  status: string;
}

// Multi-Modal Intelligence interfaces
export interface AIModelConfig {
  id: string;
  name: string;
  model_type: 'text' | 'vision' | 'audio' | 'video' | 'multimodal';
  provider: string;
  model_id: string;
  capabilities: string[];
  is_active: boolean;
  is_default: boolean;
}

export interface MultiModalSession {
  id: string;
  name: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  input_modalities: string[];
  created_at: string;
  completed_at?: string;
  modality_count: number;
  insights_count: number;
}

export interface MultiModalResult {
  session_id: string;
  results: Record<string, unknown>;
  input_modalities: string[];
  status: string;
  cross_modal_insights?: Array<{
    type: string;
    modalities: string[];
    description: string;
    confidence: number;
  }>;
}

// Plugin interfaces
export interface Plugin {
  id: string;
  name: string;
  description: string;
  version: string;
  type: 'agent_extension' | 'workflow_node' | 'integration' | 'tool' | 'custom';
  status: 'active' | 'inactive' | 'pending' | 'rejected';
  author: {
    id: string;
    username: string;
  };
  repository_url?: string;
  documentation_url?: string;
  configuration_schema: Record<string, unknown>;
  permissions_required: string[];
  dependencies: string[];
  tags: string[];
  is_public: boolean;
  download_count: number;
  rating: number;
  rating_count: number;
  created_at: string;
  updated_at: string;
}

export interface PluginInstallation {
  id: string;
  plugin: Plugin;
  configuration: Record<string, unknown>;
  is_active: boolean;
  installed_at: string;
  last_updated: string;
}

export interface PluginRating {
  id: string;
  plugin: string;
  user: {
    id: string;
    username: string;
  };
  rating: number;
  review: string;
  created_at: string;
  updated_at: string;
}

class ApiClient {
  private client: AxiosInstance;
  private baseURL: string;

  constructor() {
    this.baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
    
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 120000,
      headers: {
        'Content-Type': 'application/json',
      },
      // Use credentials for secure cookie handling
      withCredentials: true,
    });

    // Request interceptor for authentication (JWT)
    this.client.interceptors.request.use(
      (config) => {
        const token = this.getAuthToken();

        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }

        if (typeof process !== 'undefined' && process.env.NODE_ENV === 'development') {
          console.debug('API Request:', {
            url: config.url,
            method: config.method,
            hasAuth: !!token,
            headers: {
              authorization: config.headers.Authorization ? 'present' : 'missing',
              contentType: config.headers['Content-Type'],
            },
          });
        }

        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        const errorData = error.response?.data;
        const errorStatus = error.response?.status;
        const errorMessage = error.message;
        const errorConfig = error.config;

        const detailedError = {
          status: errorStatus,
          message: errorMessage,
          data: errorData,
          url: errorConfig?.url,
          method: errorConfig?.method,
          headers: {
            authorization: errorConfig?.headers?.Authorization ? 'present' : 'missing',
            contentType: errorConfig?.headers?.['Content-Type'],
          }
        };

        console.error('API Error Details:', detailedError);
        
        // Handle 401 unauthorized
        if (errorStatus === 401) {
          this.removeAuthToken();
          // Redirect to login if needed
          if (typeof window !== 'undefined') {
            // eslint-disable-next-line @next/next/no-location-assign-relative-destination
          window.location.href = '/login';
          }
        }

        // Handle 403 Forbidden
        if (errorStatus === 403) {
          console.warn('Access Forbidden (403):', {
            detail: errorData?.detail,
            error: errorData?.error,
            hasToken: !!this.getAuthToken(),
          });
        }

        // Handle 402 payment/quota required — surface upgrade path
        if (errorStatus === 402 && typeof window !== 'undefined') {
          const usage = errorData?.usage || {};
          window.dispatchEvent(
            new CustomEvent('quota-limit-reached', {
              detail: {
                message:
                  errorData?.message ||
                  errorData?.detail ||
                  'You have reached your monthly message limit. Upgrade to continue.',
                used: usage.used,
                limit: usage.limit,
                tier: usage.tier,
              },
            })
          );
        }
        
        return Promise.reject(error);
      }
    );
  }

  // JWT lives in access_token (AuthContext). Fall back to legacy keys.
  private getAuthToken(): string | null {
    if (typeof window === 'undefined') return null;
    return (
      localStorage.getItem('access_token') ||
      localStorage.getItem('auth_token') ||
      localStorage.getItem('token')
    );
  }

  public setAuthToken(token: string): void {
    if (typeof window === 'undefined') return;
    localStorage.setItem('access_token', token);
    localStorage.setItem('auth_token', token);
  }

  private removeAuthToken(): void {
    if (typeof window === 'undefined') return;
    localStorage.removeItem('access_token');
    localStorage.removeItem('auth_token');
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('refreshToken');
  }

  // Agent Management APIs
  public async getAgents(): Promise<PaginatedResponse<Agent>> {
    const response: AxiosResponse<PaginatedResponse<Agent>> = await this.client.get('/agents/api/agents/');
    return response.data;
  }

  public async getAgent(id: string): Promise<Agent> {
    const response: AxiosResponse<Agent> = await this.client.get(`/agents/api/agents/${id}/`);
    return response.data;
  }

  public async createAgent(agentData: Partial<Agent>): Promise<Agent> {
    const response: AxiosResponse<Agent> = await this.client.post('/agents/api/agents/', agentData);
    return response.data;
  }

  public async updateAgent(id: string, agentData: Partial<Agent>): Promise<Agent> {
    const response: AxiosResponse<Agent> = await this.client.patch(`/agents/api/agents/${id}/`, agentData);
    return response.data;
  }

  public async deleteAgent(id: string): Promise<void> {
    await this.client.delete(`/agents/api/agents/${id}/`);
  }

  public async activateAgent(id: string): Promise<Agent> {
    const response: AxiosResponse<Agent> = await this.client.post(`/agents/api/agents/${id}/activate/`);
    return response.data;
  }

  public async deactivateAgent(id: string): Promise<Agent> {
    const response: AxiosResponse<Agent> = await this.client.post(`/agents/api/agents/${id}/deactivate/`);
    return response.data;
  }

  // Session Management APIs
  public async getSessions(): Promise<PaginatedResponse<Session>> {
    const response: AxiosResponse<PaginatedResponse<Session>> = await this.client.get('/agents/api/sessions/');
    return response.data;
  }

  public async getSession(id: string): Promise<Session> {
    const response: AxiosResponse<Session> = await this.client.get(`/agents/api/sessions/${id}/`);
    return response.data;
  }

  public async createSession(sessionData: { name: string }): Promise<Session> {
    const response: AxiosResponse<Session> = await this.client.post('/agents/api/sessions/', sessionData);
    return response.data;
  }

  public async updateSession(id: string, sessionData: Partial<Session>): Promise<Session> {
    const response: AxiosResponse<Session> = await this.client.patch(`/agents/api/sessions/${id}/`, sessionData);
    return response.data;
  }

  public async deleteSession(id: string): Promise<void> {
    await this.client.delete(`/agents/api/sessions/${id}/`);
  }

  public async addAgentToSession(sessionId: string, agentId: string): Promise<Session> {
    const response: AxiosResponse<Session> = await this.client.post(
      `/agents/api/sessions/${sessionId}/add_agent/`,
      { agent_id: agentId }
    );
    return response.data;
  }

  // Message Management APIs
  public async getMessages(sessionId: string): Promise<PaginatedResponse<Message>> {
    const response: AxiosResponse<PaginatedResponse<Message>> = await this.client.get(
      `/agents/api/messages/?session=${sessionId}`
    );
    return response.data;
  }

  public async sendMessage(sessionId: string, messageData: {
    content: string;
    message_type: 'text' | 'image' | 'file' | 'command';
    metadata?: Record<string, unknown>;
  }): Promise<Message> {
    const response: AxiosResponse<Message> = await this.client.post(
      `/agents/api/messages/`,
      {
        session_id: sessionId,
        ...messageData
      }
    );
    return response.data;
  }

  // Task Management APIs
  public async getTasks(): Promise<PaginatedResponse<Task>> {
    const response: AxiosResponse<PaginatedResponse<Task>> = await this.client.get('/agents/api/tasks/');
    return response.data;
  }

  public async getTask(id: string): Promise<Task> {
    const response: AxiosResponse<Task> = await this.client.get(`/agents/api/tasks/${id}/`);
    return response.data;
  }

  public async createTask(taskData: Partial<Task>): Promise<Task> {
    const response: AxiosResponse<Task> = await this.client.post('/agents/api/tasks/', taskData);
    return response.data;
  }

  public async updateTask(id: string, taskData: Partial<Task>): Promise<Task> {
    const response: AxiosResponse<Task> = await this.client.patch(`/agents/api/tasks/${id}/`, taskData);
    return response.data;
  }

  public async deleteTask(id: string): Promise<void> {
    await this.client.delete(`/agents/api/tasks/${id}/`);
  }

  // Performance APIs
  public async getPerformanceMetrics(): Promise<Record<string, unknown>> {
    const response: AxiosResponse<Record<string, unknown>> = await this.client.get('/agents/api/performance/');
    return response.data;
  }

  public async getAgentPerformance(agentId: string): Promise<Record<string, unknown>> {
    const response: AxiosResponse<Record<string, unknown>> = await this.client.get(`/agents/api/performance/agent/${agentId}/`);
    return response.data;
  }

  // Groq Integration APIs
  public async chatWithGroq(messages: Array<{ role: string; content: string }>, model?: string): Promise<Record<string, unknown>> {
    const response: AxiosResponse<Record<string, unknown>> = await this.client.post('/agents/api/groq/chat/', {
      messages,
      model
    });
    return response.data;
  }

  public async getGroqModels(): Promise<string[]> {
    const response: AxiosResponse<string[]> = await this.client.get('/agents/api/groq/models/');
    return response.data;
  }

  // Health Check
  public async healthCheck(): Promise<{ status: string; message: string }> {
    try {
      await this.client.get('/agents/api/agents/');
      return { status: 'healthy', message: 'Backend is reachable' };
    } catch {
      return { status: 'unhealthy', message: 'Backend is not reachable' };
    }
  }

  // Workflow APIs
  public async saveWorkflow(workflow: WorkflowDefinition): Promise<{ success: boolean; message?: string }> {
    const response = await this.client.post('/agents/api/workflows/save_workflow/', workflow);
    return response.data;
  }

  public async executeAgentWorkflow(workflowDefinition: WorkflowDefinition, inputData: Record<string, unknown> = {}): Promise<WorkflowExecution> {
    const response = await this.client.post('/agents/api/workflows/execute_workflow/', {
      workflow_definition: workflowDefinition,
      input_data: inputData
    });
    return response.data;
  }

  public async getAgentWorkflowStatus(workflowId: string): Promise<Record<string, unknown>> {
    const response = await this.client.get(`/agents/api/workflows/workflow_status/?workflow_id=${workflowId}`);
    return response.data;
  }

  public async cancelWorkflow(workflowId: string): Promise<{ status: string }> {
    const response = await this.client.post('/agents/api/workflows/cancel_workflow/', { workflow_id: workflowId });
    return response.data;
  }

  public async getAgentWorkflowTemplates(): Promise<{ templates: WorkflowTemplate[] }> {
    const response = await this.client.get('/agents/api/workflows/workflow_templates/');
    return response.data;
  }

  public async createAgentWorkflowTemplate(template: Partial<WorkflowTemplate>): Promise<WorkflowTemplate> {
    const response = await this.client.post('/agents/api/workflows/create_template/', template);
    return response.data;
  }

  // Analytics APIs
  public async getAnalyticsDashboard(timeRange: string = '7d', includePredictions: boolean = true): Promise<AnalyticsData> {
    const response = await this.client.get(`/agents/api/analytics/dashboard_data/?time_range=${timeRange}&predictions=${includePredictions}`);
    return response.data;
  }

  public async getSystemPerformance(): Promise<Record<string, unknown>> {
    const response = await this.client.get('/agents/api/analytics/system_performance/');
    return response.data;
  }

  public async getAnalyticsInsights(): Promise<Record<string, unknown>> {
    const response = await this.client.get('/agents/api/analytics/insights/');
    return response.data;
  }

  // Automation APIs
  public async createAutomationRule(rule: Partial<AutomationRule>): Promise<AutomationRule> {
    const response = await this.client.post('/agents/api/automation/create_automated_task/', rule);
    return response.data;
  }

  public async getAutomationSuggestions(): Promise<{ suggestions: Record<string, unknown>[] }> {
    const response = await this.client.get('/agents/api/automation/task_suggestions/');
    return response.data;
  }

  public async getAutomationRules(): Promise<{ rules: AutomationRule[] }> {
    const response = await this.client.get('/agents/api/automation/');
    return response.data;
  }

  public async updateAutomationRule(ruleId: string, rule: Partial<AutomationRule>): Promise<AutomationRule> {
    const response = await this.client.patch(`/agents/api/automation/${ruleId}/`, rule);
    return response.data;
  }

  public async deleteAutomationRule(ruleId: string): Promise<void> {
    await this.client.delete(`/agents/api/automation/${ruleId}/`);
  }

  // Smart Agent APIs
  public async getSmartAgentRecommendations(taskDescription: string, preferences: Record<string, unknown> = {}): Promise<SmartAgentSelection> {
    const response = await this.client.post('/agents/api/smart-agents/recommend/', {
      task_description: taskDescription,
      preferences
    });
    return response.data;
  }

  public async optimizeAgentPerformance(agentId: string): Promise<Record<string, unknown>> {
    const response = await this.client.post(`/agents/api/smart-agents/optimize_performance/`, { agent_id: agentId });
    return response.data;
  }

  public async getAgentInsights(agentId: string): Promise<Record<string, unknown>> {
    const response = await this.client.get(`/agents/api/smart-agents/agent_insights/?agent_id=${agentId}`);
    return response.data;
  }

  // Multimodal APIs
  public async processMultimodal(data: FormData): Promise<Record<string, unknown>> {
    const response = await this.client.post('/agents/api/multimodal/process/', data, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  public async analyzeImage(imageData: FormData, analysisType: string = 'general'): Promise<Record<string, unknown>> {
    const response = await this.client.post(`/agents/api/multimodal/analyze_image/`, imageData, {
      params: { analysis_type: analysisType },
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  // Version Control APIs (for future implementation)
  public async saveWorkflowVersion(workflowId: string, versionData: { message: string; tags?: string[] }): Promise<WorkflowVersion> {
    const response = await this.client.post(`/agents/api/workflows/${workflowId}/versions/`, versionData);
    return response.data;
  }

  public async getWorkflowVersions(workflowId: string): Promise<{ versions: WorkflowVersion[] }> {
    const response = await this.client.get(`/agents/api/workflows/${workflowId}/versions/`);
    return response.data;
  }

  // Collaboration APIs (for future implementation)
  public async inviteTeamMember(email: string, role: string, permissions: string[]): Promise<TeamMember> {
    const response = await this.client.post('/agents/api/collaboration/invite/', {
      email,
      role,
      permissions
    });
    return response.data;
  }

  public async getTeamMembers(): Promise<{ members: TeamMember[] }> {
    const response = await this.client.get('/agents/api/collaboration/team/');
    return response.data;
  }

  public async addComment(content: string, nodeId?: string): Promise<Comment> {
    const response = await this.client.post('/agents/api/collaboration/comments/', {
      content,
      node_id: nodeId
    });
    return response.data;
  }

  public async getComments(nodeId?: string): Promise<{ comments: Comment[] }> {
    const params = nodeId ? { node_id: nodeId } : {};
    const response = await this.client.get('/agents/api/collaboration/comments/', { params });
    return response.data;
  }

  // MCP Integration APIs
  public async getMCPTools(): Promise<{ tools: MCPTool[]; count: number }> {
    // Prefer DB-backed tools (have UUIDs for execute); fall back to registry catalog
    try {
      const dbResponse = await this.client.get('/mcp/api/tools/');
      const results = (dbResponse.data?.results ?? dbResponse.data) as MCPTool[];
      if (Array.isArray(results) && results.length > 0) {
        return { tools: results, count: results.length };
      }
    } catch {
      // fall through to available_tools
    }
    const response = await this.client.get('/mcp/api/tools/available_tools/');
    const data = response.data as { tools?: MCPTool[]; count?: number };
    const tools = (data.tools ?? []).map((tool, index) => ({
      ...tool,
      id: tool.id || tool.name || `tool-${index}`,
      usage_count: tool.usage_count ?? 0,
      success_rate: tool.success_rate ?? 1,
      is_active: tool.is_active ?? true,
      version: tool.version ?? '1.0.0',
    }));
    return { tools, count: data.count ?? tools.length };
  }

  public async executeMCPTool(toolId: string, parameters: Record<string, unknown>, sessionId?: string): Promise<{ execution_id: string; result: Record<string, unknown>; success: boolean }> {
    const response = await this.client.post(`/mcp/api/tools/${toolId}/execute_tool/`, {
      parameters,
      session_id: sessionId
    });
    return response.data;
  }

  public async batchExecuteMCPTools(toolsConfig: MCPToolConfig[], mode: 'sequential' | 'parallel' = 'sequential', sessionId?: string): Promise<{ results: MCPToolExecution[]; execution_mode: string; total_tools: number }> {
    const response = await this.client.post('/mcp/api/tools/batch_execute/', {
      tools: toolsConfig,
      mode,
      session_id: sessionId
    });
    return response.data;
  }

  public async createMCPSession(name: string, enabledTools: string[], context: Record<string, unknown> = {}): Promise<{ session_id: string; name: string; enabled_tools: string[]; created_at: string }> {
    const response = await this.client.post('/mcp/api/sessions/create_session/', {
      name,
      enabled_tools: enabledTools,
      context
    });
    return response.data;
  }

  public async getMCPSessionContext(sessionId: string): Promise<{ session: MCPSession; executions: MCPToolExecution[] }> {
    const response = await this.client.get(`/mcp/api/sessions/${sessionId}/get_session_context/`);
    return response.data;
  }

  public async getMCPToolRecommendations(agentId: string, taskDescription: string, taskType: string): Promise<{ agent_id: string; recommended_tools: MCPToolRecommendation[]; task_type: string }> {
    const response = await this.client.post('/mcp/api/agent-integration/agent_tool_selection/', {
      agent_id: agentId,
      task_description: taskDescription,
      task_type: taskType
    });
    return response.data;
  }

  public async executeMCPToolWithAgentContext(agentId: string, toolName: string, parameters: Record<string, unknown>, useAgentMemory: boolean = true): Promise<{ result: Record<string, unknown>; agent_id: string; context_used: boolean }> {
    const response = await this.client.post('/mcp/api/agent-integration/execute_with_agent_context/', {
      agent_id: agentId,
      tool_name: toolName,
      parameters,
      use_agent_memory: useAgentMemory
    });
    return response.data;
  }

  // Real-time Collaboration APIs
  public async createCollaborationSession(name: string, description: string = '', isPublic: boolean = false): Promise<{ session_id: string; name: string; description: string; is_public: boolean; created_at: string }> {
    const response = await this.client.post('/agents/api/collaboration/create_session/', {
      name,
      description,
      is_public: isPublic
    });
    return response.data;
  }

  public async inviteCollaborator(sessionId: string, email: string, role: string = 'viewer', permissions: string[] = []): Promise<{ member_id: string; user: CollaborationUser; role: string; permissions: string[]; status: string; joined_at: string }> {
    const response = await this.client.post(`/agents/api/collaboration/${sessionId}/invite_member/`, {
      email,
      role,
      permissions
    });
    return response.data;
  }

  public async getCollaborationTeamMembers(sessionId: string): Promise<{ members: TeamMember[] }> {
    const response = await this.client.get(`/agents/api/collaboration/${sessionId}/team_members/`);
    return response.data;
  }

  public async addCollaborationComment(sessionId: string, content: string, nodeId?: string): Promise<{ comment_id: string; content: string; node_id?: string; author: CollaborationUser; created_at: string; resolved: boolean }> {
    const response = await this.client.post(`/agents/api/collaboration/${sessionId}/add_comment/`, {
      content,
      node_id: nodeId
    });
    return response.data;
  }

  public async getCollaborationComments(sessionId: string, nodeId?: string): Promise<{ comments: Comment[] }> {
    const params = nodeId ? { node_id: nodeId } : {};
    const response = await this.client.get(`/agents/api/collaboration/${sessionId}/comments/`, { params });
    return response.data;
  }

  public async getCollaborationActivity(sessionId: string, limit: number = 50): Promise<{ activities: Activity[] }> {
    const response = await this.client.get(`/agents/api/collaboration/${sessionId}/activity/`, {
      params: { limit }
    });
    return response.data;
  }

  public async updateCollaborationPresence(sessionId: string, status: 'online' | 'away' | 'offline' | 'busy', cursorPosition?: Record<string, unknown>): Promise<{ status: string }> {
    const response = await this.client.post(`/agents/api/collaboration/${sessionId}/update_presence/`, {
      status,
      cursor_position: cursorPosition
    });
    return response.data;
  }

  // Notification APIs (old - kept for backward compatibility)
  public async getAgentNotifications(): Promise<{ notifications: NotificationData[] }> {
    const response = await this.client.get('/agents/api/notifications/list_notifications/');
    return response.data;
  }

  public async markNotificationAsRead(notificationId: string): Promise<{ status: string }> {
    const response = await this.client.post(`/agents/api/notifications/${notificationId}/mark_read/`);
    return response.data;
  }

  // Authentication APIs
  public async login(credentials: { username: string; password: string }): Promise<{ token: string; user: Record<string, unknown> }> {
    const response: AxiosResponse<{ token: string; user: Record<string, unknown> }> = await this.client.post('/auth/login/', credentials);
    const { token } = response.data;
    this.setAuthToken(token);
    return response.data;
  }

  public async register(userData: { 
    username: string; 
    email: string; 
    password: string; 
    first_name?: string; 
    last_name?: string;
  }): Promise<{ token: string; user: Record<string, unknown> }> {
    const response: AxiosResponse<{ token: string; user: Record<string, unknown> }> = await this.client.post('/authentication/api/register/', userData);
    const { token } = response.data;
    this.setAuthToken(token);
    return response.data;
  }

  public async logout(): Promise<void> {
    try {
      await this.client.post('/authentication/api/logout/');
    } finally {
      this.removeAuthToken();
    }
  }

  public async getCurrentUser(): Promise<Record<string, unknown>> {
    const response: AxiosResponse<Record<string, unknown>> = await this.client.get('/authentication/api/profile/');
    return response.data;
  }

  public async updateProfile(profileData: Partial<Record<string, unknown>>): Promise<Record<string, unknown>> {
    const response: AxiosResponse<Record<string, unknown>> = await this.client.patch('/authentication/api/profile/', profileData);
    return response.data;
  }

  public async changePassword(data: { old_password: string; new_password: string }): Promise<{ message: string }> {
    const response: AxiosResponse<{ message: string }> = await this.client.post('/authentication/api/change-password/', data);
    return response.data;
  }

  public async forgotPassword(email: string): Promise<{ message: string }> {
    const response: AxiosResponse<{ message: string }> = await this.client.post('/authentication/api/forgot-password/', { email });
    return response.data;
  }

  public async resetPassword(data: { token: string; new_password: string }): Promise<{ message: string }> {
    const response: AxiosResponse<{ message: string }> = await this.client.post('/authentication/api/reset-password/', data);
    return response.data;
  }

  public async enable2FA(): Promise<{ qr_code: string; backup_codes: string[] }> {
    const response: AxiosResponse<{ qr_code: string; backup_codes: string[] }> = await this.client.post('/authentication/api/enable-2fa/');
    return response.data;
  }

  public async verify2FA(code: string): Promise<{ verified: boolean }> {
    const response: AxiosResponse<{ verified: boolean }> = await this.client.post('/authentication/api/verify-2fa/', { code });
    return response.data;
  }

  public async getAPIKeys(): Promise<{ api_keys: Array<{ id: string; name: string; key: string; created_at: string; last_used: string }> }> {
    const response = await this.client.get('/authentication/api/api-keys/');
    return response.data;
  }

  public async createAPIKey(name: string): Promise<{ id: string; name: string; key: string; created_at: string }> {
    const response = await this.client.post('/authentication/api/api-keys/', { name });
    return response.data;
  }

  public async deleteAPIKey(keyId: string): Promise<{ message: string }> {
    const response: AxiosResponse<{ message: string }> = await this.client.delete(`/authentication/api/api-keys/${keyId}/`);
    return response.data;
  }

  // API Integration Hub APIs
  public async getAPIIntegrations(): Promise<{ results?: Array<Record<string, unknown>>; integrations?: Array<Record<string, unknown>> }> {
    const response = await this.client.get('/api-integrations/api/integrations/');
    return response.data;
  }

  public async createAPIIntegration(integrationData: Record<string, unknown>): Promise<Record<string, unknown>> {
    const response = await this.client.post('/api-integrations/api/integrations/', integrationData);
    return response.data;
  }

  public async updateAPIIntegration(id: string, integrationData: Record<string, unknown>): Promise<Record<string, unknown>> {
    const response = await this.client.patch(`/api-integrations/api/integrations/${id}/`, integrationData);
    return response.data;
  }

  public async deleteAPIIntegration(id: string): Promise<void> {
    await this.client.delete(`/api-integrations/api/integrations/${id}/`);
  }

  public async testAPIIntegration(id: string): Promise<{ success: boolean; message?: string; response_time: number; status_code?: number; error?: string }> {
    const response = await this.client.post(`/api-integrations/api/integrations/${id}/test/`);
    return response.data;
  }

  public async getIntegrationTemplates(): Promise<{ templates: Array<Record<string, unknown>> }> {
    const response = await this.client.get('/api-integrations/api/templates/');
    return response.data;
  }

  public async executeAPIIntegration(id: string, parameters: Record<string, unknown>): Promise<Record<string, unknown>> {
    const tool = (parameters.tool || parameters.action || '') as string;
    const params = (parameters.params as Record<string, unknown>) || parameters;
    const response = await this.client.post(`/api-integrations/api/integrations/${id}/execute/`, {
      tool,
      params,
      action: tool,
      parameters: params,
    });
    return response.data;
  }

  public async getIntegrationLogs(id: string, limit: number = 50): Promise<{ logs: Array<Record<string, unknown>> }> {
    const response = await this.client.get(`/api-integrations/api/integrations/${id}/logs/`, { params: { limit } });
    return response.data;
  }

  public async getIntegrationMetrics(id: string, timeRange: string = '24h'): Promise<{ metrics: Record<string, unknown> }> {
    const response = await this.client.get(`/api-integrations/api/integrations/${id}/metrics/`, { params: { time_range: timeRange } });
    return response.data;
  }

  public async getIntegrationActivity(): Promise<{ results: Array<Record<string, unknown>> }> {
    const response = await this.client.get('/api-integrations/api/activity/');
    return response.data;
  }

  // Advanced Reporting APIs
  public async getReports(): Promise<{ reports: Array<Record<string, unknown>> }> {
    const response = await this.client.get('/reporting/api/reports/');
    return response.data;
  }

  public async createReport(reportData: Record<string, unknown>): Promise<Record<string, unknown>> {
    const response = await this.client.post('/reporting/api/reports/', reportData);
    return response.data;
  }

  public async updateReport(id: string, reportData: Record<string, unknown>): Promise<Record<string, unknown>> {
    const response = await this.client.patch(`/reporting/api/reports/${id}/`, reportData);
    return response.data;
  }

  public async deleteReport(id: string): Promise<void> {
    await this.client.delete(`/reporting/api/reports/${id}/`);
  }

  public async generateLegacyReport(id: string, parameters: Record<string, unknown> = {}): Promise<{ report_data: Record<string, unknown>; generated_at: string }> {
    const response = await this.client.post(`/reporting/api/reports/${id}/generate/`, parameters);
    return response.data;
  }

  public async exportReport(id: string, format: 'pdf' | 'excel' | 'csv'): Promise<{ download_url: string; expires_at: string }> {
    const response = await this.client.post(`/reporting/api/reports/${id}/export/`, { format });
    return response.data;
  }

  public async getReportTemplates(): Promise<{ templates: Array<Record<string, unknown>> }> {
    const response = await this.client.get('/reporting/api/templates/');
    return response.data;
  }

  public async scheduleReport(id: string, scheduleData: Record<string, unknown>): Promise<{ schedule_id: string; next_run: string }> {
    const response = await this.client.post(`/reporting/api/reports/${id}/schedule/`, scheduleData);
    return response.data;
  }

  public async getDashboardData(dashboardId?: string): Promise<{ widgets: Array<Record<string, unknown>>; metadata: Record<string, unknown> }> {
    const url = dashboardId ? `/reporting/api/dashboard/${dashboardId}/` : '/reporting/api/dashboard/';
    const response = await this.client.get(url);
    return response.data;
  }

  public async createCustomWidget(widgetData: Record<string, unknown>): Promise<Record<string, unknown>> {
    const response = await this.client.post('/reporting/api/widgets/', widgetData);
    return response.data;
  }

  // Notification Management APIs
  public async getNotificationCampaigns(): Promise<{ campaigns: Array<Record<string, unknown>> }> {
    const response = await this.client.get('/notifications/api/campaigns/');
    return response.data;
  }

  public async createNotificationCampaign(campaignData: Record<string, unknown>): Promise<Record<string, unknown>> {
    const response = await this.client.post('/notifications/api/campaigns/', campaignData);
    return response.data;
  }

  public async updateNotificationCampaign(id: string, campaignData: Record<string, unknown>): Promise<Record<string, unknown>> {
    const response = await this.client.patch(`/notifications/api/campaigns/${id}/`, campaignData);
    return response.data;
  }

  public async deleteNotificationCampaign(id: string): Promise<void> {
    await this.client.delete(`/notifications/api/campaigns/${id}/`);
  }

  public async sendNotificationCampaign(id: string, options: Record<string, unknown> = {}): Promise<{ sent: number; failed: number; campaign_id: string }> {
    const response = await this.client.post(`/notifications/api/campaigns/${id}/send/`, options);
    return response.data;
  }

  public async getNotificationTemplates(): Promise<{ templates: Array<Record<string, unknown>> }> {
    const response = await this.client.get('/notifications/api/templates/');
    return response.data;
  }

  public async createNotificationTemplate(templateData: Record<string, unknown>): Promise<Record<string, unknown>> {
    const response = await this.client.post('/notifications/api/templates/', templateData);
    return response.data;
  }

  public async getNotificationRules(): Promise<{ rules: Array<Record<string, unknown>> }> {
    const response = await this.client.get('/notifications/api/rules/');
    return response.data;
  }

  public async createNotificationRule(ruleData: Record<string, unknown>): Promise<Record<string, unknown>> {
    const response = await this.client.post('/notifications/api/rules/', ruleData);
    return response.data;
  }

  public async getNotificationStats(timeRange: string = '7d'): Promise<{ stats: Record<string, unknown> }> {
    const response = await this.client.get('/notifications/api/stats/', { params: { time_range: timeRange } });
    return response.data;
  }

  public async subscribeToNotifications(subscriptionData: Record<string, unknown>): Promise<{ subscription_id: string }> {
    const response = await this.client.post('/notifications/api/subscriptions/', subscriptionData);
    return response.data;
  }

  public async updateNotificationPreferences(preferences: Record<string, unknown>): Promise<Record<string, unknown>> {
    const response = await this.client.patch('/notifications/api/preferences/', preferences);
    return response.data;
  }

  // Data Pipeline Management APIs
  public async getDataPipelines(): Promise<{ pipelines: Array<Record<string, unknown>> }> {
    const response = await this.client.get('/data-pipelines/api/pipelines/');
    return response.data;
  }

  public async createDataPipeline(pipelineData: Record<string, unknown>): Promise<Record<string, unknown>> {
    const response = await this.client.post('/data-pipelines/api/pipelines/', pipelineData);
    return response.data;
  }

  public async updateDataPipeline(id: string, pipelineData: Record<string, unknown>): Promise<Record<string, unknown>> {
    const response = await this.client.patch(`/data-pipelines/api/pipelines/${id}/`, pipelineData);
    return response.data;
  }

  public async deleteDataPipeline(id: string): Promise<void> {
    await this.client.delete(`/data-pipelines/api/pipelines/${id}/`);
  }

  public async executePipeline(id: string, parameters: Record<string, unknown> = {}): Promise<{ execution_id: string; status: string; started_at: string }> {
    const response = await this.client.post(`/data-pipelines/api/pipelines/${id}/execute/`, parameters);
    return response.data;
  }

  public async getPipelineStatus(id: string): Promise<{ status: string; progress: number; current_step: string; logs: Array<Record<string, unknown>> }> {
    const response = await this.client.get(`/data-pipelines/api/pipelines/${id}/status/`);
    return response.data;
  }

  public async stopPipeline(id: string): Promise<{ status: string; stopped_at: string }> {
    const response = await this.client.post(`/data-pipelines/api/pipelines/${id}/stop/`);
    return response.data;
  }

  public async getDataSources(): Promise<{ sources: Array<Record<string, unknown>> }> {
    const response = await this.client.get('/data-pipelines/api/sources/');
    return response.data;
  }

  public async createDataSource(sourceData: Record<string, unknown>): Promise<Record<string, unknown>> {
    const response = await this.client.post('/data-pipelines/api/sources/', sourceData);
    return response.data;
  }

  public async testDataSource(id: string): Promise<{ success: boolean; connection_time: number; error?: string; sample_data?: Record<string, unknown> }> {
    const response = await this.client.post(`/data-pipelines/api/sources/${id}/test/`);
    return response.data;
  }

  public async getDataQualityRules(): Promise<{ rules: Array<Record<string, unknown>> }> {
    const response = await this.client.get('/data-pipelines/api/quality-rules/');
    return response.data;
  }

  public async createDataQualityRule(ruleData: Record<string, unknown>): Promise<Record<string, unknown>> {
    const response = await this.client.post('/data-pipelines/api/quality-rules/', ruleData);
    return response.data;
  }

  public async getPipelineMetrics(id: string, timeRange: string = '7d'): Promise<{ metrics: Record<string, unknown>; performance: Record<string, unknown> }> {
    const response = await this.client.get(`/data-pipelines/api/pipelines/${id}/metrics/`, { params: { time_range: timeRange } });
    return response.data;
  }

  public async schedulePipeline(id: string, scheduleData: Record<string, unknown>): Promise<{ schedule_id: string; next_run: string }> {
    const response = await this.client.post(`/data-pipelines/api/pipelines/${id}/schedule/`, scheduleData);
    return response.data;
  }

  // Agent Plugin Management APIs (deprecated - use Plugin System instead)
  public async getAgentPlugins(): Promise<PaginatedResponse<Plugin>> {
    const response: AxiosResponse<PaginatedResponse<Plugin>> = await this.client.get('/agents/api/plugins/');
    return response.data;
  }

  public async getAgentPlugin(id: string): Promise<Plugin> {
    const response: AxiosResponse<Plugin> = await this.client.get(`/agents/api/plugins/${id}/`);
    return response.data;
  }

  public async createAgentPlugin(pluginData: Partial<Plugin>): Promise<Plugin> {
    const response: AxiosResponse<Plugin> = await this.client.post('/agents/api/plugins/', pluginData);
    return response.data;
  }

  public async updateAgentPlugin(id: string, pluginData: Partial<Plugin>): Promise<Plugin> {
    const response: AxiosResponse<Plugin> = await this.client.patch(`/agents/api/plugins/${id}/`, pluginData);
    return response.data;
  }

  public async deleteAgentPlugin(id: string): Promise<void> {
    await this.client.delete(`/agents/api/plugins/${id}/`);
  }

  public async publishAgentPlugin(id: string): Promise<{ status: string }> {
    const response: AxiosResponse<{ status: string }> = await this.client.post(`/agents/api/plugins/${id}/publish/`);
    return response.data;
  }

  public async unpublishAgentPlugin(id: string): Promise<{ status: string }> {
    const response: AxiosResponse<{ status: string }> = await this.client.post(`/agents/api/plugins/${id}/unpublish/`);
    return response.data;
  }

  public async getPublicAgentPlugins(): Promise<PaginatedResponse<Plugin>> {
    const response: AxiosResponse<PaginatedResponse<Plugin>> = await this.client.get('/agents/api/plugins/list_public/');
    return response.data;
  }

  public async installAgentPlugin(pluginId: string): Promise<PluginInstallation> {
    const response: AxiosResponse<PluginInstallation> = await this.client.post(`/agents/api/plugins/${pluginId}/install/`);
    return response.data;
  }

  public async uninstallAgentPlugin(installationId: string): Promise<{ status: string }> {
    const response: AxiosResponse<{ status: string }> = await this.client.post(`/agents/api/plugins/${installationId}/uninstall/`);
    return response.data;
  }

  public async rateAgentPlugin(pluginId: string, ratingData: { rating: number; review?: string }): Promise<{ status: string }> {
    const response: AxiosResponse<{ status: string }> = await this.client.post(`/agents/api/plugins/${pluginId}/rate/`, ratingData);
    return response.data;
  }

  public async getPluginRatings(pluginId: string): Promise<PaginatedResponse<PluginRating>> {
    const response: AxiosResponse<PaginatedResponse<PluginRating>> = await this.client.get(`/agents/api/plugins/${pluginId}/ratings/`);
    return response.data;
  }

  public async getInstalledPlugins(): Promise<PaginatedResponse<PluginInstallation>> {
    const response: AxiosResponse<PaginatedResponse<PluginInstallation>> = await this.client.get('/agents/api/plugin-installations/');
    return response.data;
  }

  public async configurePlugin(installationId: string, configuration: Record<string, unknown>): Promise<PluginInstallation> {
    const response: AxiosResponse<PluginInstallation> = await this.client.post(`/agents/api/plugin-installations/${installationId}/configure/`, { configuration });
    return response.data;
  }

  // Multi-Agent Coordination APIs
  public async getCoordinationSessions(): Promise<{ sessions: CoordinationSession[]; count: number }> {
    const response = await this.client.get('/coordination/api/sessions/');
    return response.data;
  }

  public async createCoordinationSession(name: string, strategy: 'sequential' | 'parallel' | 'hierarchical' | 'collaborative' = 'sequential', config: Record<string, unknown> = {}): Promise<CoordinationSession> {
    const response = await this.client.post('/coordination/api/sessions/', {
      name,
      strategy,
      config
    });
    return response.data;
  }

  public async coordinateAgents(sessionId: string, agentIds: string[], task: string, strategy?: string, extras?: {
    use_model_coordination?: boolean;
    model_ids?: string[];
  }): Promise<CoordinationResult> {
    const response = await this.client.post(`/coordination/api/sessions/${sessionId}/coordinate_agents/`, {
      agent_ids: agentIds,
      task,
      strategy,
      ...(extras || {}),
    });
    return response.data;
  }

  public async quickCoordinateAgents(payload: {
    name?: string;
    strategy: string;
    agent_ids: string[];
    task: string;
    use_model_coordination?: boolean;
    model_ids?: string[];
  }): Promise<CoordinationResult & { id?: string }> {
    const response = await this.client.post('/coordination/api/sessions/quick_run/', payload);
    return response.data;
  }

  public async getCoordinationStrategies(): Promise<{ strategies: Array<{ id: string; name: string; description: string }> }> {
    const response = await this.client.get('/coordination/api/sessions/strategies/');
    return response.data;
  }

  public async deleteCoordinationSession(sessionId: string): Promise<void> {
    await this.client.delete(`/coordination/api/sessions/${sessionId}/`);
  }

  public async getCoordinationInteractions(sessionId: string): Promise<{ interactions: AgentInteraction[]; count: number }> {
    const response = await this.client.get(`/coordination/api/sessions/${sessionId}/interactions/`);
    return response.data;
  }

  public async getCoordinationMetrics(sessionId: string): Promise<{ metrics: Array<Record<string, unknown>>; summary: Record<string, unknown>; count: number }> {
    const response = await this.client.get(`/coordination/api/sessions/${sessionId}/metrics/`);
    return response.data;
  }

  // Multi-Modal Intelligence APIs
  public async getAIModels(modelType?: string, isActive?: boolean): Promise<{ models: AIModelConfig[]; count: number }> {
    const params: Record<string, string> = {};
    if (modelType) params.model_type = modelType;
    if (isActive !== undefined) params.is_active = isActive.toString();
    
    const response = await this.client.get('/intelligence/api/models/', { params });
    return response.data;
  }

  public async createAIModel(modelData: {
    name: string;
    model_type: string;
    provider: string;
    model_id: string;
    capabilities?: string[];
    config?: Record<string, unknown>;
    api_key?: string;
    is_default?: boolean;
  }): Promise<AIModelConfig> {
    const response = await this.client.post('/intelligence/api/models/', modelData);
    return response.data;
  }

  public async updateAIModel(id: string, modelData: Record<string, unknown>): Promise<AIModelConfig> {
    const response = await this.client.patch(`/intelligence/api/models/${id}/`, modelData);
    return response.data;
  }

  public async deleteAIModel(id: string): Promise<{ success: boolean }> {
    const response = await this.client.delete(`/intelligence/api/models/${id}/`);
    return response.data;
  }

  public async seedDefaultAIModels(): Promise<{ created: string[]; count: number }> {
    const response = await this.client.post('/intelligence/api/models/seed_defaults/');
    return response.data;
  }

  public async coordinateModels(payload: {
    prompt: string;
    mode: string;
    model_ids?: string[];
    options?: Record<string, unknown>;
  }): Promise<Record<string, unknown>> {
    const response = await this.client.post('/intelligence/api/coordinate/run/', payload);
    return response.data;
  }

  public async getModelCoordinationHistory(): Promise<{ results: Array<Record<string, unknown>>; count: number }> {
    const response = await this.client.get('/intelligence/api/coordinate/history/');
    return response.data;
  }

  public async getModelCoordinationModes(): Promise<{ modes: Array<{ id: string; name: string; description: string }> }> {
    const response = await this.client.get('/intelligence/api/coordinate/modes/');
    return response.data;
  }

  public async processMultiModalIntelligence(formData: FormData): Promise<MultiModalResult> {
    const response = await this.client.post('/intelligence/api/intelligence/process_multimodal/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  public async crossModalAnalysis(modalityResults: Record<string, unknown>): Promise<{
    insights: Array<{ modalities: string[]; correlation_type: string; confidence: number; description: string }>;
    analyzed_modalities: string[];
    insight_count: number;
  }> {
    const response = await this.client.post('/intelligence/api/intelligence/cross_modal_analysis/', {
      modality_results: modalityResults
    });
    return response.data;
  }

  public async getMultiModalSessions(): Promise<{ sessions: MultiModalSession[]; count: number }> {
    const response = await this.client.get('/intelligence/api/intelligence/sessions/');
    return response.data;
  }

  public async getMultiModalSessionDetail(sessionId: string): Promise<{
    id: string;
    name: string;
    status: string;
    input_modalities: string[];
    results: Record<string, unknown>;
    modality_results: Array<Record<string, unknown>>;
    cross_modal_insights: Array<Record<string, unknown>>;
    created_at: string;
  }> {
    const response = await this.client.get(`/intelligence/api/intelligence/${sessionId}/session_detail/`);
    return response.data;
  }

  // ==================== NEW FEATURE METHODS ====================
  
  // Agent Learning & Adaptation Methods
  public async getLearningProfiles(): Promise<AxiosResponse> {
    return this.client.get('/agent-learning/profiles/');
  }
  
  public async recordExperience(profileId: string, data: {
    state: Record<string, unknown>;
    action: Record<string, unknown>;
    reward: number;
    success: boolean;
    execution_time: number;
    task_type: string;
  }): Promise<AxiosResponse> {
    return this.client.post(`/agent-learning/profiles/${profileId}/record_experience/`, data);
  }
  
  public async getRecommendations(profileId: string, state: Record<string, unknown>): Promise<AxiosResponse> {
    return this.client.get(`/agent-learning/profiles/${profileId}/get_recommendations/`, {
      params: { state: JSON.stringify(state) }
    });
  }
  
  public async updateSkill(profileId: string, data: {
    skill_name: string;
    skill_category: string;
    success: boolean;
    execution_time: number;
  }): Promise<AxiosResponse> {
    return this.client.post(`/agent-learning/profiles/${profileId}/update_skill/`, data);
  }
  
  public async getTopPerformers(): Promise<AxiosResponse> {
    return this.client.get('/agent-learning/profiles/top_performers/');
  }
  
  public async getLearningHistory(profileId: string): Promise<AxiosResponse> {
    return this.client.get(`/agent-learning/profiles/${profileId}/learning_history/`);
  }
  
  public async getAdaptiveStrategies(): Promise<AxiosResponse> {
    return this.client.get('/agent-learning/strategies/');
  }
  
  public async recommendStrategy(data: {
    task_description: string;
    complexity: string;
    agents: string[];
  }): Promise<AxiosResponse> {
    return this.client.post('/agent-learning/strategies/recommend_strategy/', data);
  }
  
  public async recordStrategyUsage(strategyId: string, data: {
    success: boolean;
    completion_time: number;
    session_id?: string;
  }): Promise<AxiosResponse> {
    return this.client.post(`/agent-learning/strategies/${strategyId}/record_usage/`, data);
  }
  
  public async getTopStrategies(): Promise<AxiosResponse> {
    return this.client.get('/agent-learning/strategies/top_strategies/');
  }
  
  // Plugin System Methods
  public async getPlugins(params?: { category?: string; verified?: boolean }): Promise<AxiosResponse> {
    return this.client.get('/plugins/marketplace/', { params });
  }
  
  public async installPlugin(pluginId: string, config?: Record<string, unknown>): Promise<AxiosResponse> {
    return this.client.post(`/plugins/marketplace/${pluginId}/install/`, { config });
  }
  
  public async uninstallPlugin(pluginId: string): Promise<AxiosResponse> {
    return this.client.post(`/plugins/marketplace/${pluginId}/uninstall/`);
  }
  
  public async getPluginInstallations(): Promise<AxiosResponse> {
    return this.client.get('/plugins/installations/');
  }
  
  public async getCustomAgents(): Promise<AxiosResponse> {
    return this.client.get('/plugins/custom-agents/');
  }
  
  public async submitPluginReview(pluginId: string, data: {
    rating: number;
    review_text: string;
  }): Promise<AxiosResponse> {
    return this.client.post(`/plugins/marketplace/${pluginId}/review/`, data);
  }
  
  // Webhook & Notification Methods
  public async getWebhooks(): Promise<AxiosResponse> {
    return this.client.get('/webhooks/endpoints/');
  }
  
  public async createWebhook(data: {
    name: string;
    url: string;
    subscribed_events: string[];
    secret_key: string;
  }): Promise<AxiosResponse> {
    return this.client.post('/webhooks/endpoints/', data);
  }
  
  public async testWebhook(webhookId: string): Promise<AxiosResponse> {
    return this.client.post(`/webhooks/endpoints/${webhookId}/test/`);
  }
  
  public async getWebhookDeliveries(webhookId: string): Promise<AxiosResponse> {
    return this.client.get(`/webhooks/endpoints/${webhookId}/deliveries/`);
  }
  
  public async getWebhookNotifications(): Promise<AxiosResponse> {
    return this.client.get('/webhooks/notifications/');
  }
  
  public async markNotificationRead(notificationId: string): Promise<AxiosResponse> {
    return this.client.post(`/webhooks/notifications/${notificationId}/mark_read/`);
  }
  
  public async markAllNotificationsRead(): Promise<AxiosResponse> {
    return this.client.post('/webhooks/notifications/mark_all_read/');
  }
  
  public async getUnreadCount(): Promise<AxiosResponse> {
    return this.client.get('/webhooks/notifications/unread_count/');
  }
  
  public async deleteWebhook(webhookId: string): Promise<AxiosResponse> {
    return this.client.delete(`/webhooks/endpoints/${webhookId}/`);
  }
  
  public async getNotifications(params?: { is_read?: boolean }): Promise<{ notifications: unknown[] }> {
    const queryString = params ? `?${new URLSearchParams(params as Record<string, string>).toString()}` : '';
    const response = await this.client.get(`/webhooks/notifications/${queryString}`);
    return { notifications: response.data.results || response.data };
  }
  
  // Analytics Methods (mounted under /analytics/api/)
  public async getAnalyticsMetrics(params?: { time_range?: string; metric_type?: string }): Promise<AxiosResponse> {
    return this.client.get('/analytics/api/metrics/', { params });
  }

  public async getAnalyticsMetricTrends(params?: { time_range?: string; metric_type?: string; workflow_id?: string }): Promise<AxiosResponse> {
    return this.client.get('/analytics/api/metrics/trends/', { params });
  }

  public async getAnalyticsCosts(params?: { time_range?: string }): Promise<AxiosResponse> {
    return this.client.get('/analytics/api/costs/', { params });
  }

  public async getAnalyticsCostSummary(params?: { time_range?: string }): Promise<AxiosResponse> {
    return this.client.get('/analytics/api/costs/summary/', { params });
  }

  public async getAnalyticsOptimizations(): Promise<AxiosResponse> {
    return this.client.get('/analytics/api/optimizations/');
  }

  public async getAnalyticsAnomalies(): Promise<AxiosResponse> {
    return this.client.get('/analytics/api/anomalies/');
  }

  public async getAnalyticsReports(): Promise<AxiosResponse> {
    return this.client.get('/analytics/api/predictions/');
  }
  
  public async generateAnalyticsReport(data: {
    report_type: string;
    start_date?: string;
    end_date?: string;
  }): Promise<AxiosResponse> {
    return this.client.post('/analytics/api/predictions/', data);
  }
  
  public async getPerformanceTrends(params?: { time_range?: string; metric_type?: string }): Promise<AxiosResponse> {
    return this.client.get('/analytics/api/metrics/trends/', { params });
  }
  
  public async getPredictiveInsights(): Promise<AxiosResponse> {
    return this.client.get('/analytics/api/predictions/');
  }
  
  public async generateReport(reportId: string): Promise<{ report_data: Record<string, unknown>; generated_at: string }> {
    const response = await this.client.post(`/analytics/api/predictions/${reportId}/generate/`);
    return { report_data: response.data, generated_at: new Date().toISOString() };
  }
  
  public async getAnalyticsPredictions(): Promise<AxiosResponse> {
    return this.client.get('/analytics/api/predictions/');
  }
  
  // Workflow Builder Methods  
  public async getWorkflowTemplates(params?: { category?: string }): Promise<AxiosResponse> {
    return this.client.get('/workflow-builder/api/templates/', { params });
  }
  
  public async createWorkflowTemplate(data: {
    name: string;
    description: string;
    category: string;
    workflow_definition: Record<string, unknown>;
  }): Promise<AxiosResponse> {
    return this.client.post('/workflow-builder/api/templates/', data);
  }
  
  public async cloneWorkflowTemplate(templateId: string): Promise<AxiosResponse> {
    return this.client.post(`/workflow-builder/api/templates/${templateId}/use_template/`);
  }
  
  public async getWorkflows(): Promise<AxiosResponse> {
    return this.client.get('/workflow-builder/api/workflows/');
  }

  public async getWorkflow(workflowId: string): Promise<AxiosResponse> {
    return this.client.get(`/workflow-builder/api/workflows/${workflowId}/`);
  }
  
  public async createWorkflow(data: {
    name: string;
    description?: string;
    nodes: Array<Record<string, unknown>>;
    edges: Array<Record<string, unknown>>;
    status?: string;
  }): Promise<AxiosResponse> {
    return this.client.post('/workflow-builder/api/workflows/', data);
  }

  public async updateWorkflow(workflowId: string, data: Record<string, unknown>): Promise<AxiosResponse> {
    return this.client.patch(`/workflow-builder/api/workflows/${workflowId}/`, data);
  }
  
  public async executeWorkflow(workflowId: string, data?: Record<string, unknown>): Promise<AxiosResponse> {
    return this.client.post(`/workflow-builder/api/workflows/${workflowId}/execute/`, data || {});
  }
  
  public async validateWorkflow(workflowId: string): Promise<AxiosResponse> {
    return this.client.post(`/workflow-builder/api/workflows/${workflowId}/validate/`);
  }
  
  public async deleteWorkflowTemplate(templateId: string): Promise<AxiosResponse> {
    return this.client.delete(`/workflow-builder/api/templates/${templateId}/`);
  }
  
  public async executeWorkflowTemplate(templateId: string, data?: Record<string, unknown>): Promise<AxiosResponse> {
    return this.client.post(`/workflow-builder/api/templates/${templateId}/execute/`, data);
  }
  
  public async getWorkflowExecutions(): Promise<AxiosResponse> {
    return this.client.get('/workflow-builder/api/executions/');
  }

  // Scheduled automations
  public async getAutomations(): Promise<AxiosResponse> {
    return this.client.get('/api-integrations/api/automations/');
  }

  public async createAutomation(data: Record<string, unknown>): Promise<AxiosResponse> {
    return this.client.post('/api-integrations/api/automations/', data);
  }

  public async runAutomation(id: string): Promise<AxiosResponse> {
    return this.client.post(`/api-integrations/api/automations/${id}/run/`);
  }

  public async updateAutomation(id: string, data: Record<string, unknown>): Promise<AxiosResponse> {
    return this.client.patch(`/api-integrations/api/automations/${id}/`, data);
  }

  public async deleteAutomation(id: string): Promise<AxiosResponse> {
    return this.client.delete(`/api-integrations/api/automations/${id}/`);
  }

  public async getIntegrationTools(): Promise<AxiosResponse> {
    return this.client.get('/api-integrations/api/tools/');
  }
}

// Export singleton instance
const apiClient = new ApiClient();
export default apiClient;

// Export individual methods for easier importing
export const {
  getAgents,
  getAgent,
  createAgent,
  updateAgent,
  deleteAgent,
  activateAgent,
  deactivateAgent,
  getSessions,
  getSession,
  createSession,
  updateSession,
  deleteSession,
  addAgentToSession,
  getMessages,
  sendMessage,
  getTasks,
  getTask,
  createTask,
  updateTask,
  deleteTask,
  getPerformanceMetrics,
  getAgentPerformance,
  chatWithGroq,
  getGroqModels,
  healthCheck,
  // Authentication methods
  login,
  register,
  logout,
  getCurrentUser,
  updateProfile,
  changePassword,
  forgotPassword,
  resetPassword,
  enable2FA,
  verify2FA,
  getAPIKeys,
  createAPIKey,
  deleteAPIKey,
  // API Integration methods
  getAPIIntegrations,
  createAPIIntegration,
  updateAPIIntegration,
  deleteAPIIntegration,
  testAPIIntegration,
  getIntegrationTemplates,
  executeAPIIntegration,
  getIntegrationLogs,
  getIntegrationMetrics,
  // Reporting methods
  getReports,
  createReport,
  updateReport,
  deleteReport,
  generateLegacyReport,
  exportReport,
  getReportTemplates,
  scheduleReport,
  getDashboardData,
  createCustomWidget,
  // Notification methods
  getNotificationCampaigns,
  createNotificationCampaign,
  updateNotificationCampaign,
  deleteNotificationCampaign,
  sendNotificationCampaign,
  getNotificationTemplates,
  createNotificationTemplate,
  getNotificationRules,
  createNotificationRule,
  getNotificationStats,
  subscribeToNotifications,
  updateNotificationPreferences,
  // Data Pipeline methods
  getDataPipelines,
  createDataPipeline,
  updateDataPipeline,
  deleteDataPipeline,
  executePipeline,
  getPipelineStatus,
  stopPipeline,
  getDataSources,
  createDataSource,
  testDataSource,
  getDataQualityRules,
  createDataQualityRule,
  getPipelineMetrics,
  schedulePipeline,
  // Workflow methods
  saveWorkflow,
  executeAgentWorkflow,
  getAgentWorkflowStatus,
  cancelWorkflow,
  getAgentWorkflowTemplates,
  createAgentWorkflowTemplate,
  // Analytics methods
  getAnalyticsDashboard,
  getSystemPerformance,
  getAnalyticsInsights,
  getAnalyticsMetrics,
  getAnalyticsMetricTrends,
  getAnalyticsCosts,
  getAnalyticsCostSummary,
  getAnalyticsOptimizations,
  getAnalyticsAnomalies,
  // Automation methods
  createAutomationRule,
  getAutomationSuggestions,
  getAutomationRules,
  updateAutomationRule,
  deleteAutomationRule,
  // Smart Agent methods
  getSmartAgentRecommendations,
  optimizeAgentPerformance,
  getAgentInsights,
  // Multimodal methods
  processMultimodal,
  analyzeImage,
  // Version control methods
  saveWorkflowVersion,
  getWorkflowVersions,
  // Collaboration methods
  inviteTeamMember,
  getTeamMembers,
  addComment,
  getComments,
  // MCP Integration methods
  getMCPTools,
  executeMCPTool,
  batchExecuteMCPTools,
  createMCPSession,
  getMCPSessionContext,
  getMCPToolRecommendations,
  executeMCPToolWithAgentContext,
  // Real-time Collaboration methods
  createCollaborationSession,
  inviteCollaborator,
  getCollaborationTeamMembers,
  addCollaborationComment,
  getCollaborationComments,
  getCollaborationActivity,
  updateCollaborationPresence,
  // Notification methods (old agent notifications)
  getAgentNotifications,
  markNotificationAsRead,
  // Multi-Agent Coordination methods
  getCoordinationSessions,
  createCoordinationSession,
  coordinateAgents,
  quickCoordinateAgents,
  getCoordinationStrategies,
  deleteCoordinationSession,
  getCoordinationInteractions,
  getCoordinationMetrics,
  // Multi-Modal Intelligence methods
  getAIModels,
  createAIModel,
  updateAIModel,
  deleteAIModel,
  seedDefaultAIModels,
  coordinateModels,
  getModelCoordinationHistory,
  getModelCoordinationModes,
  processMultiModalIntelligence,
  crossModalAnalysis,
  getMultiModalSessions,
  getMultiModalSessionDetail,
  // Agent Learning methods
  getLearningProfiles,
  recordExperience,
  getRecommendations,
  updateSkill,
  getTopPerformers,
  getLearningHistory,
  getAdaptiveStrategies,
  recommendStrategy,
  recordStrategyUsage,
  getTopStrategies,
  // Plugin System methods
  getPlugins,
  installPlugin,
  uninstallPlugin,
  getPluginInstallations,
  getCustomAgents,
  submitPluginReview,
  // Webhook methods
  getWebhooks,
  createWebhook,
  testWebhook,
  getWebhookDeliveries,
  getWebhookNotifications,
  markNotificationRead,
  markAllNotificationsRead,
  getUnreadCount,
  deleteWebhook,
  getNotifications,
  // Analytics methods
  getAnalyticsReports,
  generateAnalyticsReport,
  getAnalyticsPredictions,
  getPerformanceTrends,
  getPredictiveInsights,
  generateReport,
  // Workflow Builder methods
  getWorkflowTemplates,
  createWorkflowTemplate,
  cloneWorkflowTemplate,
  getWorkflows,
  getWorkflow,
  createWorkflow,
  executeWorkflow,
  validateWorkflow,
  deleteWorkflowTemplate,
  executeWorkflowTemplate,
  getWorkflowExecutions,
  updateWorkflow,
  getAutomations,
  createAutomation,
  runAutomation,
  updateAutomation,
  deleteAutomation,
  getIntegrationTools,
  getIntegrationActivity,
} = new Proxy(apiClient, {
  get(target, prop, receiver) {
    const value = Reflect.get(target, prop, receiver);
    if (typeof value === 'function') {
      return value.bind(target);
    }
    return value;
  }
}) as typeof apiClient;