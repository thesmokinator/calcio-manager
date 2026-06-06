use rand::Rng;
use rand::seq::SliceRandom;
use serde::Deserialize;
use uuid::Uuid;

use crate::domain::models::{
    AgeCategory, Formation, GoalkeepingAttributes, MentalAttributes, MoraleLevel,
    PhysicalAttributes, Player, PlayerAttributes, PlayerRole, SeasonStats, TacticStyle, Team,
    TeamFinances, TechnicalAttributes,
};

const NAMES_TOML: &str = include_str!("../../../resources/data/names_it.toml");

#[derive(Debug, Deserialize)]
struct NamesFile {
    names: NamesSection,
    teams: TeamsSection,
}

#[derive(Debug, Deserialize)]
struct NamesSection {
    first_names: Vec<String>,
    last_names: Vec<String>,
}

#[derive(Debug, Deserialize)]
struct TeamsSection {
    prefixes: Vec<String>,
    base_names: Vec<String>,
}

fn load_names_file() -> Result<NamesFile, String> {
    toml::from_str(NAMES_TOML).map_err(|error| error.to_string())
}

fn random_attr<R: Rng + ?Sized>(rng: &mut R, base: i32, variance: i32) -> u8 {
    (base + rng.gen_range(-variance..=variance)).clamp(1, 20) as u8
}

fn age_adjusted_base(age: u8, peak_base: i32) -> i32 {
    match age {
        0..=19 => (peak_base - 3).max(1),
        20..=25 => peak_base - 1,
        26..=30 => peak_base,
        31..=35 => (peak_base - 1).max(1),
        36..=40 => (peak_base - 2).max(1),
        _ => (peak_base - 4).max(1),
    }
}

fn physical_age_penalty(age: u8) -> i32 {
    match age {
        0..=30 => 0,
        31..=35 => -2,
        36..=40 => -4,
        _ => -6,
    }
}

fn mental_age_bonus(age: u8) -> i32 {
    match age {
        0..=21 => -2,
        22..=25 => 0,
        26..=35 => 2,
        _ => 3,
    }
}

fn age_range(category: AgeCategory) -> (u8, u8) {
    match category {
        AgeCategory::Open => (18, 45),
        AgeCategory::Master30 => (30, 50),
        AgeCategory::Master40 => (40, 55),
        AgeCategory::Juniores => (16, 18),
        AgeCategory::Allievi => (14, 16),
        AgeCategory::Under14 => (12, 14),
        AgeCategory::Under12 => (10, 12),
    }
}

pub fn generate_player<R: Rng + ?Sized>(
    rng: &mut R,
    role: PlayerRole,
    category: AgeCategory,
    quality_base: i32,
    season: &str,
) -> Result<Player, String> {
    let names = load_names_file()?;
    let first_name = names
        .names
        .first_names
        .choose(rng)
        .cloned()
        .ok_or_else(|| "Missing first names".to_string())?;
    let last_name = names
        .names
        .last_names
        .choose(rng)
        .cloned()
        .ok_or_else(|| "Missing last names".to_string())?;

    let (min_age, max_age) = age_range(category);
    let age = rng.gen_range(min_age..=max_age);
    let adjusted_base = age_adjusted_base(age, quality_base);
    let phys_penalty = physical_age_penalty(age);
    let mental_bonus = mental_age_bonus(age);

    let technical = TechnicalAttributes {
        passing: random_attr(rng, adjusted_base, 4),
        dribbling: random_attr(rng, adjusted_base, 4),
        finishing: random_attr(
            rng,
            adjusted_base + if role == PlayerRole::Fwd { 2 } else { -1 },
            4,
        ),
        first_touch: random_attr(rng, adjusted_base, 4),
    };

    let mental = MentalAttributes {
        positioning: random_attr(
            rng,
            adjusted_base + mental_bonus + if role == PlayerRole::Def { 2 } else { 0 },
            4,
        ),
        decisions: random_attr(rng, adjusted_base + mental_bonus, 4),
        leadership: random_attr(rng, adjusted_base + mental_bonus - 2, 4),
        teamwork: random_attr(rng, adjusted_base + mental_bonus, 4),
    };

    let physical = PhysicalAttributes {
        pace: random_attr(
            rng,
            (adjusted_base + phys_penalty + if role == PlayerRole::Fwd { 2 } else { 0 }).max(1),
            4,
        ),
        stamina: random_attr(rng, (adjusted_base + phys_penalty).max(1), 4),
        strength: random_attr(
            rng,
            (adjusted_base + phys_penalty + if role == PlayerRole::Def { 1 } else { 0 }).max(1),
            4,
        ),
    };

    let goalkeeping = if role == PlayerRole::Gk {
        GoalkeepingAttributes {
            reflexes: random_attr(rng, adjusted_base + 3, 4),
            handling: random_attr(rng, adjusted_base + 2, 4),
        }
    } else {
        GoalkeepingAttributes {
            reflexes: random_attr(rng, 3, 2),
            handling: random_attr(rng, 3, 2),
        }
    };

    let attributes = PlayerAttributes {
        technical,
        mental,
        physical,
        goalkeeping,
    };
    let mut player = Player {
        id: Uuid::new_v4(),
        first_name,
        last_name,
        age,
        role,
        overall: 1,
        attributes,
        condition: 1.0,
        morale: MoraleLevel::Normal,
        injury: None,
        suspended: false,
        yellow_card_accumulation: 0,
        current_season_stats: SeasonStats::new(season),
        history: vec![],
    };
    player.overall = player.calculate_overall();
    Ok(player)
}

