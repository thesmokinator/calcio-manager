import { act, renderHook, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { useAsyncResource } from './useAsyncResource';

describe('useAsyncResource', () => {
  it('loads data successfully', async () => {
    const loader = vi.fn().mockResolvedValue(['item']);

    const { result } = renderHook(() => useAsyncResource(loader));

    expect(result.current.loading).toBe(true);
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.data).toEqual(['item']);
    expect(result.current.error).toBe('');
    expect(loader).toHaveBeenCalledTimes(1);
  });

  it('stores loader errors as strings', async () => {
    const loader = vi.fn().mockRejectedValue(new Error('boom'));

    const { result } = renderHook(() => useAsyncResource(loader));

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.data).toBeNull();
    expect(result.current.error).toBe('Error: boom');
  });

  it('reloads data on demand', async () => {
    const loader = vi.fn()
      .mockResolvedValueOnce(1)
      .mockResolvedValueOnce(2);

    const { result } = renderHook(() => useAsyncResource(loader));

    await waitFor(() => expect(result.current.data).toBe(1));

    act(() => result.current.reload());

    await waitFor(() => expect(result.current.data).toBe(2));
    expect(loader).toHaveBeenCalledTimes(2);
  });
});
