"""All-different constraints."""

from __future__ import annotations

from collections.abc import Sequence

from minicp.constraints.base import Constraint
from minicp.constraints.not_equal import NotEqual
from minicp.variable import IntVarLike


class AllDifferentBinary(Constraint):
    """Require pairwise different values using binary inequalities."""

    def __init__(self, variables: Sequence[IntVarLike]) -> None:
        if not variables:
            raise ValueError("all-different requires at least one variable")

        solver = variables[0].solver
        if any(variable.solver is not solver for variable in variables):
            raise ValueError("variables belong to different solvers")

        super().__init__(solver)
        self.variables = tuple(variables)

    def post(self) -> None:
        for left_index, left in enumerate(self.variables):
            for right in self.variables[left_index + 1 :]:
                self.solver.post(NotEqual(left, right))
        self.deactivate()

    def propagate(self) -> None:
        # The binary NotEqual constraints perform all propagation.
        pass


def all_different(variables: Sequence[IntVarLike]) -> AllDifferentBinary:
    """Create the binary decomposition of an all-different constraint."""

    return AllDifferentBinary(variables)
