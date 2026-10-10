import pytest

from minicp import Equal, Inconsistency, IntVar, Solver, equal, plus


def test_equal_intersects_both_domains() -> None:
    solver = Solver()
    x = IntVar(solver, 1, 4)
    y = IntVar(solver, 2, 5)
    x.remove(3)
    y.remove(4)

    solver.post(Equal(x, y))

    assert sorted(x.values()) == [2]
    assert sorted(y.values()) == [2]


def test_equal_propagates_later_domain_changes_in_both_directions() -> None:
    solver = Solver()
    x = IntVar(solver, 1, 4)
    y = IntVar(solver, 1, 4)
    solver.post(Equal(x, y))

    x.remove(2)
    solver.fix_point()
    assert not y.contains(2)

    y.remove(3)
    solver.fix_point()
    assert not x.contains(3)


def test_equal_propagates_a_fixed_variable() -> None:
    solver = Solver()
    x = IntVar(solver, 1, 3)
    y = IntVar(solver, 1, 3)
    solver.post(Equal(x, y))

    x.fix(2)
    solver.fix_point()

    assert y.value == 2


def test_equal_helper_accepts_a_constant() -> None:
    solver = Solver()
    variable = IntVar(solver, 1, 3)

    solver.post(equal(variable, 2))

    assert variable.value == 2


def test_equal_helper_accepts_two_variables() -> None:
    solver = Solver()
    x = IntVar(solver, 1, 3)
    y = IntVar(solver, 2, 4)

    solver.post(equal(x, y))

    assert sorted(x.values()) == [2, 3]
    assert sorted(y.values()) == [2, 3]


def test_equal_accepts_variable_views() -> None:
    solver = Solver()
    x = IntVar(solver, 0, 3)
    y = IntVar(solver, 1, 4)

    solver.post(Equal(plus(x, 1), y))
    y.remove(2)
    solver.fix_point()

    assert not x.contains(1)


def test_equal_detects_inconsistent_views_of_same_variable() -> None:
    solver = Solver()
    variable = IntVar(solver, 1, 3)

    with pytest.raises(Inconsistency):
        solver.post(Equal(variable, plus(variable, 1)))


def test_equal_is_restored_between_branches() -> None:
    solver = Solver()
    x = IntVar(solver, 1, 3)
    y = IntVar(solver, 1, 3)
    solver.post(Equal(x, y))

    solver.state_manager.save()
    x.remove(2)
    solver.fix_point()
    assert not y.contains(2)
    solver.state_manager.restore()

    assert x.contains(2)
    assert y.contains(2)


def test_equal_rejects_variables_from_different_solvers() -> None:
    first_solver = Solver()
    second_solver = Solver()

    with pytest.raises(ValueError, match="different solvers"):
        Equal(
            IntVar(first_solver, 0, 1),
            IntVar(second_solver, 0, 1),
        )
