use std::fs;
use std::path::PathBuf;

use chrono::{DateTime, Local};
use serde::{Deserialize, Serialize};
use tauri::{AppHandle, Manager};

use crate::domain::models::GameState;

pub const SAVE_SCHEMA_VERSION: u32 = 1;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SaveMetadata {
    pub slot: String,
    pub team: String,
    pub province: String,
    pub season: String,
    pub modified: String,
    pub version: u32,
    pub compatible: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct SaveEnvelope {
    version: u32,
    metadata: SaveMetadata,
    state: GameState,
}

#[derive(Debug, Clone)]
struct DecodedSave {
    version: u32,
    metadata: Option<SaveMetadata>,
    state: GameState,
}

#[derive(Debug, Deserialize)]
#[serde(untagged)]
enum SaveDocument {
    Envelope(SaveEnvelope),
    Legacy(GameState),
}

fn saves_dir(app: &AppHandle) -> Result<PathBuf, String> {
    let dir = app
        .path()
        .app_data_dir()
        .map_err(|error| error.to_string())?
        .join("saves");
    fs::create_dir_all(&dir).map_err(|error| error.to_string())?;
    Ok(dir)
}

pub fn save_game(app: &AppHandle, state: &GameState, slot: &str) -> Result<SaveMetadata, String> {
    let save_path = saves_dir(app)?.join(format!("{}.json", sanitize_slot(slot)));
    let envelope = SaveEnvelope {
        version: SAVE_SCHEMA_VERSION,
        metadata: metadata_from_state(slot, state, None, SAVE_SCHEMA_VERSION, true)?,
        state: state.clone(),
    };
    let json = serde_json::to_string_pretty(&envelope).map_err(|error| error.to_string())?;
    fs::write(&save_path, json).map_err(|error| error.to_string())?;
    metadata_from_state(slot, state, Some(&save_path), SAVE_SCHEMA_VERSION, true)
}

pub fn load_game(app: &AppHandle, slot: &str) -> Result<Option<GameState>, String> {
    let save_path = saves_dir(app)?.join(format!("{}.json", sanitize_slot(slot)));
    if !save_path.exists() {
        return Ok(None);
    }
    let json = fs::read_to_string(save_path).map_err(|error| error.to_string())?;
    let decoded = decode_save_document(&json)?;
    if decoded.version > SAVE_SCHEMA_VERSION {
        return Err(format!(
            "Salvataggio versione {} non supportato: aggiorna l'applicazione",
            decoded.version
        ));
    }
    Ok(Some(decoded.state))
}

pub fn list_saves(app: &AppHandle) -> Result<Vec<SaveMetadata>, String> {
    let mut saves = Vec::new();
    for entry in fs::read_dir(saves_dir(app)?).map_err(|error| error.to_string())? {
        let entry = entry.map_err(|error| error.to_string())?;
        let path = entry.path();
        if path.extension().and_then(|value| value.to_str()) != Some("json") {
            continue;
        }
        let slot = path
            .file_stem()
            .and_then(|value| value.to_str())
            .unwrap_or("save")
            .to_string();
        match fs::read_to_string(&path)
            .ok()
            .and_then(|json| decode_save_document(&json).ok())
        {
            Some(decoded) => saves.push(metadata_from_decoded_save(&slot, &decoded, Some(&path))?),
            None => saves.push(SaveMetadata {
                slot,
                team: "?".to_string(),
                province: "?".to_string(),
                season: "?".to_string(),
                modified: modified_from_path(Some(&path)),
                version: 0,
                compatible: false,
            }),
        }
    }
    saves.sort_by(|a, b| b.modified.cmp(&a.modified));
    Ok(saves)
}

pub fn delete_save(app: &AppHandle, slot: &str) -> Result<bool, String> {
    let save_path = saves_dir(app)?.join(format!("{}.json", sanitize_slot(slot)));
    if save_path.exists() {
        fs::remove_file(save_path).map_err(|error| error.to_string())?;
        return Ok(true);
    }
    Ok(false)
}

fn metadata_from_state(
    slot: &str,
    state: &GameState,
    path: Option<&PathBuf>,
    version: u32,
    compatible: bool,
) -> Result<SaveMetadata, String> {
    let team = state
        .human_team()
        .map(|team| team.name.clone())
        .unwrap_or_else(|| "?".to_string());

    Ok(SaveMetadata {
        slot: sanitize_slot(slot),
        team,
        province: state.config.province.clone(),
        season: state.season.year.clone(),
        modified: modified_from_path(path),
        version,
        compatible,
    })
}

fn metadata_from_decoded_save(
    slot: &str,
    decoded: &DecodedSave,
    path: Option<&PathBuf>,
) -> Result<SaveMetadata, String> {
    let mut metadata = metadata_from_state(
        slot,
        &decoded.state,
        path,
        decoded.version,
        decoded.version <= SAVE_SCHEMA_VERSION,
    )?;

    if let Some(persisted) = &decoded.metadata {
        metadata.team = non_empty_or(&persisted.team, metadata.team);
        metadata.province = non_empty_or(&persisted.province, metadata.province);
        metadata.season = non_empty_or(&persisted.season, metadata.season);
    }

    Ok(metadata)
}

fn decode_save_document(json: &str) -> Result<DecodedSave, String> {
    match serde_json::from_str::<SaveDocument>(json).map_err(|error| error.to_string())? {
        SaveDocument::Envelope(envelope) => Ok(DecodedSave {
            version: envelope.version,
            metadata: Some(envelope.metadata),
            state: envelope.state,
        }),
        SaveDocument::Legacy(state) => Ok(DecodedSave {
            version: 0,
            metadata: None,
            state,
        }),
    }
}

fn modified_from_path(path: Option<&PathBuf>) -> String {
    path.and_then(|path| path.metadata().ok())
        .and_then(|metadata| metadata.modified().ok())
        .map(|modified| {
            let datetime: DateTime<Local> = modified.into();
            datetime.format("%d/%m/%Y %H:%M").to_string()
        })
        .unwrap_or_else(|| "?".to_string())
}

fn non_empty_or(value: &str, fallback: String) -> String {
    if value.trim().is_empty() || value == "?" {
        fallback
    } else {
        value.to_string()
    }
}

fn sanitize_slot(slot: &str) -> String {
    slot.chars()
        .filter(|character| {
            character.is_ascii_alphanumeric() || *character == '-' || *character == '_'
        })
        .collect::<String>()
        .trim()
        .to_string()
        .if_empty("save1")
}

trait IfEmpty {
    fn if_empty(self, fallback: &str) -> String;
}

impl IfEmpty for String {
    fn if_empty(self, fallback: &str) -> String {
        if self.is_empty() {
            fallback.to_string()
        } else {
            self
        }
    }
}

#[cfg(test)]
mod tests {
    use crate::domain::services::new_game::{NewGameInput, create_new_game};

    use super::*;

    fn test_state() -> GameState {
        create_new_game(NewGameInput {
            region: "Lombardia".to_string(),
            province: "Varese".to_string(),
            comune: "Varese".to_string(),
            team_name: "Real Oratorio".to_string(),
            stadium_name: "Campo Test".to_string(),
            color_primary: "rosso".to_string(),
            color_secondary: "blu".to_string(),
            season_year: "2025-2026".to_string(),
            seed: Some(789),
        })
        .expect("new game should be created")
    }

    #[test]
    fn decodes_legacy_raw_game_state_save() {
        let state = test_state();
        let json = serde_json::to_string(&state).expect("state should serialize");

        let decoded = decode_save_document(&json).expect("legacy save should decode");

        assert_eq!(decoded.version, 0);
        assert!(decoded.metadata.is_none());
        assert_eq!(decoded.state.season.year, "2025-2026");
        assert_eq!(decoded.state.human_team().unwrap().name, "Real Oratorio");
    }

    #[test]
    fn decodes_versioned_save_envelope() {
        let state = test_state();
        let envelope = SaveEnvelope {
            version: SAVE_SCHEMA_VERSION,
            metadata: metadata_from_state("Slot Uno", &state, None, SAVE_SCHEMA_VERSION, true)
                .expect("metadata should be created"),
            state,
        };
        let json = serde_json::to_string(&envelope).expect("envelope should serialize");

        let decoded = decode_save_document(&json).expect("envelope should decode");
        let metadata = metadata_from_decoded_save("Slot Uno", &decoded, None)
            .expect("metadata should be extracted");

        assert_eq!(decoded.version, SAVE_SCHEMA_VERSION);
        assert_eq!(metadata.slot, "SlotUno");
        assert_eq!(metadata.team, "Real Oratorio");
        assert_eq!(metadata.province, "Varese");
        assert_eq!(metadata.season, "2025-2026");
        assert!(metadata.compatible);
    }

    #[test]
    fn sanitizes_empty_or_unsafe_slot_names() {
        assert_eq!(sanitize_slot("../bad slot!"), "badslot");
        assert_eq!(sanitize_slot("***"), "save1");
    }
}
