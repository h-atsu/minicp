# %%
"""N-Queens modeled with three Rust AllDifferent constraints."""

from minicp import rust as cp

# %%
N = 12

solver = cp.Solver()
queens = [cp.IntVar(solver, 0, N - 1, name=f"q[{column}]") for column in range(N)]

# Different columns are represented by separate variables. These constraints
# require distinct rows and distinct values on both diagonal coordinates.
solver.post(cp.all_different(queens))
solver.post(
    cp.all_different([cp.plus(queen, column) for column, queen in enumerate(queens)])
)
solver.post(
    cp.all_different([cp.plus(queen, -column) for column, queen in enumerate(queens)])
)

# %%
# Unlike the callback-based Python reference search, the Rust search receives
# its variables up front and stores each solution as an immutable snapshot.
search = cp.DFSearch(solver, queens)
statistics = search.solve()
solutions = [tuple(solution) for solution in search.solutions]


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
# for i, solution in enumerate(solutions):
#     print(f"Solution {i + 1}:")
#     display_solution(solution)

# %%
