import { CareerLayout } from '../components/CareerLayout';
import { Panel } from '../components/Panel';

interface GameHubScreenProps {
  onHub: () => void;
  onMenu: () => void;
  onSquad: () => void;
  onStandings: () => void;
  onCalendar: () => void;
  onPlayMatch: () => void;
}

export function GameHubScreen({ onHub, onMenu, onSquad, onStandings, onCalendar, onPlayMatch }: GameHubScreenProps) {
  return (
    <CareerLayout
      active="hub"
      onHub={onHub}
      onMenu={onMenu}
      onSquad={onSquad}
      onStandings={onStandings}
      onCalendar={onCalendar}
      onPlayMatch={onPlayMatch}
    >
      {(hub) => (
        <div className="hub-grid">
          <Panel title="Prossima partita">
            {hub.next_match ? (
              <div className="score-card">
                <span>Giornata {hub.next_match.match_day}</span>
                <strong>{hub.next_match.opponent}</strong>
                <small>{hub.next_match.location} · {hub.next_match.date ?? 'data da definire'}</small>
                <div className="fixture-line">{hub.next_match.home_team} vs {hub.next_match.away_team}</div>
              </div>
            ) : <p>Stagione completata.</p>}
          </Panel>

          <Panel title="Classifica rapida">
            <table className="compact-table">
              <tbody>
                {hub.standings.slice(0, 6).map((row) => (
                  <tr key={row.team_id} className={row.is_human ? 'human-row' : ''}>
                    <td>{row.position}</td>
                    <td>{row.team_name}</td>
                    <td>{row.points}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Panel>

          <Panel title="Ultimo risultato">
            {hub.last_result ? (
              <div className="score-card">
                <strong>{hub.last_result.score}</strong>
                <small>{hub.last_result.home_team} · {hub.last_result.away_team}</small>
              </div>
            ) : <p>Nessun risultato disponibile.</p>}
          </Panel>

          <Panel title="Rosa">
            <div className="stat-list">
              <div><strong>{hub.team.squad_count}</strong><span>Giocatori</span></div>
              <div><strong>{hub.team.available_count}</strong><span>Disponibili</span></div>
              <div><strong>{hub.team.average_overall.toFixed(1)}</strong><span>Media OVR</span></div>
              <div><strong>{hub.team.stadium_name}</strong><span>Campo</span></div>
            </div>
          </Panel>
        </div>
      )}
    </CareerLayout>
  );
}
