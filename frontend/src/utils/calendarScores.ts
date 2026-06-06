export interface ParsedCalendarScore {
  regularScore: string;
  penaltyScore: string | null;
}

export function parseCalendarScore(score?: string | null): ParsedCalendarScore | null {
  if (!score) return null;

  const penaltyScore = score.match(/^(.*?)\s*\(rig\.\s*(.*?)\)$/);
  if (!penaltyScore) return { regularScore: score, penaltyScore: null };

  return {
    regularScore: penaltyScore[1].trim(),
    penaltyScore: formatPenaltyScore(penaltyScore[2]),
  };
}

export function formatPenaltyScore(score: string) {
  return score.trim().replace(/\s*-\s*/g, ' - ');
}
