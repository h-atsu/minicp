"""Depth-first search over reversible solver state."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from time import monotonic
from typing import TYPE_CHECKING

from minicp.exceptions import Inconsistency

if TYPE_CHECKING:
    from minicp.objective import Objective
    from minicp.solver import Solver
    from minicp.variable import IntVarLike


Branch = Callable[[], None]
Branching = Callable[[], Sequence[Branch]]


class _StopSearch(Exception):
    """Stop the current search without reporting a failure."""


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
    """Counters and completion state collected during depth-first search."""

    nodes: int = 0
    failures: int = 0
    solutions: int = 0
    completed: bool = False
    elapsed_seconds: float = 0.0


class DFSearch:
    """Explore branches while saving and restoring all reversible state."""

    def __init__(self, solver: Solver, branching: Branching) -> None:
        self._solver = solver
        self._branching = branching
        self._solution_listeners: list[Callable[[], None]] = []
        self._statistics = SearchStatistics()

    def on_solution(self, listener: Callable[[], None]) -> None:
        self._solution_listeners.append(listener)

    def solve(self, *, time_limit: float | None = None) -> SearchStatistics:
        """Enumerate all solutions in the search tree."""

        return self._run(None, time_limit)

    def optimize(
        self,
        objective: Objective,
        *,
        time_limit: float | None = None,
    ) -> SearchStatistics:
        """Run branch-and-bound search for improving solutions."""

        return self._run(objective, time_limit)

    def _run(
        self,
        objective: Objective | None,
        time_limit: float | None,
    ) -> SearchStatistics:
        if time_limit is not None and time_limit < 0:
            raise ValueError("time limit must be non-negative")

        self._statistics = SearchStatistics()
        started_at = monotonic()
        deadline = None if time_limit is None else started_at + time_limit
        state = self._solver.state_manager
        state.save()
        try:
            self._solver.fix_point()
            self._dfs(objective, deadline)
            self._statistics.completed = True
        except _StopSearch:
            pass
        except Inconsistency:
            self._statistics.failures += 1
            self._statistics.completed = True
        finally:
            state.restore()
            self._statistics.elapsed_seconds = monotonic() - started_at
        return self._statistics

    def _dfs(
        self, objective: Objective | None, deadline: float | None
    ) -> None:
        if deadline is not None and monotonic() >= deadline:
            raise _StopSearch

        branches = self._branching()
        if not branches:
            self._statistics.solutions += 1
            for listener in self._solution_listeners:
                listener()
            if objective is not None:
                objective.tighten()
            return

        state = self._solver.state_manager
        for branch in branches:
            state.save()
            try:
                self._statistics.nodes += 1
                branch()
                self._solver.fix_point()
                self._dfs(objective, deadline)
            except Inconsistency:
                self._statistics.failures += 1
            finally:
                state.restore()
