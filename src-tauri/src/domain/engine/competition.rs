use std::cmp::Reverse;
use std::collections::HashMap;

use uuid::Uuid;

use crate::domain::models::{Competition, Match, MatchEventType, MatchResult, StandingRow};

pub fn initialize_standings(competition: &mut Competition, team_names: &HashMap<Uuid, String>) {
    competition.standings = competition
        .team_ids
        .iter()
        .map(|team_id| {
            StandingRow::new(
                *team_id,
                team_names.get(team_id).cloned().unwrap_or_default(),
            )
        })
        .collect();
}

pub fn update_standings(competition: &mut Competition, game_match: &Match) {
    if game_match.result.is_none() {
        return;
    }

    let home_index = competition
        .standings
        .iter()
        .position(|row| row.team_id == game_match.home_team_id);
    let away_index = competition
        .standings
        .iter()
        .position(|row| row.team_id == game_match.away_team_id);
    let (Some(home_index), Some(away_index)) = (home_index, away_index) else {
        return;
    };

    let home_points = game_match.get_points(game_match.home_team_id);
    let away_points = game_match.get_points(game_match.away_team_id);
    let home_id_str = game_match.home_team_id.to_string();
    let away_id_str = game_match.away_team_id.to_string();

    if home_index < away_index {
        let (left, right) = competition.standings.split_at_mut(away_index);
        apply_result(
            &mut left[home_index],
            &mut right[0],
            game_match,
            home_points,
            away_points,
            &home_id_str,
            &away_id_str,
        );
    } else {
        let (left, right) = competition.standings.split_at_mut(home_index);
        apply_result(
            &mut right[0],
            &mut left[away_index],
            game_match,
            home_points,
            away_points,
            &home_id_str,
            &away_id_str,
        );
    }
}

fn apply_result(
    home_row: &mut StandingRow,
    away_row: &mut StandingRow,
    game_match: &Match,
    home_points: u32,
    away_points: u32,
    home_id_str: &str,
    away_id_str: &str,
) {
    home_row.played += 1;
    away_row.played += 1;
    home_row.goals_for += game_match.score.home_goals;
    home_row.goals_against += game_match.score.away_goals;
    away_row.goals_for += game_match.score.away_goals;
    away_row.goals_against += game_match.score.home_goals;

    *home_row
        .h2h_goals_for
        .entry(away_id_str.to_string())
        .or_insert(0) += game_match.score.home_goals;
    *home_row
        .h2h_goals_against
        .entry(away_id_str.to_string())
        .or_insert(0) += game_match.score.away_goals;
    *away_row
        .h2h_goals_for
        .entry(home_id_str.to_string())
        .or_insert(0) += game_match.score.away_goals;
    *away_row
        .h2h_goals_against
        .entry(home_id_str.to_string())
        .or_insert(0) += game_match.score.home_goals;

    home_row.points += home_points;
    away_row.points += away_points;
    *home_row
        .h2h_points
        .entry(away_id_str.to_string())
        .or_insert(0) += home_points;
    *away_row
        .h2h_points
        .entry(home_id_str.to_string())
        .or_insert(0) += away_points;

    match game_match.result.expect("result checked by caller") {
        MatchResult::VittoriaCasa => {
            home_row.wins += 1;
            away_row.losses += 1;
        }
        MatchResult::VittoriaTrasferta => {
            away_row.wins += 1;
            home_row.losses += 1;
        }
        MatchResult::VittoriaCasaRigori => {
            home_row.wins_penalties += 1;
            away_row.losses_penalties += 1;
        }
        MatchResult::VittoriaTrasfertaRigori => {
            away_row.wins_penalties += 1;
            home_row.losses_penalties += 1;
        }
        MatchResult::RinunciaCasa => {
            away_row.wins += 1;
            home_row.losses += 1;
        }
        MatchResult::RinunciaTrasferta => {
            home_row.wins += 1;
            away_row.losses += 1;
        }
    }

    for event in &game_match.events {
        match event.event_type {
            MatchEventType::Ammonizione => {
                if event.team_id == Some(game_match.home_team_id) {
                    home_row.yellow_cards += 1;
                } else {
                    away_row.yellow_cards += 1;
                }
            }
            MatchEventType::Espulsione | MatchEventType::DoppiaAmmonizione => {
                if event.team_id == Some(game_match.home_team_id) {
                    home_row.red_cards += 1;
                } else {
                    away_row.red_cards += 1;
                }
            }
            _ => {}
        }
    }
}

