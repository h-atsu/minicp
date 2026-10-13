# %%
"""Stable matching modeled with all-different and table constraints."""

from itertools import product

from minicp.constraints import TableCT, all_different
from minicp.search import DFSearch, first_unfixed
from minicp.solver import Solver
from minicp.variable import IntVar

# %%
# Entries are ordered from most to least preferred.
men_preferences = (
    (0, 1, 2, 3),
    (1, 0, 3, 2),
    (1, 2, 0, 3),
    (0, 2, 3, 1),
)
women_preferences = (
    (1, 0, 2, 3),
    (0, 2, 1, 3),
    (2, 3, 0, 1),
    (0, 1, 2, 3),
)
N = len(men_preferences)


def ranks(preferences: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    return tuple(
        tuple(preference.index(person) for person in range(N))
        for preference in preferences
    )


man_rank = ranks(men_preferences)
woman_rank = ranks(women_preferences)

# %%
solver = Solver()
partner_for_man = [
    IntVar(solver, 0, N - 1, name=f"partner_for_man[{man}]")
    for man in range(N)
]
partner_for_woman = [
    IntVar(solver, 0, N - 1, name=f"partner_for_woman[{woman}]")
    for woman in range(N)
]

solver.post(all_different(partner_for_man))
solver.post(all_different(partner_for_woman))

# %%
# For each possible pair (man, woman), one table enforces both:
#   1. the two partner arrays are inverses;
#   2. the pair cannot prefer each other over both current partners.
for man, woman in product(range(N), repeat=2):
    allowed_pairs = [
        (assigned_woman, assigned_man)
        for assigned_woman, assigned_man in product(range(N), repeat=2)
        if (assigned_woman == woman) == (assigned_man == man)
        and (
            man_rank[man][assigned_woman] <= man_rank[man][woman]
            or woman_rank[woman][assigned_man] <= woman_rank[woman][man]
        )
    ]
    solver.post(
        TableCT(
            [partner_for_man[man], partner_for_woman[woman]],
            allowed_pairs,
        )
    )

# %%
variables = [*partner_for_man, *partner_for_woman]
search = DFSearch(solver, first_unfixed(variables))
solutions: list[tuple[int, ...]] = []


def record_solution() -> None:
    solutions.append(tuple(variable.value for variable in variables))


search.on_solution(record_solution)
statistics = search.solve()

print(f"Found {statistics.solutions} stable matchings")
for solution in solutions:
    print(f"partners for men: {solution[:N]}")
# %%
