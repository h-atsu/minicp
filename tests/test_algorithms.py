from minicp.algorithms import (
    maximum_matching,
    reachable_nodes,
    strongly_connected_components,
)


def test_maximum_matching_finds_an_augmenting_path() -> None:
    left_to_right, right_to_left = maximum_matching(
        [[1, 2], [1], [2, 3]]
    )

    assert left_to_right == {0: 2, 1: 1, 2: 3}
    assert right_to_left == {1: 1, 2: 0, 3: 2}


def test_maximum_matching_returns_a_partial_matching_when_needed() -> None:
    left_to_right, right_to_left = maximum_matching([[1], [1], [2]])

    assert left_to_right == {0: 1, 2: 2}
    assert right_to_left == {1: 0, 2: 2}


def test_strongly_connected_components_group_exactly_the_cycles() -> None:
    graph = {
        0: [1],
        1: [0, 2],
        2: [3],
        3: [2],
        4: [],
    }

    component = strongly_connected_components(graph)

    assert component[0] == component[1]
    assert component[2] == component[3]
    assert component[0] != component[2]
    assert component[4] not in {component[0], component[2]}


def test_reachable_nodes_accepts_multiple_starting_nodes() -> None:
    graph = {0: [1], 1: [2], 2: [], 3: [4], 4: []}

    assert reachable_nodes(graph, [0, 3]) == {0, 1, 2, 3, 4}
