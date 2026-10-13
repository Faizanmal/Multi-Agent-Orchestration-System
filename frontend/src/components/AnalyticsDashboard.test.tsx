import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AnalyticsDashboard } from './AnalyticsDashboard';
import { useAnalytics } from '@/hooks/useAnalytics';

// Mock the hook
vi.mock('@/hooks/useAnalytics', () => ({
  useAnalytics: vi.fn(),
}));

describe('AnalyticsDashboard', () => {
  const mockGetDashboard = vi.fn();
  const mockGetSystemHealth = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    vi.mocked(useAnalytics).mockReturnValue({
      getDashboard: mockGetDashboard,
      getSystemHealth: mockGetSystemHealth,
      loading: true,
    } as unknown as ReturnType<typeof useAnalytics>);

    render(<AnalyticsDashboard />);
    expect(screen.getByText('Loading dashboard...')).toBeInTheDocument();
  });

  it('renders dashboard metrics after data loads', async () => {
    const mockDashboardData = {
      agents: { total: 10, active: 5 },
      sessions: { total: 100, active: 20 },
      messages: { today: 500 },
      executions: { success_rate: 98.5, week_total: 1000 },
    };

    const mockHealthData = {
      status: 'healthy',
      services: {
        redis: { status: 'up', enabled: true },
        cosmosdb: { status: 'up', enabled: true },
        database: { status: 'down', enabled: false },
      }
    };

    mockGetDashboard.mockResolvedValueOnce(mockDashboardData);
    mockGetSystemHealth.mockResolvedValueOnce(mockHealthData);

    vi.mocked(useAnalytics).mockReturnValue({
      getDashboard: mockGetDashboard,
      getSystemHealth: mockGetSystemHealth,
      loading: false,
    } as unknown as ReturnType<typeof useAnalytics>);

    render(<AnalyticsDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Analytics Dashboard')).toBeInTheDocument();
    });

    // Check specific metrics
    expect(screen.getByText('10')).toBeInTheDocument(); // Total agents
    expect(screen.getByText('100')).toBeInTheDocument(); // Total sessions
    expect(screen.getByText('500')).toBeInTheDocument(); // Messages today
    expect(screen.getByText('98.5%')).toBeInTheDocument(); // Success rate

    // Check services rendering
    expect(screen.getByText('Redis Cache')).toBeInTheDocument();
    expect(screen.getByText('Azure CosmosDB')).toBeInTheDocument();
    expect(screen.getByText('Database')).toBeInTheDocument();
  });
});
