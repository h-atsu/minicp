from minicp import rust


def test_rust_generic_constraints_solve_tsp() -> None:
    distances = [
        [0, 2, 9, 10],
        [1, 0, 6, 4],
        [15, 7, 0, 8],
        [6, 3, 12, 0],
    ]
    solver = rust.Solver()
    successors = [rust.IntVar(solver, 0, 3) for _ in range(4)]
    solver.post(rust.circuit(successors))
    edge_distances = [
        rust.element(distances[node], successors[node]) for node in range(4)
    ]
    total_distance = rust.sum_var(edge_distances)
    objective = solver.minimize(total_distance)
    search = rust.DFSearch(solver, successors)

    statistics = search.optimize(objective)

    assert statistics.completed
    assert objective.best_value == 21
    assert search.solutions[-1] == [2, 0, 3, 1]
