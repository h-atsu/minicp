from minicp import rust


def test_rust_search_enumerates_and_restores_domains() -> None:
    solver = rust.Solver()
    variable = rust.IntVar(solver, 0, 3)
    search = rust.DFSearch(solver, [variable])

    statistics = search.solve()

    assert statistics.solutions == 4
    assert {tuple(solution) for solution in search.solutions} == {
        (0,),
        (1,),
        (2,),
        (3,),
    }
    assert set(variable.values()) == {0, 1, 2, 3}


def test_rust_search_minimizes_with_persistent_bound() -> None:
    solver = rust.Solver()
    variable = rust.IntVar(solver, 0, 5)
    objective = solver.minimize(variable)
    search = rust.DFSearch(solver, [variable], value_order=[[5, 4, 3, 2, 1, 0]])

    statistics = search.optimize(objective)

    assert [solution[0] for solution in search.solutions] == [5, 4, 3, 2, 1, 0]
    assert statistics.solutions == 6
    assert objective.best_value == 0


def test_rust_search_honors_time_limit() -> None:
    solver = rust.Solver()
    variable = rust.IntVar(solver, 0, 100)
    search = rust.DFSearch(solver, [variable])

    statistics = search.solve(time_limit=0)

    assert not statistics.completed
    assert statistics.solutions == 0
