use std::collections::HashMap;

use serde::{Deserialize, Serialize};
use uuid::Uuid;

use super::competition::Competition;
use super::config::GameConfig;
use super::game_match::Match;
use super::season::Season;
use super::team::Team;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GameState {
    pub config: GameConfig,
    pub season: Season,
    pub teams: HashMap<String, Team>,
    pub competitions: HashMap<String, Competition>,
    pub matches: HashMap<String, Match>,
    pub human_team_id: Option<Uuid>,
}

impl GameState {
    pub fn human_team(&self) -> Option<&Team> {
        self.human_team_id
            .and_then(|id| self.teams.get(&id.to_string()))
    }

    pub fn human_competition(&self) -> Option<&Competition> {
        let human_id = self.human_team_id?;
        self.competitions
            .values()
            .find(|competition| competition.team_ids.contains(&human_id))
    }

    pub fn current_competition(&self) -> Option<&Competition> {
        self.human_competition()
            .or_else(|| self.competitions.values().next())
    }

    pub fn current_competition_mut(&mut self) -> Option<&mut Competition> {
        let human_id = self.human_team_id?;
        let competition_id = self
            .competitions
            .iter()
            .find(|(_, competition)| competition.team_ids.contains(&human_id))
            .map(|(id, _)| id.clone())?;
        self.competitions.get_mut(&competition_id)
    }

    pub fn get_team(&self, team_id: Uuid) -> Option<&Team> {
        self.teams.get(&team_id.to_string())
    }

    pub fn get_match(&self, match_id: Uuid) -> Option<&Match> {
        self.matches.get(&match_id.to_string())
    }

    pub fn get_next_match_for_team(&self, team_id: Uuid) -> Option<&Match> {
        for match_day in &self.season.calendar {
            if match_day.played {
                continue;
            }
            for match_id in &match_day.match_ids {
                let Some(game_match) = self.matches.get(&match_id.to_string()) else {
                    continue;
                };
                if !game_match.played
                    && (game_match.home_team_id == team_id || game_match.away_team_id == team_id)
                {
                    return Some(game_match);
                }
            }
        }
        None
    }
}
