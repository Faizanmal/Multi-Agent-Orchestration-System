import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import CustomNode from './CustomNode';
import { ReactFlowProvider } from 'reactflow';

// Mock lucide-react icons if needed, but they usually render fine as SVG
vi.mock('lucide-react', async () => {
  const actual = await vi.importActual('lucide-react');
  return {
    ...actual as Record<string, unknown>,
    // Just mock one to check if it's used
    Bot: () => <svg data-testid="bot-icon" />,
  };
});

const renderWithFlow = (ui: React.ReactElement) => {
  return render(
    <ReactFlowProvider>
      {ui}
    </ReactFlowProvider>
  );
};

describe('CustomNode', () => {
  const defaultProps = {
    id: '1',
    type: 'custom',
    data: {
      label: 'Test Node',
      type: 'agent_task',
      config: {},
    },
    selected: false,
    zIndex: 1,
    isConnectable: true,
    xPos: 0,
    yPos: 0,
    dragging: false,
  };

  it('renders correctly with default data', () => {
    renderWithFlow(<CustomNode {...defaultProps} />);
    expect(screen.getByText('Test Node')).toBeInTheDocument();
    expect(screen.getByText('agent task')).toBeInTheDocument();
    expect(screen.getByTestId('bot-icon')).toBeInTheDocument();
  });

  it('applies selected styles when selected', () => {
    const { container } = renderWithFlow(<CustomNode {...defaultProps} selected={true} />);
    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper).toHaveClass('ring-2');
    expect(wrapper).toHaveClass('ring-blue-500');
  });

  it('displays status indicator when status is provided', () => {
    renderWithFlow(
      <CustomNode
        {...defaultProps}
        data={{ ...defaultProps.data, status: 'running' }}
      />
    );
    expect(screen.getByText('running')).toBeInTheDocument();
  });

  it('displays errors and warnings badges', () => {
    renderWithFlow(
      <CustomNode
        {...defaultProps}
        data={{
          ...defaultProps.data,
          errors: ['Error 1', 'Error 2'],
          warnings: ['Warning 1'],
        }}
      />
    );
    expect(screen.getByText('2 Errors')).toBeInTheDocument();
    expect(screen.getByText('1 Warning')).toBeInTheDocument();
  });

  it('expands to show details when requested via dropdown menu', async () => {
    const user = userEvent.setup();
    renderWithFlow(<CustomNode {...defaultProps} />);

    await user.click(screen.getAllByRole('button')[0]);
    await user.click(await screen.findByText('Expand Details'));
    await user.click(screen.getAllByRole('button')[0]);
    expect(await screen.findByText('Collapse Details')).toBeInTheDocument();
  });

  it('shows configuration and metrics when expanded', async () => {
    const user = userEvent.setup();
    renderWithFlow(
      <CustomNode
        {...defaultProps}
        data={{
          ...defaultProps.data,
          config: { apiKey: 'secret-123' },
          metrics: { executionTime: 1.23, successRate: 0.95 },
        }}
      />
    );

    await user.click(screen.getAllByRole('button')[0]);
    await user.click(await screen.findByText('Expand Details'));

    await waitFor(() => {
      expect(screen.getByText('Configuration')).toBeInTheDocument();
    });
    expect(screen.getByText('apiKey:')).toBeInTheDocument();
    expect(screen.getByText('secret-123')).toBeInTheDocument();

    expect(screen.getByText('Metrics')).toBeInTheDocument();
    expect(screen.getByText('Avg Time:')).toBeInTheDocument();
    expect(screen.getByText('1.23s')).toBeInTheDocument();
  });
});
