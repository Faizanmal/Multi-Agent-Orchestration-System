import React from 'react';
import { render, screen, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { AgentThinkingIndicator } from './AgentThinkingIndicator';

vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: React.ComponentProps<'div'>) => <div {...props}>{children}</div>,
    button: ({ children, ...props }: React.ComponentProps<'button'>) => <button {...props}>{children}</button>,
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

describe('AgentThinkingIndicator', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.runOnlyPendingTimers();
    vi.useRealTimers();
  });

  it('renders the initial thinking step', () => {
    render(<AgentThinkingIndicator />);
    expect(screen.getByText('Analyzing intent...')).toBeInTheDocument();
  });

  it('shows live status from the backend when provided', () => {
    render(<AgentThinkingIndicator status="Reasoning with Vision agent..." />);
    expect(screen.getByText('Reasoning with Vision agent...')).toBeInTheDocument();
  });

  it('cycles through thinking steps over time when no status is provided', () => {
    render(<AgentThinkingIndicator />);
    
    expect(screen.getByText('Analyzing intent...')).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(2000);
    });
    expect(screen.getByText('Searching knowledge base...')).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(2000);
    });
    expect(screen.getByText('Synthesizing data...')).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(2000);
    });
    expect(screen.getByText('Formulating response...')).toBeInTheDocument();
    
    act(() => {
      vi.advanceTimersByTime(2000);
    });
    // Cycles back to the beginning
    expect(screen.getByText('Analyzing intent...')).toBeInTheDocument();
  });
});
