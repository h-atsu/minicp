# %%
"""A 9x9 Sudoku modeled with 27 all-different constraints."""

from minicp.constraints import all_different
from minicp.search import DFSearch, first_unfixed
from minicp.solver import Solver
from minicp.variable import IntVar

# %%
# Zero denotes an empty cell.
PUZZLE = (
    (5, 3, 0, 0, 7, 0, 0, 0, 0),
    (6, 0, 0, 1, 9, 5, 0, 0, 0),
    (0, 9, 8, 0, 0, 0, 0, 6, 0),
    (8, 0, 0, 0, 6, 0, 0, 0, 3),
    (4, 0, 0, 8, 0, 3, 0, 0, 1),
    (7, 0, 0, 0, 2, 0, 0, 0, 6),
    (0, 6, 0, 0, 0, 0, 2, 8, 0),
    (0, 0, 0, 4, 1, 9, 0, 0, 5),
    (0, 0, 0, 0, 8, 0, 0, 7, 9),
)
N = 9

# %%
solver = Solver()
cells = [
    [IntVar(solver, 1, N, name=f"cell[{row},{column}]") for column in range(N)]
    for row in range(N)
]

for row in range(N):
    for column in range(N):
        if PUZZLE[row][column]:
            cells[row][column].fix(PUZZLE[row][column])

for row in range(N):
    solver.post(all_different(cells[row]))

for column in range(N):
    solver.post(all_different([cells[row][column] for row in range(N)]))

for block_row in range(0, N, 3):
    for block_column in range(0, N, 3):
        solver.post(
            all_different(
                [
                    cells[row][column]
                    for row in range(block_row, block_row + 3)
                    for column in range(block_column, block_column + 3)
                ]
            )
        )

# %%
variables = [cell for row in cells for cell in row]
search = DFSearch(solver, first_unfixed(variables))
solutions: list[tuple[int, ...]] = []


def record_solution() -> None:
    solutions.append(tuple(cell.value for cell in variables))


search.on_solution(record_solution)
statistics = search.solve()

print(f"Found {statistics.solutions} solution")
solution = solutions[0]
for row in range(N):
    values = solution[row * N : (row + 1) * N]
    print(" ".join(map(str, values)))
# %%
