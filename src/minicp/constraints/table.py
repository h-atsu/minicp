"""Table constraint using a direct support search."""

from __future__ import annotations

from collections.abc import Sequence

from minicp.constraints.base import Constraint
from minicp.variable import IntVarLike


class TableDecomp(Constraint):
    """Require the variables to match one of the allowed tuples."""

    def __init__(
        self,
        variables: Sequence[IntVarLike],
        tuples: Sequence[Sequence[int]],
    ) -> None:
        if not variables:
            raise ValueError("table requires at least one variable")

        solver = variables[0].solver
        if any(variable.solver is not solver for variable in variables):
            raise ValueError("variables belong to different solvers")
        if any(len(row) != len(variables) for row in tuples):
            raise ValueError("table rows must match the number of variables")

        super().__init__(solver)
        self.variables = tuple(variables)
        self.tuples = tuple(tuple(row) for row in tuples)

    def post(self) -> None:
        for variable in self.variables:
            variable.propagate_on_domain_change(self)
        self.propagate()

    def propagate(self) -> None:
        for column, variable in enumerate(self.variables):
            for value in variable.values():
                if not self._has_support(column, value):
                    variable.remove(value)

        if all(variable.is_fixed for variable in self.variables):
            self.deactivate()

    def _has_support(self, column: int, value: int) -> bool:
        return any(
            row[column] == value
            and all(
                variable.contains(row[index])
                for index, variable in enumerate(self.variables)
            )
            for row in self.tuples
        )
