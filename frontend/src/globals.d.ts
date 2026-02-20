// Global type declarations for browser APIs

declare global {
  interface Window {
    confirm: (message?: string) => boolean;
    prompt: (message?: string, defaultValue?: string) => string | null;
    api?: {
      getOllamaInfo?: () => Promise<{
        installed: boolean;
        binaryPath: string | null;
      }>;
      saveFile?: (
        defaultName: string,
        data: ArrayBuffer | string
      ) => Promise<string | null>;
    };
  }
}

export {};
