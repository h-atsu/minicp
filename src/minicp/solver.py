"""Constraint propagation engine."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
from typing import TYPE_CHECKING

from minicp.exceptions import Inconsistency
from minicp.state import StateManager

if TYPE_CHECKING:
    from minicp.constraints.base import Constraint
    from minicp.objective import Maximize, Minimize
    from minicp.variable import IntVarLike


class Solver:
    """Own variables' reversible state and propagate scheduled constraints."""

    def __init__(self, state_manager: StateManager | None = None) -> None:
        self.state_manager = state_manager or StateManager()
        self._queue: deque[Constraint] = deque()
        self._fix_point_listeners: list[Callable[[], None]] = []

    def post(self, constraint: Constraint) -> None:
        """Initialize a constraint and propagate to a fix-point."""

        if constraint.solver is not self:
            raise ValueError("constraint belongs to a different solver")
        constraint.post()
        self.fix_point()

    def schedule(self, constraint: Constraint) -> None:
        """Add an active constraint to the queue at most once."""

        if constraint.active and not constraint.scheduled:
            constraint.scheduled = True
            self._queue.append(constraint)

    def on_fix_point(self, listener: Callable[[], None]) -> None:
        """Call ``listener`` before each propagation cycle."""

        self._fix_point_listeners.append(listener)

    def minimize(self, variable: IntVarLike) -> Minimize:
        """Create a minimization objective for ``variable``."""

        from minicp.objective import Minimize

        if variable.solver is not self:
            raise ValueError("variable belongs to a different solver")
        return Minimize(variable)

    def maximize(self, variable: IntVarLike) -> Maximize:
        """Create a maximization objective for ``variable``."""

        from minicp.objective import Maximize

        if variable.solver is not self:
            raise ValueError("variable belongs to a different solver")
        return Maximize(variable)

    def fix_point(self) -> None:
        """Propagate scheduled constraints until the queue is empty."""

        try:
            for listener in self._fix_point_listeners:
                listener()
            while self._queue:
                constraint = self._queue.popleft()
                constraint.scheduled = False
                if constraint.active:
                    constraint.propagate()
        except Inconsistency:
            self._clear_queue()
            raise

    def _clear_queue(self) -> None:
        while self._queue:
            self._queue.popleft().scheduled = False
