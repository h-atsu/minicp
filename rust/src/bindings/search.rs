//! Thin PyO3 wrappers for the Rust search implementation.

use std::rc::Rc;

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

use crate::bindings::solver::PySolver;
use crate::bindings::variable::PyIntVar;
use crate::objective::Minimize;
use crate::search::{Search, SearchStatistics};

#[pyclass(unsendable, name = "Minimize")]
pub(crate) struct PyMinimize {
    pub(crate) inner: Minimize,
}

impl PyMinimize {
    pub(crate) fn new(
        solver: crate::solver::SharedSolver,
        variable: crate::solver::VariableId,
    ) -> Self {
        Self {
            inner: Minimize::new(solver, variable),
        }
    }
}

#[pymethods]
impl PyMinimize {
    #[getter]
    fn best_value(&self) -> Option<i64> {
        self.inner.best_value()
    }
}

#[pyclass(name = "SearchStatistics", frozen)]
pub(crate) struct PySearchStatistics {
    #[pyo3(get)]
    nodes: usize,
    #[pyo3(get)]
    failures: usize,
    #[pyo3(get)]
    solutions: usize,
    #[pyo3(get)]
    completed: bool,
    #[pyo3(get)]
    elapsed_seconds: f64,
}

impl From<SearchStatistics> for PySearchStatistics {
    fn from(statistics: SearchStatistics) -> Self {
        Self {
            nodes: statistics.nodes,
            failures: statistics.failures,
            solutions: statistics.solutions,
            completed: statistics.completed,
            elapsed_seconds: statistics.elapsed_seconds,
        }
    }
}

#[pyclass(unsendable, name = "DFSearch")]
pub(crate) struct PyDFSearch {
    inner: Search,
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
        let inner =
            Search::new(solver.inner.clone(), ids, value_order).map_err(PyValueError::new_err)?;
        Ok(Self { inner })
    }

    #[getter]
    fn solutions(&self) -> Vec<Vec<i64>> {
        self.inner.solutions().to_vec()
    }

    #[pyo3(signature = (*, time_limit=None))]
    fn solve(&mut self, time_limit: Option<f64>) -> PyResult<PySearchStatistics> {
        self.inner
            .solve(time_limit)
            .map(Into::into)
            .map_err(PyValueError::new_err)
    }

    #[pyo3(signature = (objective, *, time_limit=None))]
    fn optimize(
        &mut self,
        objective: PyRef<'_, PyMinimize>,
        time_limit: Option<f64>,
    ) -> PyResult<PySearchStatistics> {
        self.inner
            .optimize(&objective.inner, time_limit)
            .map(Into::into)
            .map_err(PyValueError::new_err)
    }
}
