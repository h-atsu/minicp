import math
from itertools import permutations

import pytest

from minicp import Circuit, Inconsistency, IntVar, Solver, circuit
from minicp.search import DFSearch, first_unfixed


def is_hamiltonian(successors: tuple[int, ...]) -> bool:
    visited: set[int] = set()
    node = 0
    for _ in successors:
        visited.add(node)
        node = successors[node]
    return node == 0 and len(visited) == len(successors)


def test_circuit_removes_invalid_successor_values() -> None:
    solver = Solver()
    successors = [IntVar(solver, -1, 4) for _ in range(4)]

    solver.post(circuit(successors))

    for node, successor in enumerate(successors):
        assert sorted(successor.values()) == [
            candidate for candidate in range(4) if candidate != node
        ]


def test_circuit_prevents_a_short_subtour() -> None:
    solver = Solver()
    successors = [IntVar(solver, 0, 4) for _ in range(5)]
    solver.post(Circuit(successors))

    successors[0].fix(1)
    solver.fix_point()
    successors[1].fix(2)
    solver.fix_point()

    assert not successors[2].contains(0)


def test_circuit_accepts_a_hamiltonian_cycle() -> None:
    solver = Solver()
    values = [2, 0, 3, 1]
    successors = [IntVar(solver, value, value) for value in values]

    solver.post(Circuit(successors))

    assert [successor.value for successor in successors] == values


def test_circuit_rejects_multiple_subtours() -> None:
    solver = Solver()
    values = [1, 0, 3, 2]
    successors = [IntVar(solver, value, value) for value in values]

    with pytest.raises(Inconsistency):
        solver.post(Circuit(successors))


def test_circuit_accepts_exactly_the_hamiltonian_permutations() -> None:
    for values in permutations(range(4)):
        solver = Solver()
        successors = [IntVar(solver, value, value) for value in values]

        if is_hamiltonian(values):
            solver.post(Circuit(successors))
        else:
            with pytest.raises(Inconsistency):
                solver.post(Circuit(successors))


def test_circuit_enumerates_every_cycle_from_a_fixed_start() -> None:
    solver = Solver()
    successors = [IntVar(solver, 0, 3) for _ in range(4)]
    solver.post(Circuit(successors))
    search = DFSearch(solver, first_unfixed(successors))
    solutions: list[tuple[int, ...]] = []

    search.on_solution(
        lambda: solutions.append(
            tuple(successor.value for successor in successors)
        )
    )

    statistics = search.solve()

    assert statistics.solutions == math.factorial(len(successors) - 1)
    assert all(is_hamiltonian(solution) for solution in solutions)


def test_circuit_state_is_restored_between_branches() -> None:
    solver = Solver()
    successors = [IntVar(solver, 0, 4) for _ in range(5)]
    solver.post(Circuit(successors))

    solver.state_manager.save()
    successors[0].fix(1)
    solver.fix_point()
    assert not successors[1].contains(0)
    solver.state_manager.restore()

    solver.state_manager.save()
    successors[0].fix(2)
    solver.fix_point()
    assert not successors[2].contains(0)
    assert successors[1].contains(0)
    solver.state_manager.restore()


def test_circuit_rejects_too_few_successors() -> None:
    with pytest.raises(ValueError, match="at least two"):
        Circuit([])


def test_circuit_rejects_variables_from_different_solvers() -> None:
    first_solver = Solver()
    second_solver = Solver()

    with pytest.raises(ValueError, match="different solvers"):
        Circuit(
            [IntVar(first_solver, 0, 1), IntVar(second_solver, 0, 1)]
        )
