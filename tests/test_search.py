from minicp import DFSearch
from minicp.examples.n_queens import (
    build_n_queens,
    first_unfixed,
    solve_n_queens,
)


def test_four_queens_solutions() -> None:
    solutions, statistics = solve_n_queens(4)

    assert set(solutions) == {(1, 3, 0, 2), (2, 0, 3, 1)}
    assert statistics.solutions == 2
    assert statistics.completed


def test_eight_queens_solution_count() -> None:
    solutions, statistics = solve_n_queens(8)

    assert len(solutions) == 92
    assert statistics.solutions == 92


def test_search_restores_root_domains() -> None:
    solver, queens = build_n_queens(4)
    search = DFSearch(solver, first_unfixed(queens))

    search.solve()

    assert all(set(queen.values()) == {0, 1, 2, 3} for queen in queens)
