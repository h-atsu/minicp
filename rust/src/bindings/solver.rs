use std::cell::RefCell;
use std::rc::Rc;

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

use crate::Inconsistency;
use crate::bindings::state::PyStateManager;
use crate::solver::{IntVar, SharedSolver, Solver};

#[pyclass(unsendable, name = "Solver")]
pub(crate) struct PySolver {
    pub(crate) inner: SharedSolver,
}

#[pymethods]
impl PySolver {
    #[new]
    #[pyo3(signature = (state_manager=None))]
    fn new(state_manager: Option<PyRef<'_, PyStateManager>>) -> Self {
        let inner = match state_manager {
            Some(manager) => Rc::new(RefCell::new(Solver {
                state_manager: manager.inner.clone(),
            })),
            None => Solver::shared(),
        };
        Self { inner }
    }

    #[getter]
    fn state_manager(&self) -> PyStateManager {
        PyStateManager::from_shared(self.inner.borrow().state_manager.clone())
    }
}

#[pyclass(unsendable, name = "IntVar")]
pub(crate) struct PyIntVar {
    inner: Rc<RefCell<IntVar>>,
}

impl PyIntVar {
    fn make(
        solver: SharedSolver,
        minimum: i64,
        maximum: i64,
        name: Option<String>,
    ) -> PyResult<Self> {
        let inner = IntVar::new(solver, minimum, maximum, name).map_err(PyValueError::new_err)?;
        Ok(Self {
            inner: Rc::new(RefCell::new(inner)),
        })
    }
}

#[pymethods]
impl PyIntVar {
    #[new]
    #[pyo3(signature = (solver, minimum, maximum, name=None))]
    fn new(
        solver: PyRef<'_, PySolver>,
        minimum: i64,
        maximum: i64,
        name: Option<String>,
    ) -> PyResult<Self> {
        Self::make(solver.inner.clone(), minimum, maximum, name)
    }

    #[getter]
    fn solver(&self) -> PySolver {
        PySolver {
            inner: self.inner.borrow().solver.clone(),
        }
    }

    #[getter]
    fn min(&self) -> i64 {
        self.inner.borrow().min()
    }

    #[getter]
    fn max(&self) -> i64 {
        self.inner.borrow().max()
    }

    #[getter]
    fn size(&self) -> usize {
        self.inner.borrow().size()
    }

    #[getter]
    fn is_fixed(&self) -> bool {
        self.inner.borrow().is_fixed()
    }

    #[getter]
    fn value(&self) -> PyResult<i64> {
        self.inner.borrow().value().map_err(PyValueError::new_err)
    }

    fn values(&self) -> Vec<i64> {
        self.inner.borrow().values()
    }

    fn contains(&self, value: i64) -> bool {
        self.inner.borrow().contains(value)
    }

    fn remove(&self, value: i64) -> PyResult<()> {
        self.inner
            .borrow_mut()
            .remove(value)
            .map_err(Inconsistency::new_err)
    }

    fn fix(&self, value: i64) -> PyResult<()> {
        self.inner
            .borrow_mut()
            .fix(value)
            .map_err(Inconsistency::new_err)
    }

    fn remove_below(&self, value: i64) -> PyResult<()> {
        self.inner
            .borrow_mut()
            .remove_below(value)
            .map_err(Inconsistency::new_err)
    }

    fn remove_above(&self, value: i64) -> PyResult<()> {
        self.inner
            .borrow_mut()
            .remove_above(value)
            .map_err(Inconsistency::new_err)
    }

    fn __repr__(&self) -> String {
        let variable = self.inner.borrow();
        let label = variable.name.as_deref().unwrap_or("IntVar");
        if variable.is_fixed() {
            format!("{label}={}", variable.value().expect("fixed variable"))
        } else {
            let mut values = variable.values();
            values.sort_unstable();
            let values = values
                .iter()
                .map(ToString::to_string)
                .collect::<Vec<_>>()
                .join(", ");
            format!("{label}={{{values}}}")
        }
    }
}

#[pyclass(unsendable, name = "BoolVar")]
pub(crate) struct PyBoolVar {
    inner: Rc<RefCell<IntVar>>,
}

#[pymethods]
impl PyBoolVar {
    #[new]
    #[pyo3(signature = (solver, name=None))]
    fn new(solver: PyRef<'_, PySolver>, name: Option<String>) -> PyResult<Self> {
        let variable =
            IntVar::new(solver.inner.clone(), 0, 1, name).map_err(PyValueError::new_err)?;
        Ok(Self {
            inner: Rc::new(RefCell::new(variable)),
        })
    }

    #[getter]
    fn solver(&self) -> PySolver {
        PySolver {
            inner: self.inner.borrow().solver.clone(),
        }
    }

    #[getter]
    fn min(&self) -> i64 {
        self.inner.borrow().min()
    }

    #[getter]
    fn max(&self) -> i64 {
        self.inner.borrow().max()
    }

    #[getter]
    fn size(&self) -> usize {
        self.inner.borrow().size()
    }

    #[getter]
    fn is_fixed(&self) -> bool {
        self.inner.borrow().is_fixed()
    }

    #[getter]
    fn value(&self) -> PyResult<i64> {
        self.inner.borrow().value().map_err(PyValueError::new_err)
    }

    #[getter]
    fn is_true(&self) -> bool {
        self.inner.borrow().value() == Ok(1)
    }

    #[getter]
    fn is_false(&self) -> bool {
        self.inner.borrow().value() == Ok(0)
    }

    fn values(&self) -> Vec<i64> {
        self.inner.borrow().values()
    }

    fn contains(&self, value: i64) -> bool {
        self.inner.borrow().contains(value)
    }

    fn remove(&self, value: i64) -> PyResult<()> {
        self.inner
            .borrow_mut()
            .remove(value)
            .map_err(Inconsistency::new_err)
    }

    fn fix(&self, value: i64) -> PyResult<()> {
        self.inner
            .borrow_mut()
            .fix(value)
            .map_err(Inconsistency::new_err)
    }

    fn remove_below(&self, value: i64) -> PyResult<()> {
        self.inner
            .borrow_mut()
            .remove_below(value)
            .map_err(Inconsistency::new_err)
    }

    fn remove_above(&self, value: i64) -> PyResult<()> {
        self.inner
            .borrow_mut()
            .remove_above(value)
            .map_err(Inconsistency::new_err)
    }
}
