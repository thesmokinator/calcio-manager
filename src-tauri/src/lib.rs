mod app_state;
mod commands;
pub mod domain;

use std::fs;

use app_state::AppState;
use commands::game::{
    create_new_game, current_game_summary, get_calendar, get_game_hub, get_squad, get_standings,
    play_next_match, preview_new_game,
};
use commands::geography::{list_comuni, list_provinces, list_regions};
use commands::saves::{delete_save, list_saves, load_game, save_current_game};
use domain::engine::comuni;
use tauri::Manager;

pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .setup(|app| {
            let app_data_dir = app.path().app_data_dir()?;
            fs::create_dir_all(&app_data_dir)?;
            comuni::configure_db_path(app_data_dir.join("calcio_manager.sqlite"));
            Ok(())
        })
        .manage(AppState::default())
        .invoke_handler(tauri::generate_handler![
            list_regions,
            list_provinces,
            list_comuni,
            preview_new_game,
            create_new_game,
            current_game_summary,
            get_game_hub,
            get_squad,
            get_standings,
            get_calendar,
            play_next_match,
            save_current_game,
            load_game,
            list_saves,
            delete_save,
        ])
        .run(tauri::generate_context!())
        .expect("error while running Calcio Manager");
}
