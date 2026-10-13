import pytest

from minicp import rust


def test_rust_tsp_finds_known_optimum() -> None:
    distances = [
        [0, 2, 9, 10],
        [1, 0, 6, 4],
        [15, 7, 0, 8],
        [6, 3, 12, 0],
    ]

    result = rust.solve_tsp(distances)

    assert result.improving_solutions[-1] == (21, [2, 0, 3, 1])
    assert result.statistics.completed
    assert result.statistics.solutions == len(result.improving_solutions)


def test_rust_tsp_honors_time_limit() -> None:
    result = rust.solve_tsp([[0, 1], [1, 0]], time_limit=0)

    assert not result.statistics.completed
    assert result.improving_solutions == []


@pytest.mark.parametrize(
    ("distances", "message"),
    [
        ([[0]], "at least two"),
        ([[0, 1], [1]], "square"),
    ],
)
def test_rust_tsp_validates_distance_matrix(
    distances: list[list[int]], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        rust.solve_tsp(distances)
