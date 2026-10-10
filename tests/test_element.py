import pytest

from minicp import Element1D, Inconsistency, IntVar, Solver, element, plus


def test_element_removes_out_of_range_indices() -> None:
    solver = Solver()
    index = IntVar(solver, -2, 5)
    result = IntVar(solver, 0, 10)

    solver.post(Element1D([4, 6, 8], index, result))

    assert sorted(index.values()) == [0, 1, 2]
    assert sorted(result.values()) == [4, 6, 8]


def test_element_filters_indices_and_result_values() -> None:
    solver = Solver()
    index = IntVar(solver, 0, 3)
    result = IntVar(solver, 5, 9)
    result.remove(8)

    solver.post(Element1D([5, 8, 5, 9], index, result))

    assert sorted(index.values()) == [0, 2, 3]
    assert sorted(result.values()) == [5, 9]


def test_element_preserves_duplicate_supporting_indices() -> None:
    solver = Solver()
    index = IntVar(solver, 0, 3)
    result = IntVar(solver, 5, 5)

    solver.post(Element1D([5, 8, 5, 9], index, result))

    assert sorted(index.values()) == [0, 2]


def test_element_propagates_later_changes_in_both_directions() -> None:
    solver = Solver()
    index = IntVar(solver, 0, 2)
    result = IntVar(solver, 3, 5)
    solver.post(Element1D([3, 4, 5], index, result))

    index.remove(1)
    solver.fix_point()
    assert not result.contains(4)

    result.remove(5)
    solver.fix_point()
    assert index.value == 0
    assert result.value == 3


def test_element_fixed_index_fixes_result() -> None:
    solver = Solver()
    index = IntVar(solver, 1, 1)
    result = IntVar(solver, 0, 10)

    solver.post(Element1D([4, 6, 8], index, result))

    assert result.value == 6


def test_element_detects_when_no_index_supports_the_result() -> None:
    solver = Solver()
    index = IntVar(solver, 0, 2)
    result = IntVar(solver, 9, 9)

    with pytest.raises(Inconsistency):
        solver.post(Element1D([3, 4, 5], index, result))


def test_element_helper_creates_and_posts_result_variable() -> None:
    solver = Solver()
    index = IntVar(solver, 0, 2)

    result = element([2, 7, 4], index)

    assert sorted(result.values()) == [2, 4, 7]
    result.fix(4)
    solver.fix_point()
    assert index.value == 2


def test_element_accepts_a_result_view() -> None:
    solver = Solver()
    index = IntVar(solver, 0, 2)
    result = IntVar(solver, 1, 4)

    solver.post(Element1D([2, 3, 5], index, plus(result, 1)))

    assert sorted(result.values()) == [1, 2, 4]


def test_element_is_restored_between_branches() -> None:
    solver = Solver()
    index = IntVar(solver, 0, 2)
    result = IntVar(solver, 3, 5)
    solver.post(Element1D([3, 4, 5], index, result))

    solver.state_manager.save()
    index.fix(0)
    solver.fix_point()
    assert result.value == 3
    solver.state_manager.restore()

    solver.state_manager.save()
    result.fix(5)
    solver.fix_point()
    assert index.value == 2
    solver.state_manager.restore()


def test_element_rejects_an_empty_array() -> None:
    solver = Solver()

    with pytest.raises(ValueError, match="at least one"):
        Element1D([], IntVar(solver, 0, 1), IntVar(solver, 0, 1))


def test_element_rejects_variables_from_different_solvers() -> None:
    first_solver = Solver()
    second_solver = Solver()

    with pytest.raises(ValueError, match="different solvers"):
        Element1D(
            [1, 2],
            IntVar(first_solver, 0, 1),
            IntVar(second_solver, 1, 2),
        )
