"""Rust backend APIs that have reached parity with the Python reference."""

from minicp._rust import (
    BoolVar,
    Constraint,
    DFSearch,
    Inconsistency,
    IntVar,
    Minimize,
    SearchStatistics,
    Solver,
    StateInt,
    StateManager,
    all_different,
    circuit,
    element,
    equal,
    not_equal,
    sum_var,
)
from minicp._rust import StateSparseSet as SparseSet

__all__ = [
    "BoolVar",
    "Constraint",
    "DFSearch",
    "Inconsistency",
    "IntVar",
    "Minimize",
    "SearchStatistics",
    "Solver",
    "SparseSet",
    "StateInt",
    "StateManager",
    "all_different",
    "circuit",
    "element",
    "equal",
    "not_equal",
    "sum_var",
]
