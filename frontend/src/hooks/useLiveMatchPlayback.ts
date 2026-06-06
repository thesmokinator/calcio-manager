import { useEffect, useMemo, useState } from 'react';
import type { MatchEventDto } from '../types';
import { eventDelayMs, visibleKeyEvents } from '../utils/liveMatch';

export function useLiveMatchPlayback(events: MatchEventDto[]) {
  const [eventIndex, setEventIndex] = useState(0);
  const [paused, setPaused] = useState(false);

  const currentEvent = events[Math.min(eventIndex, Math.max(events.length - 1, 0))];
  const finished = events.length > 0 && eventIndex >= events.length - 1;

  useEffect(() => {
    setEventIndex(0);
    setPaused(false);
  }, [events]);

  useEffect(() => {
    if (events.length === 0 || paused || finished) return;
    const timeout = window.setTimeout(() => {
      setEventIndex((current) => Math.min(current + 1, events.length - 1));
    }, eventDelayMs(currentEvent));
    return () => window.clearTimeout(timeout);
  }, [events, events.length, eventIndex, currentEvent?.event_type, paused, finished]);

  const keyEvents = useMemo(() => visibleKeyEvents(events, eventIndex), [events, eventIndex]);

  return {
    eventIndex,
    currentEvent,
    finished,
    paused,
    visibleEvents: keyEvents,
    togglePaused: () => setPaused((value) => !value),
    skipToFinal: () => setEventIndex(Math.max(events.length - 1, 0)),
  };
}
