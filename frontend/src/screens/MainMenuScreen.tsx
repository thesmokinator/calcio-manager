import { FolderOpen, PlusCircle, Settings, Trophy } from 'lucide-react';

interface MainMenuScreenProps {
  onNewGame: () => void;
  onLoadGame: () => void;
}

export function MainMenuScreen({ onNewGame, onLoadGame }: MainMenuScreenProps) {
  return (
    <main className="screen menu-screen">
      <section className="hero-card scanlines">
        <h1 className="hero-title" aria-label="CSI Calcio Manager">
          <span className="hero-title__prefix">CSI</span>
          <span>CALCIO</span>
          <span>MANAGER</span>
        </h1>
        <div className="menu-actions">
          <button className="primary-button" onClick={onNewGame}>
            <PlusCircle size={18} /> Nuova carriera
          </button>
          <button className="secondary-button" onClick={onLoadGame}>
            <FolderOpen size={18} /> Carica partita
          </button>
          <button className="ghost-button" disabled>
            <Trophy size={18} /> Hall of fame
          </button>
          <button className="ghost-button" disabled>
            <Settings size={18} /> Impostazioni
          </button>
        </div>
      </section>
    </main>
  );
}
