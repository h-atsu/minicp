//! Python wrapper for the solver arena.

use pyo3::prelude::*;

use crate::Inconsistency;
use crate::bindings::constraints::PyConstraint;
use crate::bindings::search::PyMinimize;
use crate::bindings::state::PyStateManager;
use crate::bindings::variable::{PyIntVar, ensure_same_solver};
use crate::solver::{SharedSolver, Solver};

#[pyclass(unsendable, name = "Solver")]
pub(crate) struct PySolver {
    pub(crate) inner: SharedSolver,
}

#[pymethods]
impl PySolver {
    #[new]
    #[pyo3(signature = (state_manager=None))]
    fn new(state_manager: Option<PyRef<'_, PyStateManager>>) -> Self {
        Self {
            inner: state_manager.map_or_else(Solver::shared, |manager| {
                Solver::with_manager(manager.inner.clone())
            }),
        }
    }

    #[getter]
    fn state_manager(&self) -> PyStateManager {
        PyStateManager::from_shared(self.inner.borrow().state_manager.clone())
    }

    fn post(&self, constraint: PyRef<'_, PyConstraint>) -> PyResult<()> {
        ensure_same_solver(&self.inner, &constraint.solver)?;
        self.inner
            .borrow_mut()
            .post(constraint.id)
            .map_err(Inconsistency::new_err)
    }

    fn fix_point(&self) -> PyResult<()> {
        self.inner
            .borrow_mut()
            .fix_point()
            .map_err(Inconsistency::new_err)
    }

    fn minimize(&self, variable: PyRef<'_, PyIntVar>) -> PyResult<PyMinimize> {
        ensure_same_solver(&self.inner, &variable.solver)?;
        Ok(PyMinimize::new(self.inner.clone(), variable.id))
    }
}
