"""Base and primitive constraints."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from minicp.state import StateInt

if TYPE_CHECKING:
    from minicp.solver import Solver
    from minicp.variable import IntVar


class Constraint(ABC):
    """Base class for constraints managed by a :class:`Solver`."""

    def __init__(self, solver: Solver) -> None:
        self.solver = solver
        self._active = StateInt(solver.state_manager, 1)
        self.scheduled = False

    @property
    def active(self) -> bool:
        return bool(self._active.value)

    def deactivate(self) -> None:
        self._active.set(0)

    @abstractmethod
    def post(self) -> None:
        """Register for variable events and perform initial propagation."""

    @abstractmethod
    def propagate(self) -> None:
        """Remove values that cannot participate in a solution."""


class NotEqual(Constraint):
    """The constraint ``x != y + offset``."""

    def __init__(self, x: IntVar, y: IntVar, offset: int = 0) -> None:
        if x.solver is not y.solver:
            raise ValueError("variables belong to different solvers")
        super().__init__(x.solver)
        self.x = x
        self.y = y
        self.offset = offset

    def post(self) -> None:
        if self.x.is_fixed or self.y.is_fixed:
            self.propagate()
        else:
            self.x.propagate_on_fix(self)
            self.y.propagate_on_fix(self)

    def propagate(self) -> None:
        if self.x.is_fixed:
            self.y.remove(self.x.value - self.offset)
            self.deactivate()
        elif self.y.is_fixed:
            self.x.remove(self.y.value + self.offset)
            self.deactivate()


def not_equal(x: IntVar, y: IntVar, offset: int = 0) -> NotEqual:
    """Create the constraint ``x != y + offset``."""

    return NotEqual(x, y, offset)
