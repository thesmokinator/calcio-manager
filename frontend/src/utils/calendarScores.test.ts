import { describe, expect, it } from 'vitest';
import { formatPenaltyScore, parseCalendarScore } from './calendarScores';

describe('calendarScores', () => {
  it('returns null for missing scores', () => {
    expect(parseCalendarScore(null)).toBeNull();
    expect(parseCalendarScore(undefined)).toBeNull();
  });

  it('parses regular-time scores', () => {
    expect(parseCalendarScore('2 - 1')).toEqual({ regularScore: '2 - 1', penaltyScore: null });
  });

  it('parses penalty shootout scores', () => {
    expect(parseCalendarScore('1 - 1 (rig. 5-4)')).toEqual({
      regularScore: '1 - 1',
      penaltyScore: '5 - 4',
    });
  });

  it('normalizes penalty score spacing', () => {
    expect(formatPenaltyScore('3-1')).toBe('3 - 1');
    expect(formatPenaltyScore('6 - 7')).toBe('6 - 7');
  });
});
