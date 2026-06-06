use rand::Rng;
use rand::seq::SliceRandom;
use uuid::Uuid;

use crate::domain::models::{
    CompetitionRules, Match, MatchEvent, MatchEventType, MatchResult, MatchScore, PenaltyShootout,
    Player, PlayerRole, TacticStyle, Team,
};

#[derive(Debug, Clone)]
struct MatchState<'a> {
    home: &'a Team,
    away: &'a Team,
    rules: &'a CompetitionRules,
    home_goals: u32,
    away_goals: u32,
    minute: u32,
    home_possession: f32,
    away_possession: f32,
    home_momentum: f32,
    away_momentum: f32,
    home_fouls: u32,
    away_fouls: u32,
    home_shots: u32,
    away_shots: u32,
    home_shots_on_target: u32,
    away_shots_on_target: u32,
    home_corners: u32,
    away_corners: u32,
    home_fatigue: f32,
    away_fatigue: f32,
    events: Vec<MatchEvent>,
}

impl<'a> MatchState<'a> {
    fn new(home: &'a Team, away: &'a Team, rules: &'a CompetitionRules) -> Self {
        Self {
            home,
            away,
            rules,
            home_goals: 0,
            away_goals: 0,
            minute: 0,
            home_possession: 50.0,
            away_possession: 50.0,
            home_momentum: 0.0,
            away_momentum: 0.0,
            home_fouls: 0,
            away_fouls: 0,
            home_shots: 0,
            away_shots: 0,
            home_shots_on_target: 0,
            away_shots_on_target: 0,
            home_corners: 0,
            away_corners: 0,
            home_fatigue: 0.0,
            away_fatigue: 0.0,
            events: Vec::new(),
        }
    }

    fn push(&mut self, event: MatchEvent) {
        self.events.push(event);
    }
}

fn team_attack_strength(team: &Team, fatigue: f32) -> f32 {
    let players = team.available_players();
    if players.is_empty() {
        return 1.0;
    }

    let mut score = 0.0;
    let mut count = 0;

    for player in players
        .iter()
        .filter(|player| player.role == PlayerRole::Fwd)
    {
        score += (player.attributes.technical.finishing as f32 * 2.0
            + player.attributes.technical.dribbling as f32
            + player.attributes.physical.pace as f32)
            / 4.0;
        count += 1;
    }

    for player in players
        .iter()
        .filter(|player| player.role == PlayerRole::Mid)
    {
        score += (player.attributes.technical.passing as f32 * 2.0
            + player.attributes.mental.decisions as f32
            + player.attributes.technical.first_touch as f32)
            / 4.0;
        count += 1;
    }

    if count == 0 {
        return 5.0;
    }

    (score / count as f32 - fatigue * 3.0).max(1.0)
}

fn team_defense_strength(team: &Team, fatigue: f32) -> f32 {
    let players = team.available_players();
    if players.is_empty() {
        return 1.0;
    }

    let mut score = 0.0;
    let mut count = 0;

    for player in players
        .iter()
        .filter(|player| player.role == PlayerRole::Def)
    {
        score += (player.attributes.mental.positioning as f32 * 2.0
            + player.attributes.physical.strength as f32
            + player.attributes.mental.teamwork as f32)
            / 4.0;
        count += 1;
    }

    if let Some(goalkeeper) = players.iter().find(|player| player.role == PlayerRole::Gk) {
        score += (goalkeeper.attributes.goalkeeping.reflexes as f32 * 2.0
            + goalkeeper.attributes.goalkeeping.handling as f32)
            / 3.0;
        count += 1;
    }

    if count == 0 {
        return 5.0;
    }

    (score / count as f32 - fatigue * 2.5).max(1.0)
}

fn team_midfield_strength(team: &Team, fatigue: f32) -> f32 {
    let players = team.available_players();
    let midfielders: Vec<&Player> = players
        .into_iter()
        .filter(|player| player.role == PlayerRole::Mid)
        .collect();
    if midfielders.is_empty() {
        return 5.0;
    }

    let score = midfielders
        .iter()
        .map(|player| {
            (player.attributes.technical.passing as f32 * 2.0
                + player.attributes.mental.teamwork as f32
                + player.attributes.physical.stamina as f32
                + player.attributes.mental.decisions as f32)
                / 5.0
        })
        .sum::<f32>()
        / midfielders.len() as f32;

    (score - fatigue * 2.0).max(1.0)
}

