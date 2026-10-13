mod bindings;
mod sparse_set;
mod state;
mod state_sparse_set;

use bindings::sparse_set::PySparseSet;
use bindings::state::{PyStateInt, PyStateManager};
use bindings::state_sparse_set::PyStateSparseSet;
use pyo3::prelude::*;

#[pymodule]
fn _rust(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_class::<PySparseSet>()?;
    module.add_class::<PyStateManager>()?;
    module.add_class::<PyStateInt>()?;
    module.add_class::<PyStateSparseSet>()?;
    Ok(())
}
