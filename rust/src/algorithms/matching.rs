use std::collections::{HashMap, HashSet};

pub(super) fn maximum_matching(
    adjacency: &[Vec<i64>],
) -> Option<(HashMap<usize, i64>, HashMap<i64, usize>)> {
    let mut value_to_variable = HashMap::new();
    for variable in 0..adjacency.len() {
        let mut seen = HashSet::new();
        if !augment(variable, adjacency, &mut value_to_variable, &mut seen) {
            return None;
        }
    }
    let variable_to_value = value_to_variable
        .iter()
        .map(|(value, variable)| (*variable, *value))
        .collect();
    Some((variable_to_value, value_to_variable))
}

fn augment(
    variable: usize,
    adjacency: &[Vec<i64>],
    matching: &mut HashMap<i64, usize>,
    seen: &mut HashSet<i64>,
) -> bool {
    for value in &adjacency[variable] {
        if !seen.insert(*value) {
            continue;
        }
        let previous = matching.get(value).copied();
        if previous.is_none() || augment(previous.unwrap(), adjacency, matching, seen) {
            matching.insert(*value, variable);
            return true;
        }
    }
    false
}
