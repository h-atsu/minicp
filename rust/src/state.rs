//! Reversible integer state backed by a simple trail.
//!
//! This deliberately mirrors the readable Python reference implementation:
//! every effective change below a checkpoint records the previous value.

mod sparse_set;
mod state_sparse_set;

pub(crate) use sparse_set::SparseSet;
pub(crate) use state_sparse_set::StateSparseSet;

use std::cell::RefCell;
use std::rc::Rc;

#[derive(Default)]
pub struct StateManager {
    values: Vec<i64>,
    trail: Vec<(usize, i64)>,
    checkpoints: Vec<usize>,
}

pub type SharedStateManager = Rc<RefCell<StateManager>>;

impl StateManager {
    pub fn shared() -> SharedStateManager {
        Rc::new(RefCell::new(Self::default()))
    }

    pub fn level(&self) -> isize {
        self.checkpoints.len() as isize - 1
    }

    pub fn save(&mut self) {
        self.checkpoints.push(self.trail.len());
    }

    pub fn restore(&mut self) -> Result<(), &'static str> {
        let Some(checkpoint) = self.checkpoints.pop() else {
            return Err("cannot restore: no state has been saved");
        };

        while self.trail.len() > checkpoint {
            let (id, old_value) = self.trail.pop().expect("trail is not empty");
            self.values[id] = old_value;
        }
        Ok(())
    }

    fn create_int(&mut self, value: i64) -> usize {
        let id = self.values.len();
        self.values.push(value);
        id
    }

    fn value(&self, id: usize) -> i64 {
        self.values[id]
    }

    fn set(&mut self, id: usize, value: i64) {
        let old_value = self.values[id];
        if value == old_value {
            return;
        }
        if !self.checkpoints.is_empty() {
            self.trail.push((id, old_value));
        }
        self.values[id] = value;
    }
}

#[derive(Clone)]
pub struct StateInt {
    manager: SharedStateManager,
    id: usize,
}

pub struct StateStack<T> {
    items: Vec<T>,
    size: StateInt,
}

impl<T: Clone> StateStack<T> {
    pub fn new(manager: SharedStateManager) -> Self {
        Self {
            items: Vec::new(),
            size: StateInt::new(manager, 0),
        }
    }

    pub fn push(&mut self, item: T) {
        let index = self.size.value() as usize;
        if index == self.items.len() {
            self.items.push(item);
        } else {
            self.items[index] = item;
        }
        self.size.set(index as i64 + 1);
    }

    pub fn values(&self) -> Vec<T> {
        self.items[..self.size.value() as usize].to_vec()
    }
}

impl StateInt {
    pub fn new(manager: SharedStateManager, value: i64) -> Self {
        let id = manager.borrow_mut().create_int(value);
        Self { manager, id }
    }

    pub fn value(&self) -> i64 {
        self.manager.borrow().value(self.id)
    }

    pub fn set(&self, value: i64) {
        self.manager.borrow_mut().set(self.id, value);
    }
}

#[cfg(test)]
mod tests {
    use super::{StateInt, StateManager};

    #[test]
    fn restores_nested_changes() {
        let manager = StateManager::shared();
        let state = StateInt::new(manager.clone(), 10);

        manager.borrow_mut().save();
        state.set(20);
        manager.borrow_mut().save();
        state.set(30);

        manager.borrow_mut().restore().unwrap();
        assert_eq!(state.value(), 20);
        manager.borrow_mut().restore().unwrap();
        assert_eq!(state.value(), 10);
    }
}
