import pytest

from minicp import Inconsistency, IntVar, Solver, Sum, mul, sum_var


def test_sum_propagates_fixed_term_to_other_term() -> None:
    solver = Solver()
    x = IntVar(solver, 0, 5)
    y = IntVar(solver, 0, 5)
    solver.post(Sum([x, y], 5))

    x.fix(2)
    solver.fix_point()

    assert y.is_fixed
    assert y.value == 3


def test_sum_filters_bounds() -> None:
    solver = Solver()
    x = IntVar(solver, -100, 10)
    y = IntVar(solver, 4, 6)
    z = IntVar(solver, 20, 60)

    solver.post(Sum([x, y, z]))

    assert x.min == -66
    assert x.max == -24
    assert y.min == 4
    assert y.max == 6
    assert z.min == 20
    assert z.max == 60


def test_sum_can_use_a_result_variable() -> None:
    solver = Solver()
    x = IntVar(solver, 1, 3)
    y = IntVar(solver, 2, 4)
    result = IntVar(solver, 0, 10)
    solver.post(Sum([x, y], result))

    assert result.min == 3
    assert result.max == 7

    result.fix(4)
    x.fix(1)
    solver.fix_point()

    assert y.value == 3


def test_sum_accepts_variable_views_as_terms() -> None:
    solver = Solver()
    x = IntVar(solver, 0, 5)
    y = IntVar(solver, 0, 10)
    solver.post(Sum([mul(x, 2), y], 10))

    x.fix(3)
    solver.fix_point()

    assert y.value == 4


def test_sum_var_creates_and_posts_result_variable() -> None:
    solver = Solver()
    x = IntVar(solver, -2, 3)
    y = IntVar(solver, 4, 5)

    result = sum_var([x, y])

    assert result.min == 2
    assert result.max == 8

    result.fix(3)
    solver.fix_point()

    assert x.min == -2
    assert x.max == -1


def test_sum_detects_inconsistency() -> None:
    solver = Solver()
    x = IntVar(solver, 1, 2)
    y = IntVar(solver, 3, 4)

    with pytest.raises(Inconsistency):
        solver.post(Sum([x, y], 10))


def test_sum_state_is_restored_between_branches() -> None:
    solver = Solver()
    x = IntVar(solver, 0, 5)
    y = IntVar(solver, 0, 5)
    solver.post(Sum([x, y], 5))

    solver.state_manager.save()
    x.fix(2)
    solver.fix_point()
    assert y.value == 3
    solver.state_manager.restore()

    assert set(x.values()) == {0, 1, 2, 3, 4, 5}
    assert set(y.values()) == {0, 1, 2, 3, 4, 5}

    solver.state_manager.save()
    x.fix(4)
    solver.fix_point()
    assert y.value == 1
    solver.state_manager.restore()


def test_sum_fixed_partition_is_reusable_after_restore() -> None:
    solver = Solver()
    x = IntVar(solver, 0, 6)
    y = IntVar(solver, 0, 6)
    z = IntVar(solver, 0, 6)
    solver.post(Sum([x, y, z], 6))

    solver.state_manager.save()
    z.fix(2)
    solver.fix_point()
    assert x.max == 4
    assert y.max == 4
    solver.state_manager.restore()

    solver.state_manager.save()
    x.fix(1)
    solver.fix_point()
    assert y.max == 5
    assert z.max == 5
    solver.state_manager.restore()


def test_sum_rejects_empty_scope() -> None:
    with pytest.raises(ValueError, match="at least one"):
        Sum([])


def test_sum_rejects_variables_from_different_solvers() -> None:
    first_solver = Solver()
    second_solver = Solver()
    x = IntVar(first_solver, 0, 1)
    y = IntVar(second_solver, 0, 1)

    with pytest.raises(ValueError, match="different solvers"):
        Sum([x, y])
