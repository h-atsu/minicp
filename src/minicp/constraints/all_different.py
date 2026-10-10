"""All-different constraints."""

from __future__ import annotations

from collections.abc import Sequence

from minicp.algorithms import (
    maximum_matching,
    reachable_nodes,
    strongly_connected_components,
)
from minicp.constraints.base import Constraint
from minicp.constraints.not_equal import NotEqual
from minicp.exceptions import Inconsistency
from minicp.variable import IntVarLike

type _Node = tuple[str, int]


class AllDifferentBinary(Constraint):
    """Require pairwise different values using binary inequalities."""

    def __init__(self, variables: Sequence[IntVarLike]) -> None:
        if not variables:
            raise ValueError("all-different requires at least one variable")

        solver = variables[0].solver
        if any(variable.solver is not solver for variable in variables):
            raise ValueError("variables belong to different solvers")

        super().__init__(solver)
        self.variables = tuple(variables)

    def post(self) -> None:
        for left_index, left in enumerate(self.variables):
            for right in self.variables[left_index + 1 :]:
                self.solver.post(NotEqual(left, right))
        self.deactivate()

    def propagate(self) -> None:
        # The binary NotEqual constraints perform all propagation.
        pass


class AllDifferentDC(Constraint):
    """Domain-consistent all-different using a maximum matching.

    Variables and values form a bipartite graph. A matching that covers every
    variable proves that the constraint is currently feasible. The directed
    alternating graph then identifies exactly the edges that occur in some
    covering matching; all other variable-value pairs can be removed.

    The matching and graph are rebuilt on every propagation. Keeping them as
    ordinary local data makes the algorithm easy to inspect and leaves domain
    restoration entirely to the variables.
    """

    def __init__(self, variables: Sequence[IntVarLike]) -> None:
        if not variables:
            raise ValueError("all-different requires at least one variable")

        solver = variables[0].solver
        if any(variable.solver is not solver for variable in variables):
            raise ValueError("variables belong to different solvers")

        super().__init__(solver)
        self.variables = tuple(variables)

    def post(self) -> None:
        for variable in self.variables:
            variable.propagate_on_domain_change(self)
        self.propagate()

    def propagate(self) -> None:
        adjacency = [
            sorted(variable.values()) for variable in self.variables
        ]
        variable_to_value, value_to_variable = maximum_matching(adjacency)
        if len(variable_to_value) != len(self.variables):
            raise Inconsistency("all-different has no matching")

        graph = self._alternating_graph(variable_to_value)
        component = strongly_connected_components(graph)
        free_values = (
            node
            for node in graph
            if node[0] == "value" and node[1] not in value_to_variable
        )
        reachable = reachable_nodes(graph, free_values)

        for variable_index, variable in enumerate(self.variables):
            variable_node = self._variable_node(variable_index)
            matched_value = variable_to_value[variable_index]
            for value in variable.values():
                if value == matched_value:
                    continue

                value_node = self._value_node(value)
                belongs_to_alternating_cycle = (
                    component[variable_node] == component[value_node]
                )
                belongs_to_alternating_path = value_node in reachable
                if not (
                    belongs_to_alternating_cycle
                    or belongs_to_alternating_path
                ):
                    variable.remove(value)

        if all(variable.is_fixed for variable in self.variables):
            self.deactivate()

    def _alternating_graph(
        self, variable_to_value: dict[int, int]
    ) -> dict[_Node, list[_Node]]:
        graph: dict[_Node, list[_Node]] = {}

        for variable_index, variable in enumerate(self.variables):
            variable_node = self._variable_node(variable_index)
            graph.setdefault(variable_node, [])
            for value in variable.values():
                value_node = self._value_node(value)
                graph.setdefault(value_node, [])
                if variable_to_value[variable_index] == value:
                    graph[variable_node].append(value_node)
                else:
                    graph[value_node].append(variable_node)

        return graph

    @staticmethod
    def _variable_node(index: int) -> _Node:
        return ("variable", index)

    @staticmethod
    def _value_node(value: int) -> _Node:
        return ("value", value)


def all_different(variables: Sequence[IntVarLike]) -> AllDifferentDC:
    """Create a domain-consistent all-different constraint."""

    return AllDifferentDC(variables)
