from collections.abc import Callable
from typing import Protocol

import pytest

from minicp._rust import SparseSet as RustSparseSet
from minicp.sparse_set import SparseSet as PythonSparseSet
from minicp.state import StateManager


class SparseSetLike(Protocol):
    @property
    def size(self) -> int: ...

    @property
    def min(self) -> int: ...

    @property
    def max(self) -> int: ...

    def contains(self, value: int) -> bool: ...
    def remove(self, value: int) -> bool: ...
    def values(self) -> list[int]: ...


SparseSetFactory = Callable[[int, int], SparseSetLike]


def make_python_sparse_set(minimum: int, maximum: int) -> PythonSparseSet:
    return PythonSparseSet(StateManager(), minimum, maximum)


def make_rust_sparse_set(minimum: int, maximum: int) -> RustSparseSet:
    return RustSparseSet(minimum, maximum)


@pytest.fixture(params=[make_python_sparse_set, make_rust_sparse_set])
def sparse_set_factory(
    request: pytest.FixtureRequest,
) -> SparseSetFactory:
    return request.param


def test_initial_interval(sparse_set_factory: SparseSetFactory) -> None:
    sparse_set = sparse_set_factory(2, 6)

    assert sparse_set.size == 5
    assert sparse_set.min == 2
    assert sparse_set.max == 6
    assert set(sparse_set.values()) == {2, 3, 4, 5, 6}


def test_remove_value(sparse_set_factory: SparseSetFactory) -> None:
    sparse_set = sparse_set_factory(2, 6)

    assert sparse_set.remove(4)
    assert not sparse_set.contains(4)
    assert sparse_set.size == 4
    assert set(sparse_set.values()) == {2, 3, 5, 6}


def test_remove_updates_bounds(sparse_set_factory: SparseSetFactory) -> None:
    sparse_set = sparse_set_factory(2, 6)

    sparse_set.remove(2)
    sparse_set.remove(6)

    assert sparse_set.min == 3
    assert sparse_set.max == 5


def test_removing_absent_value_does_nothing(
    sparse_set_factory: SparseSetFactory,
) -> None:
    sparse_set = sparse_set_factory(2, 6)

    assert not sparse_set.remove(10)
    assert not sparse_set.remove(10)
    assert sparse_set.size == 5


def test_python_sparse_set_removes_values_below_bound() -> None:
    sparse_set = make_python_sparse_set(2, 7)
    sparse_set.remove(3)

    assert sparse_set.remove_below(5)
    assert set(sparse_set.values()) == {5, 6, 7}
    assert sparse_set.min == 5
    assert sparse_set.max == 7
    assert not sparse_set.remove_below(5)


def test_python_sparse_set_removes_values_above_bound() -> None:
    sparse_set = make_python_sparse_set(2, 7)
    sparse_set.remove(6)

    assert sparse_set.remove_above(4)
    assert set(sparse_set.values()) == {2, 3, 4}
    assert sparse_set.min == 2
    assert sparse_set.max == 4
    assert not sparse_set.remove_above(4)


def test_empty_set_has_no_bounds(sparse_set_factory: SparseSetFactory) -> None:
    sparse_set = sparse_set_factory(2, 2)
    sparse_set.remove(2)

    assert sparse_set.size == 0
    with pytest.raises(ValueError, match="no minimum"):
        _ = sparse_set.min
    with pytest.raises(ValueError, match="no maximum"):
        _ = sparse_set.max


def test_python_sparse_set_is_restored() -> None:
    manager = StateManager()
    sparse_set = PythonSparseSet(manager, 2, 6)

    manager.save()
    sparse_set.remove(2)
    sparse_set.remove(4)
    sparse_set.remove(6)
    manager.restore()

    assert sparse_set.size == 5
    assert sparse_set.min == 2
    assert sparse_set.max == 6
    assert set(sparse_set.values()) == {2, 3, 4, 5, 6}


def test_python_sparse_set_bulk_removals_are_restored() -> None:
    manager = StateManager()
    sparse_set = PythonSparseSet(manager, 2, 7)

    manager.save()
    sparse_set.remove_below(4)
    sparse_set.remove_above(5)
    assert set(sparse_set.values()) == {4, 5}
    manager.restore()

    assert set(sparse_set.values()) == {2, 3, 4, 5, 6, 7}
