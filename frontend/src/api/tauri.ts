import { invoke } from '@tauri-apps/api/core';
import type {
  CalendarDayDto,
  GameHubDto,
  GameSummary,
  NewGameInput,
  NewGamePreview,
  PlayMatchDayResultDto,
  SaveMetadata,
  SquadDto,
  StandingRowDto,
} from '../types';

export const api = {
  listRegions: () => invoke<string[]>('list_regions'),
  listProvinces: (region: string) => invoke<string[]>('list_provinces', { region }),
  listComuni: (province: string) => invoke<string[]>('list_comuni', { province }),
  previewNewGame: (input: NewGameInput) => invoke<NewGamePreview>('preview_new_game', { input }),
  createNewGame: (input: NewGameInput) => invoke<GameSummary>('create_new_game', { input }),
  currentGameSummary: () => invoke<GameSummary | null>('current_game_summary'),
  getGameHub: () => invoke<GameHubDto | null>('get_game_hub'),
  getSquad: () => invoke<SquadDto | null>('get_squad'),
  getStandings: () => invoke<StandingRowDto[]>('get_standings'),
  getCalendar: () => invoke<CalendarDayDto[]>('get_calendar'),
  playNextMatch: () => invoke<PlayMatchDayResultDto>('play_next_match'),
  saveCurrentGame: (slot: string) => invoke<SaveMetadata>('save_current_game', { slot }),
  loadGame: (slot: string) => invoke<GameSummary | null>('load_game', { slot }),
  listSaves: () => invoke<SaveMetadata[]>('list_saves'),
  deleteSave: (slot: string) => invoke<boolean>('delete_save', { slot }),
};
