# %%
from minicp.constraints import Element1D
from minicp.search import DFSearch, first_unfixed
from minicp.solver import Solver
from minicp.variable import IntVar

# %%

solver = Solver()
x = IntVar(solver, 0, 10, name="x")
y = IntVar(solver, 1, 10, name="y")


solver.post(Element1D([1, 2, 3], x, y))

# %%

search = DFSearch(solver, first_unfixed([x, y]))
solutions: list[tuple[int, int]] = []


def record_solution() -> None:
    solutions.append((x.value, y.value))


search.on_solution(record_solution)
statistics = search.solve()

# %%

print(f"Found {statistics.solutions} solutions")
print(f"First 10 solutions: {solutions[:10]}")
# %%
