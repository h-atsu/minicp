mod bindings;
mod solver;
mod sparse_set;
mod state;
mod state_sparse_set;

use bindings::solver::{PyBoolVar, PyConstraint, PyIntVar, PySolver, equal, not_equal};
use bindings::sparse_set::PySparseSet;
use bindings::state::{PyStateInt, PyStateManager};
use bindings::state_sparse_set::PyStateSparseSet;
use pyo3::prelude::*;

pyo3::create_exception!(_rust, Inconsistency, pyo3::exceptions::PyException);

#[pymodule]
fn _rust(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_class::<PySparseSet>()?;
    module.add_class::<PyStateManager>()?;
    module.add_class::<PyStateInt>()?;
    module.add_class::<PyStateSparseSet>()?;
    module.add_class::<PySolver>()?;
    module.add_class::<PyIntVar>()?;
    module.add_class::<PyBoolVar>()?;
    module.add_class::<PyConstraint>()?;
    module.add_function(wrap_pyfunction!(not_equal, module)?)?;
    module.add_function(wrap_pyfunction!(equal, module)?)?;
    module.add("Inconsistency", module.py().get_type::<Inconsistency>())?;
    Ok(())
}
