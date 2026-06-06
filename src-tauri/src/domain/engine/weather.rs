use rand::Rng;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Weather {
    pub key: String,
    pub icon: String,
    pub temperature: i32,
}

#[derive(Debug, Clone, Copy)]
struct Condition {
    key: &'static str,
    icon: &'static str,
    weight: u32,
}

fn monthly_conditions(month: u32) -> &'static [Condition] {
    match month {
        1 => &[
            Condition {
                key: "fog",
                icon: "🌫",
                weight: 25,
            },
            Condition {
                key: "overcast",
                icon: "☁",
                weight: 25,
            },
            Condition {
                key: "rain",
                icon: "🌧",
                weight: 15,
            },
            Condition {
                key: "snow",
                icon: "❄",
                weight: 20,
            },
            Condition {
                key: "partly_cloudy",
                icon: "⛅",
                weight: 10,
            },
            Condition {
                key: "clear",
                icon: "☀",
                weight: 5,
            },
        ],
        2 => &[
            Condition {
                key: "fog",
                icon: "🌫",
                weight: 20,
            },
            Condition {
                key: "overcast",
                icon: "☁",
                weight: 25,
            },
            Condition {
                key: "rain",
                icon: "🌧",
                weight: 15,
            },
            Condition {
                key: "snow",
                icon: "❄",
                weight: 15,
            },
            Condition {
                key: "partly_cloudy",
                icon: "⛅",
                weight: 15,
            },
            Condition {
                key: "clear",
                icon: "☀",
                weight: 10,
            },
        ],
        3 => &[
            Condition {
                key: "rain",
                icon: "🌧",
                weight: 25,
            },
            Condition {
                key: "overcast",
                icon: "☁",
                weight: 20,
            },
            Condition {
                key: "partly_cloudy",
                icon: "⛅",
                weight: 25,
            },
            Condition {
                key: "clear",
                icon: "☀",
                weight: 15,
            },
            Condition {
                key: "fog",
                icon: "🌫",
                weight: 10,
            },
            Condition {
                key: "snow",
                icon: "❄",
                weight: 5,
            },
        ],
        4 => &[
            Condition {
                key: "rain",
                icon: "🌧",
                weight: 25,
            },
            Condition {
                key: "partly_cloudy",
                icon: "⛅",
                weight: 25,
            },
            Condition {
                key: "overcast",
                icon: "☁",
                weight: 15,
            },
            Condition {
                key: "clear",
                icon: "☀",
                weight: 25,
            },
            Condition {
                key: "thunderstorm",
                icon: "⛈",
                weight: 10,
            },
        ],
        5 => &[
            Condition {
                key: "clear",
                icon: "☀",
                weight: 30,
            },
            Condition {
                key: "partly_cloudy",
                icon: "⛅",
                weight: 25,
            },
            Condition {
                key: "rain",
                icon: "🌧",
                weight: 15,
            },
            Condition {
                key: "thunderstorm",
                icon: "⛈",
                weight: 15,
            },
            Condition {
                key: "overcast",
                icon: "☁",
                weight: 15,
            },
        ],
        6 => &[
            Condition {
                key: "clear",
                icon: "☀",
                weight: 35,
            },
            Condition {
                key: "partly_cloudy",
                icon: "⛅",
                weight: 20,
            },
            Condition {
                key: "thunderstorm",
                icon: "⛈",
                weight: 20,
            },
            Condition {
                key: "rain",
                icon: "🌧",
                weight: 10,
            },
            Condition {
                key: "overcast",
                icon: "☁",
                weight: 15,
            },
        ],
        7 => &[
            Condition {
                key: "clear",
                icon: "☀",
                weight: 40,
            },
            Condition {
                key: "partly_cloudy",
                icon: "⛅",
                weight: 20,
            },
            Condition {
                key: "thunderstorm",
                icon: "⛈",
                weight: 25,
            },
            Condition {
                key: "overcast",
                icon: "☁",
                weight: 10,
            },
            Condition {
                key: "rain",
                icon: "🌧",
                weight: 5,
            },
        ],
        8 => &[
            Condition {
                key: "clear",
                icon: "☀",
                weight: 35,
            },
            Condition {
                key: "partly_cloudy",
                icon: "⛅",
                weight: 20,
            },
            Condition {
                key: "thunderstorm",
                icon: "⛈",
                weight: 25,
            },
            Condition {
                key: "overcast",
                icon: "☁",
                weight: 10,
            },
            Condition {
                key: "rain",
                icon: "🌧",
                weight: 10,
            },
        ],
        10 => &[
            Condition {
                key: "rain",
                icon: "🌧",
                weight: 25,
            },
            Condition {
                key: "fog",
                icon: "🌫",
                weight: 20,
            },
            Condition {
                key: "overcast",
                icon: "☁",
                weight: 20,
            },
            Condition {
                key: "partly_cloudy",
                icon: "⛅",
                weight: 20,
            },
            Condition {
                key: "clear",
                icon: "☀",
                weight: 15,
            },
        ],
        11 => &[
            Condition {
                key: "fog",
                icon: "🌫",
                weight: 25,
            },
            Condition {
                key: "rain",
                icon: "🌧",
                weight: 25,
            },
            Condition {
                key: "overcast",
                icon: "☁",
                weight: 25,
            },
            Condition {
                key: "partly_cloudy",
                icon: "⛅",
                weight: 15,
            },
            Condition {
                key: "clear",
                icon: "☀",
                weight: 10,
            },
        ],
        12 => &[
            Condition {
                key: "fog",
                icon: "🌫",
                weight: 25,
            },
            Condition {
                key: "overcast",
                icon: "☁",
                weight: 25,
            },
            Condition {
                key: "snow",
                icon: "❄",
                weight: 20,
            },
            Condition {
                key: "rain",
                icon: "🌧",
                weight: 15,
            },
            Condition {
                key: "partly_cloudy",
                icon: "⛅",
                weight: 10,
            },
            Condition {
                key: "clear",
                icon: "☀",
                weight: 5,
            },
        ],
        _ => &[
            Condition {
                key: "clear",
                icon: "☀",
                weight: 25,
            },
            Condition {
                key: "partly_cloudy",
                icon: "⛅",
                weight: 25,
            },
            Condition {
                key: "rain",
                icon: "🌧",
                weight: 20,
            },
            Condition {
                key: "overcast",
                icon: "☁",
                weight: 15,
            },
            Condition {
                key: "thunderstorm",
                icon: "⛈",
                weight: 10,
            },
            Condition {
                key: "fog",
                icon: "🌫",
                weight: 5,
            },
        ],
    }
}

fn monthly_temps(month: u32) -> (i32, i32) {
    match month {
        1 => (-3, 7),
        2 => (-1, 9),
        3 => (3, 14),
        4 => (7, 18),
        5 => (11, 23),
        6 => (15, 28),
        7 => (18, 31),
        8 => (17, 30),
        9 => (13, 25),
        10 => (8, 18),
        11 => (3, 11),
        12 => (-2, 7),
        _ => (10, 20),
    }
}

pub fn generate_weather<R: Rng + ?Sized>(rng: &mut R, month: u32) -> Weather {
    let conditions = monthly_conditions(month);
    let total_weight: u32 = conditions.iter().map(|condition| condition.weight).sum();
    let mut roll = rng.gen_range(0..total_weight);
    let mut chosen = conditions[0];
    for condition in conditions {
        if roll < condition.weight {
            chosen = *condition;
            break;
        }
        roll -= condition.weight;
    }

    let (min_temp, max_temp) = monthly_temps(month);
    Weather {
        key: chosen.key.to_string(),
        icon: chosen.icon.to_string(),
        temperature: rng.gen_range(min_temp..=max_temp),
    }
}