fn tactic_modifier(tactic: TacticStyle) -> (f32, f32, f32) {
    match tactic {
        TacticStyle::Difensiva => (0.8, 1.2, 0.9),
        TacticStyle::Equilibrata => (1.0, 1.0, 1.0),
        TacticStyle::Offensiva => (1.2, 0.8, 1.1),
        TacticStyle::Contropiede => (1.1, 1.0, 0.85),
    }
}

fn event(minute: u32, event_type: MatchEventType, team_id: Option<Uuid>) -> MatchEvent {
    MatchEvent::new(minute, event_type, team_id)
}

fn event_with_player(
    minute: u32,
    event_type: MatchEventType,
    team_id: Uuid,
    player_id: Option<Uuid>,
) -> MatchEvent {
    let mut event = MatchEvent::new(minute, event_type, Some(team_id));
    event.player_id = player_id;
    event
}

fn attacking_player<R: Rng + ?Sized>(rng: &mut R, team: &Team) -> Option<Uuid> {
    let available = team.available_players();
    let attackers: Vec<&Player> = available
        .iter()
        .copied()
        .filter(|player| matches!(player.role, PlayerRole::Fwd | PlayerRole::Mid))
        .collect();
    attackers
        .choose(rng)
        .copied()
        .or_else(|| available.choose(rng).copied())
        .map(|player| player.id)
}

fn fouling_player<R: Rng + ?Sized>(rng: &mut R, team: &Team) -> Option<Uuid> {
    let available = team.available_players();
    let fouling_players: Vec<&Player> = available
        .iter()
        .copied()
        .filter(|player| player.role != PlayerRole::Gk)
        .collect();
    fouling_players
        .choose(rng)
        .copied()
        .or_else(|| available.choose(rng).copied())
        .map(|player| player.id)
}

fn assist_player<R: Rng + ?Sized>(rng: &mut R, team: &Team, scorer_id: Uuid) -> Option<Uuid> {
    team.available_players()
        .into_iter()
        .filter(|player| player.id != scorer_id && player.role != PlayerRole::Gk)
        .collect::<Vec<_>>()
        .choose(rng)
        .copied()
        .map(|player| player.id)
}

