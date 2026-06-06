use serde::{Deserialize, Serialize};
use uuid::Uuid;

use super::enums::{MoraleLevel, PlayerRole};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TechnicalAttributes {
    pub passing: u8,
    pub dribbling: u8,
    pub finishing: u8,
    pub first_touch: u8,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MentalAttributes {
    pub positioning: u8,
    pub decisions: u8,
    pub leadership: u8,
    pub teamwork: u8,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PhysicalAttributes {
    pub pace: u8,
    pub stamina: u8,
    pub strength: u8,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GoalkeepingAttributes {
    pub reflexes: u8,
    pub handling: u8,
}

impl Default for GoalkeepingAttributes {
    fn default() -> Self {
        Self {
            reflexes: 5,
            handling: 5,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PlayerAttributes {
    pub technical: TechnicalAttributes,
    pub mental: MentalAttributes,
    pub physical: PhysicalAttributes,
    pub goalkeeping: GoalkeepingAttributes,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Injury {
    pub description: String,
    pub days_remaining: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SeasonStats {
    pub season: String,
    pub appearances: u32,
    pub goals: u32,
    pub assists: u32,
    pub yellow_cards: u32,
    pub red_cards: u32,
    pub minutes_played: u32,
    pub average_rating: f32,
}

impl SeasonStats {
    pub fn new(season: impl Into<String>) -> Self {
        Self {
            season: season.into(),
            appearances: 0,
            goals: 0,
            assists: 0,
            yellow_cards: 0,
            red_cards: 0,
            minutes_played: 0,
            average_rating: 0.0,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Player {
    pub id: Uuid,
    pub first_name: String,
    pub last_name: String,
    pub age: u8,
    pub role: PlayerRole,
    pub overall: u8,
    pub attributes: PlayerAttributes,
    pub condition: f32,
    pub morale: MoraleLevel,
    pub injury: Option<Injury>,
    pub suspended: bool,
    pub yellow_card_accumulation: u32,
    pub current_season_stats: SeasonStats,
    pub history: Vec<SeasonStats>,
}

impl Player {
    pub fn full_name(&self) -> String {
        format!("{} {}", self.first_name, self.last_name)
    }

    pub fn short_name(&self) -> String {
        let initial = self.first_name.chars().next().unwrap_or('?');
        format!("{}. {}", initial, self.last_name)
    }

    pub fn is_available(&self) -> bool {
        self.injury.is_none() && !self.suspended
    }

    pub fn calculate_overall(&self) -> u8 {
        let attrs = &self.attributes;
        let tech = &attrs.technical;
        let ment = &attrs.mental;
        let phys = &attrs.physical;

        let score = match self.role {
            PlayerRole::Gk => {
                let gk = &attrs.goalkeeping;
                (gk.reflexes as f32 * 3.0
                    + gk.handling as f32 * 3.0
                    + ment.positioning as f32 * 2.0
                    + phys.pace as f32
                    + phys.strength as f32)
                    / 10.0
            }
            PlayerRole::Def => {
                (ment.positioning as f32 * 3.0
                    + phys.strength as f32 * 2.0
                    + phys.pace as f32
                    + tech.passing as f32 * 2.0
                    + ment.teamwork as f32
                    + ment.decisions as f32)
                    / 10.0
            }
            PlayerRole::Mid => {
                (tech.passing as f32 * 3.0
                    + ment.decisions as f32 * 2.0
                    + ment.teamwork as f32 * 2.0
                    + phys.stamina as f32
                    + tech.dribbling as f32
                    + ment.positioning as f32)
                    / 10.0
            }
            PlayerRole::Fwd => {
                (tech.finishing as f32 * 3.0
                    + tech.dribbling as f32 * 2.0
                    + phys.pace as f32 * 2.0
                    + tech.first_touch as f32
                    + ment.positioning as f32
                    + ment.decisions as f32)
                    / 10.0
            }
        };

        score.round().clamp(1.0, 20.0) as u8
    }
}
