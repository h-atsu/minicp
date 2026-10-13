# %%
"""Traveling salesperson with Circuit and branch-and-bound."""

from minicp.constraints import circuit, element, sum_var
from minicp.search import Branch, DFSearch
from minicp.solver import Solver
from minicp.variable import IntVar

# %%
# A small symmetric instance arranged roughly as a hexagon.
DISTANCE = (
    (0, 20, 36, 45, 40, 22),
    (20, 0, 22, 40, 45, 36),
    (36, 22, 0, 22, 36, 40),
    (45, 40, 22, 0, 20, 36),
    (40, 45, 36, 20, 0, 22),
    (22, 36, 40, 36, 22, 0),
)
N = len(DISTANCE)

# %%
solver = Solver()
successors = [
    IntVar(solver, 0, N - 1, name=f"successor[{node}]")
    for node in range(N)
]
solver.post(circuit(successors))

edge_distances = [
    element(DISTANCE[node], successors[node]) for node in range(N)
]
total_distance = sum_var(edge_distances)
objective = solver.minimize(total_distance)

# %%
# Deliberately try the farthest remaining successor first so that the notebook
# exposes several incumbent improvements during branch-and-bound.
def farthest_first_branching() -> list[Branch]:
    node = next(
        (
            candidate
            for candidate, successor in enumerate(successors)
            if not successor.is_fixed
        ),
        None,
    )
    if node is None:
        return []

    successor = successors[node]
    destination = max(
        successor.values(), key=lambda value: DISTANCE[node][value]
    )

    def use_edge() -> None:
        successor.fix(destination)

    def exclude_edge() -> None:
        successor.remove(destination)

    return [use_edge, exclude_edge]


search = DFSearch(solver, farthest_first_branching)
improving_solutions: list[tuple[int, tuple[int, ...]]] = []


def record_solution() -> None:
    improving_solutions.append(
        (
            total_distance.value,
            tuple(successor.value for successor in successors),
        )
    )


search.on_solution(record_solution)
statistics = search.optimize(objective)

# %%
def tour_from_successors(solution: tuple[int, ...]) -> tuple[int, ...]:
    tour = [0]
    for _ in range(1, len(solution)):
        tour.append(solution[tour[-1]])
    return tuple(tour)


print("Improving solutions:")
for distance, solution in improving_solutions:
    print(f"  distance={distance}, tour={tour_from_successors(solution)}")

best_distance, best_successors = improving_solutions[-1]
print(f"Best distance: {best_distance}")
print(f"Best tour: {tour_from_successors(best_successors)}")
print(
    f"Search: {statistics.nodes} nodes, "
    f"{statistics.failures} failures, "
    f"{statistics.solutions} improving solutions"
)
assert objective.best_value == best_distance
# %%
