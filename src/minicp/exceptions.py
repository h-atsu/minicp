"""Exceptions used by the constraint-programming engine."""


class Inconsistency(Exception):
    """Raised when propagation proves that the current branch has no solution."""
