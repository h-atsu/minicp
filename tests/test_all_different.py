import pytest

from minicp import (
    AllDifferentBinary,
    Inconsistency,
    IntVar,
    Solver,
    all_different,
    plus,
)


def test_binary_all_different_removes_a_fixed_value_from_others() -> None:
    solver = Solver()
    variables = [IntVar(solver, 0, 2) for _ in range(3)]
    solver.post(all_different(variables))

    variables[0].fix(1)
    solver.fix_point()

    assert variables[0].value == 1
    assert all(not variable.contains(1) for variable in variables[1:])


def test_binary_all_different_detects_duplicate_fixed_values() -> None:
    solver = Solver()
    first = IntVar(solver, 0, 1)
    second = IntVar(solver, 0, 1)
    solver.post(AllDifferentBinary([first, second]))

    first.fix(0)
    second.fix(0)

    with pytest.raises(Inconsistency):
        solver.fix_point()


def test_binary_all_different_does_not_detect_a_hall_set() -> None:
    solver = Solver()
    first = IntVar(solver, 1, 2)
    second = IntVar(solver, 1, 2)
    third = IntVar(solver, 1, 3)

    solver.post(AllDifferentBinary([first, second, third]))

    assert sorted(third.values()) == [1, 2, 3]


def test_binary_all_different_accepts_variable_views() -> None:
    solver = Solver()
    first = IntVar(solver, 0, 1)
    second = IntVar(solver, 1, 2)
    solver.post(AllDifferentBinary([plus(first, 1), second]))

    first.fix(0)
    solver.fix_point()

    assert second.value == 2


def test_binary_all_different_is_restored_between_branches() -> None:
    solver = Solver()
    first = IntVar(solver, 0, 2)
    second = IntVar(solver, 0, 2)
    solver.post(AllDifferentBinary([first, second]))

    solver.state_manager.save()
    first.fix(0)
    solver.fix_point()
    assert not second.contains(0)
    solver.state_manager.restore()

    solver.state_manager.save()
    first.fix(1)
    solver.fix_point()
    assert not second.contains(1)
    solver.state_manager.restore()


def test_binary_all_different_rejects_an_empty_scope() -> None:
    with pytest.raises(ValueError, match="at least one"):
        AllDifferentBinary([])


def test_binary_all_different_rejects_variables_from_different_solvers() -> None:
    first_solver = Solver()
    second_solver = Solver()

    with pytest.raises(ValueError, match="different solvers"):
        AllDifferentBinary(
            [IntVar(first_solver, 0, 1), IntVar(second_solver, 0, 1)]
        )
