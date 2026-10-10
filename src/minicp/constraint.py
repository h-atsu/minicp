"""Base and primitive constraints."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import TYPE_CHECKING

from minicp.exceptions import Inconsistency
from minicp.state import StateInt
from minicp.variable import BoolVar, IntVar, IntVarLike, minus

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


class Equal(Constraint):
    """The domain-consistent equality constraint ``x == y``."""

    def __init__(self, x: IntVarLike, y: IntVarLike) -> None:
        if x.solver is not y.solver:
            raise ValueError("variables belong to different solvers")
        super().__init__(x.solver)
        self.x = x
        self.y = y

    def post(self) -> None:
        if self.x.is_fixed or self.y.is_fixed:
            self.propagate()
        else:
            self.x.propagate_on_domain_change(self)
            self.y.propagate_on_domain_change(self)
            self.propagate()

    def propagate(self) -> None:
        if self.x.is_fixed:
            self.y.fix(self.x.value)
            self.deactivate()
            return
        if self.y.is_fixed:
            self.x.fix(self.y.value)
            self.deactivate()
            return

        common_values = set(self.x.values()) & set(self.y.values())
        for value in self.x.values():
            if value not in common_values:
                self.x.remove(value)
        for value in self.y.values():
            if value not in common_values:
                self.y.remove(value)

        if self.x.is_fixed:
            self.y.fix(self.x.value)
            self.deactivate()
        elif self.y.is_fixed:
            self.x.fix(self.y.value)
            self.deactivate()


class IsEqual(Constraint):
    """The reified constraint ``boolean <=> variable == value``."""

    def __init__(
        self,
        boolean: BoolVar,
        variable: IntVarLike,
        value: int,
    ) -> None:
        if boolean.solver is not variable.solver:
            raise ValueError("variables belong to different solvers")
        super().__init__(boolean.solver)
        self.boolean = boolean
        self.variable = variable
        self.value = value

    def post(self) -> None:
        self.propagate()
        if self.active:
            self.variable.propagate_on_domain_change(self)
            self.boolean.propagate_on_fix(self)

    def propagate(self) -> None:
        if self.boolean.is_true:
            self.variable.fix(self.value)
            self.deactivate()
        elif self.boolean.is_false:
            self.variable.remove(self.value)
            self.deactivate()
        elif not self.variable.contains(self.value):
            self.boolean.fix(False)
            self.deactivate()
        elif self.variable.is_fixed:
            self.boolean.fix(True)
            self.deactivate()


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


def not_equal(
    x: IntVarLike,
    y: IntVarLike,
    offset: int = 0,
) -> NotEqual:
    """Create the constraint ``x != y + offset``."""

    return NotEqual(x, y, offset)


def equal(x: IntVarLike, y: IntVarLike | int) -> Equal:
    """Create the constraint ``x == y`` or ``x == value``."""

    if isinstance(y, int):
        y = IntVar(x.solver, y, y)
    return Equal(x, y)


def is_equal(variable: IntVarLike, value: int) -> BoolVar:
    """Create a boolean variable representing ``variable == value``."""

    boolean = BoolVar(variable.solver)
    variable.solver.post(IsEqual(boolean, variable, value))
    return boolean


def element(values: Sequence[int], index: IntVarLike) -> IntVar:
    """Create a variable representing ``values[index]``."""

    if not values:
        raise ValueError("element requires at least one value")
    result = IntVar(index.solver, min(values), max(values))
    index.solver.post(Element1D(values, index, result))
    return result


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