fn simulate_tick<R: Rng + ?Sized>(rng: &mut R, state: &mut MatchState<'_>) {
    let home_mid = team_midfield_strength(state.home, state.home_fatigue);
    let away_mid = team_midfield_strength(state.away, state.away_fatigue);
    let (home_attack_mod, home_defense_mod, home_possession_mod) =
        tactic_modifier(state.home.tactic);
    let (away_attack_mod, away_defense_mod, away_possession_mod) =
        tactic_modifier(state.away.tactic);

    let home_possession_weight = home_mid * home_possession_mod + state.home_momentum;
    let away_possession_weight = away_mid * away_possession_mod + state.away_momentum;
    let total = home_possession_weight + away_possession_weight;
    if total > 0.0 {
        state.home_possession = (home_possession_weight / total) * 100.0;
        state.away_possession = 100.0 - state.home_possession;
    }

    let attacking_home = rng.gen_bool((state.home_possession / 100.0).clamp(0.05, 0.95) as f64);
    let possession_team_id = if attacking_home {
        state.home.id
    } else {
        state.away.id
    };
    state.push(event(
        state.minute,
        MatchEventType::Possesso,
        Some(possession_team_id),
    ));

    let (
        attack_team,
        defense_team,
        attack_fatigue,
        defense_fatigue,
        attack_mod,
        defense_mod,
        attack_id,
        defense_id,
    ) = if attacking_home {
        (
            state.home,
            state.away,
            state.home_fatigue,
            state.away_fatigue,
            home_attack_mod,
            away_defense_mod,
            state.home.id,
            state.away.id,
        )
    } else {
        (
            state.away,
            state.home,
            state.away_fatigue,
            state.home_fatigue,
            away_attack_mod,
            home_defense_mod,
            state.away.id,
            state.home.id,
        )
    };

    let attack_strength = team_attack_strength(attack_team, attack_fatigue) * attack_mod;
    let defense_strength = team_defense_strength(defense_team, defense_fatigue) * defense_mod;
    let chance_threshold =
        (30.0 + (attack_strength - defense_strength) * 3.0).clamp(10.0, 60.0) as u32;

    if rng.gen_range(1..=100) <= chance_threshold {
        let player_id = attacking_player(rng, attack_team);
        state.push(event_with_player(
            state.minute,
            MatchEventType::Occasione,
            attack_id,
            player_id,
        ));
        let shot_roll = rng.gen_range(1..=100);

        if shot_roll <= 20 {
            if attacking_home {
                state.home_corners += 1;
            } else {
                state.away_corners += 1;
            }
            state.push(event_with_player(
                state.minute,
                MatchEventType::CalcioAngolo,
                attack_id,
                player_id,
            ));
        } else if shot_roll <= 45 {
            if attacking_home {
                state.home_shots += 1;
                state.home_shots_on_target += 1;
            } else {
                state.away_shots += 1;
                state.away_shots_on_target += 1;
            }
            state.push(event_with_player(
                state.minute,
                MatchEventType::Parata,
                attack_id,
                player_id,
            ));
        } else if shot_roll <= 60 {
            if attacking_home {
                state.home_shots += 1;
            } else {
                state.away_shots += 1;
            }
            state.push(event_with_player(
                state.minute,
                MatchEventType::TiroFuori,
                attack_id,
                player_id,
            ));
        } else if shot_roll <= 70 {
            if attacking_home {
                state.home_shots += 1;
                state.home_shots_on_target += 1;
            } else {
                state.away_shots += 1;
                state.away_shots_on_target += 1;
            }
            state.push(event_with_player(
                state.minute,
                MatchEventType::Palo,
                attack_id,
                player_id,
            ));
        } else {
            let goal_chance =
                (50.0 + (attack_strength - defense_strength) * 4.0).clamp(20.0, 80.0) as u32;
            if rng.gen_range(1..=100) <= goal_chance {
                if attacking_home {
                    state.home_goals += 1;
                    state.home_shots += 1;
                    state.home_shots_on_target += 1;
                    state.home_momentum = (state.home_momentum + 2.0).min(5.0);
                    state.away_momentum = (state.away_momentum - 1.0).max(-3.0);
                } else {
                    state.away_goals += 1;
                    state.away_shots += 1;
                    state.away_shots_on_target += 1;
                    state.away_momentum = (state.away_momentum + 2.0).min(5.0);
                    state.home_momentum = (state.home_momentum - 1.0).max(-3.0);
                }

                let mut goal =
                    event_with_player(state.minute, MatchEventType::Gol, attack_id, player_id);
                if let Some(scorer_id) = player_id {
                    goal.assist_player_id = assist_player(rng, attack_team, scorer_id);
                }
                state.push(goal);
            } else {
                if attacking_home {
                    state.home_shots += 1;
                    state.home_shots_on_target += 1;
                } else {
                    state.away_shots += 1;
                    state.away_shots_on_target += 1;
                }
                state.push(event_with_player(
                    state.minute,
                    MatchEventType::Parata,
                    attack_id,
                    player_id,
                ));
            }
        }
    }

    let foul_chance = (15_i32 + rng.gen_range(-5..=5)).max(1) as u32;
    if rng.gen_range(1..=100) <= foul_chance {
        let player_id = fouling_player(rng, defense_team);
        if attacking_home {
            state.away_fouls += 1;
        } else {
            state.home_fouls += 1;
        }
        state.push(event_with_player(
            state.minute,
            MatchEventType::Fallo,
            defense_id,
            player_id,
        ));

        let card_roll = rng.gen_range(1..=100);
        if card_roll <= 5 {
            state.push(event_with_player(
                state.minute,
                MatchEventType::Espulsione,
                defense_id,
                player_id,
            ));
        } else if card_roll <= 20 {
            state.push(event_with_player(
                state.minute,
                MatchEventType::Ammonizione,
                defense_id,
                player_id,
            ));
        }
    }

    let fatigue_rate = if state.minute < state.rules.half_duration_minutes {
        0.02
    } else {
        0.035
    };
    state.home_fatigue = (state.home_fatigue + fatigue_rate).min(1.0);
    state.away_fatigue = (state.away_fatigue + fatigue_rate).min(1.0);
    state.home_momentum *= 0.9;
    state.away_momentum *= 0.9;
}

