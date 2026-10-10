"""Bound-consistent sum constraint."""

from __future__ import annotations

from collections.abc import Sequence

from minicp.constraints.base import Constraint
from minicp.exceptions import Inconsistency
from minicp.state import StateInt
from minicp.variable import IntVar, IntVarLike, minus


class Sum(Constraint):
    """The bound-consistent constraint ``sum(variables) == result``.

    Fixed variables are moved to the front of an index array. Only the
    partition size and their accumulated value need to be reversible; the
    permutation itself may remain in its latest order across backtracking.
    """

    def __init__(
        self,
        variables: Sequence[IntVarLike],
        result: IntVarLike | int = 0,
    ) -> None:
        if not variables:
            raise ValueError("sum requires at least one variable")

        solver = variables[0].solver
        if any(variable.solver is not solver for variable in variables):
            raise ValueError("variables belong to different solvers")

        terms = list(variables)
        if isinstance(result, int):
            if result != 0:
                terms.append(IntVar(solver, -result, -result))
        else:
            if result.solver is not solver:
                raise ValueError("variables belong to different solvers")
            terms.append(minus(result))

        super().__init__(solver)
        self._variables = terms
        self._fixed = list(range(len(terms)))
        self._n_fixed = StateInt(solver.state_manager, 0)
        self._sum_fixed = StateInt(solver.state_manager, 0)
        self._minimums = [0] * len(terms)
        self._maximums = [0] * len(terms)

    def post(self) -> None:
        for variable in self._variables:
            variable.propagate_on_bound_change(self)
        self.propagate()

    def propagate(self) -> None:
        n_fixed = self._n_fixed.value
        sum_min = self._sum_fixed.value
        sum_max = self._sum_fixed.value

        for position in range(n_fixed, len(self._variables)):
            index = self._fixed[position]
            variable = self._variables[index]
            self._minimums[index] = variable.min
            self._maximums[index] = variable.max
            sum_min += variable.min
            sum_max += variable.max

            if variable.is_fixed:
                self._sum_fixed.set(
                    self._sum_fixed.value + variable.value
                )
                self._fixed[position], self._fixed[n_fixed] = (
                    self._fixed[n_fixed],
                    self._fixed[position],
                )
                n_fixed += 1

        self._n_fixed.set(n_fixed)

        if sum_min > 0 or sum_max < 0:
            raise Inconsistency("sum cannot reach its target")

        for position in range(n_fixed, len(self._variables)):
            index = self._fixed[position]
            variable = self._variables[index]
            variable.remove_above(-(sum_min - self._minimums[index]))
            variable.remove_below(-(sum_max - self._maximums[index]))

        if n_fixed == len(self._variables):
            self.deactivate()


def sum_var(variables: Sequence[IntVarLike]) -> IntVar:
    """Create and constrain a variable equal to the sum of ``variables``."""

    if not variables:
        raise ValueError("sum requires at least one variable")

    solver = variables[0].solver
    minimum = sum(variable.min for variable in variables)
    maximum = sum(variable.max for variable in variables)
    result = IntVar(solver, minimum, maximum)
    solver.post(Sum(variables, result))
    return result
