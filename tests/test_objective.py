from collections.abc import Sequence

import pytest

from minicp import DFSearch, IntVar, Solver
from minicp.search import Branch, Branching, first_unfixed


def choose_largest(variable: IntVar) -> Branching:
    def branching() -> Sequence[Branch]:
        if variable.is_fixed:
            return []
        value = variable.max
        return [
            lambda: variable.fix(value),
            lambda: variable.remove(value),
        ]

    return branching


def test_minimize_reports_each_improving_solution() -> None:
    solver = Solver()
    variable = IntVar(solver, 0, 5)
    objective = solver.minimize(variable)
    search = DFSearch(solver, choose_largest(variable))
    solutions: list[int] = []
    search.on_solution(lambda: solutions.append(variable.value))

    statistics = search.optimize(objective)

    assert solutions == [5, 4, 3, 2, 1, 0]
    assert statistics.solutions == 6
    assert objective.best_value == 0
    assert set(variable.values()) == set(range(6))


def test_maximize_reports_each_improving_solution() -> None:
    solver = Solver()
    variable = IntVar(solver, 0, 5)
    objective = solver.maximize(variable)
    search = DFSearch(solver, first_unfixed([variable]))
    solutions: list[int] = []
    search.on_solution(lambda: solutions.append(variable.value))

    statistics = search.optimize(objective)

    assert solutions == [0, 1, 2, 3, 4, 5]
    assert statistics.solutions == 6
    assert objective.best_value == 5
    assert set(variable.values()) == set(range(6))


def test_objective_must_be_fixed_at_a_solution() -> None:
    solver = Solver()
    variable = IntVar(solver, 0, 1)
    objective = solver.minimize(variable)
    search = DFSearch(solver, list)

    with pytest.raises(RuntimeError, match="not fixed"):
        search.optimize(objective)


def test_solver_rejects_an_objective_from_another_solver() -> None:
    first_solver = Solver()
    second_solver = Solver()
    variable = IntVar(first_solver, 0, 1)

    with pytest.raises(ValueError, match="different solver"):
        second_solver.minimize(variable)
