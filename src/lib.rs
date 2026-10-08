mod bindings;
mod sparse_set;

use bindings::sparse_set::PySparseSet;
use pyo3::prelude::*;

#[pymodule]
fn _rust(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_class::<PySparseSet>()?;
    Ok(())
}
