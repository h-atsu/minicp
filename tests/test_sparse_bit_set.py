import pytest

from minicp import StateManager, StateSparseBitSet


def test_initially_contains_every_bit_in_its_capacity() -> None:
    bit_set = StateSparseBitSet(StateManager(), 70)

    assert all(bit_set.get(index) for index in range(70))
    assert not bit_set.is_empty


def test_empty_capacity_is_empty() -> None:
    bit_set = StateSparseBitSet(StateManager(), 0)
    support = bit_set.support_bit_set()

    assert bit_set.is_empty
    assert not bit_set.intersects(support)


def test_intersection_removes_unsupported_bits() -> None:
    bit_set = StateSparseBitSet(StateManager(), 130)
    mask = bit_set.mask_bit_set()
    for index in (1, 65, 129):
        mask.set(index)

    bit_set.intersect_with(mask)

    assert [index for index in range(130) if bit_set.get(index)] == [1, 65, 129]


def test_words_and_sparse_prefix_are_restored() -> None:
    manager = StateManager()
    bit_set = StateSparseBitSet(manager, 130)
    keep_first_word = bit_set.mask_bit_set()
    keep_first_word.set(10)

    manager.save()
    bit_set.intersect_with(keep_first_word)
    assert bit_set.get(10)
    assert not bit_set.get(70)
    manager.restore()

    assert bit_set.get(10)
    assert bit_set.get(70)
    assert bit_set.get(129)


def test_mask_combines_supports_only_on_non_empty_words() -> None:
    bit_set = StateSparseBitSet(StateManager(), 130)
    keep_outer_words = bit_set.mask_bit_set()
    keep_outer_words.set(1)
    keep_outer_words.set(129)
    bit_set.intersect_with(keep_outer_words)

    first = bit_set.support_bit_set()
    first.set(1)
    first.set(65)
    second = bit_set.support_bit_set()
    second.set(129)

    mask = bit_set.mask_bit_set()
    mask.union_with(first)
    mask.union_with(second)
    mask.intersect_with(first)

    bit_set.intersect_with(mask)

    assert bit_set.get(1)
    assert not bit_set.get(129)


def test_intersection_uses_and_updates_support_residue() -> None:
    bit_set = StateSparseBitSet(StateManager(), 130)
    support = bit_set.support_bit_set()
    support.set(65)

    assert support.residue == 0
    assert not bit_set.intersects_residue_only(support)
    assert bit_set.intersects(support)
    assert support.residue == 1
    assert bit_set.intersects_residue_only(support)


def test_residue_is_a_non_reversible_search_hint() -> None:
    manager = StateManager()
    bit_set = StateSparseBitSet(manager, 130)
    support = bit_set.support_bit_set()
    support.set(129)

    manager.save()
    assert bit_set.intersects(support)
    manager.restore()

    assert support.residue == 2
    assert bit_set.intersects_residue_only(support)


def test_rejects_bits_outside_the_capacity() -> None:
    bit_set = StateSparseBitSet(StateManager(), 3)

    with pytest.raises(IndexError):
        bit_set.get(3)
    with pytest.raises(IndexError):
        bit_set.support_bit_set().set(-1)


def test_rejects_a_mask_from_another_sparse_bit_set() -> None:
    first = StateSparseBitSet(StateManager(), 10)
    second = StateSparseBitSet(StateManager(), 10)

    with pytest.raises(ValueError, match="different StateSparseBitSet"):
        first.intersect_with(second.mask_bit_set())
