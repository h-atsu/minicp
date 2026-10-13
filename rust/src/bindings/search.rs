use std::cell::Cell;
use std::rc::Rc;
use std::time::{Duration, Instant};

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

use crate::bindings::solver::{PyIntVar, PySolver};
use crate::solver::{SharedSolver, VariableId};

#[pyclass(unsendable, name = "Minimize")]
pub(crate) struct PyMinimize {
    pub(crate) solver: SharedSolver,
    pub(crate) variable: VariableId,
    best_value: Rc<Cell<Option<i64>>>,
}

impl PyMinimize {
    pub(crate) fn new(solver: SharedSolver, variable: VariableId) -> Self {
        Self {
            solver,
            variable,
            best_value: Rc::new(Cell::new(None)),
        }
    }
}

#[pymethods]
impl PyMinimize {
    #[getter]
    fn best_value(&self) -> Option<i64> {
        self.best_value.get()
    }
}

#[pyclass(name = "SearchStatistics", frozen)]
pub(crate) struct PySearchStatistics {
    #[pyo3(get)]
    pub(crate) nodes: usize,
    #[pyo3(get)]
    pub(crate) failures: usize,
    #[pyo3(get)]
    pub(crate) solutions: usize,
    #[pyo3(get)]
    pub(crate) completed: bool,
    #[pyo3(get)]
    pub(crate) elapsed_seconds: f64,
}

#[pyclass(unsendable, name = "DFSearch")]
pub(crate) struct PyDFSearch {
    solver: SharedSolver,
    variables: Vec<VariableId>,
    value_order: Option<Vec<Vec<i64>>>,
    solutions: Vec<Vec<i64>>,
}

#[pymethods]
impl PyDFSearch {
    #[new]
    #[pyo3(signature = (solver, variables, value_order=None))]
    fn new(
        py: Python<'_>,
        solver: PyRef<'_, PySolver>,
        variables: Vec<Py<PyIntVar>>,
        value_order: Option<Vec<Vec<i64>>>,
    ) -> PyResult<Self> {
        let mut ids = Vec::with_capacity(variables.len());
        for variable in variables {
            let variable = variable.borrow(py);
            if !Rc::ptr_eq(&solver.inner, &variable.solver) {
                return Err(PyValueError::new_err(
                    "variables belong to a different solver",
                ));
            }
            ids.push(variable.id);
        }
        if value_order
            .as_ref()
            .is_some_and(|order| order.len() != ids.len())
        {
            return Err(PyValueError::new_err(
                "value_order must have one row per variable",
            ));
        }
        Ok(Self {
            solver: solver.inner.clone(),
            variables: ids,
            value_order,
            solutions: Vec::new(),
        })
    }

    #[getter]
    fn solutions(&self) -> Vec<Vec<i64>> {
        self.solutions.clone()
    }

    #[pyo3(signature = (*, time_limit=None))]
    fn solve(&mut self, time_limit: Option<f64>) -> PyResult<PySearchStatistics> {
        self.run(None, time_limit)
    }

    #[pyo3(signature = (objective, *, time_limit=None))]
    fn optimize(
        &mut self,
        objective: PyRef<'_, PyMinimize>,
        time_limit: Option<f64>,
    ) -> PyResult<PySearchStatistics> {
        if !Rc::ptr_eq(&self.solver, &objective.solver) {
            return Err(PyValueError::new_err(
                "objective belongs to a different solver",
            ));
        }
        self.run(
            Some((&objective.best_value, objective.variable)),
            time_limit,
        )
    }
}

impl PyDFSearch {
    fn run(
        &mut self,
        objective: Option<(&Cell<Option<i64>>, VariableId)>,
        time_limit: Option<f64>,
    ) -> PyResult<PySearchStatistics> {
        if time_limit.is_some_and(|limit| !limit.is_finite() || limit < 0.0) {
            return Err(PyValueError::new_err(
                "time limit must be finite and non-negative",
            ));
        }
        self.solutions.clear();
        let started = Instant::now();
        let deadline = time_limit.map(|limit| started + Duration::from_secs_f64(limit));
        let manager = self.solver.borrow().state_manager.clone();
        manager.borrow_mut().save();
        let mut counters = Counters::default();
        let root = self.solver.borrow_mut().fix_point();
        if root.is_err() {
            counters.failures += 1;
        } else {
            self.dfs(objective, deadline, &mut counters);
        }
        manager
            .borrow_mut()
            .restore()
            .expect("root state was saved");
        Ok(PySearchStatistics {
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
