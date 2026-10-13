//! Python wrappers for integer and boolean variables.

use std::rc::Rc;

use pyo3::exceptions::{PyOverflowError, PyValueError};
use pyo3::prelude::*;

use crate::Inconsistency;
use crate::bindings::solver::PySolver;
use crate::solver::{SharedSolver, VariableId};

#[pyclass(unsendable, name = "IntVar")]
pub(crate) struct PyIntVar {
    pub(crate) solver: SharedSolver,
    pub(crate) id: VariableId,
}

impl PyIntVar {
    fn make(
        solver: SharedSolver,
        minimum: i64,
        maximum: i64,
        name: Option<String>,
    ) -> PyResult<Self> {
        let id = solver
            .borrow_mut()
            .new_variable(minimum, maximum, name)
            .map_err(PyValueError::new_err)?;
        Ok(Self { solver, id })
    }
}

#[pyclass(unsendable, name = "OffsetView")]
pub(crate) struct PyOffsetView {
    pub(crate) solver: SharedSolver,
    pub(crate) id: VariableId,
    pub(crate) offset: i64,
}

impl PyOffsetView {
    fn make(solver: SharedSolver, id: VariableId, offset: i64) -> PyResult<Self> {
        let range_fits = {
            let solver = solver.borrow();
            solver.min(id).checked_add(offset).is_some()
                && solver.max(id).checked_add(offset).is_some()
        };
        if !range_fits {
            return Err(PyOverflowError::new_err(
                "offset view values must fit in a signed 64-bit integer",
            ));
        }
        Ok(Self { solver, id, offset })
    }

    fn to_underlying(&self, value: i64) -> Option<i64> {
        value.checked_sub(self.offset)
    }

    fn viewed_value(&self, value: i64) -> i64 {
        value
            .checked_add(self.offset)
            .expect("offset view range was validated")
    }
}

#[pymethods]
impl PyOffsetView {
    #[new]
    fn new(variable: PyRef<'_, PyIntVar>, offset: i64) -> PyResult<Self> {
        Self::make(variable.solver.clone(), variable.id, offset)
    }
    #[getter]
    fn solver(&self) -> PySolver {
        PySolver {
            inner: self.solver.clone(),
        }
    }
    #[getter]
    fn min(&self) -> i64 {
        self.viewed_value(self.solver.borrow().min(self.id))
    }
    #[getter]
    fn max(&self) -> i64 {
        self.viewed_value(self.solver.borrow().max(self.id))
    }
    #[getter]
    fn size(&self) -> usize {
        self.solver.borrow().size(self.id)
    }
    #[getter]
    fn is_fixed(&self) -> bool {
        self.solver.borrow().is_fixed(self.id)
    }
    #[getter]
    fn value(&self) -> PyResult<i64> {
        self.solver
            .borrow()
            .value(self.id)
            .map(|value| self.viewed_value(value))
            .map_err(PyValueError::new_err)
    }
    fn values(&self) -> Vec<i64> {
        self.solver
            .borrow()
            .values(self.id)
            .into_iter()
            .map(|value| self.viewed_value(value))
            .collect()
    }
    fn contains(&self, value: i64) -> bool {
        self.to_underlying(value)
            .is_some_and(|value| self.solver.borrow().contains(self.id, value))
    }
    fn remove(&self, value: i64) -> PyResult<()> {
        let Some(value) = self.to_underlying(value) else {
            return Ok(());
        };
        self.solver
            .borrow_mut()
            .remove(self.id, value)
            .map_err(Inconsistency::new_err)
    }
    fn fix(&self, value: i64) -> PyResult<()> {
        let value = self
            .to_underlying(value)
            .ok_or_else(|| Inconsistency::new_err("cannot fix OffsetView to absent value"))?;
        self.solver
            .borrow_mut()
            .fix(self.id, value)
            .map_err(Inconsistency::new_err)
    }
    fn remove_below(&self, value: i64) -> PyResult<()> {
        let value = self.to_underlying(value).ok_or_else(|| {
            PyOverflowError::new_err("translated lower bound does not fit in i64")
        })?;
        self.solver
            .borrow_mut()
            .remove_below(self.id, value)
            .map_err(Inconsistency::new_err)
    }
    fn remove_above(&self, value: i64) -> PyResult<()> {
        let value = self.to_underlying(value).ok_or_else(|| {
            PyOverflowError::new_err("translated upper bound does not fit in i64")
        })?;
        self.solver
            .borrow_mut()
            .remove_above(self.id, value)
            .map_err(Inconsistency::new_err)
    }
    fn __repr__(&self) -> String {
        let mut values = self.values();
        values.sort_unstable();
        if values.len() == 1 {
            format!("OffsetView={}", values[0])
        } else {
            format!(
                "OffsetView={{{}}}",
                values
                    .iter()
                    .map(ToString::to_string)
                    .collect::<Vec<_>>()
                    .join(", ")
            )
        }
    }
}

