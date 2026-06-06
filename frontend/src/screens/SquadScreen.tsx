import { useEffect, useState } from 'react';
import { api } from '../api/tauri';
import { CareerLayout } from '../components/CareerLayout';
import type { SquadDto } from '../types';

interface SquadScreenProps {
  onHub: () => void;
  onMenu: () => void;
  onSquad: () => void;
  onStandings: () => void;
  onCalendar: () => void;
  onPlayMatch: () => void;
}

export function SquadScreen({ onHub, onMenu, onSquad, onStandings, onCalendar, onPlayMatch }: SquadScreenProps) {
  const [squad, setSquad] = useState<SquadDto | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    api.getSquad().then(setSquad).catch((err) => setError(String(err)));
  }, []);

  return (
    <CareerLayout
      active="squad"
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
            <h2>Rosa</h2>
          </div>
          {error && <div className="error-box">{error}</div>}
          {!squad ? (
            <p>Caricamento rosa...</p>
          ) : (
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
          )}
        </section>
      )}
    </CareerLayout>
  );
}
