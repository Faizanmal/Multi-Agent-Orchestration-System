import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ApiHealthStatus } from './ApiHealthStatus';
import { useHealthCheck } from '@/hooks/useApi';
import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('@/hooks/useApi', () => ({
  useHealthCheck: vi.fn(),
}));

describe('ApiHealthStatus', () => {
  const mockRefetch = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state', () => {
    vi.mocked(useHealthCheck).mockReturnValue({
      data: null,
      isLoading: true,
      error: null,
      refetch: mockRefetch,
    } as unknown as ReturnType<typeof useHealthCheck>);

    render(<ApiHealthStatus />);
    expect(screen.getByText('Checking...')).toBeInTheDocument();
    expect(screen.getByText('Checking backend connection...')).toBeInTheDocument();
  });

  it('renders healthy state', () => {
    vi.mocked(useHealthCheck).mockReturnValue({
      data: { status: 'healthy', message: 'All systems operational' },
      isLoading: false,
      error: null,
      refetch: mockRefetch,
    } as unknown as ReturnType<typeof useHealthCheck>);

    render(<ApiHealthStatus />);
    expect(screen.getByText('Online')).toBeInTheDocument();
    expect(screen.getByText('All systems operational')).toBeInTheDocument();
  });

  it('renders error state', () => {
    vi.mocked(useHealthCheck).mockReturnValue({
      data: null,
      isLoading: false,
      error: new Error('Network error'),
      refetch: mockRefetch,
    } as unknown as ReturnType<typeof useHealthCheck>);

    render(<ApiHealthStatus />);
    expect(screen.getByText('Offline')).toBeInTheDocument();
    expect(screen.getByText('Unable to connect to backend')).toBeInTheDocument();
    expect(screen.getByText('Error: Network error')).toBeInTheDocument();
  });

  it('calls refetch on button click', () => {
    vi.mocked(useHealthCheck).mockReturnValue({
      data: { status: 'healthy', message: 'OK' },
      isLoading: false,
      error: null,
      refetch: mockRefetch,
    } as unknown as ReturnType<typeof useHealthCheck>);

    render(<ApiHealthStatus />);
    const buttons = screen.getAllByRole('button');
    fireEvent.click(buttons[0]);
    expect(mockRefetch).toHaveBeenCalled();
  });
});
