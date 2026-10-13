//! Matching and graph algorithms used by domain-consistent all-different.

use std::collections::{HashMap, HashSet};

pub fn supported_all_different_edges(adjacency: &[Vec<i64>]) -> Option<Vec<HashSet<i64>>> {
    let mut value_to_variable = HashMap::new();
    for variable in 0..adjacency.len() {
        let mut seen = HashSet::new();
        if !augment(variable, adjacency, &mut value_to_variable, &mut seen) {
            return None;
        }
    }
    let variable_to_value: HashMap<_, _> = value_to_variable
        .iter()
        .map(|(value, variable)| (*variable, *value))
        .collect();
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

fn reachable_nodes(graph: &[Vec<usize>], starts: impl Iterator<Item = usize>) -> HashSet<usize> {
    let mut reachable = HashSet::new();
    let mut stack: Vec<_> = starts.collect();
    while let Some(node) = stack.pop() {
        if reachable.insert(node) {
            stack.extend(graph[node].iter().copied());
        }
    }
    reachable
}

fn strongly_connected_components(graph: &[Vec<usize>]) -> Vec<usize> {
    let mut visited = vec![false; graph.len()];
    let mut order = Vec::new();
    for node in 0..graph.len() {
        visit(node, graph, &mut visited, &mut order);
    }
    let mut reverse = vec![Vec::new(); graph.len()];
    for (source, destinations) in graph.iter().enumerate() {
        for destination in destinations {
            reverse[*destination].push(source);
        }
    }
    let mut components = vec![usize::MAX; graph.len()];
    let mut component = 0;
    for node in order.into_iter().rev() {
        if components[node] == usize::MAX {
            assign_component(node, &reverse, component, &mut components);
            component += 1;
        }
    }
    components
}

fn visit(node: usize, graph: &[Vec<usize>], visited: &mut [bool], order: &mut Vec<usize>) {
    if visited[node] {
        return;
    }
    visited[node] = true;
    for destination in &graph[node] {
        visit(*destination, graph, visited, order);
    }
    order.push(node);
}

fn assign_component(node: usize, graph: &[Vec<usize>], component: usize, components: &mut [usize]) {
    if components[node] != usize::MAX {
        return;
    }
    components[node] = component;
    for destination in &graph[node] {
        assign_component(*destination, graph, component, components);
    }
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
