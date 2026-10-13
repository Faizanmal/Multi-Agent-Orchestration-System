import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { FeedbackWidget } from './FeedbackWidget';
import { useFeedback } from '@/hooks/useFeedback';
import { toast } from 'sonner';

// Mock the hooks
vi.mock('@/hooks/useFeedback', () => ({
  useFeedback: vi.fn(),
}));

vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

describe('FeedbackWidget', () => {
  const mockQuickRating = vi.fn();
  const mockThumbs = vi.fn();
  const mockSubmitFeedback = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    
    vi.mocked(useFeedback).mockReturnValue({
      quickRating: mockQuickRating,
      thumbs: mockThumbs,
      submitFeedback: mockSubmitFeedback,
      loading: false,
    } as unknown as ReturnType<typeof useFeedback>);
  });

  it('renders quick actions correctly', () => {
    render(<FeedbackWidget messageId="msg-1" />);
    // Check for comment button
    expect(screen.getByRole('button', { name: /Comment/i })).toBeInTheDocument();
  });

  it('handles thumbs up feedback', async () => {
    mockThumbs.mockResolvedValueOnce(true);
    const user = userEvent.setup();
    render(<FeedbackWidget messageId="msg-1" />);

    // Lucide icons don't have text, but we can query by clicking the button which we can find by index or role if we gave it a label.
    // The thumbs buttons don't have aria-labels, so we grab all buttons and click the first ghost button (which is thumbs up based on DOM order)
    const buttons = screen.getAllByRole('button');
    const thumbsUpButton = buttons[5]; // 0-4 are stars, 5 is thumbs up

    await user.click(thumbsUpButton);

    expect(mockThumbs).toHaveBeenCalledWith('msg-1', true);
    
    await waitFor(() => {
      expect(toast.success).toHaveBeenCalledWith('Thumbs up!');
    });
  });

  it('toggles comment box and submits comment', async () => {
    mockSubmitFeedback.mockResolvedValueOnce(true);
    const user = userEvent.setup();
    render(<FeedbackWidget messageId="msg-1" agentId="agent-1" sessionId="session-1" />);

    // Click comment button to show textarea
    const commentButton = screen.getByRole('button', { name: /Comment/i });
    await user.click(commentButton);

    const textarea = screen.getByPlaceholderText(/Share your thoughts.../i);
    expect(textarea).toBeInTheDocument();

    await user.type(textarea, 'Great response!');
    
    const submitButton = screen.getByRole('button', { name: 'Submit' });
    await user.click(submitButton);

    expect(mockSubmitFeedback).toHaveBeenCalledWith({
      feedback_type: 'text',
      comment: 'Great response!',
      message_id: 'msg-1',
      agent_id: 'agent-1',
      session_id: 'session-1',
    });

    await waitFor(() => {
      expect(toast.success).toHaveBeenCalledWith('Feedback submitted');
    });
  });
});
