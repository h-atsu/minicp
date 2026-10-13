use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;

use crate::state::{SharedStateManager, StateInt, StateManager};

#[pyclass(unsendable, name = "StateManager")]
pub(crate) struct PyStateManager {
    pub(crate) inner: SharedStateManager,
}

impl PyStateManager {
    pub(crate) fn from_shared(inner: SharedStateManager) -> Self {
        Self { inner }
    }
}

#[pymethods]
impl PyStateManager {
    #[new]
    fn new() -> Self {
        Self::from_shared(StateManager::shared())
    }

    #[getter]
    fn level(&self) -> isize {
        self.inner.borrow().level()
    }

    fn save(&self) {
        self.inner.borrow_mut().save();
    }

    fn restore(&self) -> PyResult<()> {
        self.inner
            .borrow_mut()
            .restore()
            .map_err(PyRuntimeError::new_err)
    }
}

#[pyclass(unsendable, name = "StateInt")]
pub(crate) struct PyStateInt {
    inner: StateInt,
}

#[pymethods]
impl PyStateInt {
    #[new]
    fn new(manager: PyRef<'_, PyStateManager>, value: i64) -> Self {
        Self {
            inner: StateInt::new(manager.inner.clone(), value),
        }
    }

    #[getter]
    fn value(&self) -> i64 {
        self.inner.value()
    }

    fn set(&self, value: i64) {
        self.inner.set(value);
    }
}
