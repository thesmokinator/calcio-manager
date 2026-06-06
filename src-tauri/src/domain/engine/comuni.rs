use std::collections::HashMap;
use std::path::PathBuf;
use std::sync::{Mutex, OnceLock};

use rusqlite::{Connection, params};

const COMUNI_JSON: &str = include_str!("../../../resources/data/comuni_it.json");

type ComuniSeed = HashMap<String, HashMap<String, Vec<String>>>;

type Db = Mutex<Connection>;

static DB_PATH: OnceLock<PathBuf> = OnceLock::new();

pub fn configure_db_path(path: PathBuf) {
    let _ = DB_PATH.set(path);
}

fn db() -> Result<&'static Db, String> {
    static DB: OnceLock<Result<Db, String>> = OnceLock::new();
    DB.get_or_init(init_db).as_ref().map_err(Clone::clone)
}

fn init_db() -> Result<Db, String> {
    let mut connection = match DB_PATH.get() {
        Some(path) => Connection::open(path),
        None => Connection::open_in_memory(),
    }
    .map_err(|error| error.to_string())?;

    create_schema(&connection)?;
    seed_from_json(&mut connection)?;
    Ok(Mutex::new(connection))
}

fn create_schema(connection: &Connection) -> Result<(), String> {
    connection
        .execute_batch(
            "
            CREATE TABLE IF NOT EXISTS geography_comuni (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                region TEXT NOT NULL,
                province TEXT NOT NULL,
                comune TEXT NOT NULL,
                UNIQUE(region, province, comune)
            );
            CREATE INDEX IF NOT EXISTS idx_geography_region ON geography_comuni(region);
            CREATE INDEX IF NOT EXISTS idx_geography_province ON geography_comuni(province);
            ",
        )
        .map_err(|error| error.to_string())
}

fn seed_from_json(connection: &mut Connection) -> Result<(), String> {
    let seed: ComuniSeed = serde_json::from_str(COMUNI_JSON).map_err(|error| error.to_string())?;
    let transaction = connection
        .transaction()
        .map_err(|error| error.to_string())?;

    {
        let mut insert = transaction
            .prepare(
                "
                INSERT OR IGNORE INTO geography_comuni (region, province, comune)
                VALUES (?1, ?2, ?3)
                ",
            )
            .map_err(|error| error.to_string())?;

        for (region, provinces) in seed {
            for (province, comuni) in provinces {
                for comune in comuni {
                    insert
                        .execute(params![region, province, comune])
                        .map_err(|error| error.to_string())?;
                }
            }
        }
    }

    transaction.commit().map_err(|error| error.to_string())
}

fn query_strings(sql: &str, params: impl rusqlite::Params) -> Result<Vec<String>, String> {
    let guard = db()?.lock().map_err(|error| error.to_string())?;
    let mut statement = guard.prepare(sql).map_err(|error| error.to_string())?;
    let rows = statement
        .query_map(params, |row| row.get::<_, String>(0))
        .map_err(|error| error.to_string())?;

    rows.collect::<Result<Vec<_>, _>>()
        .map_err(|error| error.to_string())
}

pub fn get_regions() -> Result<Vec<String>, String> {
    query_strings(
        "SELECT DISTINCT region FROM geography_comuni ORDER BY region COLLATE NOCASE",
        [],
    )
}

pub fn get_provinces(region: &str) -> Result<Vec<String>, String> {
    query_strings(
        "
        SELECT DISTINCT province
        FROM geography_comuni
        WHERE region = ?1
        ORDER BY province COLLATE NOCASE
        ",
        params![region],
    )
}

pub fn get_comuni(province: &str) -> Result<Vec<String>, String> {
    query_strings(
        "
        SELECT comune
        FROM geography_comuni
        WHERE province = ?1
        ORDER BY comune COLLATE NOCASE
        ",
        params![province],
    )
}

pub fn get_region_for_province(province: &str) -> Result<Option<String>, String> {
    let guard = db()?.lock().map_err(|error| error.to_string())?;
    let mut statement = guard
        .prepare(
            "
            SELECT region
            FROM geography_comuni
            WHERE province = ?1
            ORDER BY region COLLATE NOCASE
            LIMIT 1
            ",
        )
        .map_err(|error| error.to_string())?;

    match statement.query_row(params![province], |row| row.get::<_, String>(0)) {
        Ok(region) => Ok(Some(region)),
        Err(rusqlite::Error::QueryReturnedNoRows) => Ok(None),
        Err(error) => Err(error.to_string()),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn lists_regions_from_sqlite() {
        let regions = get_regions().expect("regions should load from sqlite");
        assert!(regions.iter().any(|region| region == "Lombardia"));
    }

    #[test]
    fn lists_provinces_for_region_from_sqlite() {
        let provinces = get_provinces("Lombardia").expect("provinces should load from sqlite");
        assert!(provinces.iter().any(|province| province == "Milano"));
    }

    #[test]
    fn resolves_region_for_province_from_sqlite() {
        let region = get_region_for_province("Milano").expect("region should resolve");
        assert_eq!(region.as_deref(), Some("Lombardia"));
    }
}
