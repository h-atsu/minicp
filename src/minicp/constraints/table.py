"""Table constraint using a direct support search."""

from __future__ import annotations

from collections.abc import Sequence

from minicp.constraints.base import Constraint
from minicp.exceptions import Inconsistency
from minicp.sparse_bit_set import StateSparseBitSet, SupportBitSet
from minicp.state import StateInt
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


class TableCT(Constraint):
    """Require an allowed tuple using the Compact Table algorithm.

    Tuple indices are represented by bits. ``_supported_tuples`` contains the
    rows still compatible with every current domain, while
    ``_supports[column][value]`` contains the rows assigning that value to the
    variable in that column.
    """

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

        self._supported_tuples = StateSparseBitSet(
            solver.state_manager, len(self.tuples)
        )
        supports: list[dict[int, SupportBitSet]] = [
            {} for _ in self.variables
        ]
        for tuple_index, row in enumerate(self.tuples):
            for column, value in enumerate(row):
                support = supports[column].get(value)
                if support is None:
                    support = self._supported_tuples.support_bit_set()
                    supports[column][value] = support
                support.set(tuple_index)

        self._supports = tuple(supports)
        self._mask = self._supported_tuples.mask_bit_set()
        self._last_domain_sizes = tuple(
            StateInt(solver.state_manager, -1) for _ in self.variables
        )

    def post(self) -> None:
        for variable in self.variables:
            variable.propagate_on_domain_change(self)
        self.propagate()

    def propagate(self) -> None:
        self._remove_incompatible_tuples()
        if self._supported_tuples.is_empty:
            raise Inconsistency("table has no supported tuple")

        self._remove_unsupported_values()
        if all(variable.is_fixed for variable in self.variables):
            self.deactivate()

    def _remove_incompatible_tuples(self) -> None:
        for column, variable in enumerate(self.variables):
            if variable.size == self._last_domain_sizes[column].value:
                continue

            self._mask.clear()
            for value in variable.values():
                support = self._supports[column].get(value)
                if support is not None:
                    self._mask.union_with(support)
            self._supported_tuples.intersect_with(self._mask)

    def _remove_unsupported_values(self) -> None:
        for column, variable in enumerate(self.variables):
            for value in variable.values():
                support = self._supports[column].get(value)
                if support is None or not self._supported_tuples.intersects(
                    support
                ):
                    variable.remove(value)
            self._last_domain_sizes[column].set(variable.size)
