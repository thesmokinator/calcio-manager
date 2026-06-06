import { useEffect, useState, type ReactNode } from 'react';
import { api } from '../api/tauri';
import type { GameHubDto } from '../types';
import { TeamBanner } from './TeamBanner';

type CareerSection = 'hub' | 'squad' | 'standings' | 'calendar';

interface CareerLayoutProps {
  active: CareerSection;
  onHub: () => void;
  onSquad: () => void;
  onStandings: () => void;
  onCalendar: () => void;
  onPlayMatch: () => void;
  onMenu: () => void;
  children: (hub: GameHubDto) => ReactNode;
}

export function CareerLayout({
  active,
  onHub,
  onSquad,
  onStandings,
  onCalendar,
  onPlayMatch,
  onMenu,
  children,
}: CareerLayoutProps) {
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
    <main className="screen career-screen">
      <TeamBanner
        name={hub.team.name}
        colors={hub.team.colors}
        subtitle={`${hub.team.city} · ${hub.summary.season_year} · Giornata ${hub.summary.current_match_day}/${hub.summary.total_match_days}`}
      />

      {error && <div className="error-box">{error}</div>}

      <nav className="hub-nav career-nav" aria-label="Navigazione carriera">
        <button className={active === 'hub' ? 'active' : ''} onClick={onHub}>Hub</button>
        <button className={active === 'squad' ? 'active' : ''} onClick={onSquad}>Rosa</button>
        <button className={active === 'standings' ? 'active' : ''} onClick={onStandings}>Classifica</button>
        <button className={active === 'calendar' ? 'active' : ''} onClick={onCalendar}>Calendario</button>
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

      {children(hub)}
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
