import { describe, expect, it } from 'vitest';
import { readableTextColor, teamColorHex } from './teamColors';

describe('teamColors', () => {
  it('maps known Italian color names to hex values', () => {
    expect(teamColorHex('rosso')).toBe('#dc2626');
    expect(teamColorHex('blu')).toBe('#2563eb');
  });

  it('falls back for unknown color names', () => {
    expect(teamColorHex('sconosciuto')).toBe('#475569');
  });

  it('chooses readable text for dark and light backgrounds', () => {
    expect(readableTextColor('#000000')).toBe('#ffffff');
    expect(readableTextColor('#ffffff')).toBe('#10141f');
  });
});
