import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import Login from './Login';
import { useAuthStore } from '../../stores/authStore';
import { api } from '../../services/api';

// Mock the API
vi.mock('../../services/api', () => ({
  api: {
    post: vi.fn(),
  },
}));

// Mock the auth store
vi.mock('../../stores/authStore', () => ({
  useAuthStore: vi.fn(),
}));

// Mock react-hot-toast
vi.mock('react-hot-toast', () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
  },
  Toaster: () => null,
}));

describe('Login Component', () => {
  const mockSetUser = vi.fn();
  const mockSetToken = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (useAuthStore as any).mockReturnValue({
      setUser: mockSetUser,
      setToken: mockSetToken,
    });
  });

  const renderLogin = () => {
    return render(
      <BrowserRouter>
        <Login onBackToLanding={() => {}} />
      </BrowserRouter>
    );
  };

  it('renders login form correctly', () => {
    renderLogin();

    expect(screen.getByPlaceholderText(/email address/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/password/i)).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: /sign in/i })
    ).toBeInTheDocument();
  });

  it('displays validation errors for empty fields', async () => {
    renderLogin();

    const submitButton = screen.getByRole('button', { name: /sign in/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/email is required/i)).toBeInTheDocument();
      expect(screen.getByText(/password is required/i)).toBeInTheDocument();
    });
  });

  it('validates email format', async () => {
    renderLogin();
    const user = userEvent.setup();

    const emailInput = screen.getByPlaceholderText(/email address/i);
    await user.type(emailInput, 'invalid-email');

    const submitButton = screen.getByRole('button', { name: /sign in/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(
        screen.getByText(/please enter a valid email/i)
      ).toBeInTheDocument();
    });
  });

  it('successfully logs in with valid credentials', async () => {
    const mockResponse = {
      data: {
        access_token: 'test-token',
        user: {
          id: '1',
          email: 'test@example.com',
          name: 'Test User',
          role: 'lecturer',
        },
      },
    };

    (api.post as any).mockResolvedValueOnce(mockResponse);

    renderLogin();
    const user = userEvent.setup();

    const emailInput = screen.getByPlaceholderText(/email address/i);
    const passwordInput = screen.getByPlaceholderText(/password/i);

    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'password123');

    const submitButton = screen.getByRole('button', { name: /sign in/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith(
        '/auth/login',
        expect.any(URLSearchParams)
      );
      expect(mockSetToken).toHaveBeenCalledWith('test-token');
      expect(mockSetUser).toHaveBeenCalledWith(mockResponse.data.user);
    });
  });

  it('displays error message on login failure', async () => {
    (api.post as any).mockRejectedValueOnce({
      response: {
        data: {
          detail: 'Invalid credentials',
        },
      },
    });

    renderLogin();
    const user = userEvent.setup();

    const emailInput = screen.getByPlaceholderText(/email address/i);
    const passwordInput = screen.getByPlaceholderText(/password/i);

    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'wrongpassword');

    const submitButton = screen.getByRole('button', { name: /sign in/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
    });
  });

  it('toggles password visibility', async () => {
    renderLogin();
    const user = userEvent.setup();

    const passwordInput = screen.getByPlaceholderText(/password/i);
    expect(passwordInput).toHaveAttribute('type', 'password');

    const toggleButton = screen.getByRole('button', { name: /show password/i });
    await user.click(toggleButton);

    expect(passwordInput).toHaveAttribute('type', 'text');

    await user.click(toggleButton);
    expect(passwordInput).toHaveAttribute('type', 'password');
  });

  it('opens registration modal when clicking sign up link', async () => {
    renderLogin();
    const user = userEvent.setup();

    const signUpLink = screen.getByText(/sign up/i);
    await user.click(signUpLink);

    await waitFor(() => {
      expect(screen.getByText(/create account/i)).toBeInTheDocument();
    });
  });

  it('opens forgot password modal when clicking forgot password link', async () => {
    renderLogin();
    const user = userEvent.setup();

    const forgotLink = screen.getByText(/forgot password/i);
    await user.click(forgotLink);

    await waitFor(() => {
      expect(screen.getByText(/reset password/i)).toBeInTheDocument();
    });
  });
});
