import { useEffect, useState } from 'react';
import { api } from '../api/tauri';
import { TeamBanner } from '../components/TeamBanner';
import type { SquadDto } from '../types';

interface SquadScreenProps {
  onBack: () => void;
}

export function SquadScreen({ onBack }: SquadScreenProps) {
  const [squad, setSquad] = useState<SquadDto | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    api.getSquad().then(setSquad).catch((err) => setError(String(err)));
  }, []);

  if (!squad) {
    return <main className="screen stack-screen">{error ? <div className="error-box">{error}</div> : <p>Caricamento rosa...</p>}</main>;
  }

  return (
    <main className="screen stack-screen">
      <TeamBanner name={squad.team.name} colors={squad.team.colors} subtitle="Gestione rosa" />
      <div className="screen-header slim">
        <button className="ghost-button" onClick={onBack}>← Hub</button>
        <h2>Rosa</h2>
      </div>
      <div className="table-shell">
        <table className="data-table">
          <thead>
            <tr>
              <th>Ruolo</th><th>Nome</th><th>Età</th><th>OVR</th><th>Tir</th><th>Pas</th><th>Dri</th><th>Con</th><th>Pos</th><th>Dec</th><th>Vel</th><th>Res</th><th>For</th><th>Cond</th><th>Stato</th>
            </tr>
          </thead>
          <tbody>
            {squad.players.map((player) => (
              <tr key={player.id}>
                <td>{player.role}</td>
                <td className="strong-cell">{player.name}</td>
                <td>{player.age}</td>
                <td>{player.overall}</td>
                <td>{player.finishing}</td>
                <td>{player.passing}</td>
                <td>{player.dribbling}</td>
                <td>{player.first_touch}</td>
                <td>{player.positioning}</td>
                <td>{player.decisions}</td>
                <td>{player.pace}</td>
                <td>{player.stamina}</td>
                <td>{player.strength}</td>
                <td>{Math.round(player.condition * 100)}%</td>
                <td>{player.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </main>
  );
}
