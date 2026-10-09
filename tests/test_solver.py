import pytest

from minicp import Inconsistency, IntVar, Solver, not_equal


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