pub fn generate_squad<R: Rng + ?Sized>(
    rng: &mut R,
    category: AgeCategory,
    quality_base: i32,
    squad_size: usize,
    season: &str,
) -> Result<Vec<Player>, String> {
    let mut role_counts = vec![
        (PlayerRole::Gk, 2),
        (
            PlayerRole::Def,
            3_usize.max((squad_size.saturating_sub(2)) / 3),
        ),
        (
            PlayerRole::Mid,
            3_usize.max((squad_size.saturating_sub(2)) / 3),
        ),
    ];
    let used: usize = role_counts.iter().map(|(_, count)| *count).sum();
    role_counts.push((PlayerRole::Fwd, squad_size.saturating_sub(used)));

    let mut squad = Vec::new();
    let mut used_names = std::collections::HashSet::new();

    for (role, count) in role_counts {
        for _ in 0..count {
            let mut last_player = None;
            for _ in 0..50 {
                let player = generate_player(rng, role, category, quality_base, season)?;
                if used_names.insert(player.full_name()) {
                    squad.push(player);
                    last_player = None;
                    break;
                }
                last_player = Some(player);
            }
            if let Some(player) = last_player {
                squad.push(player);
            }
        }
    }

    Ok(squad)
}

const COLORS_POOL: [(&str, &str); 15] = [
    ("bianco", "nero"),
    ("rosso", "blu"),
    ("giallo", "verde"),
    ("bianco", "rosso"),
    ("azzurro", "bianco"),
    ("nero", "verde"),
    ("arancione", "nero"),
    ("viola", "bianco"),
    ("blu", "giallo"),
    ("rosso", "nero"),
    ("verde", "bianco"),
    ("grigio", "rosso"),
    ("granata", "bianco"),
    ("celeste", "nero"),
    ("amaranto", "bianco"),
];

const STADIUM_PREFIXES: [&str; 8] = [
    "Campo Sportivo",
    "Centro Sportivo",
    "Stadio Comunale",
    "Polisportiva",
    "Oratorio",
    "Campetto Comunale",
    "Campo Parrocchiale",
    "Impianto Sportivo",
];

fn generate_stadium_name<R: Rng + ?Sized>(rng: &mut R, city: &str) -> String {
    let prefix = STADIUM_PREFIXES
        .choose(rng)
        .copied()
        .unwrap_or("Campo Sportivo");
    format!("{} {}", prefix, city)
}

fn random_tactic<R: Rng + ?Sized>(rng: &mut R) -> TacticStyle {
    *[
        TacticStyle::Difensiva,
        TacticStyle::Equilibrata,
        TacticStyle::Offensiva,
        TacticStyle::Contropiede,
    ]
    .choose(rng)
    .unwrap_or(&TacticStyle::Equilibrata)
}

#[derive(Debug, Clone)]
pub struct TeamGenerationInput {
    pub name: String,
    pub city: String,
    pub province: String,
    pub quality_base: i32,
    pub category: AgeCategory,
    pub season: String,
    pub is_human: bool,
    pub colors: Option<(String, String)>,
    pub stadium_name: Option<String>,
}

