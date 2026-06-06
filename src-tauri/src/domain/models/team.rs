use serde::{Deserialize, Serialize};
use uuid::Uuid;

use super::enums::{PlayerRole, TacticStyle};
use super::player::Player;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Formation {
    pub name: String,
    pub defenders: u8,
    pub midfielders: u8,
    pub forwards: u8,
}

impl Formation {
    pub fn new(
        name: impl Into<String>,
        defenders: u8,
        midfielders: u8,
        forwards: u8,
    ) -> Result<Self, String> {
        let formation = Self {
            name: name.into(),
            defenders,
            midfielders,
            forwards,
        };
        if formation.defenders + formation.midfielders + formation.forwards != 6 {
            return Err(format!(
                "Formation {} must contain 6 outfield players",
                formation.name
            ));
        }
        Ok(formation)
    }

    pub fn default_c7() -> Self {
        Self {
            name: "2-3-1".to_string(),
            defenders: 2,
            midfielders: 3,
            forwards: 1,
        }
    }

    pub fn default_formations() -> Vec<Self> {
        vec![
            Self {
                name: "2-3-1".to_string(),
                defenders: 2,
                midfielders: 3,
                forwards: 1,
            },
            Self {
                name: "2-2-2".to_string(),
                defenders: 2,
                midfielders: 2,
                forwards: 2,
            },
            Self {
                name: "3-2-1".to_string(),
                defenders: 3,
                midfielders: 2,
                forwards: 1,
            },
            Self {
                name: "3-1-2".to_string(),
                defenders: 3,
                midfielders: 1,
                forwards: 2,
            },
            Self {
                name: "1-3-2".to_string(),
                defenders: 1,
                midfielders: 3,
                forwards: 2,
            },
            Self {
                name: "2-1-3".to_string(),
                defenders: 2,
                midfielders: 1,
                forwards: 3,
            },
        ]
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Lineup {
    pub starters: std::collections::HashMap<String, Uuid>,
    pub substitutes: Vec<Uuid>,
    pub formation: Formation,
}

impl Default for Lineup {
    fn default() -> Self {
        Self {
            starters: Default::default(),
            substitutes: vec![],
            formation: Formation::default_c7(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TeamFinances {
    pub budget: i32,
    pub registration_fees_paid: i32,
    pub sponsor_income: i32,
    pub tournament_prizes: i32,
    pub expenses: i32,
}

impl Default for TeamFinances {
    fn default() -> Self {
        Self {
            budget: 2000,
            registration_fees_paid: 0,
            sponsor_income: 0,
            tournament_prizes: 0,
            expenses: 0,
        }
    }
}

impl TeamFinances {
    pub fn balance(&self) -> i32 {
        self.budget + self.sponsor_income + self.tournament_prizes
            - self.registration_fees_paid
            - self.expenses
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Team {
    pub id: Uuid,
    pub name: String,
    pub city: String,
    pub province: String,
    pub stadium_name: String,
    pub colors: (String, String),
    pub reputation: u8,
    pub squad: Vec<Player>,
    pub formation: Formation,
    pub tactic: TacticStyle,
    pub finances: TeamFinances,
    pub is_human: bool,
}

impl Team {
    pub fn available_players(&self) -> Vec<&Player> {
        self.squad
            .iter()
            .filter(|player| player.is_available())
            .collect()
    }

    pub fn can_play(&self) -> bool {
        self.available_players().len() >= 4
    }

    pub fn squad_average_overall(&self) -> f32 {
        if self.squad.is_empty() {
            return 0.0;
        }
        self.squad.iter().map(|p| p.overall as f32).sum::<f32>() / self.squad.len() as f32
    }

    pub fn role_count(&self, role: PlayerRole) -> usize {
        self.squad
            .iter()
            .filter(|player| player.role == role)
            .count()
    }
}
