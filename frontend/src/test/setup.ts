import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Node 26 exposes a global localStorage getter that returns undefined unless
// the process is started with --localstorage-file. Vitest's jsdom environment
// inherits that shadowed value, so provide an in-memory Storage for tests.
class MemoryStorage implements Storage {
  private store = new Map<string, string>();

  get length(): number {
    return this.store.size;
  }

  clear(): void {
    this.store.clear();
  }

  getItem(key: string): string | null {
    return this.store.has(key) ? this.store.get(key)! : null;
  }

  key(index: number): string | null {
    return Array.from(this.store.keys())[index] ?? null;
  }

  removeItem(key: string): void {
    this.store.delete(key);
  }

  setItem(key: string, value: string): void {
    this.store.set(key, String(value));
  }
}

for (const name of ['localStorage', 'sessionStorage'] as const) {
  if (typeof globalThis[name] === 'undefined') {
    const storage = new MemoryStorage();
    Object.defineProperty(globalThis, name, {
      value: storage,
      configurable: true,
      writable: true,
    });
    if (typeof window !== 'undefined') {
      Object.defineProperty(window, name, {
        value: storage,
        configurable: true,
        writable: true,
      });
    }
  }
}

// Global test setup
// Add any global test configuration here

// Mock environment variables if needed
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock IntersectionObserver
class MockIntersectionObserver implements IntersectionObserver {
  root: Element | Document | null = null;
  rootMargin: string = '';
  thresholds: ReadonlyArray<number> = [];

  constructor() {}
  observe() {
    return null;
  }
  disconnect() {
    return null;
  }
  unobserve() {
    return null;
  }
  takeRecords(): IntersectionObserverEntry[] {
    return [];
  }
}

(global as any).IntersectionObserver = MockIntersectionObserver;
