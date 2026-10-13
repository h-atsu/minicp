use std::rc::Rc;

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

use crate::Inconsistency;
use crate::bindings::state::PyStateManager;
use crate::solver::{ConstraintId, SharedSolver, Solver, VariableId};

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
}

#[pyclass(unsendable, name = "Constraint")]
pub(crate) struct PyConstraint {
    solver: SharedSolver,
    id: ConstraintId,
}

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

#[pyfunction]
#[pyo3(signature = (x, y, offset=0))]
pub(crate) fn not_equal(
    x: PyRef<'_, PyIntVar>,
    y: PyRef<'_, PyIntVar>,
    offset: i64,
) -> PyResult<PyConstraint> {
    ensure_same_solver(&x.solver, &y.solver)?;
    let id = x.solver.borrow_mut().new_not_equal(x.id, y.id, offset);
    Ok(PyConstraint {
        solver: x.solver.clone(),
        id,
    })
}

#[pyfunction]
pub(crate) fn equal(x: PyRef<'_, PyIntVar>, y: PyRef<'_, PyIntVar>) -> PyResult<PyConstraint> {
    ensure_same_solver(&x.solver, &y.solver)?;
    let id = x.solver.borrow_mut().new_equal(x.id, y.id);
    Ok(PyConstraint {
        solver: x.solver.clone(),
        id,
    })
}

fn ensure_same_solver(left: &SharedSolver, right: &SharedSolver) -> PyResult<()> {
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
