import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import Dashboard from './Dashboard';
import { useAuthStore } from '../../stores/authStore';

// Mock the auth store
vi.mock('../../stores/authStore', () => ({
  useAuthStore: vi.fn(),
}));

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('Dashboard Component', () => {
  const mockUser = {
    id: '1',
    email: 'test@example.com',
    name: 'Test User',
    role: 'lecturer',
  };

  const mockLogout = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (useAuthStore as any).mockReturnValue({
      user: mockUser,
      logout: mockLogout,
    });
  });

  const renderDashboard = () => {
    return render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );
  };

  it('renders dashboard with user information', () => {
    renderDashboard();

    expect(screen.getByText(mockUser.name)).toBeInTheDocument();
    expect(screen.getByText(mockUser.email)).toBeInTheDocument();
  });

  it('displays navigation links', () => {
    renderDashboard();

    expect(screen.getByText(/courses/i)).toBeInTheDocument();
    expect(screen.getByText(/materials/i)).toBeInTheDocument();
    expect(screen.getByText(/settings/i)).toBeInTheDocument();
  });

  it('handles logout correctly', async () => {
    renderDashboard();
    const user = userEvent.setup();

    const logoutButton = screen.getByRole('button', { name: /logout/i });
    await user.click(logoutButton);

    expect(mockLogout).toHaveBeenCalled();
    expect(mockNavigate).toHaveBeenCalledWith('/');
  });

  it('renders admin links for admin users', () => {
    (useAuthStore as any).mockReturnValue({
      user: { ...mockUser, role: 'admin' },
      logout: mockLogout,
    });

    renderDashboard();

    expect(screen.getByText(/admin panel/i)).toBeInTheDocument();
    expect(screen.getByText(/user management/i)).toBeInTheDocument();
  });

  it('does not render admin links for non-admin users', () => {
    renderDashboard();

    expect(screen.queryByText(/admin panel/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/user management/i)).not.toBeInTheDocument();
  });

  it('toggles mobile menu', async () => {
    renderDashboard();
    const user = userEvent.setup();

    // Mobile menu should be hidden initially
    const mobileMenu = screen.queryByTestId('mobile-menu');
    expect(mobileMenu).not.toBeInTheDocument();

    // Click hamburger menu
    const menuButton = screen.getByRole('button', { name: /menu/i });
    await user.click(menuButton);

    // Mobile menu should be visible
    expect(screen.getByTestId('mobile-menu')).toBeInTheDocument();

    // Click again to close
    await user.click(menuButton);
    expect(screen.queryByTestId('mobile-menu')).not.toBeInTheDocument();
  });
});
