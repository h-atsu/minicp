"""Base class for constraints."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from minicp.state import StateInt

if TYPE_CHECKING:
    from minicp.solver import Solver


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
