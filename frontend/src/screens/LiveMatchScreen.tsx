import { useEffect, useMemo, useState } from 'react';
import { api } from '../api/tauri';
import { Panel } from '../components/Panel';
import type { MatchEventDto, PlayedMatchDto, PlayMatchDayResultDto } from '../types';

const keyEvents = new Set([
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

interface LiveMatchScreenProps {
  onBack: () => void;
}

export function LiveMatchScreen({ onBack }: LiveMatchScreenProps) {
  const [result, setResult] = useState<PlayMatchDayResultDto | null>(null);
  const [error, setError] = useState('');
  const [eventIndex, setEventIndex] = useState(0);
  const [paused, setPaused] = useState(false);
  const [activeTab, setActiveTab] = useState<'events' | 'results'>('events');

  useEffect(() => {
    api.playNextMatch()
      .then((data) => {
        setResult(data);
        setEventIndex(0);
      })
      .catch((err) => setError(String(err)));
  }, []);

  const match = result?.human_match ?? null;
  const events = match?.events ?? [];
  const currentEvent = events[Math.min(eventIndex, Math.max(events.length - 1, 0))];
  const finished = Boolean(match && events.length > 0 && eventIndex >= events.length - 1);

  useEffect(() => {
    if (!match || paused || finished) return;
    const timeout = window.setTimeout(() => {
      setEventIndex((current) => Math.min(current + 1, events.length - 1));
    }, currentEvent?.event_type === 'gol' ? 1100 : 280);
    return () => window.clearTimeout(timeout);
  }, [match, events.length, eventIndex, currentEvent?.event_type, paused, finished]);

  const visibleEvents = useMemo(() => {
    return events
      .slice(0, eventIndex + 1)
      .filter((event) => keyEvents.has(event.event_type))
      .slice(-18)
      .reverse();
  }, [events, eventIndex]);

  if (error) {
    return (
      <main className="screen stack-screen">
        <div className="error-box">{error}</div>
        <button className="ghost-button" onClick={onBack}>← Hub</button>
      </main>
    );
  }

  if (!result) {
    return <main className="screen stack-screen"><p>Simulazione backend in corso...</p></main>;
  }

  if (result.season_completed || !match) {
    return (
      <main className="screen stack-screen">
        <div className="screen-header">
          <button className="ghost-button" onClick={onBack}>← Hub</button>
          <h2>Stagione completata</h2>
        </div>
        <Panel title="Fine stagione">
          <p>La stagione è terminata: il backend Rust ha generato automaticamente il nuovo calendario. Torna all’hub per continuare.</p>
        </Panel>
      </main>
    );
  }

  const homeGoals = finished ? match.home_goals : currentEvent?.home_goals ?? 0;
  const awayGoals = finished ? match.away_goals : currentEvent?.away_goals ?? 0;
  const hasPenaltyScore = finished && match.home_penalty_goals != null && match.away_penalty_goals != null;

  return (
    <main className="screen live-screen">
      <div className="match-scoreboard">
        <div className="match-team home">{match.home_team}</div>
        <div className={hasPenaltyScore ? 'match-score with-penalties' : 'match-score'}>
          <span className="match-score__regular">{homeGoals} - {awayGoals}</span>
          {hasPenaltyScore && (
            <span className="match-score__penalties">
              Rigori {match.home_penalty_goals} - {match.away_penalty_goals}
            </span>
          )}
        </div>
        <div className="match-team away">{match.away_team}</div>
      </div>

      <div className="match-meta">
        <span>Giornata {result.match_day}</span>
        <span>{currentEvent ? `${currentEvent.minute}'` : '0\''}</span>
        <span>{finished ? 'Risultato finale' : paused ? 'In pausa' : 'Live'}</span>
      </div>

      <div className="live-layout live-layout--tabs">
        <Panel title="Commento live" className="commentary-panel">
          <div className={currentEvent?.event_type === 'gol' ? 'main-commentary goal' : 'main-commentary'}>
            {currentEvent?.commentary ?? 'In attesa del fischio d’inizio...'}
          </div>
          <div className="live-controls">
            <button className="secondary-button" disabled={finished} onClick={() => setPaused((value) => !value)}>
              {paused ? 'Riprendi' : 'Pausa'}
            </button>
            <button className="ghost-button" disabled={finished} onClick={() => setEventIndex(events.length - 1)}>
              Salta al finale
            </button>
            <button className="primary-button" disabled={!finished} onClick={onBack}>
              Continua
            </button>
          </div>
        </Panel>

        <div className="live-bottom-layout">
          <Panel title="Statistiche" className="stats-panel">
            <MatchStats match={match} />
          </Panel>

          <Panel title="Dettagli giornata" className="match-details-panel">
            <div className="tab-bar" role="tablist" aria-label="Dettagli partita">
              <button
                className={activeTab === 'events' ? 'tab-button active' : 'tab-button'}
                role="tab"
                aria-selected={activeTab === 'events'}
                onClick={() => setActiveTab('events')}
              >
                Eventi chiave
              </button>
              <button
                className={activeTab === 'results' ? 'tab-button active' : 'tab-button'}
                role="tab"
                aria-selected={activeTab === 'results'}
                onClick={() => setActiveTab('results')}
              >
                Altri risultati
              </button>
            </div>

            {activeTab === 'events' ? (
              <div className="event-feed tab-panel" role="tabpanel">
                {visibleEvents.map((event, index) => <EventRow key={`${event.minute}-${event.event_type}-${index}`} event={event} />)}
              </div>
            ) : (
              <div className="other-results tab-panel" role="tabpanel">
                {result.simulated_matches
                  .filter((item) => item.id !== match.id)
                  .map((item) => (
                    <div key={item.id}>
                      <span>{item.home_team}</span>
                      <strong>{item.score}</strong>
                      <span>{item.away_team}</span>
                    </div>
                  ))}
              </div>
            )}
          </Panel>
        </div>
      </div>
    </main>
  );
}

function EventRow({ event }: { event: MatchEventDto }) {
  return (
    <div className={event.event_type === 'gol' ? 'event-row goal' : 'event-row'}>
      <strong>{event.minute}'</strong>
      <span>{event.commentary}</span>
    </div>
  );
}

function MatchStats({ match }: { match: PlayedMatchDto }) {
  return (
    <div className="match-stats">
      <StatLine label="Possesso" home={`${match.home_possession.toFixed(1)}%`} away={`${match.away_possession.toFixed(1)}%`} />
      <StatLine label="Tiri" home={match.home_shots} away={match.away_shots} />
      <StatLine label="Tiri in porta" home={match.home_shots_on_target} away={match.away_shots_on_target} />
      <StatLine label="Falli" home={match.home_fouls} away={match.away_fouls} />
      <StatLine label="Corner" home={match.home_corners} away={match.away_corners} />
    </div>
  );
}

function StatLine({ label, home, away }: { label: string; home: string | number; away: string | number }) {
  return (
    <div className="stat-line">
      <strong>{home}</strong>
      <span>{label}</span>
      <strong>{away}</strong>
    </div>
  );
}
