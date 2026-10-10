# %%
from minicp.constraints import not_equal
from minicp.search import DFSearch, first_unfixed
from minicp.solver import Solver
from minicp.variable import IntVar, plus

# %%

solver = Solver()
x = IntVar(solver, 1, 10, name="x")
y = IntVar(solver, 1, 10, name="y")


solver.post(not_equal(plus(x, 3), y))

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
