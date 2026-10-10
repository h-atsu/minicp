"""Integer decision variables."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Protocol

from minicp.exceptions import Inconsistency
from minicp.sparse_set import SparseSet
from minicp.state import StateStack

if TYPE_CHECKING:
    from minicp.constraint import Constraint
    from minicp.solver import Solver


class IntVarLike(Protocol):
    """Operations shared by domain variables and variable views."""

    solver: Solver

    @property
    def min(self) -> int: ...

    @property
    def max(self) -> int: ...

    @property
    def size(self) -> int: ...

    @property
    def is_fixed(self) -> bool: ...

    @property
    def value(self) -> int: ...

    def values(self) -> list[int]: ...

    def contains(self, value: int) -> bool: ...

    def remove(self, value: int) -> None: ...

    def fix(self, value: int) -> None: ...

    def remove_below(self, value: int) -> None: ...

    def remove_above(self, value: int) -> None: ...

    def propagate_on_fix(self, constraint: Constraint) -> None: ...

    def propagate_on_domain_change(self, constraint: Constraint) -> None: ...

    def propagate_on_bound_change(self, constraint: Constraint) -> None: ...


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


class _IntVarView(ABC):
    """Common behavior for views that delegate to another integer variable."""

    def __init__(self, variable: IntVarLike) -> None:
        self._variable = variable
        self.solver = variable.solver

    @property
    @abstractmethod
    def min(self) -> int: ...

    @abstractmethod
    def values(self) -> list[int]: ...

    @property
    def size(self) -> int:
        return self._variable.size

    @property
    def is_fixed(self) -> bool:
        return self.size == 1

    @property
    def value(self) -> int:
        if not self.is_fixed:
            raise ValueError("variable is not fixed")
        return self.min

    def propagate_on_fix(self, constraint: Constraint) -> None:
        self._variable.propagate_on_fix(constraint)

    def propagate_on_domain_change(self, constraint: Constraint) -> None:
        self._variable.propagate_on_domain_change(constraint)

    def propagate_on_bound_change(self, constraint: Constraint) -> None:
        self._variable.propagate_on_bound_change(constraint)

    def __repr__(self) -> str:
        label = type(self).__name__
        if self.is_fixed:
            return f"{label}={self.value}"
        return f"{label}={{{', '.join(map(str, sorted(self.values())))}}}"


class OffsetView(_IntVarView):
    """A view exposing the values of ``variable + offset``.

    The view has no domain of its own. Every query and update is translated
    to the wrapped variable, whose reversible domain remains the single source
    of truth.
    """

    def __init__(self, variable: IntVarLike, offset: int) -> None:
        super().__init__(variable)
        self.offset = offset

    @property
    def min(self) -> int:
        return self._variable.min + self.offset

    @property
    def max(self) -> int:
        return self._variable.max + self.offset

    def values(self) -> list[int]:
        return [value + self.offset for value in self._variable.values()]

    def contains(self, value: int) -> bool:
        return self._variable.contains(value - self.offset)

    def remove(self, value: int) -> None:
        self._variable.remove(value - self.offset)

    def fix(self, value: int) -> None:
        self._variable.fix(value - self.offset)

    def remove_below(self, value: int) -> None:
        self._variable.remove_below(value - self.offset)

    def remove_above(self, value: int) -> None:
        self._variable.remove_above(value - self.offset)


class OppositeView(_IntVarView):
    """A view exposing the values of ``-variable``."""

    def __init__(self, variable: IntVarLike) -> None:
        super().__init__(variable)

    @property
    def min(self) -> int:
        return -self._variable.max

    @property
    def max(self) -> int:
        return -self._variable.min

    def values(self) -> list[int]:
        return [-value for value in self._variable.values()]

    def contains(self, value: int) -> bool:
        return self._variable.contains(-value)

    def remove(self, value: int) -> None:
        self._variable.remove(-value)

    def fix(self, value: int) -> None:
        self._variable.fix(-value)

    def remove_below(self, value: int) -> None:
        self._variable.remove_above(-value)

    def remove_above(self, value: int) -> None:
        self._variable.remove_below(-value)


class ScaleView(_IntVarView):
    """A view exposing the values of ``coefficient * variable``.

    A strictly positive coefficient keeps the mapping one-to-one and ordered.
    Negative and zero coefficients are handled by :func:`mul` using an
    opposite view or a fixed variable respectively.
    """

    def __init__(self, variable: IntVarLike, coefficient: int) -> None:
        if coefficient <= 0:
            raise ValueError("coefficient must be strictly positive")
        super().__init__(variable)
        self.coefficient = coefficient

    @property
    def min(self) -> int:
        return self.coefficient * self._variable.min

    @property
    def max(self) -> int:
        return self.coefficient * self._variable.max

    def values(self) -> list[int]:
        return [
            self.coefficient * value
            for value in self._variable.values()
        ]

    def contains(self, value: int) -> bool:
        return (
            value % self.coefficient == 0
            and self._variable.contains(value // self.coefficient)
        )

    def remove(self, value: int) -> None:
        if value % self.coefficient == 0:
            self._variable.remove(value // self.coefficient)

    def fix(self, value: int) -> None:
        if value % self.coefficient != 0:
            raise Inconsistency(f"cannot fix {self} to absent value {value}")
        self._variable.fix(value // self.coefficient)

    def remove_below(self, value: int) -> None:
        minimum = -(-value // self.coefficient)
        self._variable.remove_below(minimum)

    def remove_above(self, value: int) -> None:
        maximum = value // self.coefficient
        self._variable.remove_above(maximum)


def plus(variable: IntVarLike, offset: int) -> IntVarLike:
    """Return a view of ``variable + offset``."""

    return variable if offset == 0 else OffsetView(variable, offset)


def minus(
    variable: IntVarLike,
    offset: int | None = None,
) -> IntVarLike:
    """Return a view of ``-variable`` or ``variable - offset``."""

    if offset is None:
        return OppositeView(variable)
    return plus(variable, -offset)


def mul(variable: IntVarLike, coefficient: int) -> IntVarLike:
    """Return a view of ``coefficient * variable``."""

    if coefficient == 0:
        return IntVar(variable.solver, 0, 0)
    if coefficient == 1:
        return variable
    if coefficient < 0:
        return OppositeView(ScaleView(variable, -coefficient))
    return ScaleView(variable, coefficient)
