"""Algorithms on directed graphs represented by adjacency mappings."""

from __future__ import annotations

from collections.abc import Hashable, Iterable, Mapping


def reachable_nodes[Node: Hashable](
    graph: Mapping[Node, Iterable[Node]], starts: Iterable[Node]
) -> set[Node]:
    """Return all nodes reachable from one or more starting nodes."""

    reachable: set[Node] = set()
    pending = list(starts)

    while pending:
        node = pending.pop()
        if node in reachable:
            continue
        reachable.add(node)
        pending.extend(graph[node])

    return reachable


def strongly_connected_components[Node: Hashable](
    graph: Mapping[Node, Iterable[Node]],
) -> dict[Node, int]:
    """Return Tarjan component numbers for a directed graph."""

    next_index = 0
    indices: dict[Node, int] = {}
    low_links: dict[Node, int] = {}
    stack: list[Node] = []
    on_stack: set[Node] = set()
    component: dict[Node, int] = {}

    def visit(node: Node) -> None:
        nonlocal next_index
        indices[node] = next_index
        low_links[node] = next_index
        next_index += 1
        stack.append(node)
        on_stack.add(node)

        for neighbor in graph[node]:
            if neighbor not in indices:
                visit(neighbor)
                low_links[node] = min(low_links[node], low_links[neighbor])
            elif neighbor in on_stack:
                low_links[node] = min(low_links[node], indices[neighbor])

        if low_links[node] != indices[node]:
            return

        component_number = len(component)
        while True:
            member = stack.pop()
            on_stack.remove(member)
            component[member] = component_number
            if member == node:
                break

    for node in graph:
        if node not in indices:
            visit(node)

    return component
