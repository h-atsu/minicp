//! A coarse-grained Rust TSP search used as an end-to-end benchmark.
//!
//! The generic constraint engine is still being ported.  Keeping this search
//! self-contained lets the notebook measure Rust without crossing the PyO3
//! boundary at every search node.

use std::time::{Duration, Instant};

#[derive(Debug, Clone)]
pub struct TspStatistics {
    pub nodes: usize,
    pub failures: usize,
    pub solutions: usize,
    pub completed: bool,
    pub elapsed_seconds: f64,
}

#[derive(Debug, Clone)]
pub struct TspSolution {
    pub distance: i64,
    pub successors: Vec<usize>,
}

#[derive(Debug, Clone)]
pub struct TspResult {
    pub improving_solutions: Vec<TspSolution>,
    pub statistics: TspStatistics,
}

pub fn solve_tsp(distances: &[Vec<i64>], time_limit: Option<f64>) -> TspResult {
    let started_at = Instant::now();
    let deadline = time_limit.map(|seconds| started_at + Duration::from_secs_f64(seconds));
    let node_count = distances.len();
    let mut search = TspSearch {
        distances,
        successors: vec![None; node_count],
        used_destinations: vec![false; node_count],
        assigned: 0,
        current_distance: 0,
        best_distance: None,
        improving_solutions: Vec::new(),
        nodes: 0,
        failures: 0,
        deadline,
        timed_out: false,
    };
    search.dfs();

    TspResult {
        statistics: TspStatistics {
            nodes: search.nodes,
            failures: search.failures,
            solutions: search.improving_solutions.len(),
            completed: !search.timed_out,
            elapsed_seconds: started_at.elapsed().as_secs_f64(),
        },
        improving_solutions: search.improving_solutions,
    }
}

struct TspSearch<'a> {
    distances: &'a [Vec<i64>],
    successors: Vec<Option<usize>>,
    used_destinations: Vec<bool>,
    assigned: usize,
    current_distance: i64,
    best_distance: Option<i64>,
    improving_solutions: Vec<TspSolution>,
    nodes: usize,
    failures: usize,
    deadline: Option<Instant>,
    timed_out: bool,
}

impl TspSearch<'_> {
    fn dfs(&mut self) {
        if self
            .deadline
            .is_some_and(|deadline| Instant::now() >= deadline)
        {
            self.timed_out = true;
            return;
        }

        if self
            .best_distance
            .is_some_and(|best| self.lower_bound() >= best)
        {
            self.failures += 1;
            return;
        }

        if self.assigned == self.successors.len() {
            let successors = self
                .successors
                .iter()
                .map(|successor| successor.expect("every successor is assigned"))
                .collect();
            self.best_distance = Some(self.current_distance);
            self.improving_solutions.push(TspSolution {
                distance: self.current_distance,
                successors,
            });
            return;
        }

        let source = self
            .successors
            .iter()
            .position(Option::is_none)
            .expect("an unassigned source exists");
        let mut destinations: Vec<_> = (0..self.successors.len())
            .filter(|destination| *destination != source && !self.used_destinations[*destination])
            .collect();
        destinations.sort_unstable_by_key(|destination| {
            std::cmp::Reverse(self.distances[source][*destination])
        });

        for destination in destinations {
            if self.timed_out {
                return;
            }
            self.nodes += 1;
            self.successors[source] = Some(destination);
            self.used_destinations[destination] = true;
            self.assigned += 1;
            self.current_distance += self.distances[source][destination];

            if self.closes_premature_cycle(source) {
                self.failures += 1;
            } else {
                self.dfs();
            }

            self.current_distance -= self.distances[source][destination];
            self.assigned -= 1;
            self.used_destinations[destination] = false;
            self.successors[source] = None;
        }
    }

    fn closes_premature_cycle(&self, source: usize) -> bool {
        let mut node = self.successors[source].expect("source was just assigned");
        for _ in 0..self.successors.len() {
            if node == source {
                return self.assigned < self.successors.len();
            }
            let Some(next) = self.successors[node] else {
                return false;
            };
            node = next;
        }
        false
    }

    fn lower_bound(&self) -> i64 {
        let mut bound = self.current_distance;
        for source in 0..self.successors.len() {
            if self.successors[source].is_some() {
                continue;
            }
            let cheapest = (0..self.successors.len())
                .filter(|destination| {
                    *destination != source && !self.used_destinations[*destination]
                })
                .map(|destination| self.distances[source][destination])
                .min();
            let Some(cheapest) = cheapest else {
                return i64::MAX;
            };
            bound = bound.saturating_add(cheapest);
        }
        bound
    }
}

#[cfg(test)]
mod tests {
    use super::solve_tsp;

    #[test]
    fn finds_the_best_hamiltonian_cycle() {
        let distances = vec![
            vec![0, 2, 9, 10],
            vec![1, 0, 6, 4],
            vec![15, 7, 0, 8],
            vec![6, 3, 12, 0],
        ];
        let result = solve_tsp(&distances, None);
        let best = result.improving_solutions.last().unwrap();

        assert_eq!(best.distance, 21);
        assert!(result.statistics.completed);
        assert_eq!(best.successors, vec![2, 0, 3, 1]);
    }

    #[test]
    fn honors_an_immediate_time_limit() {
        let distances = vec![vec![0, 1], vec![1, 0]];
        let result = solve_tsp(&distances, Some(0.0));

        assert!(!result.statistics.completed);
        assert!(result.improving_solutions.is_empty());
    }
}
