use std::sync::Mutex;

use crate::domain::models::GameState;

#[derive(Default)]
pub struct AppState {
    pub current_game: Mutex<Option<GameState>>,
}
