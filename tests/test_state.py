import pytest

from minicp import StateInt, StateManager, StateStack


def test_state_int_initial_value() -> None:
    manager = StateManager()
    state = StateInt(manager, 10)

    assert state.value == 10
    assert manager.level == -1


def test_restore() -> None:
    manager = StateManager()
    state = StateInt(manager, 10)

    manager.save()
    state.set(20)
    manager.restore()

    assert state.value == 10
    assert manager.level == -1


def test_nested_restore() -> None:
    manager = StateManager()
    state = StateInt(manager, 10)

    manager.save()
    state.set(20)

    manager.save()
    state.set(30)
    manager.restore()

    assert state.value == 20
    assert manager.level == 0

    manager.restore()

    assert state.value == 10
    assert manager.level == -1


def test_restore_multiple_changes_and_states() -> None:
    manager = StateManager()
    x = StateInt(manager, 10)
    y = StateInt(manager, 100)

    manager.save()
    x.set(20)
    x.set(30)
    y.set(200)
    manager.restore()

    assert x.value == 10
    assert y.value == 100


def test_changes_without_saved_state_are_permanent() -> None:
    manager = StateManager()
    state = StateInt(manager, 10)

    state.set(20)
    manager.save()
    state.set(30)
    manager.restore()

    assert state.value == 20


def test_restore_without_saved_state_fails() -> None:
    manager = StateManager()

    with pytest.raises(RuntimeError, match="no state has been saved"):
        manager.restore()


def test_state_stack_restores_its_visible_items() -> None:
    manager = StateManager()
    stack: StateStack[str] = StateStack(manager)
    stack.append("root")

    manager.save()
    stack.append("left")
    assert list(stack) == ["root", "left"]
    manager.restore()

    assert list(stack) == ["root"]

    manager.save()
    stack.append("right")
    assert list(stack) == ["root", "right"]
    manager.restore()
