use crate::domain::engine::comuni;

#[tauri::command]
pub fn list_regions() -> Result<Vec<String>, String> {
    comuni::get_regions()
}

#[tauri::command]
pub fn list_provinces(region: String) -> Result<Vec<String>, String> {
    comuni::get_provinces(&region)
}

#[tauri::command]
pub fn list_comuni(province: String) -> Result<Vec<String>, String> {
    comuni::get_comuni(&province)
}
