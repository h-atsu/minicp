use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

use crate::tsp;

#[pyclass(name = "TspStatistics", frozen)]
pub(crate) struct PyTspStatistics {
    #[pyo3(get)]
    nodes: usize,
    #[pyo3(get)]
    failures: usize,
    #[pyo3(get)]
    solutions: usize,
    #[pyo3(get)]
    completed: bool,
    #[pyo3(get)]
    elapsed_seconds: f64,
}

#[pyclass(name = "TspResult", frozen)]
pub(crate) struct PyTspResult {
    #[pyo3(get)]
    improving_solutions: Vec<(i64, Vec<usize>)>,
    #[pyo3(get)]
    statistics: Py<PyTspStatistics>,
}

#[pyfunction]
#[pyo3(signature = (distances, time_limit=None))]
pub(crate) fn solve_tsp(
    py: Python<'_>,
    distances: Vec<Vec<i64>>,
    time_limit: Option<f64>,
) -> PyResult<PyTspResult> {
    let node_count = distances.len();
    if node_count < 2 {
        return Err(PyValueError::new_err("TSP requires at least two nodes"));
    }
    if distances.iter().any(|row| row.len() != node_count) {
        return Err(PyValueError::new_err("distance matrix must be square"));
    }
    if time_limit.is_some_and(|limit| !limit.is_finite() || limit < 0.0) {
        return Err(PyValueError::new_err(
            "time limit must be finite and non-negative",
        ));
    }

    let result = py.detach(|| tsp::solve_tsp(&distances, time_limit));
    let statistics = Py::new(
        py,
        PyTspStatistics {
            nodes: result.statistics.nodes,
            failures: result.statistics.failures,
            solutions: result.statistics.solutions,
            completed: result.statistics.completed,
            elapsed_seconds: result.statistics.elapsed_seconds,
        },
    )?;
    Ok(PyTspResult {
        improving_solutions: result
            .improving_solutions
            .into_iter()
            .map(|solution| (solution.distance, solution.successors))
            .collect(),
        statistics,
    })
}
