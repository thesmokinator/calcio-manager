use std::collections::{BTreeMap, HashMap};

use chrono::NaiveDate;
use rand::{Rng, SeedableRng};
use rand_chacha::ChaCha8Rng;
use serde::{Deserialize, Serialize};
use uuid::Uuid;

use crate::domain::engine::calendar::{generate_match_schedule, generate_round_robin};
use crate::domain::engine::competition::initialize_standings;
use crate::domain::engine::comuni::{get_comuni, get_region_for_province};
use crate::domain::engine::player_gen::{
    TeamGenerationInput, generate_team, generate_tournament_teams,
};
use crate::domain::engine::tournament::{
    calculate_gironi_structure, collect_team_ids, generate_gironi, human_girone_index,
    select_tournament_comuni,
};
use crate::domain::models::{
    AgeCategory, Competition, CompetitionRules, GameConfig, GameFormat, GameState, Match, MatchDay,
    Season, SeasonPhase, Team,
};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NewGameInput {
    pub region: String,
    pub province: String,
    pub comune: String,
    pub team_name: String,
    pub stadium_name: String,
    pub color_primary: String,
    pub color_secondary: String,
    pub season_year: String,
    pub seed: Option<u64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TeamPreview {
    pub id: Uuid,
    pub name: String,
    pub city: String,
    pub colors: (String, String),
    pub average_overall: f32,
    pub is_human: bool,
}

impl From<&Team> for TeamPreview {
    fn from(team: &Team) -> Self {
        Self {
            id: team.id,
            name: team.name.clone(),
            city: team.city.clone(),
            colors: team.colors.clone(),
            average_overall: (team.squad_average_overall() * 10.0).round() / 10.0,
            is_human: team.is_human,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GironePreview {
    pub letter: String,
    pub teams: Vec<TeamPreview>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NewGamePreview {
    pub season_year: String,
    pub num_groups: usize,
    pub teams_per_group: usize,
    pub total_teams: usize,
    pub human_girone_index: usize,
    pub gironi: Vec<GironePreview>,
    pub seed: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GameSummary {
    pub team_name: String,
    pub comune: String,
    pub province: String,
    pub region: String,
    pub season_year: String,
    pub num_groups: usize,
    pub human_team_id: Uuid,
    pub current_match_day: u32,
    pub total_match_days: usize,
}

impl GameSummary {
    pub fn from_state(state: &GameState) -> Result<Self, String> {
        let team = state
            .human_team()
            .ok_or_else(|| "Human team is missing".to_string())?;
        Ok(Self {
            team_name: team.name.clone(),
            comune: state.config.comune.clone(),
            province: state.config.province.clone(),
            region: state.config.region.clone(),
            season_year: state.season.year.clone(),
            num_groups: state.config.num_groups,
            human_team_id: team.id,
            current_match_day: state.season.current_match_day_number(),
            total_match_days: state.season.calendar.len(),
        })
    }
}

fn seed_or_random(seed: Option<u64>) -> u64 {
    seed.unwrap_or_else(|| rand::thread_rng().r#gen())
}

fn build_teams_and_gironi(input: &NewGameInput, seed: u64) -> Result<Vec<Vec<Team>>, String> {
    let mut rng = ChaCha8Rng::seed_from_u64(seed);
    let all_comuni = get_comuni(&input.province)?;
    let (num_groups, teams_per_group) = calculate_gironi_structure(all_comuni.len(), 6, 10);
    let opponent_comuni = select_tournament_comuni(
        &mut rng,
        &all_comuni,
        &input.comune,
        num_groups,
        teams_per_group,
    );
    let mut opponent_teams = generate_tournament_teams(
        &mut rng,
        &opponent_comuni,
        &input.province,
        AgeCategory::Open,
        &input.season_year,
    )?;

    let human_team = generate_team(
        &mut rng,
        TeamGenerationInput {
            name: input.team_name.trim().to_string(),
            city: input.comune.clone(),
            province: input.province.clone(),
            quality_base: 10,
            category: AgeCategory::Open,
            season: input.season_year.clone(),
            is_human: true,
            colors: Some((input.color_primary.clone(), input.color_secondary.clone())),
            stadium_name: Some(input.stadium_name.clone()),
        },
    )?;

    let mut all_teams = vec![human_team];
    all_teams.append(&mut opponent_teams);
    Ok(generate_gironi(&all_teams, num_groups))
}

pub fn preview_new_game(input: NewGameInput) -> Result<NewGamePreview, String> {
    validate_input(&input)?;
    let seed = seed_or_random(input.seed);
    let gironi = build_teams_and_gironi(&input, seed)?;
    let human_index = human_girone_index(&gironi);
    let total_teams = gironi.iter().map(Vec::len).sum();
    let teams_per_group = gironi.first().map(Vec::len).unwrap_or(0);

    Ok(NewGamePreview {
        season_year: input.season_year,
        num_groups: gironi.len(),
        teams_per_group,
        total_teams,
        human_girone_index: human_index,
        gironi: gironi
            .iter()
            .enumerate()
            .map(|(index, teams)| GironePreview {
                letter: girone_letter(index),
                teams: teams.iter().map(TeamPreview::from).collect(),
            })
            .collect(),
        seed,
    })
}

pub fn create_new_game(input: NewGameInput) -> Result<GameState, String> {
    validate_input(&input)?;
    let seed = seed_or_random(input.seed);
    let region = if input.region.trim().is_empty() {
        get_region_for_province(&input.province)?.unwrap_or_default()
    } else {
        input.region.clone()
    };
    let gironi = build_teams_and_gironi(&input, seed)?;
    let teams_per_group = gironi.first().map(Vec::len).unwrap_or(0);
    let num_groups = gironi.len();
    let rules = CompetitionRules::for_category(AgeCategory::Open, GameFormat::C7);

    let mut all_teams = HashMap::new();
    let mut competitions = HashMap::new();
    let mut matches = HashMap::new();
    let mut calendar_by_day: BTreeMap<u32, MatchDay> = BTreeMap::new();
    let mut human_team_id = None;

    for (index, girone_teams) in gironi.into_iter().enumerate() {
        let letter = girone_letter(index);
        let team_ids = collect_team_ids(&girone_teams);
        let mut competition = Competition::new(
            letter,
            input.province.clone(),
            region.clone(),
            team_ids.clone(),
            rules.clone(),
        );

        let team_names: HashMap<Uuid, String> = girone_teams
            .iter()
            .map(|team| (team.id, team.name.clone()))
            .collect();
        initialize_standings(&mut competition, &team_names);

        let rounds = generate_round_robin(&team_ids, true);
        let (competition_matches, match_days) =
            generate_match_schedule(&rounds, competition.id, None, 7, &input.season_year)?;
        competition.total_match_days = match_days.len() as u32;
        competition.match_ids = competition_matches
            .iter()
            .map(|game_match| game_match.id)
            .collect();

        for match_day in match_days {
            calendar_by_day
                .entry(match_day.day_number)
                .and_modify(|existing| existing.match_ids.extend(match_day.match_ids.clone()))
                .or_insert(match_day);
        }

        for game_match in competition_matches {
            matches.insert(game_match.id.to_string(), game_match);
        }
        for team in girone_teams {
            if team.is_human {
                human_team_id = Some(team.id);
            }
            all_teams.insert(team.id.to_string(), team);
        }
        competitions.insert(competition.id.to_string(), competition);
    }

    let start_year = input
        .season_year
        .split('-')
        .next()
        .unwrap_or("2025")
        .parse::<i32>()
        .map_err(|error| error.to_string())?;
    let current_date = NaiveDate::from_ymd_opt(start_year, 8, 1)
        .ok_or_else(|| "Invalid season start date".to_string())?;

    let calendar: Vec<MatchDay> = calendar_by_day.into_values().collect();
    let season = Season {
        id: Uuid::new_v4(),
        year: input.season_year.clone(),
        competition_ids: competitions
            .values()
            .map(|competition| competition.id)
            .collect(),
        calendar,
        current_date,
        phase: SeasonPhase::PreSeason,
    };

    let config = GameConfig {
        format: GameFormat::C7,
        category: AgeCategory::Open,
        comune: input.comune,
        province: input.province,
        region,
        num_groups,
        teams_per_group,
        season_year: input.season_year,
        rules,
        seed,
    };

    Ok(GameState {
        config,
        season,
        teams: all_teams,
        competitions,
        matches,
        human_team_id,
    })
}

fn validate_input(input: &NewGameInput) -> Result<(), String> {
    if input.province.trim().is_empty() {
        return Err("Seleziona una provincia".to_string());
    }
    if input.comune.trim().is_empty() {
        return Err("Seleziona un comune".to_string());
    }
    if input.team_name.trim().is_empty() {
        return Err("Inserisci il nome della squadra".to_string());
    }
    if input.season_year.trim().is_empty() {
        return Err("Stagione non valida".to_string());
    }
    Ok(())
}

fn girone_letter(index: usize) -> String {
    if index < 26 {
        ((b'A' + index as u8) as char).to_string()
    } else {
        (index + 1).to_string()
    }
}

#[allow(dead_code)]
fn _assert_send_sync() {
    fn assert_send_sync<T: Send + Sync>() {}
    assert_send_sync::<GameState>();
    assert_send_sync::<Match>();
}
