import { act, renderHook } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { MatchEventDto, MatchEventType } from '../types';
import { useLiveMatchPlayback } from './useLiveMatchPlayback';

function event(event_type: MatchEventType, minute: number): MatchEventDto {
  return {
    minute,
    event_type,
    team_id: null,
    team_name: '',
    player_name: '',
    assist_name: '',
    commentary: `${minute}-${event_type}`,
    home_goals: 0,
    away_goals: 0,
  };
}

const events = [event('calcio_inizio', 0), event('fallo', 4), event('gol', 8)];

describe('useLiveMatchPlayback', () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it('advances events over time until finished', () => {
    vi.useFakeTimers();
    const { result } = renderHook(() => useLiveMatchPlayback(events));

    expect(result.current.eventIndex).toBe(0);

    act(() => vi.advanceTimersByTime(280));
    expect(result.current.eventIndex).toBe(1);

    act(() => vi.advanceTimersByTime(280));
    expect(result.current.eventIndex).toBe(2);
    expect(result.current.finished).toBe(true);
  });

  it('pauses and resumes playback', () => {
    vi.useFakeTimers();
    const { result } = renderHook(() => useLiveMatchPlayback(events));

    act(() => result.current.togglePaused());
    act(() => vi.advanceTimersByTime(280));
    expect(result.current.eventIndex).toBe(0);

    act(() => result.current.togglePaused());
    act(() => vi.advanceTimersByTime(280));
    expect(result.current.eventIndex).toBe(1);
  });

  it('skips to the final event', () => {
    const { result } = renderHook(() => useLiveMatchPlayback(events));

    act(() => result.current.skipToFinal());

    expect(result.current.eventIndex).toBe(2);
    expect(result.current.finished).toBe(true);
  });
});
