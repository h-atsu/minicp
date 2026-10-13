//! Python constructors for Rust constraints.

use pyo3::exceptions::{PyTypeError, PyValueError};
use pyo3::prelude::*;

use crate::Inconsistency;
use crate::bindings::variable::{PyIntVar, PyOffsetView, ensure_same_solver};
use crate::solver::{ConstraintId, SharedSolver, VariableId};
use crate::variable::VariableView;

#[pyclass(unsendable, name = "Constraint")]
pub(crate) struct PyConstraint {
    pub(crate) solver: SharedSolver,
    pub(crate) id: ConstraintId,
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

#[pyfunction]
pub(crate) fn all_different(py: Python<'_>, variables: Vec<Py<PyAny>>) -> PyResult<PyConstraint> {
    let (solver, views) = variable_views(py, &variables)?;
    let id = solver
        .borrow_mut()
        .new_all_different_views(views)
        .map_err(PyValueError::new_err)?;
    Ok(PyConstraint { solver, id })
}

fn variable_views(
    py: Python<'_>,
    variables: &[Py<PyAny>],
) -> PyResult<(SharedSolver, Vec<VariableView>)> {
    let first = variables
        .first()
        .ok_or_else(|| PyValueError::new_err("at least one variable is required"))?;
    let (solver, first_view) = extract_variable_view(first.bind(py))?;
    let mut views = Vec::with_capacity(variables.len());
    views.push(first_view);
    for variable in &variables[1..] {
        let (variable_solver, view) = extract_variable_view(variable.bind(py))?;
        ensure_same_solver(&solver, &variable_solver)?;
        views.push(view);
    }
    Ok((solver, views))
}

fn extract_variable_view(variable: &Bound<'_, PyAny>) -> PyResult<(SharedSolver, VariableView)> {
    if let Ok(variable) = variable.extract::<PyRef<'_, PyIntVar>>() {
        return Ok((variable.solver.clone(), VariableView::identity(variable.id)));
    }
    if let Ok(variable) = variable.extract::<PyRef<'_, PyOffsetView>>() {
        return Ok((
            variable.solver.clone(),
            VariableView {
                variable: variable.id,
                offset: variable.offset,
            },
        ));
    }
    Err(PyTypeError::new_err(
        "all_different expects IntVar or OffsetView values",
    ))
}

#[pyfunction]
pub(crate) fn circuit(py: Python<'_>, variables: Vec<Py<PyIntVar>>) -> PyResult<PyConstraint> {
    let (solver, ids) = variable_ids(py, &variables)?;
    let id = solver
        .borrow_mut()
        .new_circuit(ids)
        .map_err(PyValueError::new_err)?;
    Ok(PyConstraint { solver, id })
}

#[pyfunction]
pub(crate) fn element(values: Vec<i64>, index: PyRef<'_, PyIntVar>) -> PyResult<PyIntVar> {
    let id = index
        .solver
        .borrow_mut()
        .new_element(values, index.id)
        .map_err(Inconsistency::new_err)?;
    Ok(PyIntVar {
        solver: index.solver.clone(),
        id,
    })
}

#[pyfunction]
pub(crate) fn sum_var(py: Python<'_>, variables: Vec<Py<PyIntVar>>) -> PyResult<PyIntVar> {
    let (solver, ids) = variable_ids(py, &variables)?;
    let id = solver
        .borrow_mut()
        .new_sum_variable(ids)
        .map_err(Inconsistency::new_err)?;
    Ok(PyIntVar { solver, id })
}

fn variable_ids(
    py: Python<'_>,
    variables: &[Py<PyIntVar>],
) -> PyResult<(SharedSolver, Vec<VariableId>)> {
    let first = variables
        .first()
        .ok_or_else(|| PyValueError::new_err("at least one variable is required"))?
        .borrow(py);
    let solver = first.solver.clone();
    let mut ids = Vec::with_capacity(variables.len());
    for variable in variables {
        let variable = variable.borrow(py);
        ensure_same_solver(&solver, &variable.solver)?;
        ids.push(variable.id);
    }
    Ok((solver, ids))
}
