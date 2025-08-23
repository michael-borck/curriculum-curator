import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import App from '../../App';
import { api } from '../../services/api';

// Mock the API
vi.mock('../../services/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    defaults: {
      headers: {
        common: {},
      },
    },
  },
}));

// Mock react-hot-toast
vi.mock('react-hot-toast', () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
  },
  Toaster: () => null,
}));

describe('E2E: Complete User Flow', () => {
  const user = userEvent.setup();

  beforeEach(() => {
    vi.clearAllMocks();
    // Clear localStorage
    localStorage.clear();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  const renderApp = () => {
    return render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    );
  };

  it('completes full user journey from login to course creation', async () => {
    // Step 1: User lands on login page
    renderApp();
    expect(screen.getByText(/curriculum curator/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/email address/i)).toBeInTheDocument();

    // Step 2: User logs in
    const mockLoginResponse = {
      data: {
        access_token: 'test-token-123',
        user: {
          id: '1',
          email: 'lecturer@university.edu',
          name: 'Dr. Smith',
          role: 'lecturer',
          isVerified: true,
          isActive: true,
        },
      },
    };

    (api.post as any).mockResolvedValueOnce(mockLoginResponse);

    await user.type(
      screen.getByPlaceholderText(/email address/i),
      'lecturer@university.edu'
    );
    await user.type(screen.getByPlaceholderText(/password/i), 'SecurePass123!');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    // Step 3: User is redirected to dashboard
    await waitFor(() => {
      expect(screen.getByText(/welcome.*dr\. smith/i)).toBeInTheDocument();
    });

    // Step 4: User navigates to courses
    const mockCourses = {
      data: [
        {
          id: '1',
          title: 'Existing Unit',
          description: 'A pre-existing course',
          durationWeeks: 12,
          objectives: ['Learn basics'],
          createdAt: '2024-01-01',
        },
      ],
    };

    (api.get as any).mockResolvedValueOnce(mockCourses);

    await user.click(screen.getByText(/courses/i));

    await waitFor(() => {
      expect(screen.getByText('Existing Unit')).toBeInTheDocument();
    });

    // Step 5: User creates a new course
    await user.click(screen.getByRole('button', { name: /create unit/i }));

    // Fill in unit details
    const modal = screen.getByRole('dialog');
    const withinModal = within(modal);

    await user.type(
      withinModal.getByPlaceholderText(/course title/i),
      'Introduction to AI'
    );
    await user.type(
      withinModal.getByPlaceholderText(/description/i),
      'Learn AI fundamentals'
    );
    await user.type(withinModal.getByPlaceholderText(/duration/i), '8');
    await user.type(
      withinModal.getByPlaceholderText(/objectives/i),
      'Understand ML basics\nBuild AI models'
    );

    const newCourse = {
      data: {
        id: '2',
        title: 'Introduction to AI',
        description: 'Learn AI fundamentals',
        durationWeeks: 8,
        objectives: ['Understand ML basics', 'Build AI models'],
        createdAt: new Date().toISOString(),
      },
    };

    (api.post as any).mockResolvedValueOnce(newCourse);
    (api.get as any).mockResolvedValueOnce({
      data: [...mockCourses.data, newCourse.data],
    });

    await user.click(withinModal.getByRole('button', { name: /save/i }));

    // Step 6: Verify course was created
    await waitFor(() => {
      expect(screen.getByText('Introduction to AI')).toBeInTheDocument();
    });

    // Step 7: User opens the new course
    await user.click(screen.getByText('Introduction to AI'));

    // Mock unit details
    (api.get as any).mockResolvedValueOnce({ data: newCourse.data });
    (api.get as any).mockResolvedValueOnce({ data: [] }); // modules
    (api.get as any).mockResolvedValueOnce({ data: [] }); // materials

    await waitFor(() => {
      expect(screen.getByText(/unit overview/i)).toBeInTheDocument();
      expect(screen.getByText(/8 weeks/i)).toBeInTheDocument();
    });

    // Step 8: User adds a material
    await user.click(screen.getByRole('button', { name: /add material/i }));

    const materialModal = screen.getByRole('dialog');
    const withinMaterialModal = within(materialModal);

    await user.type(
      withinMaterialModal.getByPlaceholderText(/material title/i),
      'Lecture 1: Introduction'
    );
    await user.selectOptions(
      withinMaterialModal.getByLabelText(/material type/i),
      'lecture'
    );

    const newMaterial = {
      data: {
        id: '1',
        title: 'Lecture 1: Introduction',
        type: 'lecture',
        content: '',
        unitId: '2',
        createdAt: new Date().toISOString(),
      },
    };

    (api.post as any).mockResolvedValueOnce(newMaterial);

    await user.click(
      withinMaterialModal.getByRole('button', { name: /create/i })
    );

    // Step 9: Verify material was added
    await waitFor(() => {
      expect(screen.getByText('Lecture 1: Introduction')).toBeInTheDocument();
    });

    // Step 10: User logs out
    await user.click(screen.getByRole('button', { name: /logout/i }));

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/email address/i)).toBeInTheDocument();
    });

    // Verify token was cleared
    expect(localStorage.getItem('token')).toBeNull();
  });

  it('handles error scenarios gracefully', async () => {
    renderApp();

    // Scenario 1: Login with invalid credentials
    (api.post as any).mockRejectedValueOnce({
      response: {
        data: {
          detail: 'Invalid email or password',
        },
        status: 401,
      },
    });

    await user.type(
      screen.getByPlaceholderText(/email address/i),
      'wrong@email.com'
    );
    await user.type(screen.getByPlaceholderText(/password/i), 'wrongpass');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(
        screen.getByText(/invalid email or password/i)
      ).toBeInTheDocument();
    });

    // Clear error
    await user.clear(screen.getByPlaceholderText(/email address/i));

    // Scenario 2: Network error during course fetch
    const mockLoginResponse = {
      data: {
        access_token: 'test-token',
        user: {
          id: '1',
          email: 'test@test.com',
          name: 'Test User',
          role: 'lecturer',
        },
      },
    };

    (api.post as any).mockResolvedValueOnce(mockLoginResponse);

    await user.type(
      screen.getByPlaceholderText(/email address/i),
      'test@test.com'
    );
    await user.type(screen.getByPlaceholderText(/password/i), 'password');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText(/welcome/i)).toBeInTheDocument();
    });

    // Navigate to courses with network error
    (api.get as any).mockRejectedValueOnce(new Error('Network error'));

    await user.click(screen.getByText(/courses/i));

    await waitFor(() => {
      expect(screen.getByText(/failed to load courses/i)).toBeInTheDocument();
    });

    // Retry button should be available
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
  });

  it('handles admin user flow', async () => {
    renderApp();

    // Admin login
    const mockAdminResponse = {
      data: {
        access_token: 'admin-token',
        user: {
          id: '1',
          email: 'admin@university.edu',
          name: 'Admin User',
          role: 'admin',
          isVerified: true,
          isActive: true,
        },
      },
    };

    (api.post as any).mockResolvedValueOnce(mockAdminResponse);

    await user.type(
      screen.getByPlaceholderText(/email address/i),
      'admin@university.edu'
    );
    await user.type(screen.getByPlaceholderText(/password/i), 'AdminPass123!');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    // Admin should see admin dashboard
    await waitFor(() => {
      expect(screen.getByText(/admin dashboard/i)).toBeInTheDocument();
      expect(screen.getByText(/user management/i)).toBeInTheDocument();
      expect(screen.getByText(/system settings/i)).toBeInTheDocument();
    });

    // Navigate to user management
    (api.get as any).mockResolvedValueOnce({
      data: {
        users: [
          {
            id: '2',
            email: 'user@test.com',
            name: 'Regular User',
            role: 'lecturer',
            isActive: true,
          },
        ],
        total: 1,
      },
    });

    await user.click(screen.getByText(/user management/i));

    await waitFor(() => {
      expect(screen.getByText('user@test.com')).toBeInTheDocument();
    });

    // Admin can deactivate user
    await user.click(screen.getByRole('button', { name: /deactivate/i }));

    (api.put as any).mockResolvedValueOnce({
      data: { success: true },
    });

    // Confirm deactivation
    await user.click(screen.getByRole('button', { name: /confirm/i }));

    await waitFor(() => {
      expect(api.put).toHaveBeenCalledWith(
        expect.stringContaining('/users/2/status')
      );
    });
  });
});