pub fn generate_team<R: Rng + ?Sized>(
    rng: &mut R,
    input: TeamGenerationInput,
) -> Result<Team, String> {
    let squad = generate_squad(rng, input.category, input.quality_base, 14, &input.season)?;
    let formation = Formation::default_formations()
        .choose(rng)
        .cloned()
        .unwrap_or_else(Formation::default_c7);
    let color_pair = input.colors.unwrap_or_else(|| {
        let (a, b) = COLORS_POOL
            .choose(rng)
            .copied()
            .unwrap_or(("bianco", "nero"));
        (a.to_string(), b.to_string())
    });

    Ok(Team {
        id: Uuid::new_v4(),
        name: input.name,
        city: input.city.clone(),
        province: input.province,
        stadium_name: input
            .stadium_name
            .filter(|value| !value.trim().is_empty())
            .unwrap_or_else(|| generate_stadium_name(rng, &input.city)),
        colors: color_pair,
        reputation: (input.quality_base * 5 + rng.gen_range(-10..=10)).clamp(10, 90) as u8,
        squad,
        formation,
        tactic: random_tactic(rng),
        finances: TeamFinances::default(),
        is_human: input.is_human,
    })
}

const TEAM_PREFIXES: [&str; 7] = ["Pol.", "ASD", "US", "GS", "SS", "SC", "AC"];
const TEAM_SUFFIXES: [&str; 4] = ["Calcio", "CSI", "Sport", "United"];

pub fn generate_team_name<R: Rng + ?Sized>(rng: &mut R, comune: &str) -> String {
    let style: f32 = rng.r#gen();
    if style < 0.20 {
        return comune.to_string();
    }

    if style < 0.45 {
        let first_word = comune.split_whitespace().next().unwrap_or(comune);
        if let Some(stem) = first_word.strip_suffix('o') {
            return format!("{}ese", stem);
        }
        if first_word.ends_with('e') {
            return format!("{}se", first_word);
        }
        if let Some(stem) = first_word.strip_suffix('a') {
            return format!("{}ese", stem);
        }
        if let Some(stem) = first_word.strip_suffix('i') {
            return format!("{}ese", stem);
        }
        return comune.to_string();
    }

    if style < 0.75 {
        let prefix = TEAM_PREFIXES.choose(rng).copied().unwrap_or("ASD");
        return format!("{} {}", prefix, comune);
    }

    let suffix = TEAM_SUFFIXES.choose(rng).copied().unwrap_or("CSI");
    format!("{} {}", comune, suffix)
}

fn assign_quality<R: Rng + ?Sized>(rng: &mut R, index: usize, total: usize) -> i32 {
    let strong_cutoff = 1_usize.max(total * 15 / 100);
    let average_cutoff = strong_cutoff + 2_usize.max(total * 30 / 100);

    if index < strong_cutoff {
        rng.gen_range(12..=14)
    } else if index < average_cutoff {
        rng.gen_range(9..=11)
    } else {
        rng.gen_range(7..=9)
    }
}

pub fn generate_tournament_teams<R: Rng + ?Sized>(
    rng: &mut R,
    comuni: &[String],
    province: &str,
    category: AgeCategory,
    season: &str,
) -> Result<Vec<Team>, String> {
    let mut colors_pool: Vec<(String, String)> = COLORS_POOL
        .iter()
        .map(|(a, b)| ((*a).to_string(), (*b).to_string()))
        .collect();
    colors_pool.shuffle(rng);

    let mut indices: Vec<usize> = (0..comuni.len()).collect();
    indices.shuffle(rng);

    let mut teams = Vec::new();
    let mut used_names = std::collections::HashSet::new();

    for (rank, index) in indices.into_iter().enumerate() {
        let comune = &comuni[index];
        let quality = assign_quality(rng, rank, comuni.len());
        let mut team_name = generate_team_name(rng, comune);
        let mut attempts = 0;
        while used_names.contains(&team_name) && attempts < 50 {
            team_name = generate_team_name(rng, comune);
            attempts += 1;
        }
        used_names.insert(team_name.clone());

        let colors = colors_pool.get(rank % colors_pool.len()).cloned();
        teams.push(generate_team(
            rng,
            TeamGenerationInput {
                name: team_name,
                city: comune.clone(),
                province: province.to_string(),
                quality_base: quality,
                category,
                season: season.to_string(),
                is_human: false,
                colors,
                stadium_name: None,
            },
        )?);
    }

    Ok(teams)
}

