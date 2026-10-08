use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

use crate::sparse_set::SparseSet;

#[pyclass(name = "SparseSet")]
pub(crate) struct PySparseSet {
    inner: SparseSet,
}

#[pymethods]
impl PySparseSet {
    #[new]
    fn new(minimum: i64, maximum: i64) -> PyResult<Self> {
        let inner = SparseSet::new(minimum, maximum)
            .map_err(|error| PyValueError::new_err(error.to_string()))?;
        Ok(Self { inner })
    }

    #[getter]
    fn size(&self) -> usize {
        self.inner.size()
    }

    #[getter]
    fn min(&self) -> PyResult<i64> {
        self.inner
            .min()
            .ok_or_else(|| PyValueError::new_err("empty sparse set has no minimum"))
    }

    #[getter]
    fn max(&self) -> PyResult<i64> {
        self.inner
            .max()
            .ok_or_else(|| PyValueError::new_err("empty sparse set has no maximum"))
    }

    fn contains(&self, value: i64) -> bool {
        self.inner.contains(value)
    }

    fn remove(&mut self, value: i64) -> bool {
        self.inner.remove(value)
    }

    fn values(&self) -> Vec<i64> {
        self.inner.values().collect()
    }
}
