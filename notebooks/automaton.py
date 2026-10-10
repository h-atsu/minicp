# %%
from minicp.constraints import Automaton
from minicp.search import DFSearch, first_unfixed
from minicp.solver import Solver
from minicp.variable import IntVar

# %%
# A two-state automaton accepting binary sequences with an even number of 1s.
# State 0 means "even so far" and state 1 means "odd so far".
# Each row is (current_state, input_symbol, next_state).
transitions = [
    (0, 0, 0),
    (0, 1, 1),
    (1, 0, 1),
    (1, 1, 0),
]

solver = Solver()
symbols = [IntVar(solver, 0, 1, name=f"symbol[{i}]") for i in range(4)]
solver.post(
    Automaton(
        symbols,
        initial_state=0,
        accepting_states=[0],
        transitions=transitions,
    )
)

# %%
# The prefix 100 has odd parity, so the final symbol must be 1 to finish in
# the accepting even state.
solver.state_manager.save()
symbols[0].fix(1)
symbols[1].fix(0)
symbols[2].fix(0)
solver.fix_point()
print(f"after prefix 100: {symbols}")
solver.state_manager.restore()

# %%
search = DFSearch(solver, first_unfixed(symbols))
solutions: list[tuple[int, ...]] = []


def record_solution() -> None:
    solutions.append(tuple(symbol.value for symbol in symbols))


search.on_solution(record_solution)
statistics = search.solve()

# %%
print(f"Found {statistics.solutions} accepted sequences")
print(f"Accepted sequences: {solutions}")
# %%
