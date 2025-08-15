import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import AdminDashboard from './AdminDashboard';
import { api } from '../../services/api';

// Mock the API
vi.mock('../../services/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('AdminDashboard Component', () => {
  const mockStats = {
    total_users: 150,
    active_users: 142,
    total_courses: 45,
    total_materials: 320,
    recent_logins: 15,
    system_health: 'healthy',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderAdminDashboard = () => {
    return render(
      <BrowserRouter>
        <AdminDashboard />
      </BrowserRouter>
    );
  };

  it('renders admin dashboard with statistics', async () => {
    (api.get as any).mockResolvedValue({ data: mockStats });
    
    renderAdminDashboard();
    
    await waitFor(() => {
      expect(screen.getByText(/admin dashboard/i)).toBeInTheDocument();
      expect(screen.getByText(/150.*users/i)).toBeInTheDocument();
      expect(screen.getByText(/45.*courses/i)).toBeInTheDocument();
      expect(screen.getByText(/320.*materials/i)).toBeInTheDocument();
    });
    
    expect(api.get).toHaveBeenCalledWith('/admin/stats');
  });

  it('displays system health status', async () => {
    (api.get as any).mockResolvedValue({ data: mockStats });
    
    renderAdminDashboard();
    
    await waitFor(() => {
      expect(screen.getByText(/system.*healthy/i)).toBeInTheDocument();
    });
  });

  it('shows loading state while fetching data', () => {
    (api.get as any).mockImplementation(() => new Promise(() => {}));
    
    renderAdminDashboard();
    
    expect(screen.getByText(/loading dashboard/i)).toBeInTheDocument();
  });

  it('displays error message on API failure', async () => {
    (api.get as any).mockRejectedValue(new Error('API Error'));
    
    renderAdminDashboard();
    
    await waitFor(() => {
      expect(screen.getByText(/failed to load dashboard/i)).toBeInTheDocument();
    });
  });

  it('navigates to user management section', async () => {
    (api.get as any).mockResolvedValue({ data: mockStats });
    
    renderAdminDashboard();
    const user = userEvent.setup();
    
    await waitFor(() => {
      expect(screen.getByText(/user management/i)).toBeInTheDocument();
    });
    
    await user.click(screen.getByText(/user management/i));
    
    // Should show user management component
    expect(screen.getByText(/manage users/i)).toBeInTheDocument();
  });

  it('navigates to system settings', async () => {
    (api.get as any).mockResolvedValue({ data: mockStats });
    
    renderAdminDashboard();
    const user = userEvent.setup();
    
    await waitFor(() => {
      expect(screen.getByText(/system settings/i)).toBeInTheDocument();
    });
    
    await user.click(screen.getByText(/system settings/i));
    
    expect(screen.getByText(/configure system/i)).toBeInTheDocument();
  });

  it('shows recent activity log', async () => {
    const mockActivity = {
      ...mockStats,
      recent_activity: [
        {
          id: '1',
          user: 'john@example.com',
          action: 'login',
          timestamp: '2024-01-20T10:00:00Z',
        },
        {
          id: '2',
          user: 'jane@example.com',
          action: 'created_course',
          timestamp: '2024-01-20T09:30:00Z',
        },
      ],
    };
    
    (api.get as any).mockResolvedValue({ data: mockActivity });
    
    renderAdminDashboard();
    
    await waitFor(() => {
      expect(screen.getByText(/recent activity/i)).toBeInTheDocument();
      expect(screen.getByText('john@example.com')).toBeInTheDocument();
      expect(screen.getByText('jane@example.com')).toBeInTheDocument();
    });
  });

  it('refreshes dashboard data', async () => {
    (api.get as any).mockResolvedValue({ data: mockStats });
    
    renderAdminDashboard();
    const user = userEvent.setup();
    
    await waitFor(() => {
      expect(screen.getByText(/150.*users/i)).toBeInTheDocument();
    });
    
    // Update mock data
    const updatedStats = { ...mockStats, total_users: 155 };
    (api.get as any).mockResolvedValue({ data: updatedStats });
    
    // Click refresh button
    const refreshButton = screen.getByRole('button', { name: /refresh/i });
    await user.click(refreshButton);
    
    await waitFor(() => {
      expect(screen.getByText(/155.*users/i)).toBeInTheDocument();
    });
    
    expect(api.get).toHaveBeenCalledTimes(2);
  });

  it('displays quick actions panel', async () => {
    (api.get as any).mockResolvedValue({ data: mockStats });
    
    renderAdminDashboard();
    
    await waitFor(() => {
      expect(screen.getByText(/quick actions/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /add user/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /backup data/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /view logs/i })).toBeInTheDocument();
    });
  });
});