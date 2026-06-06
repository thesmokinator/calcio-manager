use chrono::NaiveDate;
use serde::{Deserialize, Serialize};
use uuid::Uuid;

use super::enums::SeasonPhase;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MatchDay {
    pub day_number: u32,
    pub date: NaiveDate,
    pub match_ids: Vec<Uuid>,
    pub played: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Season {
    pub id: Uuid,
    pub year: String,
    pub competition_ids: Vec<Uuid>,
    pub calendar: Vec<MatchDay>,
    pub current_date: NaiveDate,
    pub phase: SeasonPhase,
}

impl Season {
    pub fn next_match_day(&self) -> Option<&MatchDay> {
        self.calendar.iter().find(|match_day| !match_day.played)
    }

    pub fn current_match_day_number(&self) -> u32 {
        self.next_match_day()
            .map(|match_day| match_day.day_number)
            .unwrap_or(self.calendar.len() as u32)
    }

    pub fn is_season_over(&self) -> bool {
        self.calendar.iter().all(|match_day| match_day.played)
    }
}
