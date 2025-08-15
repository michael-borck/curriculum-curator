import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import RichTextEditor from './RichTextEditor';

describe('RichTextEditor Component', () => {
  const mockOnChange = vi.fn();
  const defaultProps = {
    value: '',
    onChange: mockOnChange,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderEditor = (props = {}) => {
    return render(
      <RichTextEditor {...defaultProps} {...props} />
    );
  };

  it('renders editor with toolbar', () => {
    renderEditor();
    
    // Check for toolbar buttons
    expect(screen.getByRole('button', { name: /bold/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /italic/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /underline/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /bullet list/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /ordered list/i })).toBeInTheDocument();
  });

  it('renders with initial content', () => {
    const initialContent = '<p>Hello World</p>';
    renderEditor({ value: initialContent });
    
    expect(screen.getByText('Hello World')).toBeInTheDocument();
  });

  it('calls onChange when content is modified', async () => {
    renderEditor();
    const user = userEvent.setup();
    
    const editor = screen.getByRole('textbox');
    await user.type(editor, 'New content');
    
    await waitFor(() => {
      expect(mockOnChange).toHaveBeenCalled();
    });
  });

  it('applies bold formatting', async () => {
    renderEditor({ value: '<p>Test text</p>' });
    const user = userEvent.setup();
    
    // Select text
    const editor = screen.getByRole('textbox');
    await user.tripleClick(editor);
    
    // Click bold button
    const boldButton = screen.getByRole('button', { name: /bold/i });
    await user.click(boldButton);
    
    await waitFor(() => {
      expect(mockOnChange).toHaveBeenCalledWith(
        expect.stringContaining('<strong>')
      );
    });
  });

  it('creates a bullet list', async () => {
    renderEditor();
    const user = userEvent.setup();
    
    const bulletButton = screen.getByRole('button', { name: /bullet list/i });
    await user.click(bulletButton);
    
    const editor = screen.getByRole('textbox');
    await user.type(editor, 'Item 1');
    
    await waitFor(() => {
      expect(mockOnChange).toHaveBeenCalledWith(
        expect.stringContaining('<ul>')
      );
    });
  });

  it('inserts a table', async () => {
    renderEditor();
    const user = userEvent.setup();
    
    const tableButton = screen.getByRole('button', { name: /table/i });
    await user.click(tableButton);
    
    await waitFor(() => {
      expect(mockOnChange).toHaveBeenCalledWith(
        expect.stringContaining('<table>')
      );
    });
  });

  it('handles heading levels', async () => {
    renderEditor();
    const user = userEvent.setup();
    
    const headingDropdown = screen.getByRole('button', { name: /heading/i });
    await user.click(headingDropdown);
    
    const h1Option = screen.getByText(/heading 1/i);
    await user.click(h1Option);
    
    const editor = screen.getByRole('textbox');
    await user.type(editor, 'Main Title');
    
    await waitFor(() => {
      expect(mockOnChange).toHaveBeenCalledWith(
        expect.stringContaining('<h1>')
      );
    });
  });

  it('supports undo and redo', async () => {
    renderEditor();
    const user = userEvent.setup();
    
    const editor = screen.getByRole('textbox');
    await user.type(editor, 'First text');
    
    const undoButton = screen.getByRole('button', { name: /undo/i });
    await user.click(undoButton);
    
    await waitFor(() => {
      expect(mockOnChange).toHaveBeenCalledWith('');
    });
    
    const redoButton = screen.getByRole('button', { name: /redo/i });
    await user.click(redoButton);
    
    await waitFor(() => {
      expect(mockOnChange).toHaveBeenCalledWith(
        expect.stringContaining('First text')
      );
    });
  });

  it('shows pedagogy hints when pedagogy is selected', () => {
    renderEditor({ pedagogy: 'constructivist' });
    
    expect(screen.getByText(/constructivist approach/i)).toBeInTheDocument();
  });

  it('disables editor when readonly prop is true', () => {
    renderEditor({ readonly: true });
    
    const editor = screen.getByRole('textbox');
    expect(editor).toHaveAttribute('contenteditable', 'false');
    
    // Toolbar buttons should be disabled
    const boldButton = screen.getByRole('button', { name: /bold/i });
    expect(boldButton).toBeDisabled();
  });

  it('handles code block insertion', async () => {
    renderEditor();
    const user = userEvent.setup();
    
    const codeButton = screen.getByRole('button', { name: /code block/i });
    await user.click(codeButton);
    
    await waitFor(() => {
      expect(mockOnChange).toHaveBeenCalledWith(
        expect.stringContaining('<pre><code>')
      );
    });
  });

  it('supports text alignment', async () => {
    renderEditor({ value: '<p>Align me</p>' });
    const user = userEvent.setup();
    
    // Select text
    const editor = screen.getByRole('textbox');
    await user.tripleClick(editor);
    
    const alignButton = screen.getByRole('button', { name: /align center/i });
    await user.click(alignButton);
    
    await waitFor(() => {
      expect(mockOnChange).toHaveBeenCalledWith(
        expect.stringContaining('text-align: center')
      );
    });
  });
});