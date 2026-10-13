from collections.abc import Callable
from typing import Protocol

import pytest

from minicp import python as python_backend
from minicp import rust as rust_backend


class VariableLike(Protocol):
    @property
    def value(self) -> int: ...

    def values(self) -> list[int]: ...
    def contains(self, value: int) -> bool: ...
    def fix(self, value: int) -> None: ...
    def remove(self, value: int) -> None: ...


class StateManagerLike(Protocol):
    def save(self) -> None: ...
    def restore(self) -> None: ...


class SolverLike(Protocol):
    @property
    def state_manager(self) -> StateManagerLike: ...

    def fix_point(self) -> None: ...


ConstraintFixture = tuple[SolverLike, VariableLike, VariableLike]
ConstraintFactory = Callable[[], ConstraintFixture]
CircuitFixture = tuple[SolverLike, VariableLike, VariableLike, VariableLike]
CircuitFactory = Callable[[], CircuitFixture]


def python_not_equal() -> ConstraintFixture:
    solver = python_backend.Solver()
    x = python_backend.IntVar(solver, 1, 3)
    y = python_backend.IntVar(solver, 1, 3)
    solver.post(python_backend.not_equal(x, y))
    return solver, x, y


def rust_not_equal() -> ConstraintFixture:
    solver = rust_backend.Solver()
    x = rust_backend.IntVar(solver, 1, 3)
    y = rust_backend.IntVar(solver, 1, 3)
    solver.post(rust_backend.not_equal(x, y))
    return solver, x, y


def python_equal() -> ConstraintFixture:
    solver = python_backend.Solver()
    x = python_backend.IntVar(solver, 1, 3)
    y = python_backend.IntVar(solver, 2, 4)
    solver.post(python_backend.equal(x, y))
    return solver, x, y


def rust_equal() -> ConstraintFixture:
    solver = rust_backend.Solver()
    x = rust_backend.IntVar(solver, 1, 3)
    y = rust_backend.IntVar(solver, 2, 4)
    solver.post(rust_backend.equal(x, y))
    return solver, x, y


@pytest.mark.parametrize("factory", [python_not_equal, rust_not_equal])
def test_backend_not_equal_propagates_and_restores(
    factory: ConstraintFactory,
) -> None:
    solver, x, y = factory()
    manager = solver.state_manager

    manager.save()
    x.fix(2)
    solver.fix_point()
    assert not y.contains(2)
    manager.restore()

    manager.save()
    y.fix(3)
    solver.fix_point()
    assert not x.contains(3)
    manager.restore()


@pytest.mark.parametrize("factory", [python_equal, rust_equal])
def test_backend_equal_intersects_domains(factory: ConstraintFactory) -> None:
    _, x, y = factory()

    assert set(x.values()) == {2, 3}
    assert set(y.values()) == {2, 3}


def test_rust_constraint_rejects_variables_from_different_solvers() -> None:
    first = rust_backend.IntVar(rust_backend.Solver(), 0, 1)
    second = rust_backend.IntVar(rust_backend.Solver(), 0, 1)

    with pytest.raises(ValueError, match="different solvers"):
        rust_backend.not_equal(first, second)


def python_all_different() -> ConstraintFixture:
    solver = python_backend.Solver()
    variables = [
        python_backend.IntVar(solver, 1, 2),
        python_backend.IntVar(solver, 1, 2),
        python_backend.IntVar(solver, 1, 3),
    ]
    solver.post(python_backend.all_different(variables))
    return solver, variables[0], variables[2]


def rust_all_different() -> ConstraintFixture:
    solver = rust_backend.Solver()
    variables = [
        rust_backend.IntVar(solver, 1, 2),
        rust_backend.IntVar(solver, 1, 2),
        rust_backend.IntVar(solver, 1, 3),
    ]
    solver.post(rust_backend.all_different(variables))
    return solver, variables[0], variables[2]


@pytest.mark.parametrize(
    "factory", [python_all_different, rust_all_different]
)
def test_backend_all_different_prunes_hall_set(
    factory: ConstraintFactory,
) -> None:
    _, _, variable = factory()
    assert variable.value == 3


@pytest.mark.parametrize("backend_name", ["python", "rust"])
def test_backend_all_different_accepts_offset_views(
    backend_name: str,
) -> None:
    if backend_name == "python":
        solver = python_backend.Solver()
        first = python_backend.IntVar(solver, 0, 1)
        second = python_backend.IntVar(solver, 1, 2)
        third = python_backend.IntVar(solver, 1, 3)
        constraint = python_backend.all_different(
            [python_backend.plus(first, 1), second, third]
        )
        solver.post(constraint)
    else:
        solver = rust_backend.Solver()
        first = rust_backend.IntVar(solver, 0, 1)
        second = rust_backend.IntVar(solver, 1, 2)
        third = rust_backend.IntVar(solver, 1, 3)
        constraint = rust_backend.all_different(
            [rust_backend.plus(first, 1), second, third]
        )
        solver.post(constraint)

    assert third.value == 3
    solver.state_manager.save()
    first.fix(0)
    solver.fix_point()
    assert second.value == 2
    solver.state_manager.restore()
    assert set(first.values()) == {0, 1}
    assert set(second.values()) == {1, 2}


def test_rust_offset_view_maps_domain_operations() -> None:
    solver = rust_backend.Solver()
    variable = rust_backend.IntVar(solver, 1, 3)
    view = rust_backend.plus(variable, 5)

    assert view.min == 6
    assert view.max == 8
    assert view.values() == [6, 7, 8]
    view.remove(7)
    assert variable.values() == [1, 3]
    view.fix(8)
    assert variable.value == 3


def python_circuit() -> CircuitFixture:
    solver = python_backend.Solver()
    successors = [python_backend.IntVar(solver, 0, 4) for _ in range(5)]
    solver.post(python_backend.circuit(successors))
    return solver, successors[0], successors[1], successors[2]


def rust_circuit() -> CircuitFixture:
    solver = rust_backend.Solver()
    successors = [rust_backend.IntVar(solver, 0, 4) for _ in range(5)]
    solver.post(rust_backend.circuit(successors))
    return solver, successors[0], successors[1], successors[2]


@pytest.mark.parametrize("factory", [python_circuit, rust_circuit])
def test_backend_circuit_prevents_short_subtour(
    factory: CircuitFactory,
) -> None:
    solver, first, second, third = factory()

    solver.state_manager.save()
    first.fix(1)
    solver.fix_point()
    second.fix(2)
    solver.fix_point()
    assert not third.contains(0)
    solver.state_manager.restore()

    assert third.contains(0)


@pytest.mark.parametrize("backend_name", ["python", "rust"])
def test_backend_element_and_sum_propagate(backend_name: str) -> None:
    if backend_name == "python":
        solver = python_backend.Solver()
        index = python_backend.IntVar(solver, 0, 2)
        result = python_backend.element([5, 8, 5], index)
        left = python_backend.IntVar(solver, 1, 3)
        right = python_backend.IntVar(solver, 2, 4)
        total = python_backend.sum_var([left, right])
    else:
        solver = rust_backend.Solver()
        index = rust_backend.IntVar(solver, 0, 2)
        result = rust_backend.element([5, 8, 5], index)
        left = rust_backend.IntVar(solver, 1, 3)
        right = rust_backend.IntVar(solver, 2, 4)
        total = rust_backend.sum_var([left, right])

    index.remove(1)
    total.fix(4)
    solver.fix_point()

    assert result.value == 5
    assert set(left.values()) == {1, 2}
    assert set(right.values()) == {2, 3}
