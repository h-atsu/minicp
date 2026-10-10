# %%
from minicp.constraints import TableCT
from minicp.search import DFSearch, first_unfixed
from minicp.solver import Solver
from minicp.variable import IntVar

# %%
# Each row gets one bit in TableCT's StateSparseBitSet.
allowed_tuples = [
    (1, 1, 1),  # tuple bit 0
    (1, 2, 2),  # tuple bit 1
    (2, 2, 3),  # tuple bit 2
    (2, 3, 4),  # tuple bit 3
]

solver = Solver()
x = IntVar(solver, 1, 2, name="x")
y = IntVar(solver, 1, 3, name="y")
z = IntVar(solver, 1, 4, name="z")

solver.post(TableCT([x, y, z], allowed_tuples))
print(f"after post: {x}, {y}, {z}")

# %%
# In this temporary branch x=2 keeps only tuple bits 2 and 3. TableCT then
# removes y=1 and z values 1 and 2 because those values have no remaining bit.
solver.state_manager.save()
x.fix(2)
solver.fix_point()
print(f"inside x=2 branch: {x}, {y}, {z}")
solver.state_manager.restore()
print(f"after restore: {x}, {y}, {z}")

# %%
search = DFSearch(solver, first_unfixed([x, y, z]))
solutions: list[tuple[int, int, int]] = []


def record_solution() -> None:
    solutions.append((x.value, y.value, z.value))


search.on_solution(record_solution)
statistics = search.solve()

# %%
print(f"Found {statistics.solutions} solutions")
print(f"Solutions: {solutions}")
