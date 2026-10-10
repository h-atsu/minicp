# %%
"""Subset Sum modeled with binary variables and a sum constraint."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from minicp.constraint import Sum
from minicp.search import Branch, DFSearch
from minicp.solver import Solver
from minicp.variable import IntVar, IntVarLike, mul

# %%


def first_unfixed(
    variables: Sequence[IntVarLike],
) -> Callable[[], list[Branch]]:
    """Branch on whether the first undecided item is selected."""

    def branching() -> list[Branch]:
        variable = next(
            (candidate for candidate in variables if not candidate.is_fixed),
            None,
        )
        if variable is None:
            return []

        def select() -> None:
            variable.fix(1)

        def exclude() -> None:
            variable.fix(0)

        return [select, exclude]

    return branching


# %%
VALUES = [3, 5, 6, 7, 9]
TARGET = 12

solver = Solver()
selected = [
    IntVar(solver, 0, 1, name=f"selected[{index}]")
    for index in range(len(VALUES))
]

# mul(selected[i], VALUES[i]) is a view: it exposes either 0 or VALUES[i]
# without creating another independent domain.
weighted_values = [
    mul(is_selected, value)
    for is_selected, value in zip(selected, VALUES, strict=True)
]
solver.post(Sum(weighted_values, TARGET))

# %%
search = DFSearch(solver, first_unfixed(selected))
solutions: list[tuple[int, ...]] = []


def record_solution() -> None:
    subset = tuple(
        value
        for value, is_selected in zip(VALUES, selected, strict=True)
        if is_selected.value == 1
    )
    solutions.append(subset)


search.on_solution(record_solution)
statistics = search.solve()

# %%
print(f"Values: {VALUES}")
print(f"Target: {TARGET}")
print(f"Found {statistics.solutions} solutions")

for index, subset in enumerate(solutions, start=1):
    print(f"Solution {index}: {subset} (sum={sum(subset)})")

print(statistics)

# %%
