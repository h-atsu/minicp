"""Element constraint over a constant array."""

from __future__ import annotations

from collections.abc import Sequence

from minicp.constraints.base import Constraint
from minicp.variable import IntVar, IntVarLike


class Element1D(Constraint):
    """The domain-consistent constraint ``values[index] == result``."""

    def __init__(
        self,
        values: Sequence[int],
        index: IntVarLike,
        result: IntVarLike,
    ) -> None:
        if not values:
            raise ValueError("element requires at least one value")
        if index.solver is not result.solver:
            raise ValueError("variables belong to different solvers")
        super().__init__(index.solver)
        self.values = tuple(values)
        self.index = index
        self.result = result

    def post(self) -> None:
        self.index.propagate_on_domain_change(self)
        self.result.propagate_on_domain_change(self)
        self.index.remove_below(0)
        self.index.remove_above(len(self.values) - 1)
        self.propagate()

    def propagate(self) -> None:
        if self.index.is_fixed:
            self.result.fix(self.values[self.index.value])
            self.deactivate()
            return

        for position in self.index.values():
            if not self.result.contains(self.values[position]):
                self.index.remove(position)

        if self.index.is_fixed:
            self.result.fix(self.values[self.index.value])
            self.deactivate()
            return

        supported_values = {
            self.values[position] for position in self.index.values()
        }
        for value in self.result.values():
            if value not in supported_values:
                self.result.remove(value)

        if self.result.is_fixed:
            self.deactivate()


def element(values: Sequence[int], index: IntVarLike) -> IntVar:
    """Create a variable representing ``values[index]``."""

    if not values:
        raise ValueError("element requires at least one value")
    result = IntVar(index.solver, min(values), max(values))
    index.solver.post(Element1D(values, index, result))
    return result
