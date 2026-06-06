import type { GameHubDto } from '../types';

export function defaultSaveSlot(hub: GameHubDto) {
  const team = hub.team.name
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/gi, '_')
    .replace(/^_+|_+$/g, '');
  return `${team || 'save'}_${hub.summary.season_year}`;
}
