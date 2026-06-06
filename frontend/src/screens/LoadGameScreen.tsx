import { useState } from 'react';
import { api } from '../api/tauri';
import { useAsyncResource } from '../hooks/useAsyncResource';
import type { SaveMetadata } from '../types';

interface LoadGameScreenProps {
  onLoaded: () => void;
  onBack: () => void;
}

export function LoadGameScreen({ onLoaded, onBack }: LoadGameScreenProps) {
  const { data: saves, error: loadError, loading } = useAsyncResource<SaveMetadata[]>(() => api.listSaves());
  const [actionError, setActionError] = useState<string>('');
  const error = actionError || loadError;

  async function load(slot: string) {
    setActionError('');
    try {
      const result = await api.loadGame(slot);
      if (result) onLoaded();
      else setActionError('Salvataggio non trovato.');
    } catch (err) {
      setActionError(String(err));
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
          {loading ? (
            <p className="muted">Caricamento salvataggi...</p>
          ) : (saves ?? []).length === 0 ? (
            <p className="muted">Nessun salvataggio trovato.</p>
          ) : (
            <div className="save-list">
              {(saves ?? []).map((save) => (
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
