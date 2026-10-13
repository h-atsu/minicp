//! Algorithms shared by global constraints.

mod graph;
mod matching;

use std::collections::{HashMap, HashSet};

use graph::{reachable_nodes, strongly_connected_components};
use matching::maximum_matching;

pub fn supported_all_different_edges(adjacency: &[Vec<i64>]) -> Option<Vec<HashSet<i64>>> {
    let (variable_to_value, value_to_variable) = maximum_matching(adjacency)?;
    let mut values: Vec<_> = adjacency.iter().flatten().copied().collect();
    values.sort_unstable();
    values.dedup();
    let value_index: HashMap<_, _> = values
        .iter()
        .enumerate()
        .map(|(index, value)| (*value, adjacency.len() + index))
        .collect();
    let mut graph = vec![Vec::new(); adjacency.len() + values.len()];
    for (variable, domain) in adjacency.iter().enumerate() {
        for value in domain {
            let value_node = value_index[value];
            if variable_to_value[&variable] == *value {
                graph[variable].push(value_node);
            } else {
                graph[value_node].push(variable);
            }
        }
    }
    let free = values
        .iter()
        .filter(|value| !value_to_variable.contains_key(value))
        .map(|value| value_index[value]);
    let reachable = reachable_nodes(&graph, free);
    let components = strongly_connected_components(&graph);
    Some(
        adjacency
            .iter()
            .enumerate()
            .map(|(variable, domain)| {
                domain
                    .iter()
                    .filter(|value| {
                        variable_to_value[&variable] == **value
                            || components[variable] == components[value_index[value]]
                            || reachable.contains(&value_index[value])
                    })
                    .copied()
                    .collect()
            })
            .collect(),
    )
}

#[cfg(test)]
mod tests {
    use super::supported_all_different_edges;

    #[test]
    fn detects_no_matching() {
        assert!(supported_all_different_edges(&[vec![1], vec![1]]).is_none());
    }

    #[test]
    fn removes_unsupported_edge() {
        let supported = supported_all_different_edges(&[vec![1, 2], vec![1]]).unwrap();
        assert_eq!(supported[0], [2].into());
        assert_eq!(supported[1], [1].into());
    }
}
