import { api } from '../api/tauri';
import { CareerLayout } from '../components/CareerLayout';
import { useAsyncResource } from '../hooks/useAsyncResource';
import type { StandingRowDto } from '../types';

interface StandingsScreenProps {
  onHub: () => void;
  onMenu: () => void;
  onSquad: () => void;
  onStandings: () => void;
  onCalendar: () => void;
  onPlayMatch: () => void;
}

export function StandingsScreen({ onHub, onMenu, onSquad, onStandings, onCalendar, onPlayMatch }: StandingsScreenProps) {
  const { data: standings, error, loading } = useAsyncResource<StandingRowDto[]>(() => api.getStandings());

  return (
    <CareerLayout
      active="standings"
      onHub={onHub}
      onMenu={onMenu}
      onSquad={onSquad}
      onStandings={onStandings}
      onCalendar={onCalendar}
      onPlayMatch={onPlayMatch}
    >
      {() => (
        <section className="career-content">
          <div className="screen-header slim">
            <h2>Classifica</h2>
          </div>
          {error && <div className="error-box">{error}</div>}
          {loading && <p>Caricamento classifica...</p>}
          {!loading && <div className="table-shell">
            <table className="data-table standings-table">
              <thead>
                <tr><th>Pos</th><th>Squadra</th><th>G</th><th>V</th><th>VR</th><th>LR</th><th>P</th><th>GF</th><th>GS</th><th>DR</th><th>PT</th></tr>
              </thead>
              <tbody>
                {(standings ?? []).map((row) => (
                  <tr key={row.team_id} className={row.is_human ? 'human-row' : ''}>
                    <td>{row.position}</td>
                    <td className="strong-cell">{row.team_name}</td>
                    <td>{row.played}</td>
                    <td>{row.wins}</td>
                    <td>{row.wins_penalties}</td>
                    <td>{row.losses_penalties}</td>
                    <td>{row.losses}</td>
                    <td>{row.goals_for}</td>
                    <td>{row.goals_against}</td>
                    <td>{row.goal_difference}</td>
                    <td className="points-cell">{row.points}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>}
        </section>
      )}
    </CareerLayout>
  );
}
