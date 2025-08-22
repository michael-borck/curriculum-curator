import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useAuthStore } from './authStore';

describe('AuthStore', () => {
  beforeEach(() => {
    // Reset the store state before each test
    const { result } = renderHook(() => useAuthStore());
    act(() => {
      result.current.logout();
    });
  });

  it('initializes with null user and not authenticated', () => {
    const { result } = renderHook(() => useAuthStore());

    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });

  it('handles login correctly', () => {
    const { result } = renderHook(() => useAuthStore());

    const mockUser = {
      id: '1',
      email: 'test@example.com',
      name: 'Test User',
      role: 'lecturer' as const,
      is_verified: true,
      is_active: true,
      createdAt: '2024-01-01',
    };

    act(() => {
      result.current.login(mockUser);
    });

    expect(result.current.user).toEqual(mockUser);
    expect(result.current.isAuthenticated).toBe(true);
  });

  it('handles logout correctly', () => {
    const { result } = renderHook(() => useAuthStore());

    // First login
    const mockUser = {
      id: '1',
      email: 'test@example.com',
      name: 'Test User',
      role: 'lecturer' as const,
      is_verified: true,
      is_active: true,
      createdAt: '2024-01-01',
    };

    act(() => {
      result.current.login(mockUser);
    });

    expect(result.current.isAuthenticated).toBe(true);

    // Then logout
    act(() => {
      result.current.logout();
    });

    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });

  it('preserves state across multiple hook instances', () => {
    const { result: result1 } = renderHook(() => useAuthStore());
    const { result: result2 } = renderHook(() => useAuthStore());

    const mockUser = {
      id: '1',
      email: 'test@example.com',
      name: 'Test User',
      role: 'lecturer' as const,
      is_verified: true,
      is_active: true,
      createdAt: '2024-01-01',
    };

    act(() => {
      result1.current.login(mockUser);
    });

    // Both instances should have the same state
    expect(result2.current.user).toEqual(mockUser);
    expect(result1.current.user).toEqual(result2.current.user);
    expect(result2.current.isAuthenticated).toBe(true);
  });

  it('handles admin user login', () => {
    const { result } = renderHook(() => useAuthStore());

    const mockAdminUser = {
      id: '2',
      email: 'admin@example.com',
      name: 'Admin User',
      role: 'admin' as const,
      is_verified: true,
      is_active: true,
      createdAt: '2024-01-01',
    };

    act(() => {
      result.current.login(mockAdminUser);
    });

    expect(result.current.user).toEqual(mockAdminUser);
    expect(result.current.user?.role).toBe('admin');
    expect(result.current.isAuthenticated).toBe(true);
  });
});
