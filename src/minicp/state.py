"""Reversible state used while exploring a search tree."""

from __future__ import annotations

from collections.abc import Iterator


class StateManager:
    """Save and restore changes made to stateful integers.

    This intentionally uses a simple trail: every effective change made below
    a saved state records the previous value.  It can be optimized later
    without changing the public API.
    """

    def __init__(self) -> None:
        self._trail: list[tuple[StateInt, int]] = []
        self._checkpoints: list[int] = []

    @property
    def level(self) -> int:
        """Return the current search level, starting at ``-1``."""

        return len(self._checkpoints) - 1

    def save(self) -> None:
        """Save the current state and enter a new search level."""

        self._checkpoints.append(len(self._trail))

    def restore(self) -> None:
        """Restore the most recently saved state."""

        if not self._checkpoints:
            raise RuntimeError("cannot restore: no state has been saved")

        checkpoint = self._checkpoints.pop()
        while len(self._trail) > checkpoint:
            state, old_value = self._trail.pop()
            state._restore(old_value)

    def _record(self, state: StateInt, old_value: int) -> None:
        if self._checkpoints:
            self._trail.append((state, old_value))


class StateInt:
    """An integer whose value is restored by a :class:`StateManager`."""

    def __init__(self, manager: StateManager, value: int) -> None:
        self._manager = manager
        self._value = value

    @property
    def value(self) -> int:
        return self._value

    def set(self, value: int) -> None:
        """Set a new value, recording the old one when necessary."""

        if value == self._value:
            return

        self._manager._record(self, self._value)
        self._value = value

    def _restore(self, value: int) -> None:
        # Restoring must not create another trail entry.
        self._value = value


class StateStack[T]:
    """A stack whose logical size is restored with the search state.

    Stored objects do not need to be copied. On restoration only the visible
    prefix changes, which is sufficient for reversible listener lists.
    """

    def __init__(self, manager: StateManager) -> None:
        self._items: list[T] = []
        self._size = StateInt(manager, 0)

    def append(self, item: T) -> None:
        index = self._size.value
        if index == len(self._items):
            self._items.append(item)
        else:
            self._items[index] = item
        self._size.set(index + 1)

    def __len__(self) -> int:
        return self._size.value

    def __iter__(self) -> Iterator[T]:
        for index in range(self._size.value):
            yield self._items[index]
