// Global type declarations for browser APIs

declare global {
  interface Window {
    confirm: (message?: string) => boolean;
    prompt: (message?: string, defaultValue?: string) => string | null;
  }
}

export {};
