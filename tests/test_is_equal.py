import pytest

from minicp import BoolVar, IntVar, IsEqual, Solver, is_equal


def test_bool_var_has_a_binary_domain() -> None:
    solver = Solver()
    boolean = BoolVar(solver)

    assert boolean.values() == [0, 1]
    assert not boolean.is_true
    assert not boolean.is_false

    boolean.fix(True)

    assert boolean.is_true
    assert not boolean.is_false


@pytest.mark.parametrize(
    ("truth", "expected_values"),
    [(True, [2]), (False, [1, 3])],
)
def test_boolean_value_propagates_to_integer_variable(
    truth: bool,
    expected_values: list[int],
) -> None:
    solver = Solver()
    boolean = BoolVar(solver)
    variable = IntVar(solver, 1, 3)
    solver.post(IsEqual(boolean, variable, 2))

    boolean.fix(truth)
    solver.fix_point()

    assert sorted(variable.values()) == expected_values


def test_removing_reified_value_makes_boolean_false() -> None:
    solver = Solver()
    boolean = BoolVar(solver)
    variable = IntVar(solver, 1, 3)
    solver.post(IsEqual(boolean, variable, 2))

    variable.remove(2)
    solver.fix_point()

    assert boolean.is_false


def test_fixing_reified_value_makes_boolean_true() -> None:
    solver = Solver()
    boolean = BoolVar(solver)
    variable = IntVar(solver, 1, 3)
    solver.post(IsEqual(boolean, variable, 2))

    variable.fix(2)
    solver.fix_point()

    assert boolean.is_true


def test_is_equal_creates_and_posts_boolean_variable() -> None:
    solver = Solver()
    variable = IntVar(solver, 1, 3)

    boolean = is_equal(variable, 2)
    boolean.fix(False)
    solver.fix_point()

    assert not variable.contains(2)


def test_reified_equality_is_restored_between_branches() -> None:
    solver = Solver()
    boolean = BoolVar(solver)
    variable = IntVar(solver, 1, 3)
    solver.post(IsEqual(boolean, variable, 2))

    solver.state_manager.save()
    boolean.fix(True)
    solver.fix_point()
    assert variable.value == 2
    solver.state_manager.restore()

    solver.state_manager.save()
    boolean.fix(False)
    solver.fix_point()
    assert sorted(variable.values()) == [1, 3]
    solver.state_manager.restore()


def test_is_equal_rejects_variables_from_different_solvers() -> None:
    first_solver = Solver()
    second_solver = Solver()

    with pytest.raises(ValueError, match="different solvers"):
        IsEqual(
            BoolVar(first_solver),
            IntVar(second_solver, 0, 1),
            1,
        )
