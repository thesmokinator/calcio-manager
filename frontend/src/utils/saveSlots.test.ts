import { describe, expect, it } from 'vitest';
import type { GameHubDto } from '../types';
import { defaultSaveSlot } from './saveSlots';

function hubWithTeamName(teamName: string): GameHubDto {
  return {
    summary: {
      team_name: teamName,
      comune: 'Barasso',
      province: 'Varese',
      region: 'Lombardia',
      season_year: '2026-2027',
      num_groups: 1,
      human_team_id: 'team-1',
      current_match_day: 1,
      total_match_days: 14,
    },
    team: {
      id: 'team-1',
      name: teamName,
      city: 'Barasso',
      province: 'Varese',
      stadium_name: 'Campo',
      colors: ['rosso', 'blu'],
      average_overall: 10,
      squad_count: 14,
      available_count: 14,
      injured_count: 0,
      suspended_count: 0,
    },
    competition_name: 'Girone A',
    next_match: null,
    last_result: null,
    standings: [],
  };
}

describe('defaultSaveSlot', () => {
  it('normalizes team name and appends season', () => {
    expect(defaultSaveSlot(hubWithTeamName('ASD Barassese'))).toBe('asd_barassese_2026-2027');
  });

  it('falls back to save for punctuation-only names', () => {
    expect(defaultSaveSlot(hubWithTeamName('!!!'))).toBe('save_2026-2027');
  });
});
