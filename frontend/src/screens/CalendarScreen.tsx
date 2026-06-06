import { useEffect, useMemo, useState } from 'react';
import { api } from '../api/tauri';
import { CareerLayout } from '../components/CareerLayout';
import { useAsyncResource } from '../hooks/useAsyncResource';
import type { CalendarDayDto } from '../types';
import { parseCalendarScore } from '../utils/calendarScores';

interface CalendarScreenProps {
  onHub: () => void;
  onMenu: () => void;
  onSquad: () => void;
  onStandings: () => void;
  onCalendar: () => void;
  onPlayMatch: () => void;
}

export function CalendarScreen({ onHub, onMenu, onSquad, onStandings, onCalendar, onPlayMatch }: CalendarScreenProps) {
  const [selectedDayIndex, setSelectedDayIndex] = useState(0);
  const { data: calendarDays, error, loading } = useAsyncResource<CalendarDayDto[]>(() => api.getCalendar());
  const days = calendarDays ?? [];

  useEffect(() => {
    if (!calendarDays) return;
    const firstUnplayedIndex = calendarDays.findIndex((day) => !day.played);
    setSelectedDayIndex(firstUnplayedIndex >= 0 ? firstUnplayedIndex : Math.max(calendarDays.length - 1, 0));
  }, [calendarDays]);

  const selectedDay = days[selectedDayIndex] ?? null;
  const playedCount = useMemo(() => days.filter((day) => day.played).length, [days]);

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
          {loading ? (
            <p>Caricamento calendario...</p>
          ) : selectedDay ? (
            <div className="calendar-pager">
              <div className="calendar-heading">
                <div>
                  <h2>Calendario</h2>
                  <span>Giornata {selectedDay.day_number} · {selectedDay.date} · {playedCount}/{days.length} giocate</span>
                </div>
                <div className="calendar-pager__bar">
                  <button
                    className="ghost-button"
                    disabled={selectedDayIndex === 0}
                    onClick={() => setSelectedDayIndex((index) => Math.max(index - 1, 0))}
                  >
                    ← Precedente
                  </button>
                  <button
                    className="ghost-button"
                    disabled={selectedDayIndex >= days.length - 1}
                    onClick={() => setSelectedDayIndex((index) => Math.min(index + 1, days.length - 1))}
                  >
                    Successiva →
                  </button>
                </div>
              </div>

              {error && <div className="error-box">{error}</div>}

              <div className="calendar-day-tabs" aria-label="Seleziona giornata">
                {days.map((day, index) => (
                  <button
                    key={day.day_number}
                    className={index === selectedDayIndex ? 'active' : ''}
                    aria-label={`Vai alla giornata ${day.day_number}`}
                    onClick={() => setSelectedDayIndex(index)}
                  >
                    {day.day_number}
                  </button>
                ))}
              </div>

              <section className="calendar-day calendar-day--single">
                <header>
                  <strong>Giornata {selectedDay.day_number}</strong>
                  <span>{selectedDay.date}</span>
                </header>
                <div className="calendar-matches">
                  {selectedDay.matches.map((match) => (
                    <div key={match.id} className={match.is_human_match ? 'calendar-match human' : 'calendar-match'}>
                      <span className="calendar-team home-team">{match.home_team}</span>
                      <CalendarScore score={match.score} />
                      <span className="calendar-team away-team">{match.away_team}</span>
                    </div>
                  ))}
                </div>
              </section>
            </div>
          ) : (
            <>
              <div className="screen-header slim">
                <h2>Calendario</h2>
              </div>
              {error && <div className="error-box">{error}</div>}
              <p className="muted">Calendario non disponibile.</p>
            </>
          )}
        </section>
      )}
    </CareerLayout>
  );
}

function CalendarScore({ score }: { score?: string | null }) {
  const parsed = parseCalendarScore(score);
  if (!parsed) return <strong className="calendar-score pending">vs</strong>;
  if (!parsed.penaltyScore) return <strong className="calendar-score">{parsed.regularScore}</strong>;

  return (
    <strong className="calendar-score with-penalties">
      <span className="calendar-score__regular">{parsed.regularScore}</span>
      <span className="calendar-score__shootout">Rigori {parsed.penaltyScore}</span>
    </strong>
  );
}
