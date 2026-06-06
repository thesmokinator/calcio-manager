import { useEffect, useMemo, useState } from 'react';
import { api } from '../api/tauri';
import { Panel } from '../components/Panel';
import type { NewGameInput, NewGamePreview } from '../types';

const colors = ['bianco', 'nero', 'rosso', 'blu', 'giallo', 'verde', 'azzurro', 'arancione', 'viola', 'grigio', 'granata', 'celeste', 'amaranto'];

function defaultSeasonYear() {
  const start = new Date().getFullYear() - 1;
  return `${start}-${start + 1}`;
}

interface NewGameWizardProps {
  onCreated: () => void;
  onBack: () => void;
}

export function NewGameWizard({ onCreated, onBack }: NewGameWizardProps) {
  const [regions, setRegions] = useState<string[]>([]);
  const [provinces, setProvinces] = useState<string[]>([]);
  const [comuni, setComuni] = useState<string[]>([]);
  const [preview, setPreview] = useState<NewGamePreview | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [form, setForm] = useState<NewGameInput>({
    region: '',
    province: '',
    comune: '',
    team_name: '',
    stadium_name: '',
    color_primary: 'rosso',
    color_secondary: 'blu',
    season_year: defaultSeasonYear(),
    seed: null,
  });

  useEffect(() => {
    api.listRegions().then(setRegions).catch((err) => setError(String(err)));
  }, []);

  useEffect(() => {
    if (!form.region) return;
    api.listProvinces(form.region).then((items) => {
      setProvinces(items);
      setForm((current) => ({ ...current, province: '', comune: '' }));
      setComuni([]);
      setPreview(null);
    }).catch((err) => setError(String(err)));
  }, [form.region]);

  useEffect(() => {
    if (!form.province) return;
    api.listComuni(form.province).then((items) => {
      setComuni(items);
      setForm((current) => ({ ...current, comune: '' }));
      setPreview(null);
    }).catch((err) => setError(String(err)));
  }, [form.province]);

  const canPreview = useMemo(() => Boolean(form.province && form.comune && form.team_name.trim()), [form]);

  function update<K extends keyof NewGameInput>(key: K, value: NewGameInput[K]) {
    setForm((current) => ({ ...current, [key]: value }));
    setPreview(null);
  }

  async function generatePreview() {
    setBusy(true);
    setError('');
    try {
      const result = await api.previewNewGame(form);
      setPreview(result);
      setForm((current) => ({ ...current, seed: result.seed }));
    } catch (err) {
      setError(String(err));
    } finally {
      setBusy(false);
    }
  }

  async function createGame() {
    setBusy(true);
    setError('');
    try {
      await api.createNewGame(form);
      onCreated();
    } catch (err) {
      setError(String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="screen wizard-screen">
      <div className="screen-header wizard-header">
        <button className="ghost-button" onClick={onBack}>← Menu</button>
        <div className="wizard-header__title">
          <div className="eyebrow">Nuova carriera</div>
          <h2>Costruisci la tua favola CSI</h2>
        </div>
      </div>

      {error && <div className="error-box">{error}</div>}

      <div className="wizard-grid">
        <Panel title="1. Territorio">
          <label>Regione</label>
          <select value={form.region} onChange={(event) => update('region', event.target.value)}>
            <option value="">Seleziona...</option>
            {regions.map((region) => <option key={region}>{region}</option>)}
          </select>

          <label>Provincia</label>
          <select value={form.province} onChange={(event) => update('province', event.target.value)} disabled={!form.region}>
            <option value="">Seleziona...</option>
            {provinces.map((province) => <option key={province}>{province}</option>)}
          </select>

          <label>Comune</label>
          <select value={form.comune} onChange={(event) => update('comune', event.target.value)} disabled={!form.province}>
            <option value="">Seleziona...</option>
            {comuni.map((comune) => <option key={comune}>{comune}</option>)}
          </select>
        </Panel>

        <Panel title="2. Identità club">
          <label>Nome squadra</label>
          <input value={form.team_name} onChange={(event) => update('team_name', event.target.value)} placeholder="ASD Oratorio San Giorgio" />

          <label>Campo/Stadio</label>
          <input value={form.stadium_name} onChange={(event) => update('stadium_name', event.target.value)} placeholder="Campo Sportivo Comunale" />

          <div className="two-cols">
            <div>
              <label>Colore 1</label>
              <select value={form.color_primary} onChange={(event) => update('color_primary', event.target.value)}>
                {colors.map((color) => <option key={color}>{color}</option>)}
              </select>
            </div>
            <div>
              <label>Colore 2</label>
              <select value={form.color_secondary} onChange={(event) => update('color_secondary', event.target.value)}>
                {colors.map((color) => <option key={color}>{color}</option>)}
              </select>
            </div>
          </div>

          <label>Stagione</label>
          <input value={form.season_year} onChange={(event) => update('season_year', event.target.value)} />

          <button className="primary-button full" disabled={!canPreview || busy} onClick={generatePreview}>
            Genera anteprima gironi
          </button>
        </Panel>

        <Panel title="3. Anteprima campionato" className="preview-panel">
          {!preview ? (
            <p className="muted">Seleziona territorio e club per generare gironi, squadre e livello medio.</p>
          ) : (
            <>
              <div className="preview-summary">
                <strong>{preview.total_teams}</strong> squadre · <strong>{preview.num_groups}</strong> gironi · stagione <strong>{preview.season_year}</strong>
              </div>
              <div className="gironi-preview">
                {preview.gironi.map((girone, index) => (
                  <section key={girone.letter} className={index === preview.human_girone_index ? 'girone-card human' : 'girone-card'}>
                    <h3>Girone {girone.letter}{index === preview.human_girone_index ? ' · la tua squadra' : ''}</h3>
                    <table>
                      <tbody>
                        {girone.teams.map((team) => (
                          <tr key={team.id} className={team.is_human ? 'human-row' : ''}>
                            <td>{team.name}{team.is_human ? ' ★' : ''}</td>
                            <td>{team.city}</td>
                            <td>{team.average_overall.toFixed(1)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </section>
                ))}
              </div>
              <button className="primary-button full" disabled={busy} onClick={createGame}>
                Inizia carriera
              </button>
            </>
          )}
        </Panel>
      </div>
    </main>
  );
}
