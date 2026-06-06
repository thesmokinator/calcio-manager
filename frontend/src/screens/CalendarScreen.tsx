import { useEffect, useState } from 'react';
import { api } from '../api/tauri';
import { CareerLayout } from '../components/CareerLayout';
import type { CalendarDayDto } from '../types';

interface CalendarScreenProps {
  onHub: () => void;
  onMenu: () => void;
  onSquad: () => void;
  onStandings: () => void;
  onCalendar: () => void;
  onPlayMatch: () => void;
}

export function CalendarScreen({ onHub, onMenu, onSquad, onStandings, onCalendar, onPlayMatch }: CalendarScreenProps) {
  const [days, setDays] = useState<CalendarDayDto[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    api.getCalendar().then(setDays).catch((err) => setError(String(err)));
  }, []);

  return (
    <CareerLayout
      active="calendar"
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
                      <span className="calendar-team home-team">{match.home_team}</span>
                      <CalendarScore score={match.score} />
                      <span className="calendar-team away-team">{match.away_team}</span>
                    </div>
                  ))}
                </div>
              </section>
            ))}
          </div>
        </section>
      )}
    </CareerLayout>
  );
}

function CalendarScore({ score }: { score?: string | null }) {
  if (!score) return <strong className="calendar-score pending">vs</strong>;

  const penaltyScore = score.match(/^(.*?)\s*\(rig\.\s*(.*?)\)$/);
  if (!penaltyScore) return <strong className="calendar-score">{score}</strong>;

  return (
    <strong className="calendar-score with-penalties">
      <span>{penaltyScore[1].trim()}</span>
      <small>Rig. {penaltyScore[2].trim()}</small>
    </strong>
  );
}
