import pytest

from minicp import (
    Constraint,
    Inconsistency,
    IntVar,
    IntVarLike,
    OffsetView,
    OppositeView,
    ScaleView,
    Solver,
    minus,
    mul,
    not_equal,
    plus,
)


class PropagationCounter(Constraint):
    def __init__(self, solver: Solver) -> None:
        super().__init__(solver)
        self.count = 0

    def post(self) -> None:
        pass

    def propagate(self) -> None:
        self.count += 1


def test_offset_view_translates_queries_and_updates() -> None:
    solver = Solver()
    x = IntVar(solver, -2, 2)
    y = OffsetView(x, 3)

    assert y.solver is solver
    assert y.min == 1
    assert y.max == 5
    assert set(y.values()) == {1, 2, 3, 4, 5}
    assert y.contains(2)

    y.remove(2)
    y.remove_below(3)
    y.remove_above(4)

    assert set(x.values()) == {0, 1}
    assert set(y.values()) == {3, 4}


def test_view_satisfies_protocol_without_inheriting_domain_variable() -> None:
    solver = Solver()
    x = IntVar(solver, 0, 2)
    view: IntVarLike = OffsetView(x, 1)

    assert not isinstance(view, IntVar)
    assert set(view.values()) == {1, 2, 3}


def test_opposite_view_reverses_bounds_and_updates() -> None:
    solver = Solver()
    x = IntVar(solver, -2, 3)
    y = OppositeView(x)

    assert y.min == -3
    assert y.max == 2

    y.remove_below(-1)
    assert set(y.values()) == {-1, 0, 1, 2}
    assert set(x.values()) == {-2, -1, 0, 1}

    y.remove_above(1)
    assert set(y.values()) == {-1, 0, 1}
    assert set(x.values()) == {-1, 0, 1}


def test_scale_view_has_holes_and_rounds_bound_updates() -> None:
    solver = Solver()
    x = IntVar(solver, -2, 3)
    y = ScaleView(x, 3)

    assert y.min == -6
    assert y.max == 9
    assert set(y.values()) == {-6, -3, 0, 3, 6, 9}
    assert y.contains(6)
    assert not y.contains(5)

    y.remove(5)
    y.remove_below(-4)
    y.remove_above(7)

    assert set(x.values()) == {-1, 0, 1, 2}
    assert set(y.values()) == {-3, 0, 3, 6}


def test_scale_view_rejects_absent_fixed_value() -> None:
    solver = Solver()
    x = IntVar(solver, 0, 3)
    y = ScaleView(x, 2)

    with pytest.raises(Inconsistency):
        y.fix(3)


def test_view_factories_simplify_identity_cases() -> None:
    solver = Solver()
    x = IntVar(solver, 0, 3)

    assert plus(x, 0) is x
    assert minus(x, 0) is x
    assert mul(x, 1) is x

    zero = mul(x, 0)
    assert zero.is_fixed
    assert zero.value == 0


def test_views_can_be_composed() -> None:
    solver = Solver()
    x = IntVar(solver, 0, 9)
    y = minus(mul(x, -2), 1)

    assert y.min == -19
    assert y.max == -1
    assert set(y.values()) == set(range(-19, 0, 2))

    y.remove(-19)
    assert not x.contains(9)
    assert y.min == -17


def test_view_subscriptions_are_forwarded_to_wrapped_variable() -> None:
    solver = Solver()
    x = IntVar(solver, 0, 4)
    y = plus(x, 2)
    on_domain_change = PropagationCounter(solver)
    on_bound_change = PropagationCounter(solver)
    on_fix = PropagationCounter(solver)
    y.propagate_on_domain_change(on_domain_change)
    y.propagate_on_bound_change(on_bound_change)
    y.propagate_on_fix(on_fix)

    x.remove(0)
    solver.fix_point()

    assert on_domain_change.count == 1
    assert on_bound_change.count == 1
    assert on_fix.count == 0

    y.fix(3)
    solver.fix_point()

    assert x.value == 1
    assert on_domain_change.count == 2
    assert on_bound_change.count == 2
    assert on_fix.count == 1


def test_view_can_be_used_by_a_constraint() -> None:
    solver = Solver()
    x = IntVar(solver, 0, 3)
    y = IntVar(solver, 0, 3)
    solver.post(not_equal(x, plus(y, 1)))

    y.fix(1)
    solver.fix_point()

    assert not x.contains(2)


def test_view_updates_are_restored_with_wrapped_variable() -> None:
    solver = Solver()
    x = IntVar(solver, 0, 4)
    y = mul(minus(x), 2)

    solver.state_manager.save()
    y.remove_below(-4)
    assert set(x.values()) == {0, 1, 2}
    solver.state_manager.restore()

    assert set(x.values()) == {0, 1, 2, 3, 4}
    assert set(y.values()) == {0, -2, -4, -6, -8}