#[pyfunction]
pub(crate) fn plus(variable: PyRef<'_, PyIntVar>, offset: i64) -> PyResult<PyOffsetView> {
    PyOffsetView::make(variable.solver.clone(), variable.id, offset)
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
            inner: self.solver.clone(),
        }
    }
    #[getter]
    fn min(&self) -> i64 {
        self.solver.borrow().min(self.id)
    }
    #[getter]
    fn max(&self) -> i64 {
        self.solver.borrow().max(self.id)
    }
    #[getter]
    fn size(&self) -> usize {
        self.solver.borrow().size(self.id)
    }
    #[getter]
    fn is_fixed(&self) -> bool {
        self.solver.borrow().is_fixed(self.id)
    }
    #[getter]
    fn value(&self) -> PyResult<i64> {
        self.solver
            .borrow()
            .value(self.id)
            .map_err(PyValueError::new_err)
    }
    fn values(&self) -> Vec<i64> {
        self.solver.borrow().values(self.id)
    }
    fn contains(&self, value: i64) -> bool {
        self.solver.borrow().contains(self.id, value)
    }
    fn remove(&self, value: i64) -> PyResult<()> {
        self.solver
            .borrow_mut()
            .remove(self.id, value)
            .map_err(Inconsistency::new_err)
    }
    fn fix(&self, value: i64) -> PyResult<()> {
        self.solver
            .borrow_mut()
            .fix(self.id, value)
            .map_err(Inconsistency::new_err)
    }
    fn remove_below(&self, value: i64) -> PyResult<()> {
        self.solver
            .borrow_mut()
            .remove_below(self.id, value)
            .map_err(Inconsistency::new_err)
    }
    fn remove_above(&self, value: i64) -> PyResult<()> {
        self.solver
            .borrow_mut()
            .remove_above(self.id, value)
            .map_err(Inconsistency::new_err)
    }
    fn __repr__(&self) -> String {
        variable_repr(&self.solver, self.id)
    }
}

#[pyclass(unsendable, name = "BoolVar")]
pub(crate) struct PyBoolVar {
    solver: SharedSolver,
    id: VariableId,
}

#[pymethods]
impl PyBoolVar {
    #[new]
    #[pyo3(signature = (solver, name=None))]
    fn new(solver: PyRef<'_, PySolver>, name: Option<String>) -> PyResult<Self> {
        let id = solver
            .inner
            .borrow_mut()
            .new_variable(0, 1, name)
            .map_err(PyValueError::new_err)?;
        Ok(Self {
            solver: solver.inner.clone(),
            id,
        })
    }
    #[getter]
    fn solver(&self) -> PySolver {
        PySolver {
            inner: self.solver.clone(),
        }
    }
    #[getter]
    fn min(&self) -> i64 {
        self.solver.borrow().min(self.id)
    }
    #[getter]
    fn max(&self) -> i64 {
        self.solver.borrow().max(self.id)
    }
    #[getter]
    fn size(&self) -> usize {
        self.solver.borrow().size(self.id)
    }
    #[getter]
    fn is_fixed(&self) -> bool {
        self.solver.borrow().is_fixed(self.id)
    }
    #[getter]
    fn value(&self) -> PyResult<i64> {
        self.solver
            .borrow()
            .value(self.id)
            .map_err(PyValueError::new_err)
    }
    #[getter]
    fn is_true(&self) -> bool {
        self.solver.borrow().value(self.id) == Ok(1)
    }
    #[getter]
    fn is_false(&self) -> bool {
        self.solver.borrow().value(self.id) == Ok(0)
    }
    fn values(&self) -> Vec<i64> {
        self.solver.borrow().values(self.id)
    }
    fn contains(&self, value: i64) -> bool {
        self.solver.borrow().contains(self.id, value)
    }
    fn remove(&self, value: i64) -> PyResult<()> {
        self.solver
            .borrow_mut()
            .remove(self.id, value)
            .map_err(Inconsistency::new_err)
    }
    fn fix(&self, value: i64) -> PyResult<()> {
        self.solver
            .borrow_mut()
            .fix(self.id, value)
            .map_err(Inconsistency::new_err)
    }
    fn remove_below(&self, value: i64) -> PyResult<()> {
        self.solver
            .borrow_mut()
            .remove_below(self.id, value)
            .map_err(Inconsistency::new_err)
    }
    fn remove_above(&self, value: i64) -> PyResult<()> {
        self.solver
            .borrow_mut()
            .remove_above(self.id, value)
            .map_err(Inconsistency::new_err)
    }
}

pub(crate) fn ensure_same_solver(left: &SharedSolver, right: &SharedSolver) -> PyResult<()> {
    if Rc::ptr_eq(left, right) {
        Ok(())
    } else {
        Err(PyValueError::new_err(
            "variables belong to different solvers",
        ))
    }
}

fn variable_repr(solver: &SharedSolver, id: VariableId) -> String {
    let solver = solver.borrow();
    let label = solver.name(id).unwrap_or("IntVar");
    if solver.is_fixed(id) {
        format!("{label}={}", solver.value(id).expect("fixed"))
    } else {
        let mut values = solver.values(id);
        values.sort_unstable();
        format!(
            "{label}={{{}}}",
            values
                .iter()
                .map(ToString::to_string)
                .collect::<Vec<_>>()
                .join(", ")
        )
    }
}
