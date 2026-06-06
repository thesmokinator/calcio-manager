use std::collections::HashMap;

use serde::{Deserialize, Serialize};
use uuid::Uuid;

use super::config::CompetitionRules;
use super::enums::{AgeCategory, CompetitionPhase, CompetitionType, Division, GameFormat};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StandingRow {
    pub team_id: Uuid,
    pub team_name: String,
    pub played: u32,
    pub wins: u32,
    pub wins_penalties: u32,
    pub losses_penalties: u32,
    pub losses: u32,
    pub goals_for: u32,
    pub goals_against: u32,
    pub points: u32,
    pub h2h_points: HashMap<String, u32>,
    pub h2h_goals_for: HashMap<String, u32>,
    pub h2h_goals_against: HashMap<String, u32>,
    pub yellow_cards: u32,
    pub red_cards: u32,
}

impl StandingRow {
    pub fn new(team_id: Uuid, team_name: impl Into<String>) -> Self {
        Self {
            team_id,
            team_name: team_name.into(),
            played: 0,
            wins: 0,
            wins_penalties: 0,
            losses_penalties: 0,
            losses: 0,
            goals_for: 0,
            goals_against: 0,
            points: 0,
            h2h_points: HashMap::new(),
            h2h_goals_for: HashMap::new(),
            h2h_goals_against: HashMap::new(),
            yellow_cards: 0,
            red_cards: 0,
        }
    }

    pub fn goal_difference(&self) -> i32 {
        self.goals_for as i32 - self.goals_against as i32
    }

    pub fn discipline_score(&self) -> u32 {
        self.yellow_cards + self.red_cards * 3
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Competition {
    pub id: Uuid,
    pub name: String,
    pub girone: String,
    pub format: GameFormat,
    pub category: AgeCategory,
    pub competition_type: CompetitionType,
    pub phase: CompetitionPhase,
    pub division: Division,
    pub province: String,
    pub region: String,
    pub team_ids: Vec<Uuid>,
    pub standings: Vec<StandingRow>,
    pub match_ids: Vec<Uuid>,
    pub rules: CompetitionRules,
    pub current_match_day: u32,
    pub total_match_days: u32,
    pub completed: bool,
}

impl Competition {
    pub fn new(
        girone: impl Into<String>,
        province: impl Into<String>,
        region: impl Into<String>,
        team_ids: Vec<Uuid>,
        rules: CompetitionRules,
    ) -> Self {
        Self {
            id: Uuid::new_v4(),
            name: String::new(),
            girone: girone.into(),
            format: GameFormat::C7,
            category: AgeCategory::Open,
            competition_type: CompetitionType::Campionato,
            phase: CompetitionPhase::Territoriale,
            division: Division::SerieOro,
            province: province.into(),
            region: region.into(),
            team_ids,
            standings: vec![],
            match_ids: vec![],
            rules,
            current_match_day: 0,
            total_match_days: 0,
            completed: false,
        }
    }

    pub fn num_teams(&self) -> usize {
        self.team_ids.len()
    }
}
