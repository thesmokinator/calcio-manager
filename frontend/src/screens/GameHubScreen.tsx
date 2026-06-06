import { useEffect, useState } from 'react';
import { api } from '../api/tauri';
import { Panel } from '../components/Panel';
import { TeamBanner } from '../components/TeamBanner';
import type { GameHubDto } from '../types';

interface GameHubScreenProps {
  onMenu: () => void;
  onSquad: () => void;
  onStandings: () => void;
  onCalendar: () => void;
  onPlayMatch: () => void;
}

export function GameHubScreen({ onMenu, onSquad, onStandings, onCalendar, onPlayMatch }: GameHubScreenProps) {
  const [hub, setHub] = useState<GameHubDto | null>(null);
  const [error, setError] = useState('');
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [saveSlot, setSaveSlot] = useState('save1');
  const [saveMessage, setSaveMessage] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.getGameHub().then((data) => {
      setHub(data);
      if (data) setSaveSlot(defaultSaveSlot(data));
    }).catch((err) => setError(String(err)));
  }, []);

  async function save() {
    const slot = saveSlot.trim();
    if (!slot || saving) return;

    setSaving(true);
    setError('');
    setSaveMessage('');
    try {
      const saved = await api.saveCurrentGame(slot);
      setSaveSlot(saved.slot);
      setSaveMessage(`Salvataggio “${saved.slot}” completato.`);
    } catch (err) {
      setError(String(err));
    } finally {
      setSaving(false);
    }
  }

  function openSaveDialog() {
    if (hub) setSaveSlot((slot) => slot || defaultSaveSlot(hub));
    setSaveMessage('');
    setError('');
    setSaveDialogOpen(true);
  }

  if (!hub) {
    return <main className="screen stack-screen">{error ? <div className="error-box">{error}</div> : <p>Caricamento...</p>}</main>;
  }

  return (
    <main className="screen hub-screen">
      <TeamBanner
        name={hub.team.name}
        colors={hub.team.colors}
        subtitle={`${hub.team.city} · ${hub.summary.season_year} · Giornata ${hub.summary.current_match_day}/${hub.summary.total_match_days}`}
      />

      {error && <div className="error-box">{error}</div>}

      <nav className="hub-nav">
        <button onClick={onSquad}>Rosa</button>
        <button onClick={onStandings}>Classifica</button>
        <button onClick={onCalendar}>Calendario</button>
        <button onClick={onPlayMatch}>Gioca partita</button>
        <button onClick={openSaveDialog}>Salva</button>
        <button onClick={onMenu}>Menu</button>
      </nav>

      {saveDialogOpen && (
        <div className="modal-backdrop" role="presentation" onClick={() => !saving && setSaveDialogOpen(false)}>
          <section
            className="modal-card"
            role="dialog"
            aria-modal="true"
            aria-labelledby="save-dialog-title"
            onClick={(event) => event.stopPropagation()}
          >
            <h2 id="save-dialog-title">Salva partita</h2>
            <p className="muted">Scegli il nome dello slot. Se esiste già, verrà aggiornato.</p>
            <label htmlFor="save-slot">Nome salvataggio</label>
            <input
              id="save-slot"
              value={saveSlot}
              onChange={(event) => setSaveSlot(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter') void save();
                if (event.key === 'Escape' && !saving) setSaveDialogOpen(false);
              }}
              autoFocus
            />
            {saveMessage && <div className="success-box">{saveMessage}</div>}
            <div className="modal-actions">
              <button className="ghost-button" onClick={() => setSaveDialogOpen(false)} disabled={saving}>Chiudi</button>
              <button className="primary-button" onClick={() => void save()} disabled={!saveSlot.trim() || saving}>
                {saving ? 'Salvataggio...' : 'Salva'}
              </button>
            </div>
          </section>
        </div>
      )}

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
    </main>
  );
}

function defaultSaveSlot(hub: GameHubDto) {
  const team = hub.team.name
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/gi, '_')
    .replace(/^_+|_+$/g, '');
  return `${team || 'save'}_${hub.summary.season_year}`;
}
