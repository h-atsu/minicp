"""Maximum matching in bipartite graphs."""

from __future__ import annotations

from collections.abc import Hashable, Sequence


def maximum_matching[RightNode: Hashable](
    adjacency: Sequence[Sequence[RightNode]],
) -> tuple[dict[int, RightNode], dict[RightNode, int]]:
    """Match as many left nodes as possible to distinct right nodes.

    A left node is its index in ``adjacency``. Each sequence contains its
    neighboring right nodes. The two returned dictionaries describe the same
    matching in both directions.
    """

    left_to_right: dict[int, RightNode] = {}
    right_to_left: dict[RightNode, int] = {}

    def augment(left: int, seen_right: set[RightNode]) -> bool:
        for right in adjacency[left]:
            if right in seen_right:
                continue
            seen_right.add(right)

            owner = right_to_left.get(right)
            if owner is None or augment(owner, seen_right):
                left_to_right[left] = right
                right_to_left[right] = left
                return True
        return False

    for left in range(len(adjacency)):
        augment(left, set())

    return left_to_right, right_to_left
