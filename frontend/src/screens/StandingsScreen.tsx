import { useEffect, useState } from 'react';
import { api } from '../api/tauri';
import type { StandingRowDto } from '../types';

interface StandingsScreenProps {
  onBack: () => void;
}

export function StandingsScreen({ onBack }: StandingsScreenProps) {
  const [standings, setStandings] = useState<StandingRowDto[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    api.getStandings().then(setStandings).catch((err) => setError(String(err)));
  }, []);

  return (
    <main className="screen stack-screen">
      <div className="screen-header">
        <button className="ghost-button" onClick={onBack}>← Hub</button>
        <h2>Classifica</h2>
      </div>
      {error && <div className="error-box">{error}</div>}
      <div className="table-shell">
        <table className="data-table standings-table">
          <thead>
            <tr><th>Pos</th><th>Squadra</th><th>G</th><th>V</th><th>VR</th><th>LR</th><th>P</th><th>GF</th><th>GS</th><th>DR</th><th>PT</th></tr>
          </thead>
          <tbody>
            {standings.map((row) => (
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
      </div>
    </main>
  );
}
