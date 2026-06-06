import { api } from '../api/tauri';
import {
  LiveCommentaryPanel,
  MatchDetailsTabs,
  MatchMeta,
  MatchScoreboard,
  MatchStatsPanel,
} from '../components/LiveMatchPanels';
import { Panel } from '../components/Panel';
import { useAsyncResource } from '../hooks/useAsyncResource';
import { useLiveMatchPlayback } from '../hooks/useLiveMatchPlayback';
import type { PlayMatchDayResultDto } from '../types';

interface LiveMatchScreenProps {
  onBack: () => void;
}

export function LiveMatchScreen({ onBack }: LiveMatchScreenProps) {
  const { data: result, error, loading } = useAsyncResource<PlayMatchDayResultDto>(() => api.playNextMatch());
  const match = result?.human_match ?? null;
  const events = match?.events ?? [];
  const {
    currentEvent,
    finished,
    paused,
    visibleEvents,
    togglePaused,
    skipToFinal,
  } = useLiveMatchPlayback(events);

  if (error) {
    return (
      <main className="screen stack-screen">
        <div className="error-box">{error}</div>
        <button className="ghost-button" onClick={onBack}>← Hub</button>
      </main>
    );
  }

  if (loading || !result) {
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
  const status = finished ? 'Risultato finale' : paused ? 'In pausa' : 'Live';

  return (
    <main className="screen live-screen">
      <MatchScoreboard match={match} homeGoals={homeGoals} awayGoals={awayGoals} finished={finished} />
      <MatchMeta matchDay={result.match_day} minute={currentEvent?.minute ?? 0} status={status} />

      <div className="live-layout live-layout--tabs">
        <LiveCommentaryPanel
          currentEvent={currentEvent}
          finished={finished}
          paused={paused}
          onTogglePause={togglePaused}
          onSkipToFinal={skipToFinal}
          onContinue={onBack}
        />

        <div className="live-bottom-layout">
          <MatchStatsPanel match={match} />
          <MatchDetailsTabs
            visibleEvents={visibleEvents}
            simulatedMatches={result.simulated_matches}
            currentMatchId={match.id}
          />
        </div>
      </div>
    </main>
  );
}
