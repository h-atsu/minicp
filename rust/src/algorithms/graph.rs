use std::collections::HashSet;

pub(super) fn reachable_nodes(
    graph: &[Vec<usize>],
    starts: impl Iterator<Item = usize>,
) -> HashSet<usize> {
    let mut reachable = HashSet::new();
    let mut stack: Vec<_> = starts.collect();
    while let Some(node) = stack.pop() {
        if reachable.insert(node) {
            stack.extend(graph[node].iter().copied());
        }
    }
    reachable
}

pub(super) fn strongly_connected_components(graph: &[Vec<usize>]) -> Vec<usize> {
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
