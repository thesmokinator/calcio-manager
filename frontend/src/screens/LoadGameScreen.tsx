import { useEffect, useState } from 'react';
import { api } from '../api/tauri';
import type { SaveMetadata } from '../types';

interface LoadGameScreenProps {
  onLoaded: () => void;
  onBack: () => void;
}

export function LoadGameScreen({ onLoaded, onBack }: LoadGameScreenProps) {
  const [saves, setSaves] = useState<SaveMetadata[]>([]);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    api.listSaves().then(setSaves).catch((err) => setError(String(err)));
  }, []);

  async function load(slot: string) {
    setError('');
    try {
      const result = await api.loadGame(slot);
      if (result) onLoaded();
      else setError('Salvataggio non trovato.');
    } catch (err) {
      setError(String(err));
    }
  }

  return (
    <main className="screen stack-screen">
      <div className="screen-header">
        <button className="ghost-button" onClick={onBack}>← Menu</button>
        <h2>Carica partita</h2>
      </div>
      {error && <div className="error-box">{error}</div>}
      <section className="panel">
        <div className="panel-body">
          {saves.length === 0 ? (
            <p className="muted">Nessun salvataggio trovato.</p>
          ) : (
            <div className="save-list">
              {saves.map((save) => (
                <button
                  key={save.slot}
                  className="save-row"
                  onClick={() => load(save.slot)}
                  disabled={!save.compatible}
                >
                  <strong>{save.team}</strong>
                  <span>{save.province} · {save.season}</span>
                  <small>
                    {save.slot} · {save.modified} · v{save.version}
                    {!save.compatible ? ' · non compatibile' : ''}
                  </small>
                </button>
              ))}
            </div>
          )}
        </div>
      </section>
    </main>
  );
}
