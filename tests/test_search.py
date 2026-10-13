import pytest

from minicp import DFSearch, IntVar, Solver, first_unfixed, not_equal


def build_n_queens(n: int) -> tuple[Solver, list[IntVar]]:
    solver = Solver()
    queens = [IntVar(solver, 0, n - 1) for _ in range(n)]

    for i in range(n):
        for j in range(i + 1, n):
            distance = j - i
            solver.post(not_equal(queens[i], queens[j]))
            solver.post(not_equal(queens[i], queens[j], distance))
            solver.post(not_equal(queens[i], queens[j], -distance))

    return solver, queens


def solve_n_queens(n: int) -> tuple[list[tuple[int, ...]], int]:
    solver, queens = build_n_queens(n)
    search = DFSearch(solver, first_unfixed(queens))
    solutions: list[tuple[int, ...]] = []
    search.on_solution(
        lambda: solutions.append(tuple(queen.value for queen in queens))
    )
    statistics = search.solve()
    return solutions, statistics.solutions


def test_four_queens_solutions() -> None:
    solutions, solution_count = solve_n_queens(4)

    assert set(solutions) == {(1, 3, 0, 2), (2, 0, 3, 1)}
    assert solution_count == 2


def test_eight_queens_solution_count() -> None:
    solutions, solution_count = solve_n_queens(8)

    assert len(solutions) == 92
    assert solution_count == 92


def test_search_restores_root_domains() -> None:
    solver, queens = build_n_queens(4)
    search = DFSearch(solver, first_unfixed(queens))

    search.solve()

    assert all(set(queen.values()) == {0, 1, 2, 3} for queen in queens)


def test_search_can_stop_at_a_time_limit() -> None:
    solver = Solver()
    variable = IntVar(solver, 0, 100)
    search = DFSearch(solver, first_unfixed([variable]))

    statistics = search.solve(time_limit=0)

    assert not statistics.completed
    assert statistics.solutions == 0
    assert statistics.elapsed_seconds >= 0
    assert set(variable.values()) == set(range(101))


def test_search_rejects_a_negative_time_limit() -> None:
    solver = Solver()
    search = DFSearch(solver, list)

    with pytest.raises(ValueError, match="non-negative"):
        search.solve(time_limit=-1)
