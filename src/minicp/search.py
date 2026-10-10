"""Depth-first search over reversible solver state."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from minicp.exceptions import Inconsistency

if TYPE_CHECKING:
    from minicp.solver import Solver
    from minicp.variable import IntVarLike


Branch = Callable[[], None]
Branching = Callable[[], Sequence[Branch]]


def first_unfixed(
    variables: Sequence[IntVarLike],
) -> Branching:
    """Branch on the minimum value of the first non-fixed variable."""

    def branching() -> list[Branch]:
        variable = next(
            (candidate for candidate in variables if not candidate.is_fixed),
            None,
        )
        if variable is None:
            return []

        value = variable.min

        def assign() -> None:
            variable.fix(value)

        def exclude() -> None:
            variable.remove(value)

        return [assign, exclude]

    return branching


@dataclass
class SearchStatistics:
    """Counters collected during a complete depth-first search."""

    nodes: int = 0
    failures: int = 0
    solutions: int = 0
    completed: bool = False


class DFSearch:
    """Explore branches while saving and restoring all reversible state."""

    def __init__(self, solver: Solver, branching: Branching) -> None:
        self._solver = solver
        self._branching = branching
        self._solution_listeners: list[Callable[[], None]] = []
        self._statistics = SearchStatistics()

    def on_solution(self, listener: Callable[[], None]) -> None:
        self._solution_listeners.append(listener)

    def solve(self) -> SearchStatistics:
        self._statistics = SearchStatistics()
        state = self._solver.state_manager
        state.save()
        try:
            self._dfs()
            self._statistics.completed = True
        except Inconsistency:
            self._statistics.failures += 1
            self._statistics.completed = True
        finally:
            state.restore()
        return self._statistics

    def _dfs(self) -> None:
        branches = self._branching()
        if not branches:
            self._statistics.solutions += 1
            for listener in self._solution_listeners:
                listener()
            return

        state = self._solver.state_manager
        for branch in branches:
            state.save()
            try:
                self._statistics.nodes += 1
                branch()
                self._solver.fix_point()
                self._dfs()
            except Inconsistency:
                self._statistics.failures += 1
            finally:
                state.restore()
