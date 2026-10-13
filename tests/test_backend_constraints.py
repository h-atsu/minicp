from collections.abc import Callable
from typing import Protocol

import pytest

from minicp import python as python_backend
from minicp import rust as rust_backend


class VariableLike(Protocol):
    def values(self) -> list[int]: ...
    def contains(self, value: int) -> bool: ...
    def fix(self, value: int) -> None: ...


class StateManagerLike(Protocol):
    def save(self) -> None: ...
    def restore(self) -> None: ...


class SolverLike(Protocol):
    @property
    def state_manager(self) -> StateManagerLike: ...

    def fix_point(self) -> None: ...


ConstraintFixture = tuple[SolverLike, VariableLike, VariableLike]
ConstraintFactory = Callable[[], ConstraintFixture]


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
