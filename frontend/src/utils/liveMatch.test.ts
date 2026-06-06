import { describe, expect, it } from 'vitest';
import type { MatchEventDto, MatchEventType } from '../types';
import { eventDelayMs, visibleKeyEvents } from './liveMatch';

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

describe('liveMatch utils', () => {
  it('filters, limits and reverses visible key events', () => {
    const events = [
      event('calcio_inizio', 0),
      event('possesso', 3),
      event('gol', 10),
      event('fallo', 12),
    ];

    expect(visibleKeyEvents(events, 3, 2).map((item) => item.event_type)).toEqual(['fallo', 'gol']);
  });

  it('uses a longer delay for goals', () => {
    expect(eventDelayMs(event('gol', 10))).toBe(1100);
    expect(eventDelayMs(event('fallo', 11))).toBe(280);
  });
});
