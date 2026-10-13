"""Hamiltonian circuit constraint in a successor model."""

from __future__ import annotations

from collections.abc import Sequence

from minicp.constraints.all_different import AllDifferentDC
from minicp.constraints.base import Constraint
from minicp.state import StateInt
from minicp.variable import IntVarLike


class Circuit(Constraint):
    """Require the successor variables to form one Hamiltonian circuit.

    ``successors[i] == j`` represents the directed edge from node ``i`` to
    node ``j``. All-different gives every node one predecessor. Reversible
    path endpoints additionally prevent a circuit from closing before it
    contains every node.
    """

    def __init__(self, successors: Sequence[IntVarLike]) -> None:
        if len(successors) < 2:
            raise ValueError("circuit requires at least two successors")

        solver = successors[0].solver
        if any(successor.solver is not solver for successor in successors):
            raise ValueError("variables belong to different solvers")

        super().__init__(solver)
        self.successors = tuple(successors)
        manager = solver.state_manager
        self._destination = tuple(
            StateInt(manager, node) for node in range(len(successors))
        )
        self._origin = tuple(
            StateInt(manager, node) for node in range(len(successors))
        )
        self._length = tuple(
            StateInt(manager, 0) for _ in successors
        )
        self._processed = tuple(
            StateInt(manager, 0) for _ in successors
        )

    def post(self) -> None:
        node_count = len(self.successors)
        for node, successor in enumerate(self.successors):
            successor.remove_below(0)
            successor.remove_above(node_count - 1)
            successor.remove(node)
            successor.propagate_on_fix(self)

        self.solver.post(AllDifferentDC(self.successors))
        self.propagate()

    def propagate(self) -> None:
        for node, successor in enumerate(self.successors):
            if successor.is_fixed and not self._processed[node].value:
                self._connect(node, successor.value)

        if all(successor.is_fixed for successor in self.successors):
            self.deactivate()

    def _connect(self, node: int, successor: int) -> None:
        """Join the path ending at ``node`` to the path starting at successor."""

        origin = self._origin[node].value
        destination = self._destination[successor].value
        length = self._length[origin].value + self._length[successor].value + 1

        self._destination[origin].set(destination)
        self._origin[destination].set(origin)
        self._length[origin].set(length)
        self._processed[node].set(1)

        if length < len(self.successors) - 1:
            self.successors[destination].remove(origin)


def circuit(successors: Sequence[IntVarLike]) -> Circuit:
    """Create a Hamiltonian circuit constraint for successor variables."""

    return Circuit(successors)
