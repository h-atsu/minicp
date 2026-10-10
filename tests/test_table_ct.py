import pytest

from minicp import Inconsistency, IntVar, Solver, TableCT, plus


def test_compact_table_removes_values_without_a_supporting_tuple() -> None:
    solver = Solver()
    x = IntVar(solver, 1, 3)
    y = IntVar(solver, 1, 3)

    solver.post(TableCT([x, y], [(1, 1), (1, 2), (2, 2)]))

    assert sorted(x.values()) == [1, 2]
    assert sorted(y.values()) == [1, 2]


def test_compact_table_propagates_after_a_domain_change() -> None:
    solver = Solver()
    x = IntVar(solver, 1, 2)
    y = IntVar(solver, 1, 2)
    solver.post(TableCT([x, y], [(1, 1), (1, 2), (2, 2)]))

    x.remove(1)
    solver.fix_point()

    assert x.value == 2
    assert y.value == 2


def test_compact_table_combines_changes_from_every_column() -> None:
    solver = Solver()
    x = IntVar(solver, 0, 2)
    y = IntVar(solver, 0, 2)
    z = IntVar(solver, 0, 2)
    solver.post(
        TableCT(
            [x, y, z],
            [(0, 0, 0), (0, 1, 1), (1, 1, 0), (2, 2, 2)],
        )
    )

    x.remove(2)
    z.fix(1)
    solver.fix_point()

    assert x.value == 0
    assert y.value == 1


def test_compact_table_rejects_an_empty_table() -> None:
    solver = Solver()
    variable = IntVar(solver, 0, 1)

    with pytest.raises(Inconsistency, match="no supported tuple"):
        solver.post(TableCT([variable], []))


def test_compact_table_ignores_tuples_outside_initial_domains() -> None:
    solver = Solver()
    x = IntVar(solver, 1, 2)
    y = IntVar(solver, 1, 2)

    solver.post(TableCT([x, y], [(0, 0), (1, 2), (3, 1)]))

    assert x.value == 1
    assert y.value == 2


def test_compact_table_accepts_variable_views() -> None:
    solver = Solver()
    x = IntVar(solver, 0, 2)
    y = IntVar(solver, 1, 3)

    solver.post(TableCT([plus(x, 1), y], [(1, 1), (3, 2)]))

    assert sorted(x.values()) == [0, 2]
    assert sorted(y.values()) == [1, 2]


def test_compact_table_is_restored_between_branches() -> None:
    solver = Solver()
    x = IntVar(solver, 0, 1)
    y = IntVar(solver, 0, 1)
    solver.post(TableCT([x, y], [(0, 0), (1, 1)]))

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


def test_compact_table_works_across_multiple_words() -> None:
    solver = Solver()
    x = IntVar(solver, 0, 129)
    y = IntVar(solver, 0, 1)
    tuples = [(value, value % 2) for value in range(130)]
    solver.post(TableCT([x, y], tuples))

    y.fix(1)
    solver.fix_point()

    assert x.values()
    assert all(value % 2 == 1 for value in x.values())
    assert 129 in x.values()


def test_compact_table_rejects_an_empty_scope() -> None:
    with pytest.raises(ValueError, match="at least one"):
        TableCT([], [()])


def test_compact_table_rejects_a_tuple_with_the_wrong_arity() -> None:
    solver = Solver()

    with pytest.raises(ValueError, match="rows must match"):
        TableCT([IntVar(solver, 0, 1)], [(0, 1)])


def test_compact_table_rejects_variables_from_different_solvers() -> None:
    first_solver = Solver()
    second_solver = Solver()

    with pytest.raises(ValueError, match="different solvers"):
        TableCT(
            [
                IntVar(first_solver, 0, 1),
                IntVar(second_solver, 0, 1),
            ],
            [(0, 0)],
        )
