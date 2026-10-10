from itertools import product

import pytest

from minicp import (
    AllDifferentBinary,
    AllDifferentDC,
    Inconsistency,
    IntVar,
    Solver,
    all_different,
    plus,
)


def test_binary_all_different_removes_a_fixed_value_from_others() -> None:
    solver = Solver()
    variables = [IntVar(solver, 0, 2) for _ in range(3)]
    solver.post(AllDifferentBinary(variables))

    variables[0].fix(1)
    solver.fix_point()

    assert variables[0].value == 1
    assert all(not variable.contains(1) for variable in variables[1:])


def test_domain_consistent_all_different_prunes_a_hall_set() -> None:
    solver = Solver()
    first = IntVar(solver, 1, 2)
    second = IntVar(solver, 1, 2)
    third = IntVar(solver, 1, 3)

    solver.post(AllDifferentDC([first, second, third]))

    assert third.value == 3


def test_all_different_helper_is_domain_consistent() -> None:
    solver = Solver()
    first = IntVar(solver, 1, 2)
    second = IntVar(solver, 1, 2)
    third = IntVar(solver, 1, 3)

    solver.post(all_different([first, second, third]))

    assert third.value == 3


def test_domain_consistent_all_different_detects_no_covering_matching() -> None:
    solver = Solver()
    variables = [IntVar(solver, 1, 2) for _ in range(3)]

    with pytest.raises(Inconsistency, match="no matching"):
        solver.post(AllDifferentDC(variables))


def test_domain_consistent_all_different_keeps_alternating_cycles() -> None:
    solver = Solver()
    first = IntVar(solver, 1, 2)
    second = IntVar(solver, 1, 2)

    solver.post(AllDifferentDC([first, second]))

    assert sorted(first.values()) == [1, 2]
    assert sorted(second.values()) == [1, 2]


def test_domain_consistent_all_different_keeps_paths_from_free_values() -> None:
    solver = Solver()
    first = IntVar(solver, 1, 2)
    second = IntVar(solver, 2, 3)

    solver.post(AllDifferentDC([first, second]))

    assert sorted(first.values()) == [1, 2]
    assert sorted(second.values()) == [2, 3]


def test_domain_consistent_all_different_accepts_variable_views() -> None:
    solver = Solver()
    first = IntVar(solver, 0, 1)
    second = IntVar(solver, 1, 2)

    solver.post(AllDifferentDC([plus(first, 1), second]))
    first.fix(0)
    solver.fix_point()

    assert second.value == 2


def test_domain_consistent_all_different_is_restored_between_branches() -> None:
    solver = Solver()
    first = IntVar(solver, 0, 2)
    second = IntVar(solver, 0, 2)
    solver.post(AllDifferentDC([first, second]))

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


def test_domain_consistent_all_different_rejects_an_empty_scope() -> None:
    with pytest.raises(ValueError, match="at least one"):
        AllDifferentDC([])


def test_domain_consistent_rejects_variables_from_different_solvers() -> None:
    first_solver = Solver()
    second_solver = Solver()

    with pytest.raises(ValueError, match="different solvers"):
        AllDifferentDC(
            [IntVar(first_solver, 0, 1), IntVar(second_solver, 0, 1)]
        )


def test_domain_consistent_filtering_matches_exhaustive_solutions() -> None:
    possible_domains = [
        set(values)
        for mask in range(1, 1 << 3)
        if (values := [value for value in range(3) if mask & (1 << value)])
    ]

    for domains in product(possible_domains, repeat=3):
        solutions = [
            assignment
            for assignment in product(*domains)
            if len(set(assignment)) == len(assignment)
        ]
        solver = Solver()
        variables = [IntVar(solver, 0, 2) for _ in domains]
        for variable, domain in zip(variables, domains, strict=True):
            for value in set(range(3)) - domain:
                variable.remove(value)

        if not solutions:
            with pytest.raises(Inconsistency):
                solver.post(AllDifferentDC(variables))
            continue

        solver.post(AllDifferentDC(variables))
        for index, variable in enumerate(variables):
            supported = {solution[index] for solution in solutions}
            assert set(variable.values()) == supported


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
