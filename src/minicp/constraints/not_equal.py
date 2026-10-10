"""Not-equal constraint."""

from __future__ import annotations

from minicp.constraints.base import Constraint
from minicp.variable import IntVarLike


class NotEqual(Constraint):
    """The constraint ``x != y + offset``."""

    def __init__(
        self,
        x: IntVarLike,
        y: IntVarLike,
        offset: int = 0,
    ) -> None:
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


def not_equal(
    x: IntVarLike,
    y: IntVarLike,
    offset: int = 0,
) -> NotEqual:
    """Create the constraint ``x != y + offset``."""

    return NotEqual(x, y, offset)
