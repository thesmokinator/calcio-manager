use chrono::{Datelike, Duration, NaiveDate};
use uuid::Uuid;

use crate::domain::models::{Match, MatchDay};

pub fn generate_round_robin(team_ids: &[Uuid], home_and_away: bool) -> Vec<Vec<(Uuid, Uuid)>> {
    let mut teams = team_ids.to_vec();
    let mut n = teams.len();
    let bye_id = Uuid::nil();

    if !n.is_multiple_of(2) {
        teams.push(bye_id);
        n += 1;
    }

    let half = n / 2;
    let fixed = teams[0];
    let mut rotation = teams[1..].to_vec();
    let mut rounds = Vec::new();

    for _ in 0..(n - 1) {
        let mut round_matches = vec![(fixed, *rotation.last().expect("rotation is never empty"))];

        for j in 1..half {
            let home = rotation[j - 1];
            let away = rotation[n - 2 - j];
            round_matches.push((home, away));
        }

        round_matches.retain(|(home, away)| *home != bye_id && *away != bye_id);
        rounds.push(round_matches);

        if let Some(last) = rotation.pop() {
            rotation.insert(0, last);
        }
    }

    if home_and_away {
        let return_rounds: Vec<Vec<(Uuid, Uuid)>> = rounds
            .iter()
            .map(|round| round.iter().map(|(home, away)| (*away, *home)).collect())
            .collect();
        rounds.extend(return_rounds);
    }

    rounds
}

pub fn season_start_date(season_year: &str) -> Result<NaiveDate, String> {
    let start_year = season_year
        .split('-')
        .next()
        .ok_or_else(|| "Invalid season year".to_string())?
        .parse::<i32>()
        .map_err(|error| error.to_string())?;

    let sept_1 = NaiveDate::from_ymd_opt(start_year, 9, 1)
        .ok_or_else(|| "Invalid September date".to_string())?;
    let days_until_saturday =
        (5_i64 - sept_1.weekday().num_days_from_monday() as i64).rem_euclid(7);
    let first_saturday = sept_1 + Duration::days(days_until_saturday);
    Ok(first_saturday + Duration::days(14))
}

pub fn generate_match_schedule(
    rounds: &[Vec<(Uuid, Uuid)>],
    competition_id: Uuid,
    start_date: Option<NaiveDate>,
    interval_days: i64,
    season_year: &str,
) -> Result<(Vec<Match>, Vec<MatchDay>), String> {
    let start_date = match start_date {
        Some(date) => date,
        None => season_start_date(season_year)?,
    };

    let mut matches = Vec::new();
    let mut match_days = Vec::new();

    for (round_index, round_matches) in rounds.iter().enumerate() {
        let match_day_date = start_date + Duration::days(round_index as i64 * interval_days);
        let mut match_ids = Vec::new();

        for (home_id, away_id) in round_matches {
            let game_match = Match::new(
                *home_id,
                *away_id,
                competition_id,
                round_index as u32 + 1,
                Some(match_day_date),
            );
            match_ids.push(game_match.id);
            matches.push(game_match);
        }

        match_days.push(MatchDay {
            day_number: round_index as u32 + 1,
            date: match_day_date,
            match_ids,
            played: false,
        });
    }

    Ok((matches, match_days))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn generates_home_and_away_schedule() {
        let teams = vec![
            Uuid::new_v4(),
            Uuid::new_v4(),
            Uuid::new_v4(),
            Uuid::new_v4(),
        ];
        let rounds = generate_round_robin(&teams, true);
        assert_eq!(rounds.len(), 6);
        assert!(rounds.iter().all(|round| round.len() == 2));
    }

    #[test]
    fn season_starts_on_third_saturday_of_september() {
        let start = season_start_date("2025-2026").unwrap();
        assert_eq!(start, NaiveDate::from_ymd_opt(2025, 9, 20).unwrap());
    }
}
