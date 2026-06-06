use rand::Rng;
use rand::seq::SliceRandom;
use uuid::Uuid;

use crate::domain::models::Team;

pub fn calculate_gironi_structure(
    num_teams_available: usize,
    min_per_group: usize,
    max_per_group: usize,
) -> (usize, usize) {
    if num_teams_available <= max_per_group {
        return (1, min_per_group.max(num_teams_available));
    }

    let mut best_groups = 1;
    let mut best_size = num_teams_available;
    let mut best_diff = 8_usize.abs_diff(num_teams_available);

    for groups in 2..=(num_teams_available / min_per_group) {
        let size = num_teams_available / groups;
        if (min_per_group..=max_per_group).contains(&size) {
            let diff = 8_usize.abs_diff(size);
            if diff < best_diff {
                best_diff = diff;
                best_groups = groups;
                best_size = size;
            }
        }
    }

    (best_groups, best_size)
}

pub fn generate_gironi(all_teams: &[Team], num_groups: usize) -> Vec<Vec<Team>> {
    if num_groups <= 1 {
        return vec![all_teams.to_vec()];
    }

    let mut sorted_teams = all_teams.to_vec();
    sorted_teams.sort_by(|a, b| {
        b.squad_average_overall()
            .total_cmp(&a.squad_average_overall())
    });

    let mut gironi = vec![Vec::new(); num_groups];
    for (index, team) in sorted_teams.into_iter().enumerate() {
        let row = index / num_groups;
        let group_index = if row.is_multiple_of(2) {
            index % num_groups
        } else {
            num_groups - 1 - (index % num_groups)
        };
        gironi[group_index].push(team);
    }

    gironi
}

pub fn select_tournament_comuni<R: Rng + ?Sized>(
    rng: &mut R,
    all_comuni: &[String],
    human_comune: &str,
    num_groups: usize,
    teams_per_group: usize,
) -> Vec<String> {
    let total_needed = num_groups * teams_per_group - 1;
    let mut available: Vec<String> = all_comuni
        .iter()
        .filter(|comune| comune.as_str() != human_comune)
        .cloned()
        .collect();
    available.shuffle(rng);
    available.truncate(total_needed.min(available.len()));
    available
}

pub fn human_girone_index(gironi: &[Vec<Team>]) -> usize {
    gironi
        .iter()
        .position(|girone| girone.iter().any(|team| team.is_human))
        .unwrap_or(0)
}

pub fn collect_team_ids(girone: &[Team]) -> Vec<Uuid> {
    girone.iter().map(|team| team.id).collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn small_tournament_uses_one_girone() {
        assert_eq!(calculate_gironi_structure(8, 6, 10), (1, 8));
    }

    #[test]
    fn larger_tournament_prefers_groups_around_eight() {
        let (groups, size) = calculate_gironi_structure(32, 6, 10);
        assert_eq!((groups, size), (4, 8));
    }
}
