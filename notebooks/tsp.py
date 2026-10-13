# %%
"""Euclidean traveling salesperson with Circuit and branch-and-bound."""

from math import hypot
from random import Random

import plotly.graph_objects as go

from minicp import python as python_backend
from minicp import rust as rust_backend
from minicp.constraints import circuit, element, sum_var
from minicp.search import Branch, DFSearch

# %%
# Generate a reproducible Euclidean instance. Distances are multiplied by 100
# and rounded because MiniCP currently has integer variables only.
N = 15
SEED = 42
DISTANCE_SCALE = 100
TIME_LIMIT_SECONDS = 10.0
# Change only this value to compare the reference CP model and the
# coarse-grained Rust search on exactly the same Euclidean instance.
BACKEND = "rust"
random = Random(SEED)
coordinates = tuple((random.uniform(0, 10), random.uniform(0, 10)) for _ in range(N))


def euclidean_distance(left: int, right: int) -> int:
    left_x, left_y = coordinates[left]
    right_x, right_y = coordinates[right]
    return round(hypot(right_x - left_x, right_y - left_y) * DISTANCE_SCALE)


DISTANCE = tuple(
    tuple(euclidean_distance(left, right) for right in range(N)) for left in range(N)
)

# %%
def solve_with_python() -> tuple[
    list[tuple[int, tuple[int, ...]]],
    python_backend.SearchStatistics,
    int | None,
]:
    """Build and solve the TSP with the readable Python CP backend."""

    solver = python_backend.Solver()
    successors = [
        python_backend.IntVar(solver, 0, N - 1, name=f"successor[{node}]")
        for node in range(N)
    ]
    solver.post(circuit(successors))
    edge_distances = [
        element(DISTANCE[node], successors[node]) for node in range(N)
    ]
    total_distance = sum_var(edge_distances)
    objective = solver.minimize(total_distance)

    # Deliberately try the farthest remaining successor first so that both
    # implementations expose several incumbent improvements.
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
        return [
            lambda: successor.fix(destination),
            lambda: successor.remove(destination),
        ]

    search = DFSearch(solver, farthest_first_branching)
    solutions: list[tuple[int, tuple[int, ...]]] = []
    search.on_solution(
        lambda: solutions.append(
            (
                total_distance.value,
                tuple(successor.value for successor in successors),
            )
        )
    )
    statistics = search.optimize(objective, time_limit=TIME_LIMIT_SECONDS)
    return solutions, statistics, objective.best_value


def solve_with_rust() -> tuple[
    list[tuple[int, tuple[int, ...]]],
    rust_backend.TspStatistics,
    int | None,
]:
    """Solve entirely in Rust, crossing the PyO3 boundary only once."""

    result = rust_backend.solve_tsp(
        [list(row) for row in DISTANCE],
        time_limit=TIME_LIMIT_SECONDS,
    )
    solutions = [
        (distance, tuple(successors))
        for distance, successors in result.improving_solutions
    ]
    best_value = solutions[-1][0] if solutions else None
    return solutions, result.statistics, best_value


# %%
if BACKEND == "python":
    improving_solutions, statistics, objective_best_value = solve_with_python()
elif BACKEND == "rust":
    improving_solutions, statistics, objective_best_value = solve_with_rust()
else:
    raise ValueError("BACKEND must be 'python' or 'rust'")


# %%
def tour_from_successors(solution: tuple[int, ...]) -> tuple[int, ...]:
    tour = [0]
    for _ in range(1, len(solution)):
        tour.append(solution[tour[-1]])
    return tuple(tour)


print("Improving solutions:")
for distance, solution in improving_solutions:
    print(
        f"  distance={distance / DISTANCE_SCALE:.2f}, "
        f"tour={tour_from_successors(solution)}"
    )

if not improving_solutions:
    raise RuntimeError("the time limit expired before finding a tour")

best_distance, best_successors = improving_solutions[-1]
best_tour = tour_from_successors(best_successors)
print(f"Best distance: {best_distance / DISTANCE_SCALE:.2f}")
print(f"Best tour: {best_tour}")
print(
    f"Search ({BACKEND} backend): {statistics.nodes} nodes, "
    f"{statistics.failures} failures, "
    f"{statistics.solutions} improving solutions, "
    f"{statistics.elapsed_seconds:.3f} seconds, "
    f"completed={statistics.completed}"
)
assert objective_best_value == best_distance

# %%
# Close the tour by repeating its first node, then draw the optimal cycle.
closed_tour = (*best_tour, best_tour[0])
tour_x = [coordinates[node][0] for node in closed_tour]
tour_y = [coordinates[node][1] for node in closed_tour]

figure = go.Figure()
figure.add_trace(
    go.Scatter(
        x=tour_x,
        y=tour_y,
        mode="lines",
        line={"color": "#2563eb", "width": 2},
        hoverinfo="skip",
        name="optimal tour",
    )
)
figure.add_trace(
    go.Scatter(
        x=[point[0] for point in coordinates],
        y=[point[1] for point in coordinates],
        mode="markers+text",
        marker={"color": "#f97316", "size": 12},
        text=[str(node) for node in range(N)],
        textposition="top center",
        customdata=list(range(N)),
        hovertemplate="node %{customdata}<br>x=%{x:.2f}<br>y=%{y:.2f}<extra></extra>",
        name="nodes",
    )
)
figure.update_layout(
    title=(
        f"Best Euclidean TSP tour found with {BACKEND} backend "
        f"(distance={best_distance / DISTANCE_SCALE:.2f})"
    ),
    xaxis_title="x",
    yaxis_title="y",
    yaxis={"scaleanchor": "x", "scaleratio": 1},
    template="plotly_white",
    showlegend=False,
)


figure.show()
# %%
