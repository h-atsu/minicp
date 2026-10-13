mod algorithms;
mod bindings;
mod constraints;
mod objective;
mod search;
mod solver;
mod state;
mod variable;

use bindings::constraints::{
    PyConstraint, all_different, circuit, element, equal, not_equal, sum_var,
};
use bindings::search::{PyDFSearch, PyMinimize, PySearchStatistics};
use bindings::solver::PySolver;
use bindings::sparse_set::PySparseSet;
use bindings::state::{PyStateInt, PyStateManager};
use bindings::state_sparse_set::PyStateSparseSet;
use bindings::variable::{PyBoolVar, PyIntVar, PyOffsetView, plus};
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
    module.add_class::<PyOffsetView>()?;
    module.add_class::<PyConstraint>()?;
    module.add_class::<PyMinimize>()?;
    module.add_class::<PySearchStatistics>()?;
    module.add_class::<PyDFSearch>()?;
    module.add_function(wrap_pyfunction!(not_equal, module)?)?;
    module.add_function(wrap_pyfunction!(equal, module)?)?;
    module.add_function(wrap_pyfunction!(all_different, module)?)?;
    module.add_function(wrap_pyfunction!(circuit, module)?)?;
    module.add_function(wrap_pyfunction!(element, module)?)?;
    module.add_function(wrap_pyfunction!(sum_var, module)?)?;
    module.add_function(wrap_pyfunction!(plus, module)?)?;
    module.add("Inconsistency", module.py().get_type::<Inconsistency>())?;
    Ok(())
}
