import pytest

from minicp import Inconsistency, IntVar, Solver, TableDecomp, plus


def test_table_removes_values_without_a_supporting_tuple() -> None:
    solver = Solver()
    x = IntVar(solver, 1, 3)
    y = IntVar(solver, 1, 3)

    solver.post(TableDecomp([x, y], [(1, 1), (1, 2), (2, 2)]))

    assert sorted(x.values()) == [1, 2]
    assert sorted(y.values()) == [1, 2]


def test_table_propagates_after_a_domain_change() -> None:
    solver = Solver()
    x = IntVar(solver, 1, 2)
    y = IntVar(solver, 1, 2)
    solver.post(TableDecomp([x, y], [(1, 1), (1, 2), (2, 2)]))

    x.remove(1)
    solver.fix_point()

    assert x.value == 2
    assert y.value == 2


def test_table_checks_support_across_every_column() -> None:
    solver = Solver()
    x = IntVar(solver, 0, 1)
    y = IntVar(solver, 0, 1)
    z = IntVar(solver, 0, 1)
    solver.post(
        TableDecomp(
            [x, y, z],
            [(0, 0, 0), (0, 1, 1), (1, 1, 0)],
        )
    )

    z.fix(1)
    solver.fix_point()

    assert x.value == 0
    assert y.value == 1


def test_table_detects_an_empty_table() -> None:
    solver = Solver()
    variable = IntVar(solver, 0, 1)

    with pytest.raises(Inconsistency):
        solver.post(TableDecomp([variable], []))


def test_table_accepts_variable_views() -> None:
    solver = Solver()
    x = IntVar(solver, 0, 2)
    y = IntVar(solver, 1, 3)

    solver.post(TableDecomp([plus(x, 1), y], [(1, 1), (3, 2)]))

    assert sorted(x.values()) == [0, 2]
    assert sorted(y.values()) == [1, 2]


def test_table_is_restored_between_branches() -> None:
    solver = Solver()
    x = IntVar(solver, 0, 1)
    y = IntVar(solver, 0, 1)
    solver.post(TableDecomp([x, y], [(0, 0), (1, 1)]))

    solver.state_manager.save()
    x.fix(0)
    solver.fix_point()
    assert y.value == 0
    solver.state_manager.restore()

    solver.state_manager.save()
    x.fix(1)
    solver.fix_point()
    assert y.value == 1
    solver.state_manager.restore()


def test_table_rejects_an_empty_scope() -> None:
    with pytest.raises(ValueError, match="at least one"):
        TableDecomp([], [()])


def test_table_rejects_a_tuple_with_the_wrong_arity() -> None:
    solver = Solver()

    with pytest.raises(ValueError, match="rows must match"):
        TableDecomp([IntVar(solver, 0, 1)], [(0, 1)])


def test_table_rejects_variables_from_different_solvers() -> None:
    first_solver = Solver()
    second_solver = Solver()

    with pytest.raises(ValueError, match="different solvers"):
        TableDecomp(
            [
                IntVar(first_solver, 0, 1),
                IntVar(second_solver, 0, 1),
            ],
            [(0, 0)],
        )
