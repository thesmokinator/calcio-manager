import { useState } from 'react';
import type { MatchEventDto, PlayedMatchDto } from '../types';
import { Panel } from './Panel';

export function MatchScoreboard({ match, homeGoals, awayGoals, finished }: {
  match: PlayedMatchDto;
  homeGoals: number;
  awayGoals: number;
  finished: boolean;
}) {
  const hasPenaltyScore = finished && match.home_penalty_goals != null && match.away_penalty_goals != null;

  return (
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
  );
}

export function MatchMeta({ matchDay, minute, status }: { matchDay?: number | null; minute: number; status: string }) {
  return (
    <div className="match-meta">
      <span>Giornata {matchDay}</span>
      <span>{minute}'</span>
      <span>{status}</span>
    </div>
  );
}

export function LiveCommentaryPanel({
  currentEvent,
  finished,
  paused,
  onTogglePause,
  onSkipToFinal,
  onContinue,
}: {
  currentEvent?: MatchEventDto;
  finished: boolean;
  paused: boolean;
  onTogglePause: () => void;
  onSkipToFinal: () => void;
  onContinue: () => void;
}) {
  return (
    <Panel title="Commento live" className="commentary-panel">
      <div className={currentEvent?.event_type === 'gol' ? 'main-commentary goal' : 'main-commentary'}>
        {currentEvent?.commentary ?? 'In attesa del fischio d’inizio...'}
      </div>
      <div className="live-controls">
        <button className="secondary-button" disabled={finished} onClick={onTogglePause}>
          {paused ? 'Riprendi' : 'Pausa'}
        </button>
        <button className="ghost-button" disabled={finished} onClick={onSkipToFinal}>
          Salta al finale
        </button>
        <button className="primary-button" disabled={!finished} onClick={onContinue}>
          Continua
        </button>
      </div>
    </Panel>
  );
}

export function MatchStatsPanel({ match }: { match: PlayedMatchDto }) {
  return (
    <Panel title="Statistiche" className="stats-panel">
      <div className="match-stats">
        <StatLine label="Possesso" home={`${match.home_possession.toFixed(1)}%`} away={`${match.away_possession.toFixed(1)}%`} />
        <StatLine label="Tiri" home={match.home_shots} away={match.away_shots} />
        <StatLine label="Tiri in porta" home={match.home_shots_on_target} away={match.away_shots_on_target} />
        <StatLine label="Falli" home={match.home_fouls} away={match.away_fouls} />
        <StatLine label="Corner" home={match.home_corners} away={match.away_corners} />
      </div>
    </Panel>
  );
}

export function MatchDetailsTabs({ visibleEvents, simulatedMatches, currentMatchId }: {
  visibleEvents: MatchEventDto[];
  simulatedMatches: PlayedMatchDto[];
  currentMatchId: string;
}) {
  const [activeTab, setActiveTab] = useState<'events' | 'results'>('events');

  return (
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
          {simulatedMatches
            .filter((item) => item.id !== currentMatchId)
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

function StatLine({ label, home, away }: { label: string; home: string | number; away: string | number }) {
  return (
    <div className="stat-line">
      <strong>{home}</strong>
      <span>{label}</span>
      <strong>{away}</strong>
    </div>
  );
}
