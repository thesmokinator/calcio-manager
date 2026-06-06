use std::collections::{BTreeMap, HashMap};

use chrono::NaiveDate;
use uuid::Uuid;

use crate::domain::engine::calendar::{generate_match_schedule, generate_round_robin};
use crate::domain::engine::competition::initialize_standings;
use crate::domain::models::{GameState, Match, MatchDay, Season, SeasonPhase};

pub fn compute_season_year(start_year: i32) -> String {
    format!("{}-{}", start_year, start_year + 1)
}

pub fn advance_season(game_state: &mut GameState) -> Result<(), String> {
    let current_start = game_state
        .season
        .year
        .split('-')
        .next()
        .unwrap_or("2025")
        .parse::<i32>()
        .map_err(|error| error.to_string())?;
    let new_start = current_start + 1;
    let new_year = compute_season_year(new_start);

    let mut all_matches: HashMap<String, Match> = HashMap::new();
    let mut calendar_by_day: BTreeMap<u32, MatchDay> = BTreeMap::new();

    for competition in game_state.competitions.values_mut() {
        let team_names: HashMap<Uuid, String> = competition
            .team_ids
            .iter()
            .filter_map(|team_id| {
                game_state
                    .teams
                    .get(&team_id.to_string())
                    .map(|team| (*team_id, team.name.clone()))
            })
            .collect();
        initialize_standings(competition, &team_names);
        competition.current_match_day = 0;
        competition.completed = false;

        let rounds = generate_round_robin(&competition.team_ids, true);
        let (matches, match_days) =
            generate_match_schedule(&rounds, competition.id, None, 7, &new_year)?;
        competition.match_ids = matches.iter().map(|game_match| game_match.id).collect();
        competition.total_match_days = match_days.len() as u32;

        for match_day in match_days {
            calendar_by_day
                .entry(match_day.day_number)
                .and_modify(|existing| existing.match_ids.extend(match_day.match_ids.clone()))
                .or_insert(match_day);
        }

        for game_match in matches {
            all_matches.insert(game_match.id.to_string(), game_match);
        }
    }

    let current_date = NaiveDate::from_ymd_opt(new_start, 8, 1)
        .ok_or_else(|| "Invalid new season date".to_string())?;
    game_state.season = Season {
        id: Uuid::new_v4(),
        year: new_year.clone(),
        competition_ids: game_state
            .competitions
            .values()
            .map(|competition| competition.id)
            .collect(),
        calendar: calendar_by_day.into_values().collect(),
        current_date,
        phase: SeasonPhase::PreSeason,
    };
    game_state.matches = all_matches;
    game_state.config.season_year = new_year;

    Ok(())
}

#[cfg(test)]
mod tests {
    use crate::domain::services::new_game::{NewGameInput, create_new_game};

    use super::*;

    #[test]
    fn computes_next_season_year() {
        assert_eq!(compute_season_year(2026), "2026-2027");
    }

    #[test]
    fn advance_season_regenerates_calendar_matches_and_standings() {
        let mut state = create_new_game(NewGameInput {
            region: "Lombardia".to_string(),
            province: "Varese".to_string(),
            comune: "Varese".to_string(),
            team_name: "Real Oratorio".to_string(),
            stadium_name: "Campo Test".to_string(),
            color_primary: "rosso".to_string(),
            color_secondary: "blu".to_string(),
            season_year: "2025-2026".to_string(),
            seed: Some(123),
        })
        .expect("new game should be created");
        let old_season_id = state.season.id;
        let old_match_ids: std::collections::HashSet<_> = state.matches.keys().cloned().collect();

        for competition in state.competitions.values_mut() {
            for row in &mut competition.standings {
                row.played = 3;
                row.points = 7;
                row.goals_for = 5;
            }
            competition.current_match_day = competition.total_match_days;
            competition.completed = true;
        }

        advance_season(&mut state).expect("season should advance");

        assert_ne!(state.season.id, old_season_id);
        assert_eq!(state.season.year, "2026-2027");
        assert_eq!(state.config.season_year, "2026-2027");
        assert!(!state.season.calendar.is_empty());
        assert!(state.season.calendar.iter().all(|day| !day.played));
        assert!(state.matches.keys().all(|id| !old_match_ids.contains(id)));
        assert!(state.matches.values().all(|game_match| !game_match.played));
        assert!(state.competitions.values().all(|competition| {
            !competition.completed
                && competition.current_match_day == 0
                && !competition.match_ids.is_empty()
                && competition.standings.iter().all(|row| {
                    row.played == 0
                        && row.points == 0
                        && row.goals_for == 0
                        && row.goals_against == 0
                })
        }));
    }
}
