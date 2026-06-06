import type { ColorPair } from '../types';
import { readableTextColor, teamColorHex } from '../utils/teamColors';

interface TeamBannerProps {
  name: string;
  colors: ColorPair;
  subtitle?: string;
}

export function TeamBanner({ name, colors, subtitle }: TeamBannerProps) {
  const bg = teamColorHex(colors[0]);
  const fg = readableTextColor(bg);

  return (
    <header className="team-banner" style={{ background: bg, color: fg }}>
      <div className="team-banner__name">{name}</div>
      {subtitle && <div className="team-banner__subtitle">{subtitle}</div>}
    </header>
  );
}
