//! Core solver objects shared by the Rust variable and constraint layers.

use std::cell::RefCell;
use std::rc::Rc;

use crate::state::{SharedStateManager, StateManager};
use crate::state_sparse_set::StateSparseSet;

pub struct Solver {
    pub state_manager: SharedStateManager,
}

pub type SharedSolver = Rc<RefCell<Solver>>;

impl Solver {
    pub fn shared() -> SharedSolver {
        Rc::new(RefCell::new(Self {
            state_manager: StateManager::shared(),
        }))
    }
}

pub struct IntVar {
    pub solver: SharedSolver,
    domain: StateSparseSet,
    pub name: Option<String>,
}

impl IntVar {
    pub fn new(
        solver: SharedSolver,
        minimum: i64,
        maximum: i64,
        name: Option<String>,
    ) -> Result<Self, String> {
        let manager = solver.borrow().state_manager.clone();
        let domain =
            StateSparseSet::new(manager, minimum, maximum).map_err(|error| error.to_string())?;
        Ok(Self {
            solver,
            domain,
            name,
        })
    }

    pub fn min(&self) -> i64 {
        self.domain.min().expect("an IntVar domain is not empty")
    }

    pub fn max(&self) -> i64 {
        self.domain.max().expect("an IntVar domain is not empty")
    }

    pub fn size(&self) -> usize {
        self.domain.size()
    }

    pub fn is_fixed(&self) -> bool {
        self.size() == 1
    }

    pub fn value(&self) -> Result<i64, &'static str> {
        self.is_fixed()
            .then(|| self.min())
            .ok_or("variable is not fixed")
    }

    pub fn values(&self) -> Vec<i64> {
        self.domain.values().collect()
    }

    pub fn contains(&self, value: i64) -> bool {
        self.domain.contains(value)
    }

    pub fn remove(&mut self, value: i64) -> Result<(), String> {
        if !self.domain.remove(value) {
            return Ok(());
        }
        if self.domain.size() == 0 {
            return Err(format!("removing {value} emptied {}", self.label()));
        }
        Ok(())
    }

    pub fn fix(&mut self, value: i64) -> Result<(), String> {
        if !self.contains(value) {
            return Err(format!(
                "cannot fix {} to absent value {value}",
                self.label()
            ));
        }
        if self.is_fixed() {
            return Ok(());
        }
        for candidate in self.values() {
            if candidate != value {
                self.domain.remove(candidate);
            }
        }
        Ok(())
    }

    pub fn remove_below(&mut self, value: i64) -> Result<(), String> {
        if !self.domain.remove_below(value) {
            return Ok(());
        }
        if self.domain.size() == 0 {
            return Err(format!(
                "removing values below {value} emptied {}",
                self.label()
            ));
        }
        Ok(())
    }

    pub fn remove_above(&mut self, value: i64) -> Result<(), String> {
        if !self.domain.remove_above(value) {
            return Ok(());
        }
        if self.domain.size() == 0 {
            return Err(format!(
                "removing values above {value} emptied {}",
                self.label()
            ));
        }
        Ok(())
    }

    fn label(&self) -> &str {
        self.name.as_deref().unwrap_or("IntVar")
    }
}

#[cfg(test)]
mod tests {
    use std::rc::Rc;

    use super::{IntVar, Solver};

    #[test]
    fn variable_domain_is_reversible() {
        let solver = Solver::shared();
        let mut variable = IntVar::new(solver.clone(), 1, 4, None).unwrap();
        assert!(Rc::ptr_eq(&variable.solver, &solver));
        solver.borrow().state_manager.borrow_mut().save();
        variable.fix(3).unwrap();
        assert_eq!(variable.value(), Ok(3));
        solver
            .borrow()
            .state_manager
            .borrow_mut()
            .restore()
            .unwrap();
        assert_eq!(
            variable
                .values()
                .into_iter()
                .collect::<std::collections::HashSet<_>>(),
            (1..=4).collect()
        );
    }
}
