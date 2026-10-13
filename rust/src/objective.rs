//! Persistent branch-and-bound objectives.

use std::cell::Cell;
use std::rc::Rc;

use crate::solver::{SharedSolver, VariableId};

pub struct Minimize {
    pub solver: SharedSolver,
    pub variable: VariableId,
    pub(crate) best_value: Rc<Cell<Option<i64>>>,
}

impl Minimize {
    pub fn new(solver: SharedSolver, variable: VariableId) -> Self {
        Self {
            solver,
            variable,
            best_value: Rc::new(Cell::new(None)),
        }
    }
    pub fn best_value(&self) -> Option<i64> {
        self.best_value.get()
    }
}
