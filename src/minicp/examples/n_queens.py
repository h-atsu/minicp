"""N-Queens modeled with pairwise not-equal constraints."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from minicp.constraint import not_equal
from minicp.search import Branch, DFSearch, SearchStatistics
from minicp.solver import Solver
from minicp.variable import IntVar


def build_n_queens(n: int) -> tuple[Solver, list[IntVar]]:
    """Build an N-Queens model without starting the search."""

    if n < 1:
        raise ValueError("n must be at least 1")

    solver = Solver()
    queens = [
        IntVar(solver, 0, n - 1, name=f"q[{column}]")
        for column in range(n)
    ]

    for i in range(n):
        for j in range(i + 1, n):
            distance = j - i
            solver.post(not_equal(queens[i], queens[j]))
            solver.post(not_equal(queens[i], queens[j], distance))
            solver.post(not_equal(queens[i], queens[j], -distance))

    return solver, queens


def first_unfixed(variables: Sequence[IntVar]) -> Callable[[], list[Branch]]:
    """Branch on the minimum value of the first non-fixed variable."""

    def branching() -> list[Branch]:
        variable = next(
            (candidate for candidate in variables if not candidate.is_fixed),
            None,
        )
        if variable is None:
            return []

        value = variable.min

        def assign() -> None:
            variable.fix(value)

        def exclude() -> None:
            variable.remove(value)

        return [assign, exclude]

    return branching


def solve_n_queens(
    n: int,
) -> tuple[list[tuple[int, ...]], SearchStatistics]:
    """Return every N-Queens solution and the DFS statistics."""

    solver, queens = build_n_queens(n)
    search = DFSearch(solver, first_unfixed(queens))
    solutions: list[tuple[int, ...]] = []

    def record_solution() -> None:
        solutions.append(tuple(queen.value for queen in queens))

    search.on_solution(record_solution)
    statistics = search.solve()
    return solutions, statistics
