use chrono::NaiveDate;
use serde::{Deserialize, Serialize};
use uuid::Uuid;

use super::enums::{MatchEventType, MatchResult};
use super::team::Lineup;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MatchEvent {
    pub minute: u32,
    pub event_type: MatchEventType,
    pub team_id: Option<Uuid>,
    pub player_id: Option<Uuid>,
    pub assist_player_id: Option<Uuid>,
    pub commentary: String,
}

impl MatchEvent {
    pub fn new(minute: u32, event_type: MatchEventType, team_id: Option<Uuid>) -> Self {
        Self {
            minute,
            event_type,
            team_id,
            player_id: None,
            assist_player_id: None,
            commentary: String::new(),
        }
    }
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct PenaltyShootout {
    pub home_scores: Vec<bool>,
    pub away_scores: Vec<bool>,
}

impl PenaltyShootout {
    pub fn home_goals(&self) -> u32 {
        self.home_scores.iter().filter(|scored| **scored).count() as u32
    }

    pub fn away_goals(&self) -> u32 {
        self.away_scores.iter().filter(|scored| **scored).count() as u32
    }
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct MatchScore {
    pub home_goals: u32,
    pub away_goals: u32,
    pub penalty_shootout: Option<PenaltyShootout>,
}

impl MatchScore {
    pub fn is_draw_regular_time(&self) -> bool {
        self.home_goals == self.away_goals
    }

    pub fn display(&self) -> String {
        match &self.penalty_shootout {
            Some(shootout) => format!(
                "{} - {} (rig. {}-{})",
                self.home_goals,
                self.away_goals,
                shootout.home_goals(),
                shootout.away_goals()
            ),
            None => format!("{} - {}", self.home_goals, self.away_goals),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Match {
    pub id: Uuid,
    pub home_team_id: Uuid,
    pub away_team_id: Uuid,
    pub competition_id: Uuid,
    pub match_day: u32,
    pub match_date: Option<NaiveDate>,
    pub played: bool,
    pub score: MatchScore,
    pub result: Option<MatchResult>,
    pub events: Vec<MatchEvent>,
    pub home_lineup: Lineup,
    pub away_lineup: Lineup,
    pub home_possession: f32,
    pub away_possession: f32,
    pub home_shots: u32,
    pub away_shots: u32,
    pub home_shots_on_target: u32,
    pub away_shots_on_target: u32,
    pub home_fouls: u32,
    pub away_fouls: u32,
    pub home_corners: u32,
    pub away_corners: u32,
}

impl Match {
    pub fn new(
        home_team_id: Uuid,
        away_team_id: Uuid,
        competition_id: Uuid,
        match_day: u32,
        match_date: Option<NaiveDate>,
    ) -> Self {
        Self {
            id: Uuid::new_v4(),
            home_team_id,
            away_team_id,
            competition_id,
            match_day,
            match_date,
            played: false,
            score: MatchScore::default(),
            result: None,
            events: vec![],
            home_lineup: Lineup::default(),
            away_lineup: Lineup::default(),
            home_possession: 50.0,
            away_possession: 50.0,
            home_shots: 0,
            away_shots: 0,
            home_shots_on_target: 0,
            away_shots_on_target: 0,
            home_fouls: 0,
            away_fouls: 0,
            home_corners: 0,
            away_corners: 0,
        }
    }

    pub fn get_points(&self, team_id: Uuid) -> u32 {
        let Some(result) = self.result else {
            return 0;
        };
        let is_home = team_id == self.home_team_id;
        match result {
            MatchResult::VittoriaCasa => {
                if is_home {
                    3
                } else {
                    0
                }
            }
            MatchResult::VittoriaTrasferta => {
                if is_home {
                    0
                } else {
                    3
                }
            }
            MatchResult::VittoriaCasaRigori => {
                if is_home {
                    2
                } else {
                    1
                }
            }
            MatchResult::VittoriaTrasfertaRigori => {
                if is_home {
                    1
                } else {
                    2
                }
            }
            MatchResult::RinunciaCasa => {
                if is_home {
                    0
                } else {
                    3
                }
            }
            MatchResult::RinunciaTrasferta => {
                if is_home {
                    3
                } else {
                    0
                }
            }
        }
    }
}
