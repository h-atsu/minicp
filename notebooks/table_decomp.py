# %%
from minicp.constraints import TableDecomp, equal
from minicp.search import DFSearch, first_unfixed
from minicp.solver import Solver
from minicp.variable import IntVar

# %%

solver = Solver()
x = IntVar(solver, 0, 10, name="x")
y = IntVar(solver, 1, 10, name="y")
z = IntVar(solver, 0, 10, name="z")

solver.post(
    TableDecomp(
        [x, y, z],
        [
            (1, 1, 1),
            (1, 2, 2),
            (2, 2, 3),
        ],
    )
)

solver.post(equal(z, 3))
# %%

search = DFSearch(solver, first_unfixed([x, y, z]))
solutions: list[tuple[int, int, int]] = []


def record_solution() -> None:
    solutions.append((x.value, y.value, z.value))


search.on_solution(record_solution)
statistics = search.solve()

# %%

print(f"Found {statistics.solutions} solutions")
print(f"First 10 solutions: {solutions[:10]}")
# %%
