use tauri::{AppHandle, State};

use crate::app_state::AppState;
use crate::domain::services::new_game::GameSummary;
use crate::domain::services::saves::{self, SaveMetadata};

#[tauri::command]
pub fn save_current_game(
    app: AppHandle,
    slot: String,
    state: State<AppState>,
) -> Result<SaveMetadata, String> {
    let guard = state
        .current_game
        .lock()
        .map_err(|error| error.to_string())?;
    let game_state = guard
        .as_ref()
        .ok_or_else(|| "Nessuna partita in corso".to_string())?;
    saves::save_game(&app, game_state, &slot)
}

#[tauri::command]
pub fn load_game(
    app: AppHandle,
    slot: String,
    state: State<AppState>,
) -> Result<Option<GameSummary>, String> {
    let loaded = saves::load_game(&app, &slot)?;
    let Some(game_state) = loaded else {
        return Ok(None);
    };
    let summary = GameSummary::from_state(&game_state)?;
    *state
        .current_game
        .lock()
        .map_err(|error| error.to_string())? = Some(game_state);
    Ok(Some(summary))
}

#[tauri::command]
pub fn list_saves(app: AppHandle) -> Result<Vec<SaveMetadata>, String> {
    saves::list_saves(&app)
}

#[tauri::command]
pub fn delete_save(app: AppHandle, slot: String) -> Result<bool, String> {
    saves::delete_save(&app, &slot)
}
