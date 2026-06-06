use std::collections::HashMap;
use std::sync::OnceLock;

use toml::Value;

use crate::domain::models::MatchEventType;

const COMMENTARY_IT: &str = include_str!("../../../resources/data/commentary_it.toml");

type TemplateMap = HashMap<String, Vec<String>>;

#[derive(Debug, Clone, Default)]
pub struct CommentaryVars {
    pub team: String,
    pub opponent: String,
    pub player: String,
    pub scorer: String,
    pub assist: String,
    pub home: String,
    pub away: String,
    pub home_goals: u32,
    pub away_goals: u32,
}

impl CommentaryVars {
    fn score(&self) -> String {
        format!("{} - {}", self.home_goals, self.away_goals)
    }
}

fn templates() -> &'static TemplateMap {
    static TEMPLATES: OnceLock<TemplateMap> = OnceLock::new();
    TEMPLATES.get_or_init(load_templates)
}

fn load_templates() -> TemplateMap {
    let parsed = COMMENTARY_IT
        .parse::<Value>()
        .unwrap_or(Value::Table(Default::default()));
    let mut map = HashMap::new();

    let Some(table) = parsed.as_table() else {
        return map;
    };

    for (section, value) in table {
        let Some(section_table) = value.as_table() else {
            continue;
        };
        for (key, value) in section_table {
            let Some(items) = value.as_array() else {
                continue;
            };
            let templates: Vec<String> = items
                .iter()
                .filter_map(|item| item.as_str().map(ToString::to_string))
                .collect();
            if templates.is_empty() {
                continue;
            }
            let map_key = if key == "templates" {
                section.clone()
            } else {
                format!("{}_{}", section, key)
            };
            map.insert(map_key, templates);
        }
    }

    map
}

pub fn generate_commentary(
    event_type: MatchEventType,
    vars: &CommentaryVars,
    minute: u32,
) -> String {
    let Some(section) = section_for_event(event_type) else {
        return fallback(event_type, vars);
    };

    let key = if event_type == MatchEventType::Gol && !vars.assist.is_empty() {
        "goal_templates_with_assist"
    } else {
        section
    };

    let selected = templates()
        .get(key)
        .or_else(|| templates().get(section))
        .and_then(|items| {
            if items.is_empty() {
                None
            } else {
                let index = deterministic_index(items.len(), minute, event_type, vars);
                items.get(index)
            }
        });

    match selected {
        Some(template) => interpolate(template, vars),
        None => fallback(event_type, vars),
    }
}

fn deterministic_index(
    len: usize,
    minute: u32,
    event_type: MatchEventType,
    vars: &CommentaryVars,
) -> usize {
    let mut hash = minute as usize ^ event_type as usize;
    for byte in vars
        .team
        .bytes()
        .chain(vars.player.bytes())
        .chain(vars.assist.bytes())
    {
        hash = hash.wrapping_mul(31).wrapping_add(byte as usize);
    }
    hash % len
}

fn section_for_event(event_type: MatchEventType) -> Option<&'static str> {
    match event_type {
        MatchEventType::Gol => Some("goal"),
        MatchEventType::Occasione => Some("chance"),
        MatchEventType::Parata => Some("shot_saved"),
        MatchEventType::TiroFuori => Some("shot_wide"),
        MatchEventType::Palo => Some("shot_post"),
        MatchEventType::Fallo => Some("foul"),
        MatchEventType::Ammonizione => Some("yellow_card"),
        MatchEventType::Espulsione => Some("red_card"),
        MatchEventType::DoppiaAmmonizione => Some("second_yellow"),
        MatchEventType::Sostituzione => Some("substitution"),
        MatchEventType::CalcioAngolo => Some("corner"),
        MatchEventType::Intervallo => Some("half_time"),
        MatchEventType::FinePartita => Some("full_time"),
        MatchEventType::CalcioInizio => Some("kick_off"),
        MatchEventType::InizioRigori => Some("penalty_shootout_start"),
        MatchEventType::RigoreSegnato => Some("penalty_scored"),
        MatchEventType::RigoreSbagliato => Some("penalty_missed"),
        MatchEventType::RigoreParato => Some("penalty_saved"),
        MatchEventType::Possesso => Some("possession"),
        MatchEventType::TimeOut => Some("timeout"),
        MatchEventType::Punizione => Some("free_kick"),
    }
}

fn interpolate(template: &str, vars: &CommentaryVars) -> String {
    template
        .replace("{team}", &vars.team)
        .replace("{opponent}", &vars.opponent)
        .replace("{player}", safe_value(&vars.player, "un giocatore"))
        .replace("{scorer}", safe_value(&vars.scorer, "un giocatore"))
        .replace("{assist}", safe_value(&vars.assist, "un compagno"))
        .replace("{home}", &vars.home)
        .replace("{away}", &vars.away)
        .replace("{home_goals}", &vars.home_goals.to_string())
        .replace("{away_goals}", &vars.away_goals.to_string())
        .replace("{score}", &vars.score())
}

fn safe_value<'a>(value: &'a str, fallback: &'a str) -> &'a str {
    if value.is_empty() { fallback } else { value }
}

fn fallback(event_type: MatchEventType, vars: &CommentaryVars) -> String {
    match event_type {
        MatchEventType::Gol => format!(
            "GOOOL! {} segna per {}!",
            safe_value(&vars.scorer, "un giocatore"),
            vars.team
        ),
        MatchEventType::Intervallo => format!(
            "Intervallo: {} {} - {} {}",
            vars.home, vars.home_goals, vars.away_goals, vars.away
        ),
        MatchEventType::FinePartita => format!(
            "Fine partita: {} {} - {} {}",
            vars.home, vars.home_goals, vars.away_goals, vars.away
        ),
        MatchEventType::CalcioInizio => format!("Si gioca! {} contro {}.", vars.home, vars.away),
        _ => format!("Evento: {:?}", event_type),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn loads_goal_templates() {
        assert!(
            templates()
                .get("goal")
                .is_some_and(|items| !items.is_empty())
        );
    }

    #[test]
    fn interpolates_commentary() {
        let vars = CommentaryVars {
            team: "Aurora".to_string(),
            player: "M. Rossi".to_string(),
            scorer: "M. Rossi".to_string(),
            home: "Aurora".to_string(),
            away: "Stella".to_string(),
            home_goals: 1,
            away_goals: 0,
            ..Default::default()
        };
        let text = generate_commentary(MatchEventType::Gol, &vars, 12);
        assert!(text.contains("Rossi") || text.contains("GOOOL"));
    }
}
