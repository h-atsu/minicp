//! Reversible depth-first search and branch-and-bound objectives.

use std::cell::Cell;
use std::time::{Duration, Instant};

use crate::objective::Minimize;
use crate::solver::{SharedSolver, VariableId};

pub struct SearchStatistics {
    pub nodes: usize,
    pub failures: usize,
    pub solutions: usize,
    pub completed: bool,
    pub elapsed_seconds: f64,
}

pub struct Search {
    solver: SharedSolver,
    variables: Vec<VariableId>,
    value_order: Option<Vec<Vec<i64>>>,
    solutions: Vec<Vec<i64>>,
}

impl Search {
    pub fn new(
        solver: SharedSolver,
        variables: Vec<VariableId>,
        value_order: Option<Vec<Vec<i64>>>,
    ) -> Result<Self, &'static str> {
        if value_order
            .as_ref()
            .is_some_and(|order| order.len() != variables.len())
        {
            return Err("value_order must have one row per variable");
        }
        Ok(Self {
            solver,
            variables,
            value_order,
            solutions: Vec::new(),
        })
    }

    pub fn solutions(&self) -> &[Vec<i64>] {
        &self.solutions
    }
    pub fn solve(&mut self, time_limit: Option<f64>) -> Result<SearchStatistics, &'static str> {
        self.run(None, time_limit)
    }
    pub fn optimize(
        &mut self,
        objective: &Minimize,
        time_limit: Option<f64>,
    ) -> Result<SearchStatistics, &'static str> {
        if !std::rc::Rc::ptr_eq(&self.solver, &objective.solver) {
            return Err("objective belongs to a different solver");
        }
        self.run(
            Some((&objective.best_value, objective.variable)),
            time_limit,
        )
    }

    fn run(
        &mut self,
        objective: Option<(&Cell<Option<i64>>, VariableId)>,
        time_limit: Option<f64>,
    ) -> Result<SearchStatistics, &'static str> {
        if time_limit.is_some_and(|limit| !limit.is_finite() || limit < 0.0) {
            return Err("time limit must be finite and non-negative");
        }
        self.solutions.clear();
        let started = Instant::now();
        let deadline = time_limit.map(|limit| started + Duration::from_secs_f64(limit));
        let manager = self.solver.borrow().state_manager.clone();
        manager.borrow_mut().save();
        let mut counters = Counters::default();
        if self.solver.borrow_mut().fix_point().is_err() {
            counters.failures += 1;
        } else {
            self.dfs(objective, deadline, &mut counters);
        }
        manager
            .borrow_mut()
            .restore()
            .expect("root state was saved");
        Ok(SearchStatistics {
            nodes: counters.nodes,
            failures: counters.failures,
            solutions: self.solutions.len(),
            completed: !counters.timed_out,
            elapsed_seconds: started.elapsed().as_secs_f64(),
        })
    }

    fn dfs(
        &mut self,
        objective: Option<(&Cell<Option<i64>>, VariableId)>,
        deadline: Option<Instant>,
        counters: &mut Counters,
    ) {
        if deadline.is_some_and(|limit| Instant::now() >= limit) {
            counters.timed_out = true;
            return;
        }
        if let Some((best, variable)) = objective {
            if let Some(value) = best.get() {
                let bounded = self.solver.borrow_mut().remove_above(variable, value - 1);
                let propagated = match bounded {
                    Ok(()) => self.solver.borrow_mut().fix_point(),
                    Err(error) => Err(error),
                };
                if propagated.is_err() {
                    counters.failures += 1;
                    return;
                }
            }
        }
        let Some((position, variable)) = self
            .variables
            .iter()
            .copied()
            .enumerate()
            .find(|(_, variable)| !self.solver.borrow().is_fixed(*variable))
        else {
            self.solutions.push(
                self.variables
                    .iter()
                    .map(|variable| {
                        self.solver
                            .borrow()
                            .value(*variable)
                            .expect("solution variable is fixed")
                    })
                    .collect(),
            );
            if let Some((best, objective_variable)) = objective {
                best.set(Some(
                    self.solver
                        .borrow()
                        .value(objective_variable)
                        .expect("objective is fixed"),
                ));
            }
            return;
        };
        let value = self
            .value_order
            .as_ref()
            .and_then(|orders| {
                orders[position]
                    .iter()
                    .find(|value| self.solver.borrow().contains(variable, **value))
                    .copied()
            })
            .unwrap_or_else(|| self.solver.borrow().min(variable));
        for assign in [true, false] {
            if counters.timed_out {
                return;
            }
            counters.nodes += 1;
            let manager = self.solver.borrow().state_manager.clone();
            manager.borrow_mut().save();
            let branch = if assign {
                self.solver.borrow_mut().fix(variable, value)
            } else {
                self.solver.borrow_mut().remove(variable, value)
            };
            let propagated = match branch {
                Ok(()) => self.solver.borrow_mut().fix_point(),
                Err(error) => Err(error),
            };
            if propagated.is_err() {
                counters.failures += 1;
            } else {
                self.dfs(objective, deadline, counters);
            }
            manager
                .borrow_mut()
                .restore()
                .expect("branch state was saved");
        }
    }
}

#[derive(Default)]
struct Counters {
    nodes: usize,
    failures: usize,
    timed_out: bool,
}
