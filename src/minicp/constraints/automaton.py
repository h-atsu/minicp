"""Finite automaton constraint."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from minicp.constraints.base import Constraint
from minicp.exceptions import Inconsistency
from minicp.variable import IntVarLike


class Automaton(Constraint):
    """Accept a sequence of symbols along a path through an automaton.

    A transition is a ``(state, symbol, next_state)`` tuple. Propagation keeps
    a symbol value exactly when it belongs to a path from ``initial_state`` to
    one of ``accepting_states``.
    """

    def __init__(
        self,
        symbols: Sequence[IntVarLike],
        initial_state: int,
        accepting_states: Iterable[int],
        transitions: Iterable[tuple[int, int, int]],
    ) -> None:
        if not symbols:
            raise ValueError("automaton requires at least one symbol")

        solver = symbols[0].solver
        if any(symbol.solver is not solver for symbol in symbols):
            raise ValueError("variables belong to different solvers")

        super().__init__(solver)
        self.symbols = tuple(symbols)
        self.initial_state = initial_state
        self.accepting_states = frozenset(accepting_states)
        self.transitions = tuple(transitions)

    def post(self) -> None:
        for symbol in self.symbols:
            symbol.propagate_on_domain_change(self)
        self.propagate()

    def propagate(self) -> None:
        forward = self._forward_reachable_states()
        backward = self._backward_reachable_states()

        if self.initial_state not in backward[0]:
            raise Inconsistency("automaton has no accepting path")

        for position, symbol in enumerate(self.symbols):
            supported_values = {
                value
                for state, value, next_state in self.transitions
                if state in forward[position]
                and next_state in backward[position + 1]
                and symbol.contains(value)
            }
            for value in symbol.values():
                if value not in supported_values:
                    symbol.remove(value)

        if all(symbol.is_fixed for symbol in self.symbols):
            self.deactivate()

    def _forward_reachable_states(self) -> list[set[int]]:
        reachable = [{self.initial_state}]
        for symbol in self.symbols:
            next_states = {
                next_state
                for state, value, next_state in self.transitions
                if state in reachable[-1] and symbol.contains(value)
            }
            reachable.append(next_states)
        return reachable

    def _backward_reachable_states(self) -> list[set[int]]:
        reachable = [set() for _ in range(len(self.symbols) + 1)]
        reachable[-1] = set(self.accepting_states)
        for position in range(len(self.symbols) - 1, -1, -1):
            symbol = self.symbols[position]
            reachable[position] = {
                state
                for state, value, next_state in self.transitions
                if next_state in reachable[position + 1]
                and symbol.contains(value)
            }
        return reachable
