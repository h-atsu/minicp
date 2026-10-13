from collections.abc import Callable
from typing import Protocol

import pytest

from minicp import SparseSet, StateInt, StateManager
from minicp import python as python_backend
from minicp import rust as rust_backend


class StateManagerLike(Protocol):
    @property
    def level(self) -> int: ...

    def save(self) -> None: ...
    def restore(self) -> None: ...


class StateIntLike(Protocol):
    @property
    def value(self) -> int: ...

    def set(self, value: int) -> None: ...


class SparseSetLike(Protocol):
    @property
    def size(self) -> int: ...

    @property
    def min(self) -> int: ...

    @property
    def max(self) -> int: ...

    def remove(self, value: int) -> bool: ...
    def remove_below(self, value: int) -> bool: ...
    def remove_above(self, value: int) -> bool: ...
    def values(self) -> list[int]: ...


StateFactory = Callable[[], tuple[StateManagerLike, StateIntLike]]
SparseSetFactory = Callable[[], tuple[StateManagerLike, SparseSetLike]]


def make_python_state() -> tuple[StateManagerLike, StateIntLike]:
    manager = python_backend.StateManager()
    return manager, python_backend.StateInt(manager, 10)


def make_rust_state() -> tuple[StateManagerLike, StateIntLike]:
    manager = rust_backend.StateManager()
    return manager, rust_backend.StateInt(manager, 10)


def make_python_sparse_set() -> tuple[StateManagerLike, SparseSetLike]:
    manager = python_backend.StateManager()
    return manager, python_backend.SparseSet(manager, 2, 7)


def make_rust_sparse_set() -> tuple[StateManagerLike, SparseSetLike]:
    manager = rust_backend.StateManager()
    return manager, rust_backend.SparseSet(manager, 2, 7)


@pytest.mark.parametrize("factory", [make_python_state, make_rust_state])
def test_backend_state_int_restores_nested_changes(factory: StateFactory) -> None:
    manager, state = factory()

    manager.save()
    state.set(20)
    manager.save()
    state.set(30)
    manager.restore()

    assert state.value == 20
    assert manager.level == 0

    manager.restore()
    assert state.value == 10
    assert manager.level == -1


@pytest.mark.parametrize(
    "factory", [make_python_sparse_set, make_rust_sparse_set]
)
def test_backend_sparse_set_restores_bulk_changes(
    factory: SparseSetFactory,
) -> None:
    manager, sparse_set = factory()

    manager.save()
    sparse_set.remove(3)
    sparse_set.remove_below(5)
    sparse_set.remove_above(6)
    assert set(sparse_set.values()) == {5, 6}
    assert sparse_set.min == 5
    assert sparse_set.max == 6
    manager.restore()

    assert sparse_set.size == 6
    assert set(sparse_set.values()) == {2, 3, 4, 5, 6, 7}
    assert sparse_set.min == 2
    assert sparse_set.max == 7


def test_top_level_api_remains_the_python_backend() -> None:
    assert StateManager is python_backend.StateManager
    assert StateInt is python_backend.StateInt
    assert SparseSet is python_backend.SparseSet