pub fn simulate_penalty_shootout<R: Rng + ?Sized>(
    rng: &mut R,
    home: &Team,
    away: &Team,
    events: &mut Vec<MatchEvent>,
) -> PenaltyShootout {
    let mut shootout = PenaltyShootout::default();
    let home_takers = sorted_penalty_takers(home);
    let away_takers = sorted_penalty_takers(away);
    let home_gk = home
        .available_players()
        .into_iter()
        .find(|player| player.role == PlayerRole::Gk);
    let away_gk = away
        .available_players()
        .into_iter()
        .find(|player| player.role == PlayerRole::Gk);

    if home_takers.is_empty() || away_takers.is_empty() {
        return shootout;
    }

    events.push(event(90, MatchEventType::InizioRigori, Some(home.id)));

    for index in 0..5 {
        let home_scored = take_penalty(
            rng,
            home_takers[index % home_takers.len()],
            away_gk,
            home.id,
            events,
        );
        shootout.home_scores.push(home_scored);
        let away_scored = take_penalty(
            rng,
            away_takers[index % away_takers.len()],
            home_gk,
            away.id,
            events,
        );
        shootout.away_scores.push(away_scored);

        let remaining = 4_i32 - index as i32;
        let diff = shootout.home_goals() as i32 - shootout.away_goals() as i32;
        if diff > remaining || -diff > remaining {
            break;
        }
    }

    let mut round_index = 5;
    while shootout.home_goals() == shootout.away_goals() && round_index <= 20 {
        let home_scored = take_penalty(
            rng,
            home_takers[round_index % home_takers.len()],
            away_gk,
            home.id,
            events,
        );
        shootout.home_scores.push(home_scored);
        let away_scored = take_penalty(
            rng,
            away_takers[round_index % away_takers.len()],
            home_gk,
            away.id,
            events,
        );
        shootout.away_scores.push(away_scored);
        round_index += 1;
    }

    shootout
}

fn sorted_penalty_takers(team: &Team) -> Vec<&Player> {
    let mut takers: Vec<&Player> = team
        .available_players()
        .into_iter()
        .filter(|player| player.role != PlayerRole::Gk)
        .collect();
    takers.sort_by_key(|player| std::cmp::Reverse(player.attributes.technical.finishing));
    takers
}

fn take_penalty<R: Rng + ?Sized>(
    rng: &mut R,
    taker: &Player,
    goalkeeper: Option<&Player>,
    team_id: Uuid,
    events: &mut Vec<MatchEvent>,
) -> bool {
    let finishing = taker.attributes.technical.finishing as f32;
    let gk_skill = goalkeeper
        .map(|goalkeeper| {
            (goalkeeper.attributes.goalkeeping.reflexes as f32
                + goalkeeper.attributes.goalkeeping.handling as f32)
                / 2.0
        })
        .unwrap_or(10.0);
    let score_chance = (75.0 + (finishing - gk_skill) * 2.0).clamp(40.0, 95.0) as u32;
    let scored = rng.gen_range(1..=100) <= score_chance;

    let event_type = if scored {
        MatchEventType::RigoreSegnato
    } else if rng.gen_bool(0.6) {
        MatchEventType::RigoreParato
    } else {
        MatchEventType::RigoreSbagliato
    };
    events.push(event_with_player(90, event_type, team_id, Some(taker.id)));
    scored
}

