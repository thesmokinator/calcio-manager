use serde::{Deserialize, Serialize};

use super::enums::{AgeCategory, GameFormat};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CompetitionRules {
    pub format: GameFormat,
    pub category: AgeCategory,
    pub half_duration_minutes: u32,
    pub num_periods: u32,
    pub players_on_pitch: u32,
    pub min_players_to_play: u32,
    pub max_squad_size: u32,
    pub points_win: u32,
    pub points_win_penalties: u32,
    pub points_loss_penalties: u32,
    pub points_loss: u32,
    pub penalties_after_draw: bool,
    pub unlimited_subs: bool,
    pub rolling_subs: bool,
    pub offside: bool,
    pub timeout_per_half: u32,
    pub timeout_duration_minutes: u32,
    pub numerical_inferiority_minutes: u32,
}

impl Default for CompetitionRules {
    fn default() -> Self {
        Self::for_category(AgeCategory::Open, GameFormat::C7)
    }
}

impl CompetitionRules {
    pub fn for_category(category: AgeCategory, format: GameFormat) -> Self {
        let mut rules = Self {
            format,
            category,
            half_duration_minutes: 25,
            num_periods: 2,
            players_on_pitch: 7,
            min_players_to_play: 4,
            max_squad_size: 14,
            points_win: 3,
            points_win_penalties: 2,
            points_loss_penalties: 1,
            points_loss: 0,
            penalties_after_draw: true,
            unlimited_subs: true,
            rolling_subs: false,
            offside: false,
            timeout_per_half: 1,
            timeout_duration_minutes: 2,
            numerical_inferiority_minutes: 0,
        };

        match format {
            GameFormat::C7 => match category {
                AgeCategory::Open | AgeCategory::Master30 => rules.half_duration_minutes = 25,
                AgeCategory::Master40 | AgeCategory::Juniores | AgeCategory::Allievi => {
                    rules.half_duration_minutes = 20;
                }
                AgeCategory::Under14 => rules.half_duration_minutes = 15,
                AgeCategory::Under12 => {
                    rules.half_duration_minutes = 8;
                    rules.num_periods = 4;
                }
            },
            GameFormat::C5 => {
                rules.players_on_pitch = 5;
                rules.min_players_to_play = 3;
                rules.half_duration_minutes = 20;
                rules.rolling_subs = true;
                rules.timeout_per_half = 0;
                rules.numerical_inferiority_minutes = 2;
            }
        }

        rules
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GameConfig {
    pub format: GameFormat,
    pub category: AgeCategory,
    pub comune: String,
    pub province: String,
    pub region: String,
    pub num_groups: usize,
    pub teams_per_group: usize,
    pub season_year: String,
    pub rules: CompetitionRules,
    pub seed: u64,
}

impl Default for GameConfig {
    fn default() -> Self {
        let category = AgeCategory::Open;
        let format = GameFormat::C7;
        Self {
            format,
            category,
            comune: String::new(),
            province: "Varese".to_string(),
            region: "Lombardia".to_string(),
            num_groups: 1,
            teams_per_group: 8,
            season_year: "2025-2026".to_string(),
            rules: CompetitionRules::for_category(category, format),
            seed: 0,
        }
    }
}