pub fn sort_standings(standings: &[StandingRow]) -> Vec<StandingRow> {
    let mut sorted = standings.to_vec();
    sorted.sort_by_key(|row| {
        (
            Reverse(row.points),
            Reverse(row.goal_difference()),
            Reverse(row.goals_for),
            row.discipline_score(),
            row.played,
        )
    });

    let mut i = 0;
    while i < sorted.len() {
        let mut j = i + 1;
        while j < sorted.len() && sorted[j].points == sorted[i].points {
            j += 1;
        }

        if j - i > 1 {
            let tied_ids: Vec<String> = sorted[i..j]
                .iter()
                .map(|row| row.team_id.to_string())
                .collect();
            sorted[i..j].sort_by_key(|row| {
                let h2h_points: u32 = tied_ids
                    .iter()
                    .filter(|team_id| *team_id != &row.team_id.to_string())
                    .map(|team_id| row.h2h_points.get(team_id).copied().unwrap_or(0))
                    .sum();
                let h2h_for: u32 = tied_ids
                    .iter()
                    .filter(|team_id| *team_id != &row.team_id.to_string())
                    .map(|team_id| row.h2h_goals_for.get(team_id).copied().unwrap_or(0))
                    .sum();
                let h2h_against: u32 = tied_ids
                    .iter()
                    .filter(|team_id| *team_id != &row.team_id.to_string())
                    .map(|team_id| row.h2h_goals_against.get(team_id).copied().unwrap_or(0))
                    .sum();

                (
                    Reverse(h2h_points),
                    Reverse(h2h_for as i32 - h2h_against as i32),
                    Reverse(row.goal_difference()),
                    Reverse(row.goals_for),
                    row.discipline_score(),
                )
            });
        }

        i = j;
    }

    sorted
}

#[cfg(test)]
mod tests {
    use crate::domain::models::{CompetitionRules, MatchEvent, MatchScore};

    use super::*;

    fn competition_with_teams(ids: &[Uuid]) -> Competition {
        let mut competition = Competition::new(
            "A",
            "Varese",
            "Lombardia",
            ids.to_vec(),
            CompetitionRules::default(),
        );
        let team_names = ids
            .iter()
            .enumerate()
            .map(|(index, id)| (*id, format!("Team {}", index + 1)))
            .collect();
        initialize_standings(&mut competition, &team_names);
        competition
    }

    #[test]
    fn update_standings_applies_win_points_goals_and_cards() {
        let home = Uuid::new_v4();
        let away = Uuid::new_v4();
        let mut competition = competition_with_teams(&[home, away]);
        let mut game_match = Match::new(home, away, competition.id, 1, None);
        game_match.played = true;
        game_match.score = MatchScore {
            home_goals: 2,
            away_goals: 1,
            penalty_shootout: None,
        };
        game_match.result = Some(MatchResult::VittoriaCasa);
        game_match.events = vec![
            MatchEvent::new(12, MatchEventType::Ammonizione, Some(home)),
            MatchEvent::new(44, MatchEventType::Espulsione, Some(away)),
        ];

        update_standings(&mut competition, &game_match);

        let home_row = competition
            .standings
            .iter()
            .find(|row| row.team_id == home)
            .unwrap();
        let away_row = competition
            .standings
            .iter()
            .find(|row| row.team_id == away)
            .unwrap();
        assert_eq!(home_row.played, 1);
        assert_eq!(home_row.wins, 1);
        assert_eq!(home_row.points, 3);
        assert_eq!(home_row.goals_for, 2);
        assert_eq!(home_row.goals_against, 1);
        assert_eq!(home_row.yellow_cards, 1);
        assert_eq!(away_row.losses, 1);
        assert_eq!(away_row.points, 0);
        assert_eq!(away_row.red_cards, 1);
    }

    #[test]
    fn update_standings_applies_penalty_points() {
        let home = Uuid::new_v4();
        let away = Uuid::new_v4();
        let mut competition = competition_with_teams(&[home, away]);
        let mut game_match = Match::new(home, away, competition.id, 1, None);
        game_match.played = true;
        game_match.score = MatchScore {
            home_goals: 1,
            away_goals: 1,
            penalty_shootout: None,
        };
        game_match.result = Some(MatchResult::VittoriaTrasfertaRigori);

        update_standings(&mut competition, &game_match);

        let home_row = competition
            .standings
            .iter()
            .find(|row| row.team_id == home)
            .unwrap();
        let away_row = competition
            .standings
            .iter()
            .find(|row| row.team_id == away)
            .unwrap();
        assert_eq!(home_row.losses_penalties, 1);
        assert_eq!(home_row.points, 1);
        assert_eq!(away_row.wins_penalties, 1);
        assert_eq!(away_row.points, 2);
    }

    #[test]
    fn sort_standings_uses_head_to_head_for_tied_teams() {
        let team_a = Uuid::new_v4();
        let team_b = Uuid::new_v4();
        let mut competition = competition_with_teams(&[team_a, team_b]);
        let mut first_leg = Match::new(team_a, team_b, competition.id, 1, None);
        first_leg.score = MatchScore {
            home_goals: 2,
            away_goals: 1,
            penalty_shootout: None,
        };
        first_leg.result = Some(MatchResult::VittoriaCasa);
        update_standings(&mut competition, &first_leg);

        let mut second_leg = Match::new(team_b, team_a, competition.id, 2, None);
        second_leg.score = MatchScore {
            home_goals: 1,
            away_goals: 0,
            penalty_shootout: None,
        };
        second_leg.result = Some(MatchResult::VittoriaCasa);
        update_standings(&mut competition, &second_leg);

        let sorted = sort_standings(&competition.standings);
        assert_eq!(sorted[0].team_id, team_a);
        assert_eq!(sorted[0].points, sorted[1].points);
        assert_eq!(sorted[0].goal_difference(), sorted[1].goal_difference());
    }
}
