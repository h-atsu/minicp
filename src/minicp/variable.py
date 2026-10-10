"""Integer decision variables."""

from __future__ import annotations

from typing import TYPE_CHECKING

from minicp.exceptions import Inconsistency
from minicp.sparse_set import SparseSet
from minicp.state import StateStack

if TYPE_CHECKING:
    from minicp.constraint import Constraint
    from minicp.solver import Solver


class IntVar:
    """An integer variable backed by a reversible sparse-set domain."""

    def __init__(
        self,
        solver: Solver,
        minimum: int,
        maximum: int,
        name: str | None = None,
    ) -> None:
        self.solver = solver
        self.name = name
        self._domain = SparseSet(solver.state_manager, minimum, maximum)
        self._on_fix: StateStack[Constraint] = StateStack(solver.state_manager)
        self._on_domain_change: StateStack[Constraint] = StateStack(
            solver.state_manager
        )
        self._on_bound_change: StateStack[Constraint] = StateStack(
            solver.state_manager
        )

    @property
    def min(self) -> int:
        return self._domain.min

    @property
    def max(self) -> int:
        return self._domain.max

    @property
    def size(self) -> int:
        return self._domain.size

    @property
    def is_fixed(self) -> bool:
        return self.size == 1

    @property
    def value(self) -> int:
        if not self.is_fixed:
            raise ValueError("variable is not fixed")
        return self.min

    def values(self) -> list[int]:
        return self._domain.values()

    def contains(self, value: int) -> bool:
        return self._domain.contains(value)

    def remove(self, value: int) -> None:
        """Remove a value and notify constraints interested in the change."""

        if not self.contains(value):
            return

        old_size = self.size
        old_min = self.min
        old_max = self.max
        self._domain.remove(value)

        if self.size == 0:
            raise Inconsistency(f"removing {value} emptied {self}")

        self._notify_change(old_size, old_min, old_max)

    def fix(self, value: int) -> None:
        """Remove every domain value except ``value``."""

        if not self.contains(value):
            raise Inconsistency(f"cannot fix {self} to absent value {value}")
        if self.is_fixed:
            return

        old_size = self.size
        old_min = self.min
        old_max = self.max
        for candidate in self.values():
            if candidate != value:
                self._domain.remove(candidate)

        self._notify_change(old_size, old_min, old_max)

    def remove_below(self, value: int) -> None:
        """Remove every domain value strictly smaller than ``value``."""

        old_size = self.size
        old_min = self.min
        old_max = self.max
        if not self._domain.remove_below(value):
            return

        if self.size == 0:
            raise Inconsistency(f"removing values below {value} emptied {self.name or 'IntVar'}")

        self._notify_change(old_size, old_min, old_max)

    def remove_above(self, value: int) -> None:
        """Remove every domain value strictly larger than ``value``."""

        old_size = self.size
        old_min = self.min
        old_max = self.max
        if not self._domain.remove_above(value):
            return

        if self.size == 0:
            raise Inconsistency(f"removing values above {value} emptied {self.name or 'IntVar'}")

        self._notify_change(old_size, old_min, old_max)

    def propagate_on_fix(self, constraint: Constraint) -> None:
        self._on_fix.append(constraint)

    def propagate_on_domain_change(self, constraint: Constraint) -> None:
        self._on_domain_change.append(constraint)

    def propagate_on_bound_change(self, constraint: Constraint) -> None:
        self._on_bound_change.append(constraint)

    def _notify_change(self, old_size: int, old_min: int, old_max: int) -> None:
        self._schedule_all(self._on_domain_change)

        if self.min != old_min or self.max != old_max:
            self._schedule_all(self._on_bound_change)

        if old_size > 1 and self.is_fixed:
            self._schedule_all(self._on_fix)

    def _schedule_all(self, constraints: StateStack[Constraint]) -> None:
        for constraint in constraints:
            self.solver.schedule(constraint)

    def __repr__(self) -> str:
        label = self.name or "IntVar"
        if self.is_fixed:
            return f"{label}={self.value}"
        return f"{label}={{{', '.join(map(str, sorted(self.values())))}}}"
