import type { MatchEventDto } from '../types';

export const keyEventTypes = new Set([
  'calcio_inizio',
  'gol',
  'occasione',
  'parata',
  'tiro_fuori',
  'palo',
  'fallo',
  'ammonizione',
  'espulsione',
  'intervallo',
  'fine_partita',
  'inizio_rigori',
  'rigore_segnato',
  'rigore_sbagliato',
  'rigore_parato',
  'calcio_angolo',
]);

export function visibleKeyEvents(events: MatchEventDto[], eventIndex: number, limit = 18) {
  return events
    .slice(0, eventIndex + 1)
    .filter((event) => keyEventTypes.has(event.event_type))
    .slice(-limit)
    .reverse();
}

export function eventDelayMs(event?: MatchEventDto) {
  return event?.event_type === 'gol' ? 1100 : 280;
}
