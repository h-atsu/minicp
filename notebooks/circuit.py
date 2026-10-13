# %%
"""Inspect subtour elimination in the successor model."""

from minicp.constraints import circuit
from minicp.search import DFSearch, first_unfixed
from minicp.solver import Solver
from minicp.variable import IntVar

# %%
N = 5
solver = Solver()
successors = [
    IntVar(solver, 0, N - 1, name=f"successor[{node}]")
    for node in range(N)
]
solver.post(circuit(successors))

print("Initial domains:")
for successor in successors:
    print(successor)

# %%
# The path 0 -> 1 -> 2 cannot return to 0 before visiting nodes 3 and 4.
solver.state_manager.save()
successors[0].fix(1)
successors[1].fix(2)
solver.fix_point()
print(f"After fixing 0 -> 1 -> 2: {successors[2]}")
assert not successors[2].contains(0)
solver.state_manager.restore()

# %%
search = DFSearch(solver, first_unfixed(successors))
solutions: list[tuple[int, ...]] = []


def record_solution() -> None:
    solutions.append(tuple(successor.value for successor in successors))


search.on_solution(record_solution)
statistics = search.solve()

print(f"Found {statistics.solutions} Hamiltonian circuits")
print(f"First 5 successor arrays: {solutions[:5]}")
# %%
