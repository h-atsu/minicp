"""Equality and reified equality constraints."""

from __future__ import annotations

from minicp.constraints.base import Constraint
from minicp.variable import BoolVar, IntVar, IntVarLike


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
