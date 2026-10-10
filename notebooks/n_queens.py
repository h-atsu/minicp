# %%
"""N-Queens modeled with pairwise not-equal constraints."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from minicp.constraint import not_equal
from minicp.search import Branch, DFSearch
from minicp.solver import Solver
from minicp.variable import IntVar

# %%


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


# %%
N = 11

solver = Solver()
queens = [IntVar(solver, 0, N - 1, name=f"q[{column}]") for column in range(N)]

for i in range(N):
    for j in range(i + 1, N):
        distance = j - i
        solver.post(not_equal(queens[i], queens[j]))
        solver.post(not_equal(queens[i], queens[j], distance))
        solver.post(not_equal(queens[i], queens[j], -distance))


# %%

search = DFSearch(solver, first_unfixed(queens))
solutions: list[tuple[int, ...]] = []


def record_solution() -> None:
    solutions.append(tuple(queen.value for queen in queens))


search.on_solution(record_solution)
statistics = search.solve()


# %%
def display_solution(solution: tuple[int, ...]) -> None:
    for row in range(N):
        for column in range(N):
            if solution[column] == row:
                print("Q", end=" ")
            else:
                print(".", end=" ")
        print()
    print()


print(f"Found {statistics.solutions} solutions")
for i, solution in enumerate(solutions):
    print(f"Solution {i + 1}:")
    display_solution(solution)

# %%
