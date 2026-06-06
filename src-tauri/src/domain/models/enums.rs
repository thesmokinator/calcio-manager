use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum GameFormat {
    C7,
    C5,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum PlayerRole {
    #[serde(rename = "POR")]
    Gk,
    #[serde(rename = "DIF")]
    Def,
    #[serde(rename = "CEN")]
    Mid,
    #[serde(rename = "ATT")]
    Fwd,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum AgeCategory {
    Open,
    Master30,
    Master40,
    Juniores,
    Allievi,
    Under14,
    Under12,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum CompetitionType {
    Campionato,
    Coppa,
    TorneoEstivo,
    Playoff,
    Playout,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum CompetitionPhase {
    Territoriale,
    Regionale,
    Nazionale,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Division {
    Eccellenza,
    SerieOro,
    SerieArgento,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum SeasonPhase {
    OffSeason,
    PreSeason,
    InSeason,
    Playoffs,
    TorneiEstivi,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum MatchEventType {
    CalcioInizio,
    Gol,
    Occasione,
    Parata,
    TiroFuori,
    Palo,
    Fallo,
    Ammonizione,
    Espulsione,
    DoppiaAmmonizione,
    Sostituzione,
    TimeOut,
    Intervallo,
    FinePartita,
    InizioRigori,
    RigoreSegnato,
    RigoreSbagliato,
    RigoreParato,
    CalcioAngolo,
    Punizione,
    Possesso,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum MatchResult {
    VittoriaCasa,
    VittoriaTrasferta,
    VittoriaCasaRigori,
    VittoriaTrasfertaRigori,
    RinunciaCasa,
    RinunciaTrasferta,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum MoraleLevel {
    Terrible = 1,
    Low = 2,
    Normal = 3,
    Good = 4,
    Excellent = 5,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum TacticStyle {
    Difensiva,
    Equilibrata,
    Offensiva,
    Contropiede,
}
