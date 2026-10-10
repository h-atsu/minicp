from __future__ import annotations

from collections.abc import Callable

import pytest

from minicp import Constraint, Inconsistency, IntVar, Solver, not_equal


class PropagationCounter(Constraint):
    def __init__(self, solver: Solver) -> None:
        super().__init__(solver)
        self.count = 0

    def post(self) -> None:
        pass

    def propagate(self) -> None:
        self.count += 1


def test_not_equal_propagates_when_variable_is_fixed() -> None:
    solver = Solver()
    x = IntVar(solver, 0, 3, name="x")
    y = IntVar(solver, 0, 3, name="y")
    solver.post(not_equal(x, y, offset=1))

    x.fix(2)
    solver.fix_point()

    assert not y.contains(1)
    assert set(y.values()) == {0, 2, 3}


def test_not_equal_detects_inconsistency() -> None:
    solver = Solver()
    x = IntVar(solver, 0, 1)
    y = IntVar(solver, 0, 1)
    solver.post(not_equal(x, y))
    x.fix(0)
    y.fix(0)

    with pytest.raises(Inconsistency):
        solver.fix_point()


def test_propagation_is_restored_between_branches() -> None:
    solver = Solver()
    x = IntVar(solver, 0, 2)
    y = IntVar(solver, 0, 2)
    solver.post(not_equal(x, y))

    solver.state_manager.save()
    x.fix(1)
    solver.fix_point()
    assert not y.contains(1)
    solver.state_manager.restore()

    assert set(x.values()) == {0, 1, 2}
    assert set(y.values()) == {0, 1, 2}


def test_bound_removals_notify_the_matching_events() -> None:
    solver = Solver()
    x = IntVar(solver, 0, 4)
    on_domain_change = PropagationCounter(solver)
    on_bound_change = PropagationCounter(solver)
    on_fix = PropagationCounter(solver)
    x.propagate_on_domain_change(on_domain_change)
    x.propagate_on_bound_change(on_bound_change)
    x.propagate_on_fix(on_fix)

    x.remove_below(2)
    solver.fix_point()

    assert set(x.values()) == {2, 3, 4}
    assert on_domain_change.count == 1
    assert on_bound_change.count == 1
    assert on_fix.count == 0

    x.remove_above(2)
    solver.fix_point()

    assert x.value == 2
    assert on_domain_change.count == 2
    assert on_bound_change.count == 2
    assert on_fix.count == 1


def test_bound_removal_that_changes_nothing_schedules_nothing() -> None:
    solver = Solver()
    x = IntVar(solver, 0, 4)
    on_domain_change = PropagationCounter(solver)
    x.propagate_on_domain_change(on_domain_change)

    x.remove_below(0)
    x.remove_above(4)
    solver.fix_point()

    assert on_domain_change.count == 0


@pytest.mark.parametrize(
    ("operation", "value"),
    [
        (IntVar.remove_below, 5),
        (IntVar.remove_above, -1),
    ],
)
def test_bound_removal_detects_inconsistency(
    operation: Callable[[IntVar, int], None],
    value: int,
) -> None:
    solver = Solver()
    x = IntVar(solver, 0, 4)

    with pytest.raises(Inconsistency):
        operation(x, value)


def test_bound_removals_are_restored_between_branches() -> None:
    solver = Solver()
    x = IntVar(solver, 0, 5)

    solver.state_manager.save()
    x.remove_below(2)
    x.remove_above(3)
    assert set(x.values()) == {2, 3}
    solver.state_manager.restore()

    assert set(x.values()) == {0, 1, 2, 3, 4, 5}
