"""Reversible sparse bit sets used by Compact Table."""

from __future__ import annotations

from minicp.state import StateInt, StateManager

_WORD_SIZE = 64
_FULL_WORD = (1 << _WORD_SIZE) - 1


class _BitSet:
    """A non-reversible bit set with a fixed capacity."""

    def __init__(self, owner: StateSparseBitSet) -> None:
        self._owner = owner
        self._words = [0] * owner._n_words

    def set(self, index: int) -> None:
        self._owner._check_index(index)
        word_index, bit_index = divmod(index, _WORD_SIZE)
        self._words[word_index] |= 1 << bit_index

    def get(self, index: int) -> bool:
        self._owner._check_index(index)
        word_index, bit_index = divmod(index, _WORD_SIZE)
        return bool(self._words[word_index] & (1 << bit_index))

    def _check_compatible(self, other: _BitSet) -> None:
        if other._owner is not self._owner:
            raise ValueError("bit sets belong to different StateSparseBitSets")


class SupportBitSet(_BitSet):
    """Tuple support for one variable-value pair.

    ``residue`` remembers a word where an intersection was last found. It is
    only a search hint, so it deliberately is not reversible.
    """

    def __init__(self, owner: StateSparseBitSet) -> None:
        super().__init__(owner)
        self.residue = 0


class MaskBitSet(_BitSet):
    """Scratch bit set whose operations skip empty words in its owner."""

    def clear(self) -> None:
        for word_index in self._owner._non_zero_word_indices():
            self._words[word_index] = 0

    def union_with(self, other: _BitSet) -> None:
        self._check_compatible(other)
        for word_index in self._owner._non_zero_word_indices():
            self._words[word_index] |= other._words[word_index]

    def intersect_with(self, other: _BitSet) -> None:
        self._check_compatible(other)
        for word_index in self._owner._non_zero_word_indices():
            self._words[word_index] &= other._words[word_index]


class StateSparseBitSet:
    """A reversible bit set that only scans words containing set bits.

    The set initially contains every bit from ``0`` through ``capacity - 1``.
    Intersections can only remove bits. Empty words are moved outside a
    reversible active prefix, just as values are removed from a sparse set.
    """

    def __init__(self, manager: StateManager, capacity: int) -> None:
        if capacity < 0:
            raise ValueError("capacity must be non-negative")

        self.capacity = capacity
        self._n_words = (capacity + _WORD_SIZE - 1) // _WORD_SIZE
        self._words = [StateInt(manager, _FULL_WORD) for _ in range(self._n_words)]
        if capacity % _WORD_SIZE:
            self._words[-1].set((1 << (capacity % _WORD_SIZE)) - 1)

        self._non_zero_indices = list(range(self._n_words))
        self._non_zero_size = StateInt(manager, self._n_words)

    def support_bit_set(self) -> SupportBitSet:
        return SupportBitSet(self)

    def mask_bit_set(self) -> MaskBitSet:
        return MaskBitSet(self)

    @property
    def is_empty(self) -> bool:
        return self._non_zero_size.value == 0

    def get(self, index: int) -> bool:
        self._check_index(index)
        word_index, bit_index = divmod(index, _WORD_SIZE)
        return bool(self._words[word_index].value & (1 << bit_index))

    def intersect_with(self, bit_set: _BitSet) -> None:
        self._check_compatible(bit_set)
        for sparse_index in range(self._non_zero_size.value - 1, -1, -1):
            word_index = self._non_zero_indices[sparse_index]
            new_word = self._words[word_index].value & bit_set._words[word_index]
            self._words[word_index].set(new_word)

            if new_word == 0:
                last = self._non_zero_size.value - 1
                self._non_zero_indices[sparse_index], self._non_zero_indices[last] = (
                    self._non_zero_indices[last],
                    self._non_zero_indices[sparse_index],
                )
                self._non_zero_size.set(last)

    def intersects_residue_only(self, support: SupportBitSet) -> bool:
        self._check_compatible(support)
        if self._n_words == 0:
            return False
        word_index = support.residue
        return bool(
            self._words[word_index].value & support._words[word_index]
        )

    def intersects(self, support: SupportBitSet) -> bool:
        if self.intersects_residue_only(support):
            return True

        for word_index in reversed(tuple(self._non_zero_word_indices())):
            if self._words[word_index].value & support._words[word_index]:
                support.residue = word_index
                return True
        return False

    def _non_zero_word_indices(self) -> tuple[int, ...]:
        return tuple(self._non_zero_indices[: self._non_zero_size.value])

    def _check_compatible(self, bit_set: _BitSet) -> None:
        if bit_set._owner is not self:
            raise ValueError("bit set belongs to a different StateSparseBitSet")

    def _check_index(self, index: int) -> None:
        if not 0 <= index < self.capacity:
            raise IndexError(f"bit index {index} outside [0, {self.capacity})")
