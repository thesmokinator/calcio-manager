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

#[cfg(test)]
mod tests {
    use super::*;
    use crate::domain::models::{
        GoalkeepingAttributes, Injury, MentalAttributes, MoraleLevel, PhysicalAttributes,
        PlayerAttributes, SeasonStats, TechnicalAttributes,
    };

    #[test]
    fn formation_requires_six_outfield_players() {
        assert!(Formation::new("2-3-1", 2, 3, 1).is_ok());
        assert!(Formation::new("invalid", 2, 2, 1).is_err());
    }

    #[test]
    fn team_finances_balance_accounts_for_income_and_expenses() {
        let finances = TeamFinances {
            budget: 2_000,
            registration_fees_paid: 300,
            sponsor_income: 500,
            tournament_prizes: 100,
            expenses: 250,
        };

        assert_eq!(finances.balance(), 2_050);
    }

    #[test]
    fn team_availability_ignores_injured_and_suspended_players() {
        let team = Team {
            id: Uuid::new_v4(),
            name: "ASD Test".to_string(),
            city: "Barasso".to_string(),
            province: "Varese".to_string(),
            stadium_name: "Campo".to_string(),
            colors: ("rosso".to_string(), "blu".to_string()),
            reputation: 10,
            squad: vec![
                player(PlayerRole::Gk, true),
                player(PlayerRole::Def, true),
                player(PlayerRole::Mid, true),
                player(PlayerRole::Fwd, true),
                player(PlayerRole::Fwd, false),
            ],
            formation: Formation::default_c7(),
            tactic: TacticStyle::Equilibrata,
            finances: TeamFinances::default(),
            is_human: false,
        };

        assert_eq!(team.available_players().len(), 4);
        assert!(team.can_play());
    }

    fn player(role: PlayerRole, available: bool) -> Player {
        Player {
            id: Uuid::new_v4(),
            first_name: "Mario".to_string(),
            last_name: "Rossi".to_string(),
            age: 24,
            role,
            overall: 10,
            attributes: PlayerAttributes {
                technical: TechnicalAttributes {
                    passing: 10,
                    dribbling: 10,
                    finishing: 10,
                    first_touch: 10,
                },
                mental: MentalAttributes {
                    positioning: 10,
                    decisions: 10,
                    leadership: 10,
                    teamwork: 10,
                },
                physical: PhysicalAttributes {
                    pace: 10,
                    stamina: 10,
                    strength: 10,
                },
                goalkeeping: GoalkeepingAttributes::default(),
            },
            condition: 1.0,
            morale: MoraleLevel::Normal,
            injury: (!available).then(|| Injury {
                description: "Test injury".to_string(),
                days_remaining: 3,
            }),
            suspended: false,
            yellow_card_accumulation: 0,
            current_season_stats: SeasonStats::new("2026-2027"),
            history: vec![],
        }
    }
}
