import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import CourseManager from './CourseManager';
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

// Mock react-hot-toast
vi.mock('react-hot-toast', () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

describe('CourseManager Component', () => {
  const mockCourses = [
    {
      id: '1',
      title: 'Introduction to React',
      description: 'Learn React basics',
      duration_weeks: 8,
      objectives: ['Learn components', 'Understand hooks'],
      created_at: '2024-01-01',
    },
    {
      id: '2',
      title: 'Advanced TypeScript',
      description: 'Master TypeScript',
      duration_weeks: 6,
      objectives: ['Type safety', 'Generics'],
      created_at: '2024-01-15',
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    (api.get as any).mockResolvedValue({ data: mockCourses });
  });

  const renderCourseManager = () => {
    return render(
      <BrowserRouter>
        <CourseManager />
      </BrowserRouter>
    );
  };

  it('renders course list on load', async () => {
    renderCourseManager();
    
    await waitFor(() => {
      expect(screen.getByText('Introduction to React')).toBeInTheDocument();
      expect(screen.getByText('Advanced TypeScript')).toBeInTheDocument();
    });
    
    expect(api.get).toHaveBeenCalledWith('/courses/');
  });

  it('displays loading state while fetching courses', () => {
    (api.get as any).mockImplementation(() => new Promise(() => {}));
    renderCourseManager();
    
    expect(screen.getByText(/loading courses/i)).toBeInTheDocument();
  });

  it('displays error message on fetch failure', async () => {
    (api.get as any).mockRejectedValue(new Error('Network error'));
    renderCourseManager();
    
    await waitFor(() => {
      expect(screen.getByText(/failed to load courses/i)).toBeInTheDocument();
    });
  });

  it('opens create course modal', async () => {
    renderCourseManager();
    const user = userEvent.setup();
    
    await waitFor(() => {
      expect(screen.getByText('Introduction to React')).toBeInTheDocument();
    });
    
    const createButton = screen.getByRole('button', { name: /create course/i });
    await user.click(createButton);
    
    expect(screen.getByText(/new course/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/course title/i)).toBeInTheDocument();
  });

  it('creates a new course', async () => {
    const newCourse = {
      id: '3',
      title: 'New Course',
      description: 'New description',
      duration_weeks: 4,
      objectives: ['Objective 1'],
    };
    
    (api.post as any).mockResolvedValue({ data: newCourse });
    
    renderCourseManager();
    const user = userEvent.setup();
    
    await waitFor(() => {
      expect(screen.getByText('Introduction to React')).toBeInTheDocument();
    });
    
    // Open modal
    const createButton = screen.getByRole('button', { name: /create course/i });
    await user.click(createButton);
    
    // Fill form
    await user.type(screen.getByPlaceholderText(/course title/i), 'New Course');
    await user.type(screen.getByPlaceholderText(/description/i), 'New description');
    await user.type(screen.getByPlaceholderText(/duration/i), '4');
    await user.type(screen.getByPlaceholderText(/objectives/i), 'Objective 1');
    
    // Submit
    const submitButton = screen.getByRole('button', { name: /save/i });
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/courses/', expect.objectContaining({
        title: 'New Course',
        description: 'New description',
        duration_weeks: 4,
      }));
    });
  });

  it('edits an existing course', async () => {
    renderCourseManager();
    const user = userEvent.setup();
    
    await waitFor(() => {
      expect(screen.getByText('Introduction to React')).toBeInTheDocument();
    });
    
    // Click edit button for first course
    const editButtons = screen.getAllByRole('button', { name: /edit/i });
    await user.click(editButtons[0]);
    
    // Modal should open with pre-filled data
    expect(screen.getByDisplayValue('Introduction to React')).toBeInTheDocument();
    
    // Update title
    const titleInput = screen.getByDisplayValue('Introduction to React');
    await user.clear(titleInput);
    await user.type(titleInput, 'Updated React Course');
    
    // Submit
    const saveButton = screen.getByRole('button', { name: /save/i });
    await user.click(saveButton);
    
    await waitFor(() => {
      expect(api.put).toHaveBeenCalledWith('/courses/1', expect.objectContaining({
        title: 'Updated React Course',
      }));
    });
  });

  it('deletes a course with confirmation', async () => {
    (api.delete as any).mockResolvedValue({ data: { success: true } });
    
    renderCourseManager();
    const user = userEvent.setup();
    
    await waitFor(() => {
      expect(screen.getByText('Introduction to React')).toBeInTheDocument();
    });
    
    // Click delete button
    const deleteButtons = screen.getAllByRole('button', { name: /delete/i });
    await user.click(deleteButtons[0]);
    
    // Confirmation dialog should appear
    expect(screen.getByText(/are you sure/i)).toBeInTheDocument();
    
    // Confirm deletion
    const confirmButton = screen.getByRole('button', { name: /confirm/i });
    await user.click(confirmButton);
    
    await waitFor(() => {
      expect(api.delete).toHaveBeenCalledWith('/courses/1');
    });
  });

  it('filters courses by search term', async () => {
    renderCourseManager();
    const user = userEvent.setup();
    
    await waitFor(() => {
      expect(screen.getByText('Introduction to React')).toBeInTheDocument();
      expect(screen.getByText('Advanced TypeScript')).toBeInTheDocument();
    });
    
    // Search for 'React'
    const searchInput = screen.getByPlaceholderText(/search courses/i);
    await user.type(searchInput, 'React');
    
    await waitFor(() => {
      expect(screen.getByText('Introduction to React')).toBeInTheDocument();
      expect(screen.queryByText('Advanced TypeScript')).not.toBeInTheDocument();
    });
  });

  it('sorts courses by different criteria', async () => {
    renderCourseManager();
    const user = userEvent.setup();
    
    await waitFor(() => {
      expect(screen.getByText('Introduction to React')).toBeInTheDocument();
    });
    
    // Click sort dropdown
    const sortButton = screen.getByRole('button', { name: /sort/i });
    await user.click(sortButton);
    
    // Select 'Duration'
    const durationOption = screen.getByText(/duration/i);
    await user.click(durationOption);
    
    // Courses should be re-ordered
    const courseTitles = screen.getAllByTestId('course-title');
    expect(courseTitles[0]).toHaveTextContent('Advanced TypeScript'); // 6 weeks
    expect(courseTitles[1]).toHaveTextContent('Introduction to React'); // 8 weeks
  });

  it('displays course statistics', async () => {
    renderCourseManager();
    
    await waitFor(() => {
      expect(screen.getByText(/total courses: 2/i)).toBeInTheDocument();
      expect(screen.getByText(/total duration: 14 weeks/i)).toBeInTheDocument();
    });
  });
});