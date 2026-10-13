"""Rust backend APIs that have reached parity with the Python reference."""

from minicp._rust import (
    BoolVar,
    Constraint,
    Inconsistency,
    IntVar,
    Solver,
    StateInt,
    StateManager,
    all_different,
    circuit,
    equal,
    not_equal,
)
from minicp._rust import StateSparseSet as SparseSet

__all__ = [
    "BoolVar",
    "Constraint",
    "Inconsistency",
    "IntVar",
    "Solver",
    "SparseSet",
    "StateInt",
    "StateManager",
    "all_different",
    "circuit",
    "equal",
    "not_equal",
]
