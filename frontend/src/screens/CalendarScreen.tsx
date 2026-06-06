import { useEffect, useState } from 'react';
import { api } from '../api/tauri';
import type { CalendarDayDto } from '../types';

interface CalendarScreenProps {
  onBack: () => void;
}

export function CalendarScreen({ onBack }: CalendarScreenProps) {
  const [days, setDays] = useState<CalendarDayDto[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    api.getCalendar().then(setDays).catch((err) => setError(String(err)));
  }, []);

  return (
    <main className="screen stack-screen">
      <div className="screen-header">
        <button className="ghost-button" onClick={onBack}>← Hub</button>
        <h2>Calendario</h2>
      </div>
      {error && <div className="error-box">{error}</div>}
      <div className="calendar-list">
        {days.map((day) => (
          <section key={day.day_number} className="calendar-day">
            <header>
              <strong>Giornata {day.day_number}</strong>
              <span>{day.date}</span>
            </header>
            <div className="calendar-matches">
              {day.matches.map((match) => (
                <div key={match.id} className={match.is_human_match ? 'calendar-match human' : 'calendar-match'}>
                  <span>{match.home_team}</span>
                  <strong>{match.score ?? 'vs'}</strong>
                  <span>{match.away_team}</span>
                </div>
              ))}
            </div>
          </section>
        ))}
      </div>
    </main>
  );
}
