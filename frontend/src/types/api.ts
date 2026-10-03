/** Shared API / list response helpers for typed frontend data fetching. */
import type { LucideIcon } from 'lucide-react';

export interface Paginated<T> {
  results?: T[];
  count?: number;
  next?: string | null;
  previous?: string | null;
}

// ---------------------------------------------------------------------------
// Auth / billing
// ---------------------------------------------------------------------------

export interface AuthUser {
  id: string;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  display_name?: string;
  avatar?: string | null;
  role?: string;
  subscription_tier?: 'free' | 'pro' | 'premium' | string;
  is_email_verified?: boolean;
  date_joined?: string;
}

export interface BillingStatus {
  plan: string;
  usage: {
    used_tokens: number;
    total_tokens: number;
    percentage: number;
  };
  stripe_configured: boolean;
}

// ---------------------------------------------------------------------------
// Integrations
// ---------------------------------------------------------------------------

export interface IntegrationRecord {
  id: string;
  name: string;
  description?: string;
  category?: string;
  status?: string;
  endpoint?: string;
  type?: string;
  total_calls?: number;
  last_sync?: string;
  last_tested?: string;
  success_rate?: number;
  avg_response_time?: number;
  usage?: number | {
    requests?: number;
    messages?: number;
    events?: number;
    storage?: number;
    limit: number;
  };
  authentication?: Record<string, unknown>;
  apiKey?: string;
  error?: string;
  created_at?: string;
  updated_at?: string;
}

export interface ActivityLogRecord {
  id?: string;
  integration: string;
  integration_name?: string;
  status: string;
  timestamp: string;
  response_time?: number;
  request_data?: { tool?: string; action?: string };
  error_message?: string;
  response_data?: Record<string, unknown>;
}

export interface IntegrationTemplate {
  id: string;
  name: string;
  description?: string;
  provider?: string;
  icon?: string | LucideIcon;
  config_template?: {
    provider_key?: string;
    auth_type?: string;
    tools?: unknown[];
    sub_agents?: unknown[];
  };
}

export interface IntegrationTool {
  name: string;
  description?: string;
  integration_id: string;
  integration_name: string;
  provider?: string;
  parameters?: Record<string, string>;
}

// ---------------------------------------------------------------------------
// Automations / workflows
// ---------------------------------------------------------------------------

export interface AutomationRecord {
  id: string;
  name: string;
  automation_type: string;
  frequency: string;
  cron_expression?: string;
  is_active: boolean;
  config?: Record<string, unknown>;
  workflow?: string | null;
  next_run_at?: string;
  last_run_at?: string;
  last_result?: {
    status?: string;
    message?: string;
    summary?: string;
    [key: string]: unknown;
  };
  created_at?: string;
  updated_at?: string;
}

export interface WorkflowRecord {
  id: string;
  name: string;
  description?: string;
  nodes?: unknown[];
  edges?: unknown[];
  workflow_definition?: { nodes?: unknown[]; edges?: unknown[] };
  category?: string;
  status?: string;
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
}

// ---------------------------------------------------------------------------
// Agents / chat
// ---------------------------------------------------------------------------

export interface AgentRecord {
  id: string;
  name: string;
  type: 'orchestrator' | 'vision' | 'reasoning' | 'action' | 'memory' | 'custom' | string;
  status?: 'idle' | 'active' | 'processing' | 'error' | 'offline' | string;
  capabilities?: string[];
  configuration?: Record<string, unknown>;
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface ChatAgent {
  id: string;
  name: string;
  type?: string;
  description?: string;
}

export interface ChatSession {
  id: string;
  title?: string;
  name?: string;
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  message_type?: string;
  created_at?: string;
  metadata?: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Multi-model intelligence
// ---------------------------------------------------------------------------

export type AIModelType = 'text' | 'vision' | 'audio' | 'video' | 'multimodal';

export type AIModelProvider =
  | 'groq'
  | 'openai'
  | 'anthropic'
  | 'google'
  | 'mistral'
  | 'nvidia'
  | 'custom'
  | string;

export interface AIModelRecord {
  id: string;
  name: string;
  model_type: AIModelType | string;
  provider: AIModelProvider;
  model_id: string;
  capabilities: string[];
  is_active: boolean;
  is_default: boolean;
  config?: Record<string, unknown>;
  created_at?: string;
  updated_at?: string;
}

export interface AIModelCreatePayload {
  name: string;
  model_type: AIModelType | string;
  provider: AIModelProvider;
  model_id: string;
  capabilities?: string[];
  config?: Record<string, unknown>;
  is_default?: boolean;
  api_key?: string;
}

export interface ModelExecutionRecord {
  id: string;
  provider: string;
  model_name: string;
  complexity?: string;
  duration_ms?: number;
  tokens_used?: number;
  estimated_cost?: number | string;
  success?: boolean;
  created_at?: string;
}

export type ModelCoordinationMode = 'route' | 'collaborative' | 'debate' | 'pipeline';

export interface ModelCoordinationRequest {
  prompt: string;
  mode: ModelCoordinationMode;
  model_ids?: string[];
  options?: {
    rounds?: number;
    priority?: string;
    judge_model_id?: string;
    stages?: Array<{ model_id: string; role?: string }>;
  };
}

export interface ModelCoordinationResult {
  run_id: string;
  mode: ModelCoordinationMode | string;
  models_used: Array<{ id: string; name: string; provider: string; model_id: string }>;
  duration_ms: number;
  final_answer: string;
  selected?: { id: string; name: string; provider: string; model_id: string } | null;
  verdict?: {
    winner_model_id?: string;
    confidence?: number;
    reason?: string;
    final_answer?: string;
  };
  stages?: Array<Record<string, unknown>>;
  rounds?: Array<Record<string, unknown>>;
  per_model?: Record<string, unknown>;
  error?: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

export function integrationListFromResponse(
  data: Paginated<IntegrationRecord> | IntegrationRecord[] | { integrations?: IntegrationRecord[] } | null | undefined,
): IntegrationRecord[] {
  if (Array.isArray(data)) return data;
  if (!data) return [];
  if ('integrations' in data && data.integrations) return data.integrations;
  if ('results' in data && Array.isArray(data.results)) return data.results;
  return [];
}

export function paginatedItems<T>(data: Paginated<T> | T[] | null | undefined): T[] {
  if (Array.isArray(data)) return data;
  return data?.results ?? [];
}

export function errorMessage(error: unknown): string {
  if (error instanceof Error) return error.message;
  if (typeof error === 'object' && error !== null && 'message' in error) {
    return String((error as { message: unknown }).message);
  }
  return 'Unknown error';
}

export function axiosErrorDetail(error: unknown): string | undefined {
  if (typeof error === 'object' && error !== null && 'response' in error) {
    const data = (error as {
      response?: {
        data?: {
          detail?: string;
          error?: string;
          message?: string;
        };
      };
    }).response?.data;
    return data?.message || data?.detail || data?.error;
  }
  return undefined;
}

export function axiosErrorStatus(error: unknown): number | undefined {
  if (typeof error === 'object' && error !== null && 'response' in error) {
    return (error as { response?: { status?: number } }).response?.status;
  }
  return undefined;
}

export function isQuotaLimitError(error: unknown): boolean {
  return axiosErrorStatus(error) === 402;
}
