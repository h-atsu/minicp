"""Rust backend APIs that have reached parity with the Python reference."""

from minicp._rust import (
    BoolVar,
    Inconsistency,
    IntVar,
    Solver,
    StateInt,
    StateManager,
    TspResult,
    TspStatistics,
    solve_tsp,
)
from minicp._rust import StateSparseSet as SparseSet

__all__ = [
    "BoolVar",
    "Inconsistency",
    "IntVar",
    "Solver",
    "SparseSet",
    "StateInt",
    "StateManager",
    "TspResult",
    "TspStatistics",
    "solve_tsp",
]
