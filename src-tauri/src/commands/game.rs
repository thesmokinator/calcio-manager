use serde::{Deserialize, Serialize};
use tauri::State;
use uuid::Uuid;

use crate::app_state::AppState;
use rand::SeedableRng;
use rand_chacha::ChaCha8Rng;

use crate::domain::engine::commentary::{CommentaryVars, generate_commentary};
use crate::domain::engine::competition::{sort_standings, update_standings};
use crate::domain::engine::match_engine::simulate_match;
use crate::domain::models::{
    GameState, Match, MatchEvent, MatchEventType, PlayerRole, StandingRow, Team,
};
use crate::domain::services::new_game::{self, GameSummary, NewGameInput, NewGamePreview};
use crate::domain::services::season::advance_season;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TeamCardDto {
    pub id: Uuid,
    pub name: String,
    pub city: String,
    pub province: String,
    pub stadium_name: String,
    pub colors: (String, String),
    pub average_overall: f32,
    pub squad_count: usize,
    pub available_count: usize,
    pub injured_count: usize,
    pub suspended_count: usize,
}

impl From<&Team> for TeamCardDto {
    fn from(team: &Team) -> Self {
        Self {
            id: team.id,
            name: team.name.clone(),
            city: team.city.clone(),
            province: team.province.clone(),
            stadium_name: team.stadium_name.clone(),
            colors: team.colors.clone(),
            average_overall: (team.squad_average_overall() * 10.0).round() / 10.0,
            squad_count: team.squad.len(),
            available_count: team.available_players().len(),
            injured_count: team
                .squad
                .iter()
                .filter(|player| player.injury.is_some())
                .count(),
            suspended_count: team.squad.iter().filter(|player| player.suspended).count(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NextMatchDto {
    pub id: Uuid,
    pub match_day: u32,
    pub date: Option<String>,
    pub home_team: String,
    pub away_team: String,
    pub opponent: String,
    pub location: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LastResultDto {
    pub home_team: String,
    pub away_team: String,
    pub score: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StandingRowDto {
    pub position: usize,
    pub team_id: Uuid,
    pub team_name: String,
    pub played: u32,
    pub wins: u32,
    pub wins_penalties: u32,
    pub losses_penalties: u32,
    pub losses: u32,
    pub goals_for: u32,
    pub goals_against: u32,
    pub goal_difference: i32,
    pub points: u32,
    pub is_human: bool,
}

impl StandingRowDto {
    fn from_row(position: usize, row: &StandingRow, human_team_id: Option<Uuid>) -> Self {
        Self {
            position,
            team_id: row.team_id,
            team_name: row.team_name.clone(),
            played: row.played,
            wins: row.wins,
            wins_penalties: row.wins_penalties,
            losses_penalties: row.losses_penalties,
            losses: row.losses,
            goals_for: row.goals_for,
            goals_against: row.goals_against,
            goal_difference: row.goal_difference(),
            points: row.points,
            is_human: human_team_id == Some(row.team_id),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GameHubDto {
    pub summary: GameSummary,
    pub team: TeamCardDto,
    pub competition_name: String,
    pub next_match: Option<NextMatchDto>,
    pub last_result: Option<LastResultDto>,
    pub standings: Vec<StandingRowDto>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SquadPlayerDto {
    pub id: Uuid,
    pub role: PlayerRole,
    pub name: String,
    pub age: u8,
    pub overall: u8,
    pub passing: u8,
    pub dribbling: u8,
    pub finishing: u8,
    pub first_touch: u8,
    pub positioning: u8,
    pub decisions: u8,
    pub pace: u8,
    pub stamina: u8,
    pub strength: u8,
    pub condition: f32,
    pub status: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SquadDto {
    pub team: TeamCardDto,
    pub players: Vec<SquadPlayerDto>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CalendarMatchDto {
    pub id: Uuid,
    pub home_team: String,
    pub away_team: String,
    pub score: Option<String>,
    pub played: bool,
    pub is_human_match: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CalendarDayDto {
    pub day_number: u32,
    pub date: String,
    pub played: bool,
    pub matches: Vec<CalendarMatchDto>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MatchEventDto {
    pub minute: u32,
    pub event_type: MatchEventType,
    pub team_id: Option<Uuid>,
    pub team_name: String,
    pub player_name: String,
    pub assist_name: String,
    pub commentary: String,
    pub home_goals: u32,
    pub away_goals: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PlayedMatchDto {
    pub id: Uuid,
    pub home_team: String,
    pub away_team: String,
    pub score: String,
    pub home_goals: u32,
    pub away_goals: u32,
    pub home_penalty_goals: Option<u32>,
    pub away_penalty_goals: Option<u32>,
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
    pub events: Vec<MatchEventDto>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PlayMatchDayResultDto {
    pub season_completed: bool,
    pub match_day: Option<u32>,
    pub human_match: Option<PlayedMatchDto>,
    pub simulated_matches: Vec<PlayedMatchDto>,
}

struct EventCommentaryContext<'a> {
    game_state: &'a GameState,
    event: &'a MatchEvent,
    game_match: &'a Match,
    event_team_name: &'a str,
    player_name: &'a str,
    assist_name: &'a str,
    home_goals: u32,
    away_goals: u32,
}

#[tauri::command]
pub fn preview_new_game(input: NewGameInput) -> Result<NewGamePreview, String> {
    new_game::preview_new_game(input)
}

#[tauri::command]
pub fn create_new_game(input: NewGameInput, state: State<AppState>) -> Result<GameSummary, String> {
    let game_state = new_game::create_new_game(input)?;
    let summary = GameSummary::from_state(&game_state)?;
    *state
        .current_game
        .lock()
        .map_err(|error| error.to_string())? = Some(game_state);
    Ok(summary)
}

#[tauri::command]
pub fn current_game_summary(state: State<AppState>) -> Result<Option<GameSummary>, String> {
    state
        .current_game
        .lock()
        .map_err(|error| error.to_string())?
        .as_ref()
        .map(GameSummary::from_state)
        .transpose()
}

#[tauri::command]
pub fn get_game_hub(state: State<AppState>) -> Result<Option<GameHubDto>, String> {
    let guard = state
        .current_game
        .lock()
        .map_err(|error| error.to_string())?;
    let Some(game_state) = guard.as_ref() else {
        return Ok(None);
    };

    let team = game_state
        .human_team()
        .ok_or_else(|| "Human team is missing".to_string())?;
    let competition = game_state.current_competition();
    let standings = competition
        .map(|competition| sort_standings(&competition.standings))
        .unwrap_or_default()
        .iter()
        .enumerate()
        .map(|(index, row)| StandingRowDto::from_row(index + 1, row, game_state.human_team_id))
        .collect();

    Ok(Some(GameHubDto {
        summary: GameSummary::from_state(game_state)?,
        team: TeamCardDto::from(team),
        competition_name: competition
            .map(|competition| {
                format!(
                    "Campionato CSI {} | Serie Oro | Girone {}",
                    competition.province, competition.girone
                )
            })
            .unwrap_or_default(),
        next_match: next_match_dto(game_state, team.id),
        last_result: last_result_dto(game_state, team.id),
        standings,
    }))
}

#[tauri::command]
pub fn get_squad(state: State<AppState>) -> Result<Option<SquadDto>, String> {
    let guard = state
        .current_game
        .lock()
        .map_err(|error| error.to_string())?;
    let Some(game_state) = guard.as_ref() else {
        return Ok(None);
    };
    let team = game_state
        .human_team()
        .ok_or_else(|| "Human team is missing".to_string())?;

    let mut players: Vec<SquadPlayerDto> = team
        .squad
        .iter()
        .map(|player| {
            let status = if let Some(injury) = &player.injury {
                format!("Infortunato: {} gg", injury.days_remaining)
            } else if player.suspended {
                "Squalificato".to_string()
            } else {
                String::new()
            };
            SquadPlayerDto {
                id: player.id,
                role: player.role,
                name: player.full_name(),
                age: player.age,
                overall: player.overall,
                passing: player.attributes.technical.passing,
                dribbling: player.attributes.technical.dribbling,
                finishing: player.attributes.technical.finishing,
                first_touch: player.attributes.technical.first_touch,
                positioning: player.attributes.mental.positioning,
                decisions: player.attributes.mental.decisions,
                pace: player.attributes.physical.pace,
                stamina: player.attributes.physical.stamina,
                strength: player.attributes.physical.strength,
                condition: player.condition,
                status,
            }
        })
        .collect();
    players.sort_by_key(|player| (role_order(player.role), std::cmp::Reverse(player.overall)));

    Ok(Some(SquadDto {
        team: TeamCardDto::from(team),
        players,
    }))
}

#[tauri::command]
pub fn get_standings(state: State<AppState>) -> Result<Vec<StandingRowDto>, String> {
    let guard = state
        .current_game
        .lock()
        .map_err(|error| error.to_string())?;
    let Some(game_state) = guard.as_ref() else {
        return Ok(vec![]);
    };
    let Some(competition) = game_state.current_competition() else {
        return Ok(vec![]);
    };
    Ok(sort_standings(&competition.standings)
        .iter()
        .enumerate()
        .map(|(index, row)| StandingRowDto::from_row(index + 1, row, game_state.human_team_id))
        .collect())
}

#[tauri::command]
pub fn get_calendar(state: State<AppState>) -> Result<Vec<CalendarDayDto>, String> {
    let guard = state
        .current_game
        .lock()
        .map_err(|error| error.to_string())?;
    let Some(game_state) = guard.as_ref() else {
        return Ok(vec![]);
    };

    let days = game_state
        .season
        .calendar
        .iter()
        .map(|day| CalendarDayDto {
            day_number: day.day_number,
            date: day.date.to_string(),
            played: day.played,
            matches: day
                .match_ids
                .iter()
                .filter_map(|match_id| game_state.get_match(*match_id))
                .map(|game_match| CalendarMatchDto {
                    id: game_match.id,
                    home_team: team_name(game_state, game_match.home_team_id),
                    away_team: team_name(game_state, game_match.away_team_id),
                    score: game_match.played.then(|| game_match.score.display()),
                    played: game_match.played,
                    is_human_match: game_state.human_team_id.is_some_and(|human_id| {
                        game_match.home_team_id == human_id || game_match.away_team_id == human_id
                    }),
                })
                .collect(),
        })
        .collect();

    Ok(days)
}

#[tauri::command]
pub fn play_next_match(state: State<AppState>) -> Result<PlayMatchDayResultDto, String> {
    let mut guard = state
        .current_game
        .lock()
        .map_err(|error| error.to_string())?;
    let Some(game_state) = guard.as_mut() else {
        return Err("Nessuna partita in corso".to_string());
    };
    play_next_match_day(game_state)
}

fn play_next_match_day(game_state: &mut GameState) -> Result<PlayMatchDayResultDto, String> {
    let human_team_id = game_state
        .human_team_id
        .ok_or_else(|| "Squadra umana non impostata".to_string())?;
    let Some(human_match) = game_state.get_next_match_for_team(human_team_id).cloned() else {
        advance_season(game_state)?;
        return Ok(PlayMatchDayResultDto {
            season_completed: true,
            match_day: None,
            human_match: None,
            simulated_matches: vec![],
        });
    };

    let match_day = human_match.match_day;
    let match_ids = game_state
        .season
        .calendar
        .iter()
        .find(|day| day.day_number == match_day)
        .map(|day| day.match_ids.clone())
        .ok_or_else(|| "Giornata non trovata".to_string())?;

    let mut results = Vec::new();
    for match_id in match_ids {
        let Some(scheduled_match) = game_state.get_match(match_id).cloned() else {
            continue;
        };
        if scheduled_match.played {
            continue;
        }
        let home = game_state
            .get_team(scheduled_match.home_team_id)
            .cloned()
            .ok_or_else(|| "Squadra di casa mancante".to_string())?;
        let away = game_state
            .get_team(scheduled_match.away_team_id)
            .cloned()
            .ok_or_else(|| "Squadra ospite mancante".to_string())?;
        let rules = game_state
            .competitions
            .get(&scheduled_match.competition_id.to_string())
            .map(|competition| competition.rules.clone())
            .unwrap_or_default();
        let mut rng = ChaCha8Rng::seed_from_u64(match_seed(
            game_state.config.seed,
            match_day,
            scheduled_match.id,
        ));
        results.push(simulate_match(
            &mut rng,
            &scheduled_match,
            &home,
            &away,
            &rules,
        ));
    }

    let mut human_result = None;
    let mut simulated_matches = Vec::new();
    for result in results {
        let dto = played_match_dto(game_state, &result);
        if result.id == human_match.id {
            human_result = Some(dto.clone());
        }
        if let Some(competition) = game_state
            .competitions
            .get_mut(&result.competition_id.to_string())
        {
            update_standings(competition, &result);
            competition.current_match_day = match_day;
        }
        game_state.matches.insert(result.id.to_string(), result);
        simulated_matches.push(dto);
    }

    if let Some(day) = game_state
        .season
        .calendar
        .iter_mut()
        .find(|day| day.day_number == match_day)
    {
        day.played = true;
        game_state.season.current_date = day.date;
    }

    Ok(PlayMatchDayResultDto {
        season_completed: false,
        match_day: Some(match_day),
        human_match: human_result,
        simulated_matches,
    })
}

fn match_seed(base_seed: u64, match_day: u32, match_id: Uuid) -> u64 {
    match_id
        .as_bytes()
        .iter()
        .fold(base_seed ^ match_day as u64, |seed, byte| {
            seed.rotate_left(5) ^ *byte as u64
        })
}

fn role_order(role: PlayerRole) -> u8 {
    match role {
        PlayerRole::Gk => 0,
        PlayerRole::Def => 1,
        PlayerRole::Mid => 2,
        PlayerRole::Fwd => 3,
    }
}

fn next_match_dto(
    game_state: &crate::domain::models::GameState,
    team_id: Uuid,
) -> Option<NextMatchDto> {
    let game_match = game_state.get_next_match_for_team(team_id)?;
    let home_team = team_name(game_state, game_match.home_team_id);
    let away_team = team_name(game_state, game_match.away_team_id);
    let opponent = if game_match.home_team_id == team_id {
        away_team.clone()
    } else {
        home_team.clone()
    };
    let location = if game_match.home_team_id == team_id {
        "Casa"
    } else {
        "Trasferta"
    }
    .to_string();
    Some(NextMatchDto {
        id: game_match.id,
        match_day: game_match.match_day,
        date: game_match.match_date.map(|date| date.to_string()),
        home_team,
        away_team,
        opponent,
        location,
    })
}

fn last_result_dto(
    game_state: &crate::domain::models::GameState,
    team_id: Uuid,
) -> Option<LastResultDto> {
    for day in game_state.season.calendar.iter().rev() {
        if !day.played {
            continue;
        }
        for match_id in &day.match_ids {
            let Some(game_match) = game_state.get_match(*match_id) else {
                continue;
            };
            if !game_match.played {
                continue;
            }
            if game_match.home_team_id != team_id && game_match.away_team_id != team_id {
                continue;
            }
            return Some(LastResultDto {
                home_team: team_name(game_state, game_match.home_team_id),
                away_team: team_name(game_state, game_match.away_team_id),
                score: game_match.score.display(),
            });
        }
    }
    None
}

fn played_match_dto(game_state: &GameState, game_match: &Match) -> PlayedMatchDto {
    let penalty_shootout = game_match.score.penalty_shootout.as_ref();

    PlayedMatchDto {
        id: game_match.id,
        home_team: team_name(game_state, game_match.home_team_id),
        away_team: team_name(game_state, game_match.away_team_id),
        score: game_match.score.display(),
        home_goals: game_match.score.home_goals,
        away_goals: game_match.score.away_goals,
        home_penalty_goals: penalty_shootout.map(|shootout| shootout.home_goals()),
        away_penalty_goals: penalty_shootout.map(|shootout| shootout.away_goals()),
        home_possession: game_match.home_possession,
        away_possession: game_match.away_possession,
        home_shots: game_match.home_shots,
        away_shots: game_match.away_shots,
        home_shots_on_target: game_match.home_shots_on_target,
        away_shots_on_target: game_match.away_shots_on_target,
        home_fouls: game_match.home_fouls,
        away_fouls: game_match.away_fouls,
        home_corners: game_match.home_corners,
        away_corners: game_match.away_corners,
        events: match_event_dtos(game_state, game_match),
    }
}

fn match_event_dtos(game_state: &GameState, game_match: &Match) -> Vec<MatchEventDto> {
    let mut home_goals = 0;
    let mut away_goals = 0;
    game_match
        .events
        .iter()
        .map(|event| {
            if event.event_type == MatchEventType::Gol {
                if event.team_id == Some(game_match.home_team_id) {
                    home_goals += 1;
                } else if event.team_id == Some(game_match.away_team_id) {
                    away_goals += 1;
                }
            }

            let team_name = event
                .team_id
                .map(|team_id| team_name(game_state, team_id))
                .unwrap_or_default();
            let player_name = event
                .player_id
                .map(|player_id| lookup_player_name(game_state, player_id))
                .unwrap_or_default();
            let assist_name = event
                .assist_player_id
                .map(|player_id| lookup_player_name(game_state, player_id))
                .unwrap_or_default();
            let commentary = event_commentary(EventCommentaryContext {
                game_state,
                event,
                game_match,
                event_team_name: &team_name,
                player_name: &player_name,
                assist_name: &assist_name,
                home_goals,
                away_goals,
            });

            MatchEventDto {
                minute: event.minute,
                event_type: event.event_type,
                team_id: event.team_id,
                team_name,
                player_name,
                assist_name,
                commentary,
                home_goals,
                away_goals,
            }
        })
        .collect()
}

fn event_commentary(context: EventCommentaryContext<'_>) -> String {
    let home = team_name(context.game_state, context.game_match.home_team_id);
    let away = team_name(context.game_state, context.game_match.away_team_id);
    let opponent = match context.event.team_id {
        Some(team_id) if team_id == context.game_match.home_team_id => away.clone(),
        Some(team_id) if team_id == context.game_match.away_team_id => home.clone(),
        _ => String::new(),
    };

    let vars = CommentaryVars {
        team: context.event_team_name.to_string(),
        opponent,
        player: context.player_name.to_string(),
        scorer: context.player_name.to_string(),
        assist: context.assist_name.to_string(),
        home,
        away,
        home_goals: context.home_goals,
        away_goals: context.away_goals,
    };

    generate_commentary(context.event.event_type, &vars, context.event.minute)
}

fn team_name(game_state: &GameState, team_id: Uuid) -> String {
    game_state
        .get_team(team_id)
        .map(|team| team.name.clone())
        .unwrap_or_else(|| "?".to_string())
}

fn lookup_player_name(game_state: &GameState, player_id: Uuid) -> String {
    game_state
        .teams
        .values()
        .flat_map(|team| team.squad.iter())
        .find(|player| player.id == player_id)
        .map(|player| player.short_name())
        .unwrap_or_else(|| "?".to_string())
}

#[allow(dead_code)]
fn _match_type_is_used(_: &Match) {}

#[cfg(test)]
mod tests {
    use crate::domain::services::new_game::{NewGameInput, create_new_game};

    use super::*;

    fn test_input() -> NewGameInput {
        NewGameInput {
            region: "Lombardia".to_string(),
            province: "Varese".to_string(),
            comune: "Varese".to_string(),
            team_name: "Real Oratorio".to_string(),
            stadium_name: "Campo Test".to_string(),
            color_primary: "rosso".to_string(),
            color_secondary: "blu".to_string(),
            season_year: "2025-2026".to_string(),
            seed: Some(456),
        }
    }

    #[test]
    fn play_next_match_day_simulates_whole_day_and_updates_standings() {
        let mut state = create_new_game(test_input()).expect("new game should be created");
        let human_team_id = state.human_team_id.expect("human team should exist");
        let human_match = state
            .get_next_match_for_team(human_team_id)
            .expect("human team should have a next match")
            .clone();
        let match_day_id = human_match.match_day;
        let match_ids = state
            .season
            .calendar
            .iter()
            .find(|day| day.day_number == match_day_id)
            .expect("match day should exist")
            .match_ids
            .clone();
        let competition_id = human_match.competition_id;

        let result = play_next_match_day(&mut state).expect("match day should be simulated");

        assert!(!result.season_completed);
        assert_eq!(result.match_day, Some(match_day_id));
        assert_eq!(result.simulated_matches.len(), match_ids.len());
        assert!(result.human_match.is_some());
        assert!(match_ids.iter().all(|id| {
            state
                .matches
                .get(&id.to_string())
                .is_some_and(|game_match| game_match.played && game_match.result.is_some())
        }));
        assert!(
            state
                .season
                .calendar
                .iter()
                .find(|day| day.day_number == match_day_id)
                .is_some_and(|day| day.played)
        );

        let competition = state
            .competitions
            .get(&competition_id.to_string())
            .expect("competition should exist");
        assert_eq!(competition.current_match_day, match_day_id);
        let competition_match_count = match_ids
            .iter()
            .filter(|id| {
                state
                    .matches
                    .get(&id.to_string())
                    .is_some_and(|game_match| game_match.competition_id == competition_id)
            })
            .count();
        assert_eq!(
            competition
                .standings
                .iter()
                .map(|row| row.played)
                .sum::<u32>(),
            (competition_match_count * 2) as u32
        );
        assert!(competition.standings.iter().any(|row| row.points > 0));
    }

    #[test]
    fn play_next_match_day_advances_season_when_no_matches_remain() {
        let mut state = create_new_game(test_input()).expect("new game should be created");
        for day in &mut state.season.calendar {
            day.played = true;
        }
        for game_match in state.matches.values_mut() {
            game_match.played = true;
        }

        let result = play_next_match_day(&mut state).expect("season should advance");

        assert!(result.season_completed);
        assert_eq!(state.season.year, "2026-2027");
        assert!(state.season.calendar.iter().all(|day| !day.played));
    }
}
