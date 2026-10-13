"""Branch-and-bound objectives."""

from __future__ import annotations

from typing import Protocol

from minicp.variable import IntVarLike


class Objective(Protocol):
    """An objective tightened whenever search finds a solution."""

    @property
    def best_value(self) -> int | None: ...

    def tighten(self) -> None: ...


class Minimize:
    """Minimize an integer variable with a persistent upper bound."""

    def __init__(self, variable: IntVarLike) -> None:
        self.variable = variable
        self._best_value: int | None = None
        variable.solver.on_fix_point(self._enforce_bound)

    @property
    def best_value(self) -> int | None:
        return self._best_value

    def tighten(self) -> None:
        if not self.variable.is_fixed:
            raise RuntimeError("objective variable is not fixed")
        self._best_value = self.variable.value

    def _enforce_bound(self) -> None:
        if self._best_value is not None:
            self.variable.remove_above(self._best_value - 1)


class Maximize:
    """Maximize an integer variable with a persistent lower bound."""

    def __init__(self, variable: IntVarLike) -> None:
        self.variable = variable
        self._best_value: int | None = None
        variable.solver.on_fix_point(self._enforce_bound)

    @property
    def best_value(self) -> int | None:
        return self._best_value

    def tighten(self) -> None:
        if not self.variable.is_fixed:
            raise RuntimeError("objective variable is not fixed")
        self._best_value = self.variable.value

    def _enforce_bound(self) -> None:
        if self._best_value is not None:
            self.variable.remove_below(self._best_value + 1)
