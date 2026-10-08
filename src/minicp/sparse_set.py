"""A reversible sparse set implemented in Python."""

from __future__ import annotations

from minicp.state import StateInt, StateManager


class SparseSet:
    """A reversible set containing an initial interval of integers."""

    def __init__(
        self,
        manager: StateManager,
        minimum: int,
        maximum: int,
    ) -> None:
        if minimum > maximum:
            raise ValueError("minimum must be less than or equal to maximum")

        length = maximum - minimum + 1
        self._values = list(range(length))
        self._indices = list(range(length))
        self._size = StateInt(manager, length)
        self._min = StateInt(manager, 0)
        self._max = StateInt(manager, length - 1)
        self._offset = minimum

    @property
    def size(self) -> int:
        return self._size.value

    @property
    def min(self) -> int:
        if self.size == 0:
            raise ValueError("empty sparse set has no minimum")
        return self._min.value + self._offset

    @property
    def max(self) -> int:
        if self.size == 0:
            raise ValueError("empty sparse set has no maximum")
        return self._max.value + self._offset

    def contains(self, value: int) -> bool:
        normalized = value - self._offset
        return self._contains_normalized(normalized)

    def remove(self, value: int) -> bool:
        normalized = value - self._offset
        if not self._contains_normalized(normalized):
            return False

        last = self._values[self.size - 1]
        self._exchange_positions(normalized, last)
        self._size.set(self.size - 1)

        if self.size > 0:
            if normalized == self._min.value:
                new_min = next(
                    candidate
                    for candidate in range(normalized + 1, self._max.value + 1)
                    if self._contains_normalized(candidate)
                )
                self._min.set(new_min)

            if normalized == self._max.value:
                new_max = next(
                    candidate
                    for candidate in range(normalized - 1, self._min.value - 1, -1)
                    if self._contains_normalized(candidate)
                )
                self._max.set(new_max)

        return True

    def values(self) -> list[int]:
        return [
            value + self._offset
            for value in self._values[: self.size]
        ]

    def _contains_normalized(self, value: int) -> bool:
        return 0 <= value < len(self._values) and self._indices[value] < self.size

    def _exchange_positions(self, first: int, second: int) -> None:
        first_index = self._indices[first]
        second_index = self._indices[second]
        self._values[first_index], self._values[second_index] = (
            self._values[second_index],
            self._values[first_index],
        )
        self._indices[first], self._indices[second] = second_index, first_index
