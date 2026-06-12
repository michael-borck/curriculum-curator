import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import type { AxiosAdapter, AxiosResponse } from 'axios';
import api, { generateContentStream } from './api';

const echoAdapter: AxiosAdapter = config =>
  Promise.resolve({
    data: {},
    status: 200,
    statusText: 'OK',
    headers: {},
    config,
  } as AxiosResponse);

describe('api client', () => {
  const originalAdapter = api.defaults.adapter;

  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    if (originalAdapter !== undefined) {
      api.defaults.adapter = originalAdapter;
    }
    vi.restoreAllMocks();
  });

  describe('request interceptor', () => {
    it('attaches a Bearer token from localStorage', async () => {
      localStorage.setItem('token', 'abc123');
      api.defaults.adapter = echoAdapter;

      const response = await api.get('/units');

      expect(response.config.headers.Authorization).toBe('Bearer abc123');
    });

    it('sends no Authorization header without a token', async () => {
      api.defaults.adapter = echoAdapter;

      const response = await api.get('/units');

      expect(response.config.headers.Authorization).toBeUndefined();
    });
  });

  describe('response interceptor', () => {
    it('clears the stored token on a 401 response', async () => {
      localStorage.setItem('token', 'expired');
      api.defaults.adapter = () =>
        Promise.reject({ response: { status: 401 } });

      await expect(api.get('/units')).rejects.toMatchObject({
        response: { status: 401 },
      });
      expect(localStorage.getItem('token')).toBeNull();
    });

    it('keeps the token on non-401 errors', async () => {
      localStorage.setItem('token', 'still-valid');
      api.defaults.adapter = () =>
        Promise.reject({ response: { status: 500 } });

      await expect(api.get('/units')).rejects.toMatchObject({
        response: { status: 500 },
      });
      expect(localStorage.getItem('token')).toBe('still-valid');
    });
  });
});

describe('generateContentStream', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  const sseResponse = (chunks: string[]): Response => {
    const encoder = new TextEncoder();
    let index = 0;
    return {
      ok: true,
      body: {
        getReader: () => ({
          read: (): Promise<{
            done: boolean;
            value: Uint8Array | undefined;
          }> =>
            index < chunks.length
              ? Promise.resolve({
                  done: false,
                  value: encoder.encode(chunks[index++]),
                })
              : Promise.resolve({ done: true, value: undefined }),
        }),
      },
    } as unknown as Response;
  };

  it('emits parsed SSE content chunks and completes', async () => {
    vi.spyOn(window, 'fetch').mockResolvedValue(
      sseResponse([
        'data: {"content":"Hello"}\n',
        'data: {"content":" world"}\n',
      ])
    );
    const onChunk = vi.fn();
    const onComplete = vi.fn();
    const onError = vi.fn();

    await generateContentStream(
      'notes',
      'inquiry-based',
      'Recursion',
      onChunk,
      onComplete,
      onError
    );

    expect(onChunk.mock.calls.map(call => call[0])).toEqual([
      'Hello',
      ' world',
    ]);
    expect(onComplete).toHaveBeenCalledOnce();
    expect(onError).not.toHaveBeenCalled();
  });

  it('skips malformed SSE lines without failing', async () => {
    vi.spyOn(window, 'fetch').mockResolvedValue(
      sseResponse(['data: not-json\n', 'data: {"content":"ok"}\n'])
    );
    const onChunk = vi.fn();
    const onComplete = vi.fn();

    await generateContentStream(
      'notes',
      'inquiry-based',
      'Recursion',
      onChunk,
      onComplete
    );

    expect(onChunk).toHaveBeenCalledExactlyOnceWith('ok');
    expect(onComplete).toHaveBeenCalledOnce();
  });

  it('reports an error for a non-OK HTTP response', async () => {
    vi.spyOn(window, 'fetch').mockResolvedValue({
      ok: false,
      status: 500,
    } as Response);
    const onChunk = vi.fn();
    const onError = vi.fn();

    await generateContentStream(
      'notes',
      'inquiry-based',
      'Recursion',
      onChunk,
      undefined,
      onError
    );

    expect(onChunk).not.toHaveBeenCalled();
    expect(onError).toHaveBeenCalledOnce();
    expect(onError.mock.calls[0]?.[0]).toBeInstanceOf(Error);
  });
});
