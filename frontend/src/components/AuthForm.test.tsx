import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AuthForm } from './AuthForm';
import { useAuth } from '@/hooks/useAuth';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';

// Mock the hooks
vi.mock('@/hooks/useAuth', () => ({
  useAuth: vi.fn(),
}));

vi.mock('next/navigation', () => ({
  useRouter: vi.fn(),
}));

vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

describe('AuthForm', () => {
  const mockLogin = vi.fn();
  const mockRegister = vi.fn();
  const mockPush = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    
    vi.mocked(useAuth).mockReturnValue({
      login: mockLogin,
      register: mockRegister,
      loading: false,
    } as unknown as ReturnType<typeof useAuth>);

    vi.mocked(useRouter).mockReturnValue({
      push: mockPush,
    } as unknown as ReturnType<typeof useRouter>);
  });

  it('renders login form by default', () => {
    render(<AuthForm />);
    expect(screen.getByRole('heading', { name: /Welcome to Multi-Agent System/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/Username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Password/i)).toBeInTheDocument();
    expect(document.querySelector('form button[type="submit"]')).toHaveTextContent('Login');
  });

  it('handles successful login', async () => {
    mockLogin.mockResolvedValueOnce(true);
    const user = userEvent.setup();
    render(<AuthForm />);

    await user.type(screen.getByLabelText(/Username/i), 'testuser');
    await user.type(screen.getByLabelText(/Password/i), 'password123');
    await user.click(document.querySelector('form button[type="submit"]') as HTMLElement);

    expect(mockLogin).toHaveBeenCalledWith({ username: 'testuser', password: 'password123' });
    
    await waitFor(() => {
      expect(toast.success).toHaveBeenCalledWith('Login successful!');
      expect(mockPush).toHaveBeenCalledWith('/dashboard');
    });
  });

  it('handles failed login', async () => {
    mockLogin.mockResolvedValueOnce(false);
    const user = userEvent.setup();
    render(<AuthForm />);

    await user.type(screen.getByLabelText(/Username/i), 'testuser');
    await user.type(screen.getByLabelText(/Password/i), 'wrongpassword');
    await user.click(document.querySelector('form button[type="submit"]') as HTMLElement);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Login failed');
      expect(mockPush).not.toHaveBeenCalled();
    });
  });

  it('switches to register tab and handles successful registration', async () => {
    mockRegister.mockResolvedValueOnce(true);
    const user = userEvent.setup();
    render(<AuthForm />);

    // Switch to register tab
    await user.click(screen.getByRole('tab', { name: /Register/i }));

    const usernameInputs = screen.getAllByLabelText(/Username/i);
    const passwordInputs = screen.getAllByLabelText(/^Password/i);
    
    const regUsername = usernameInputs[usernameInputs.length - 1];
    const regPassword = passwordInputs[passwordInputs.length - 1];
    
    await user.type(regUsername, 'newuser');
    await user.type(screen.getByLabelText(/Email/i), 'new@test.com');
    await user.type(regPassword, 'password123');
    await user.type(screen.getByLabelText(/Confirm Password/i), 'password123');
    
    await user.click(screen.getByRole('button', { name: 'Create Account' }));

    expect(mockRegister).toHaveBeenCalledWith({
      username: 'newuser',
      email: 'new@test.com',
      password: 'password123',
    });

    await waitFor(() => {
      expect(toast.success).toHaveBeenCalledWith('Registration successful!');
      expect(mockPush).toHaveBeenCalledWith('/dashboard');
    });
  });

  it('shows error if passwords do not match during registration', async () => {
    const user = userEvent.setup();
    render(<AuthForm />);

    await user.click(screen.getByRole('tab', { name: /Register/i }));

    const usernameInputs = screen.getAllByLabelText(/Username/i);
    const passwordInputs = screen.getAllByLabelText(/^Password/i);
    
    const regUsername = usernameInputs[usernameInputs.length - 1];
    const regPassword = passwordInputs[passwordInputs.length - 1];
    
    await user.type(regUsername, 'newuser');
    await user.type(screen.getByLabelText(/Email/i), 'new@test.com');
    await user.type(regPassword, 'password123');
    await user.type(screen.getByLabelText(/Confirm Password/i), 'differentpassword');
    
    await user.click(screen.getByRole('button', { name: 'Create Account' }));

    expect(toast.error).toHaveBeenCalledWith('Passwords do not match');
    expect(mockRegister).not.toHaveBeenCalled();
  });
});