#[allow(dead_code)]
pub fn generate_league_teams<R: Rng + ?Sized>(
    rng: &mut R,
    num_teams: usize,
    province: &str,
    category: AgeCategory,
    season: &str,
) -> Result<Vec<Team>, String> {
    let names = load_names_file()?;
    let mut base_names = names.teams.base_names;
    let prefixes = names.teams.prefixes;
    base_names.shuffle(rng);

    let locations: Vec<String> = vec![
        "Varese",
        "Busto Arsizio",
        "Gallarate",
        "Saronno",
        "Tradate",
        "Luino",
        "Laveno",
        "Castellanza",
        "Malnate",
        "Gavirate",
        "Sesto Calende",
        "Angera",
        "Besozzo",
        "Caronno",
        "Somma Lombardo",
        "Cardano al Campo",
        "Vergiate",
        "Oggiona",
        "Castiglione Olona",
        "Azzate",
    ]
    .into_iter()
    .map(str::to_string)
    .collect();

    let mut teams = Vec::new();
    for index in 0..num_teams {
        let city = locations[index % locations.len()].clone();
        let prefix = prefixes
            .choose(rng)
            .cloned()
            .unwrap_or_else(|| "ASD".to_string());
        let base = base_names
            .get(index % base_names.len())
            .cloned()
            .unwrap_or_else(|| "Aurora".to_string());
        let name_style = rng.gen_range(0..3);
        let team_name = match name_style {
            0 => format!("{} {}", prefix, city),
            1 => format!("{} {}", prefix, base),
            _ => format!("{} {}", base, city),
        };
        let quality = if index < 2 {
            rng.gen_range(12..=14)
        } else if index < 5 {
            rng.gen_range(9..=11)
        } else {
            rng.gen_range(7..=9)
        };
        teams.push(generate_team(
            rng,
            TeamGenerationInput {
                name: team_name,
                city,
                province: province.to_string(),
                quality_base: quality,
                category,
                season: season.to_string(),
                is_human: false,
                colors: None,
                stadium_name: None,
            },
        )?);
    }

    Ok(teams)
}

#[cfg(test)]
mod tests {
    use rand::SeedableRng;
    use rand_chacha::ChaCha8Rng;

    use super::*;

    #[test]
    fn generated_open_player_has_valid_attributes_and_stats_season() {
        let mut rng = ChaCha8Rng::seed_from_u64(10);
        let player = generate_player(
            &mut rng,
            PlayerRole::Fwd,
            AgeCategory::Open,
            10,
            "2025-2026",
        )
        .expect("player should be generated");

        assert!((18..=45).contains(&player.age));
        assert_eq!(player.role, PlayerRole::Fwd);
        assert_eq!(player.current_season_stats.season, "2025-2026");
        assert_eq!(player.overall, player.calculate_overall());
        assert!((1..=20).contains(&player.overall));
        assert!((1..=20).contains(&player.attributes.technical.finishing));
        assert!((1..=20).contains(&player.attributes.physical.pace));
    }

    #[test]
    fn generated_squad_has_expected_size_and_role_distribution() {
        let mut rng = ChaCha8Rng::seed_from_u64(11);
        let squad = generate_squad(&mut rng, AgeCategory::Open, 10, 14, "2025-2026")
            .expect("squad should be generated");

        assert_eq!(squad.len(), 14);
        assert_eq!(squad.iter().filter(|p| p.role == PlayerRole::Gk).count(), 2);
        assert!(squad.iter().filter(|p| p.role == PlayerRole::Def).count() >= 3);
        assert!(squad.iter().filter(|p| p.role == PlayerRole::Mid).count() >= 3);
        assert!(squad.iter().filter(|p| p.role == PlayerRole::Fwd).count() >= 1);
        assert!(
            squad
                .iter()
                .all(|p| p.current_season_stats.season == "2025-2026")
        );
    }

    #[test]
    fn generated_team_preserves_human_customization() {
        let mut rng = ChaCha8Rng::seed_from_u64(12);
        let team = generate_team(
            &mut rng,
            TeamGenerationInput {
                name: "Real Oratorio".to_string(),
                city: "Varese".to_string(),
                province: "Varese".to_string(),
                quality_base: 10,
                category: AgeCategory::Open,
                season: "2025-2026".to_string(),
                is_human: true,
                colors: Some(("rosso".to_string(), "blu".to_string())),
                stadium_name: Some("Campo Test".to_string()),
            },
        )
        .expect("team should be generated");

        assert_eq!(team.name, "Real Oratorio");
        assert_eq!(team.colors, ("rosso".to_string(), "blu".to_string()));
        assert_eq!(team.stadium_name, "Campo Test");
        assert!(team.is_human);
        assert!(team.can_play());
        assert_eq!(team.squad.len(), 14);
    }
}
