const colorMap: Record<string, string> = {
  bianco: '#d4d4d4',
  nero: '#2f3437',
  rosso: '#dc2626',
  blu: '#2563eb',
  giallo: '#eab308',
  verde: '#16a34a',
  azzurro: '#38bdf8',
  arancione: '#f97316',
  viola: '#a855f7',
  grigio: '#9ca3af',
  granata: '#7f1d1d',
  celeste: '#7dd3fc',
  amaranto: '#881337',
};

export function teamColorHex(name: string) {
  return colorMap[name] ?? '#475569';
}

export function readableTextColor(hex: string) {
  const r = Number.parseInt(hex.slice(1, 3), 16);
  const g = Number.parseInt(hex.slice(3, 5), 16);
  const b = Number.parseInt(hex.slice(5, 7), 16);
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  return luminance < 0.5 ? '#ffffff' : '#10141f';
}
