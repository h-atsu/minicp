//! Arena ownership and propagation-queue bookkeeping.

use std::cell::RefCell;
use std::collections::VecDeque;
use std::rc::Rc;

use crate::constraints::{Constraint, ConstraintKind};
use crate::state::{SharedStateManager, StateInt, StateManager};
use crate::variable::Variable;

pub type VariableId = usize;
pub type ConstraintId = usize;
pub type SharedSolver = Rc<RefCell<Solver>>;
pub type SolverResult<T> = Result<T, String>;

pub struct Solver {
    pub state_manager: SharedStateManager,
    pub(crate) variables: Vec<Variable>,
    pub(crate) constraints: Vec<Constraint>,
    pub(crate) queue: VecDeque<ConstraintId>,
}

impl Solver {
    pub fn shared() -> SharedSolver {
        Self::with_manager(StateManager::shared())
    }

    pub fn with_manager(state_manager: SharedStateManager) -> SharedSolver {
        Rc::new(RefCell::new(Self {
            state_manager,
            variables: Vec::new(),
            constraints: Vec::new(),
            queue: VecDeque::new(),
        }))
    }

    pub(crate) fn new_constraint(&mut self, kind: ConstraintKind) -> ConstraintId {
        let id = self.constraints.len();
        self.constraints.push(Constraint {
            kind,
            active: StateInt::new(self.state_manager.clone(), 1),
            scheduled: false,
            posted: false,
        });
        id
    }

    pub(crate) fn deactivate(&mut self, constraint: ConstraintId) {
        self.constraints[constraint].active.set(0);
    }

    pub(crate) fn schedule(&mut self, constraint: ConstraintId) {
        let data = &mut self.constraints[constraint];
        if data.active.value() != 0 && !data.scheduled {
            data.scheduled = true;
            self.queue.push_back(constraint);
        }
    }

    pub(crate) fn clear_queue(&mut self) {
        while let Some(constraint) = self.queue.pop_front() {
            self.constraints[constraint].scheduled = false;
        }
    }
}

#[cfg(test)]
mod tests {
    use super::Solver;
    use std::collections::HashSet;

    #[test]
    fn propagates_not_equal_and_restores_domains() {
        let solver = Solver::shared();
        let (x, y) = {
            let mut inner = solver.borrow_mut();
            let x = inner.new_variable(1, 3, None).unwrap();
            let y = inner.new_variable(1, 3, None).unwrap();
            let constraint = inner.new_not_equal(x, y, 0);
            inner.post(constraint).unwrap();
            (x, y)
        };
        solver.borrow().state_manager.borrow_mut().save();
        solver.borrow_mut().fix(x, 2).unwrap();
        solver.borrow_mut().fix_point().unwrap();
        assert!(!solver.borrow().contains(y, 2));
        solver
            .borrow()
            .state_manager
            .borrow_mut()
            .restore()
            .unwrap();
        assert!(solver.borrow().contains(y, 2));
    }

    #[test]
    fn propagates_equal_domains() {
        let solver = Solver::shared();
        let mut inner = solver.borrow_mut();
        let x = inner.new_variable(1, 3, None).unwrap();
        let y = inner.new_variable(2, 4, None).unwrap();
        let constraint = inner.new_equal(x, y);
        inner.post(constraint).unwrap();
        assert_eq!(
            inner.values(x).into_iter().collect::<HashSet<_>>(),
            HashSet::from([2, 3])
        );
        assert_eq!(
            inner.values(y).into_iter().collect::<HashSet<_>>(),
            HashSet::from([2, 3])
        );
    }
}