pub fn simulate_match<R: Rng + ?Sized>(
    rng: &mut R,
    scheduled_match: &Match,
    home: &Team,
    away: &Team,
    rules: &CompetitionRules,
) -> Match {
    let mut result = scheduled_match.clone();
    result.events.clear();
    result.played = false;
    result.result = None;
    result.score = MatchScore::default();

    if !home.can_play() {
        result.played = true;
        result.score = MatchScore {
            home_goals: 0,
            away_goals: 3,
            penalty_shootout: None,
        };
        result.result = Some(MatchResult::RinunciaCasa);
        result
            .events
            .push(event(0, MatchEventType::FinePartita, Some(away.id)));
        return result;
    }
    if !away.can_play() {
        result.played = true;
        result.score = MatchScore {
            home_goals: 3,
            away_goals: 0,
            penalty_shootout: None,
        };
        result.result = Some(MatchResult::RinunciaTrasferta);
        result
            .events
            .push(event(0, MatchEventType::FinePartita, Some(home.id)));
        return result;
    }

    let mut state = MatchState::new(home, away, rules);
    state.push(event(0, MatchEventType::CalcioInizio, Some(home.id)));

    let half_duration = rules.half_duration_minutes;
    for minute in 1..=half_duration {
        state.minute = minute;
        simulate_tick(rng, &mut state);
    }

    state.push(event(half_duration, MatchEventType::Intervallo, None));
    state.home_fatigue *= 0.5;
    state.away_fatigue *= 0.5;

    for minute in (half_duration + 1)..=(half_duration * 2) {
        state.minute = minute;
        simulate_tick(rng, &mut state);
    }

    state.push(event(half_duration * 2, MatchEventType::FinePartita, None));

    result.played = true;
    result.home_possession = (state.home_possession * 10.0).round() / 10.0;
    result.away_possession = (state.away_possession * 10.0).round() / 10.0;
    result.home_shots = state.home_shots;
    result.away_shots = state.away_shots;
    result.home_shots_on_target = state.home_shots_on_target;
    result.away_shots_on_target = state.away_shots_on_target;
    result.home_fouls = state.home_fouls;
    result.away_fouls = state.away_fouls;
    result.home_corners = state.home_corners;
    result.away_corners = state.away_corners;

    let mut score = MatchScore {
        home_goals: state.home_goals,
        away_goals: state.away_goals,
        penalty_shootout: None,
    };

    result.result = if state.home_goals > state.away_goals {
        Some(MatchResult::VittoriaCasa)
    } else if state.away_goals > state.home_goals {
        Some(MatchResult::VittoriaTrasferta)
    } else if rules.penalties_after_draw {
        let shootout = simulate_penalty_shootout(rng, home, away, &mut state.events);
        let result = if shootout.home_goals() > shootout.away_goals() {
            MatchResult::VittoriaCasaRigori
        } else {
            MatchResult::VittoriaTrasfertaRigori
        };
        score.penalty_shootout = Some(shootout);
        Some(result)
    } else {
        None
    };

    result.score = score;
    result.events = state.events;
    result
}

#[cfg(test)]
mod tests {
    use rand::SeedableRng;
    use rand_chacha::ChaCha8Rng;

    use crate::domain::engine::player_gen::{TeamGenerationInput, generate_team};
    use crate::domain::models::{AgeCategory, CompetitionRules, GameFormat, Match};

    use super::*;

    fn teams() -> (Team, Team) {
        let mut rng = ChaCha8Rng::seed_from_u64(42);
        let home = generate_team(
            &mut rng,
            TeamGenerationInput {
                name: "Pol. Aurora".to_string(),
                city: "Varese".to_string(),
                province: "Varese".to_string(),
                quality_base: 10,
                category: AgeCategory::Open,
                season: "2025-2026".to_string(),
                is_human: false,
                colors: None,
                stadium_name: None,
            },
        )
        .unwrap();
        let away = generate_team(
            &mut rng,
            TeamGenerationInput {
                name: "FC Stella".to_string(),
                city: "Busto Arsizio".to_string(),
                province: "Varese".to_string(),
                quality_base: 10,
                category: AgeCategory::Open,
                season: "2025-2026".to_string(),
                is_human: false,
                colors: None,
                stadium_name: None,
            },
        )
        .unwrap();
        (home, away)
    }

    #[test]
    fn match_produces_result_and_events() {
        let (home, away) = teams();
        let scheduled = Match::new(home.id, away.id, Uuid::new_v4(), 1, None);
        let rules = CompetitionRules::for_category(AgeCategory::Open, GameFormat::C7);
        let mut rng = ChaCha8Rng::seed_from_u64(7);
        let result = simulate_match(&mut rng, &scheduled, &home, &away, &rules);
        assert!(result.played);
        assert!(result.result.is_some());
        assert!(!result.events.is_empty());
    }

    #[test]
    fn forfeit_when_home_has_too_few_players() {
        let (mut home, away) = teams();
        home.squad.truncate(2);
        let scheduled = Match::new(home.id, away.id, Uuid::new_v4(), 1, None);
        let rules = CompetitionRules::for_category(AgeCategory::Open, GameFormat::C7);
        let mut rng = ChaCha8Rng::seed_from_u64(7);
        let result = simulate_match(&mut rng, &scheduled, &home, &away, &rules);
        assert_eq!(result.result, Some(MatchResult::RinunciaCasa));
        assert_eq!(result.score.home_goals, 0);
        assert_eq!(result.score.away_goals, 3);
    }
}
