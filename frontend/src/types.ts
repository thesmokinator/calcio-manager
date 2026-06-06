export type ColorPair = [string, string];

export interface NewGameInput {
  region: string;
  province: string;
  comune: string;
  team_name: string;
  stadium_name: string;
  color_primary: string;
  color_secondary: string;
  season_year: string;
  seed?: number | null;
}

export interface TeamPreview {
  id: string;
  name: string;
  city: string;
  colors: ColorPair;
  average_overall: number;
  is_human: boolean;
}

export interface GironePreview {
  letter: string;
  teams: TeamPreview[];
}

export interface NewGamePreview {
  season_year: string;
  num_groups: number;
  teams_per_group: number;
  total_teams: number;
  human_girone_index: number;
  gironi: GironePreview[];
  seed: number;
}

export interface GameSummary {
  team_name: string;
  comune: string;
  province: string;
  region: string;
  season_year: string;
  num_groups: number;
  human_team_id: string;
  current_match_day: number;
  total_match_days: number;
}

export interface TeamCardDto {
  id: string;
  name: string;
  city: string;
  province: string;
  stadium_name: string;
  colors: ColorPair;
  average_overall: number;
  squad_count: number;
  available_count: number;
  injured_count: number;
  suspended_count: number;
}

export interface NextMatchDto {
  id: string;
  match_day: number;
  date?: string | null;
  home_team: string;
  away_team: string;
  opponent: string;
  location: string;
}

export interface LastResultDto {
  home_team: string;
  away_team: string;
  score: string;
}

export interface StandingRowDto {
  position: number;
  team_id: string;
  team_name: string;
  played: number;
  wins: number;
  wins_penalties: number;
  losses_penalties: number;
  losses: number;
  goals_for: number;
  goals_against: number;
  goal_difference: number;
  points: number;
  is_human: boolean;
}

export interface GameHubDto {
  summary: GameSummary;
  team: TeamCardDto;
  competition_name: string;
  next_match?: NextMatchDto | null;
  last_result?: LastResultDto | null;
  standings: StandingRowDto[];
}

export type PlayerRole = 'POR' | 'DIF' | 'CEN' | 'ATT';

export interface SquadPlayerDto {
  id: string;
  role: PlayerRole;
  name: string;
  age: number;
  overall: number;
  passing: number;
  dribbling: number;
  finishing: number;
  first_touch: number;
  positioning: number;
  decisions: number;
  pace: number;
  stamina: number;
  strength: number;
  condition: number;
  status: string;
}

export interface SquadDto {
  team: TeamCardDto;
  players: SquadPlayerDto[];
}

export interface CalendarMatchDto {
  id: string;
  home_team: string;
  away_team: string;
  score?: string | null;
  played: boolean;
  is_human_match: boolean;
}

export interface CalendarDayDto {
  day_number: number;
  date: string;
  played: boolean;
  matches: CalendarMatchDto[];
}

export type MatchEventType =
  | 'calcio_inizio'
  | 'gol'
  | 'occasione'
  | 'parata'
  | 'tiro_fuori'
  | 'palo'
  | 'fallo'
  | 'ammonizione'
  | 'espulsione'
  | 'doppia_ammonizione'
  | 'sostituzione'
  | 'time_out'
  | 'intervallo'
  | 'fine_partita'
  | 'inizio_rigori'
  | 'rigore_segnato'
  | 'rigore_sbagliato'
  | 'rigore_parato'
  | 'calcio_angolo'
  | 'punizione'
  | 'possesso';

export interface MatchEventDto {
  minute: number;
  event_type: MatchEventType;
  team_id?: string | null;
  team_name: string;
  player_name: string;
  assist_name: string;
  commentary: string;
  home_goals: number;
  away_goals: number;
}

export interface PlayedMatchDto {
  id: string;
  home_team: string;
  away_team: string;
  score: string;
  home_goals: number;
  away_goals: number;
  home_penalty_goals?: number | null;
  away_penalty_goals?: number | null;
  home_possession: number;
  away_possession: number;
  home_shots: number;
  away_shots: number;
  home_shots_on_target: number;
  away_shots_on_target: number;
  home_fouls: number;
  away_fouls: number;
  home_corners: number;
  away_corners: number;
  events: MatchEventDto[];
}

export interface PlayMatchDayResultDto {
  season_completed: boolean;
  match_day?: number | null;
  human_match?: PlayedMatchDto | null;
  simulated_matches: PlayedMatchDto[];
}

export interface SaveMetadata {
  slot: string;
  team: string;
  province: string;
  season: string;
  modified: string;
  version: number;
  compatible: boolean;
}
