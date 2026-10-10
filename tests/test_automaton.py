import pytest

from minicp import Automaton, Inconsistency, IntVar, Solver, plus

EVEN_PARITY_TRANSITIONS = [
    (0, 0, 0),
    (0, 1, 1),
    (1, 0, 1),
    (1, 1, 0),
]


def test_automaton_removes_values_without_an_accepting_path() -> None:
    solver = Solver()
    symbols = [IntVar(solver, 0, 1) for _ in range(3)]
    solver.post(Automaton(symbols, 0, [0], EVEN_PARITY_TRANSITIONS))

    symbols[0].fix(1)
    symbols[1].fix(0)
    solver.fix_point()

    assert symbols[2].value == 1


def test_automaton_removes_labels_absent_from_the_transition_relation() -> None:
    solver = Solver()
    symbol = IntVar(solver, 0, 2)

    solver.post(Automaton([symbol], 0, [1], [(0, 1, 1)]))

    assert symbol.value == 1


def test_automaton_detects_when_no_accepting_path_exists() -> None:
    solver = Solver()
    symbol = IntVar(solver, 0, 1)

    with pytest.raises(Inconsistency, match="no accepting path"):
        solver.post(Automaton([symbol], 0, [2], EVEN_PARITY_TRANSITIONS))


def test_automaton_accepts_multiple_final_states() -> None:
    solver = Solver()
    symbol = IntVar(solver, 0, 1)

    solver.post(Automaton([symbol], 0, [0, 1], EVEN_PARITY_TRANSITIONS))

    assert sorted(symbol.values()) == [0, 1]


def test_automaton_accepts_nondeterministic_transitions() -> None:
    solver = Solver()
    first = IntVar(solver, 0, 0)
    second = IntVar(solver, 0, 1)
    transitions = [(0, 0, 0), (0, 0, 1), (0, 1, 2), (1, 1, 3)]

    solver.post(Automaton([first, second], 0, [3], transitions))

    assert second.value == 1


def test_automaton_accepts_variable_views() -> None:
    solver = Solver()
    symbol = IntVar(solver, 0, 1)

    solver.post(Automaton([plus(symbol, 1)], 0, [1], [(0, 2, 1)]))

    assert symbol.value == 1


def test_automaton_is_restored_between_branches() -> None:
    solver = Solver()
    first = IntVar(solver, 0, 1)
    second = IntVar(solver, 0, 1)
    solver.post(
        Automaton([first, second], 0, [0], EVEN_PARITY_TRANSITIONS)
    )

    solver.state_manager.save()
    first.fix(0)
    solver.fix_point()
    assert second.value == 0
    solver.state_manager.restore()

    solver.state_manager.save()
    first.fix(1)
    solver.fix_point()
    assert second.value == 1
    solver.state_manager.restore()


def test_automaton_rejects_an_empty_symbol_sequence() -> None:
    with pytest.raises(ValueError, match="at least one symbol"):
        Automaton([], 0, [0], [])


def test_automaton_rejects_variables_from_different_solvers() -> None:
    first_solver = Solver()
    second_solver = Solver()

    with pytest.raises(ValueError, match="different solvers"):
        Automaton(
            [IntVar(first_solver, 0, 1), IntVar(second_solver, 0, 1)],
            0,
            [0],
            EVEN_PARITY_TRANSITIONS,
        )
