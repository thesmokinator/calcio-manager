import { useEffect, useState } from 'react';
import { api } from './api/tauri';
import { CalendarScreen } from './screens/CalendarScreen';
import { GameHubScreen } from './screens/GameHubScreen';
import { LoadGameScreen } from './screens/LoadGameScreen';
import { LiveMatchScreen } from './screens/LiveMatchScreen';
import { MainMenuScreen } from './screens/MainMenuScreen';
import { NewGameWizard } from './screens/NewGameWizard';
import { SquadScreen } from './screens/SquadScreen';
import { StandingsScreen } from './screens/StandingsScreen';

type Screen = 'menu' | 'new-game' | 'load-game' | 'hub' | 'squad' | 'standings' | 'calendar' | 'live-match';

export default function App() {
  const [screen, setScreen] = useState<Screen>('menu');
  const [bootError, setBootError] = useState('');

  useEffect(() => {
    api.currentGameSummary()
      .then((summary) => {
        if (summary) setScreen('hub');
      })
      .catch((err) => setBootError(String(err)));
  }, []);

  if (bootError) {
    return (
      <main className="screen stack-screen">
        <div className="error-box">{bootError}</div>
        <button className="ghost-button" onClick={() => setBootError('')}>Continua</button>
      </main>
    );
  }

  switch (screen) {
    case 'new-game':
      return <NewGameWizard onCreated={() => setScreen('hub')} onBack={() => setScreen('menu')} />;
    case 'load-game':
      return <LoadGameScreen onLoaded={() => setScreen('hub')} onBack={() => setScreen('menu')} />;
    case 'hub':
      return (
        <GameHubScreen
          onMenu={() => setScreen('menu')}
          onSquad={() => setScreen('squad')}
          onStandings={() => setScreen('standings')}
          onCalendar={() => setScreen('calendar')}
          onPlayMatch={() => setScreen('live-match')}
        />
      );
    case 'squad':
      return <SquadScreen onBack={() => setScreen('hub')} />;
    case 'standings':
      return <StandingsScreen onBack={() => setScreen('hub')} />;
    case 'calendar':
      return <CalendarScreen onBack={() => setScreen('hub')} />;
    case 'live-match':
      return <LiveMatchScreen onBack={() => setScreen('hub')} />;
    case 'menu':
    default:
      return <MainMenuScreen onNewGame={() => setScreen('new-game')} onLoadGame={() => setScreen('load-game')} />;
  }
}
