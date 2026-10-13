//! Arena-based variables, constraints, and propagation queue.

use std::cell::RefCell;
use std::collections::{HashSet, VecDeque};
use std::rc::Rc;

use crate::state::{SharedStateManager, StateInt, StateManager, StateStack};
use crate::state_sparse_set::StateSparseSet;

pub type VariableId = usize;
pub type ConstraintId = usize;
pub type SharedSolver = Rc<RefCell<Solver>>;
pub type SolverResult<T> = Result<T, String>;

struct Variable {
    domain: StateSparseSet,
    name: Option<String>,
    on_fix: StateStack<ConstraintId>,
    on_domain_change: StateStack<ConstraintId>,
    on_bound_change: StateStack<ConstraintId>,
}

#[derive(Clone)]
enum ConstraintKind {
    NotEqual {
        x: VariableId,
        y: VariableId,
        offset: i64,
    },
    Equal {
        x: VariableId,
        y: VariableId,
    },
}

struct Constraint {
    kind: ConstraintKind,
    active: StateInt,
    scheduled: bool,
    posted: bool,
}

pub struct Solver {
    pub state_manager: SharedStateManager,
    variables: Vec<Variable>,
    constraints: Vec<Constraint>,
    queue: VecDeque<ConstraintId>,
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

    pub fn new_variable(
        &mut self,
        minimum: i64,
        maximum: i64,
        name: Option<String>,
    ) -> SolverResult<VariableId> {
        let domain = StateSparseSet::new(self.state_manager.clone(), minimum, maximum)
            .map_err(|error| error.to_string())?;
        let id = self.variables.len();
        self.variables.push(Variable {
            domain,
            name,
            on_fix: StateStack::new(self.state_manager.clone()),
            on_domain_change: StateStack::new(self.state_manager.clone()),
            on_bound_change: StateStack::new(self.state_manager.clone()),
        });
        Ok(id)
    }

    pub fn new_not_equal(&mut self, x: VariableId, y: VariableId, offset: i64) -> ConstraintId {
        self.new_constraint(ConstraintKind::NotEqual { x, y, offset })
    }

    pub fn new_equal(&mut self, x: VariableId, y: VariableId) -> ConstraintId {
        self.new_constraint(ConstraintKind::Equal { x, y })
    }

    fn new_constraint(&mut self, kind: ConstraintKind) -> ConstraintId {
        let id = self.constraints.len();
        self.constraints.push(Constraint {
            kind,
            active: StateInt::new(self.state_manager.clone(), 1),
            scheduled: false,
            posted: false,
        });
        id
    }

    pub fn post(&mut self, constraint: ConstraintId) -> SolverResult<()> {
        if self.constraints[constraint].posted {
            return Err("constraint has already been posted".into());
        }
        self.constraints[constraint].posted = true;
        match self.constraints[constraint].kind.clone() {
            ConstraintKind::NotEqual { x, y, .. } => {
                if self.is_fixed(x) || self.is_fixed(y) {
                    self.propagate(constraint)?;
                } else {
                    self.variables[x].on_fix.push(constraint);
                    self.variables[y].on_fix.push(constraint);
                }
            }
            ConstraintKind::Equal { x, y } => {
                if !self.is_fixed(x) && !self.is_fixed(y) {
                    self.variables[x].on_domain_change.push(constraint);
                    self.variables[y].on_domain_change.push(constraint);
                }
                self.propagate(constraint)?;
            }
        }
        self.fix_point()
    }

    pub fn fix_point(&mut self) -> SolverResult<()> {
        while let Some(constraint) = self.queue.pop_front() {
            self.constraints[constraint].scheduled = false;
            if self.constraints[constraint].active.value() != 0 {
                if let Err(error) = self.propagate(constraint) {
                    self.clear_queue();
                    return Err(error);
                }
            }
        }
        Ok(())
    }

    fn propagate(&mut self, constraint: ConstraintId) -> SolverResult<()> {
        match self.constraints[constraint].kind.clone() {
            ConstraintKind::NotEqual { x, y, offset } => {
                if self.is_fixed(x) {
                    self.remove(y, self.value(x)? - offset)?;
                    self.deactivate(constraint);
                } else if self.is_fixed(y) {
                    self.remove(x, self.value(y)? + offset)?;
                    self.deactivate(constraint);
                }
            }
            ConstraintKind::Equal { x, y } => {
                if self.is_fixed(x) {
                    self.fix(y, self.value(x)?)?;
                    self.deactivate(constraint);
                } else if self.is_fixed(y) {
                    self.fix(x, self.value(y)?)?;
                    self.deactivate(constraint);
                } else {
                    let right: HashSet<_> = self.values(y).into_iter().collect();
                    for value in self.values(x) {
                        if !right.contains(&value) {
                            self.remove(x, value)?;
                        }
                    }
                    let left: HashSet<_> = self.values(x).into_iter().collect();
                    for value in self.values(y) {
                        if !left.contains(&value) {
                            self.remove(y, value)?;
                        }
                    }
                    if self.is_fixed(x) {
                        self.fix(y, self.value(x)?)?;
                        self.deactivate(constraint);
                    } else if self.is_fixed(y) {
                        self.fix(x, self.value(y)?)?;
                        self.deactivate(constraint);
                    }
                }
            }
        }
        Ok(())
    }

    fn deactivate(&mut self, constraint: ConstraintId) {
        self.constraints[constraint].active.set(0);
    }

    fn schedule(&mut self, constraint: ConstraintId) {
        let data = &mut self.constraints[constraint];
        if data.active.value() != 0 && !data.scheduled {
            data.scheduled = true;
            self.queue.push_back(constraint);
        }
    }

    fn clear_queue(&mut self) {
        while let Some(constraint) = self.queue.pop_front() {
            self.constraints[constraint].scheduled = false;
        }
    }

    pub fn min(&self, variable: VariableId) -> i64 {
        self.variables[variable]
            .domain
            .min()
            .expect("non-empty domain")
    }
    pub fn max(&self, variable: VariableId) -> i64 {
        self.variables[variable]
            .domain
            .max()
            .expect("non-empty domain")
    }
    pub fn size(&self, variable: VariableId) -> usize {
        self.variables[variable].domain.size()
    }
    pub fn is_fixed(&self, variable: VariableId) -> bool {
        self.size(variable) == 1
    }
    pub fn value(&self, variable: VariableId) -> SolverResult<i64> {
        self.is_fixed(variable)
            .then(|| self.min(variable))
            .ok_or_else(|| "variable is not fixed".into())
    }
    pub fn values(&self, variable: VariableId) -> Vec<i64> {
        self.variables[variable].domain.values().collect()
    }
    pub fn contains(&self, variable: VariableId, value: i64) -> bool {
        self.variables[variable].domain.contains(value)
    }

    pub fn remove(&mut self, variable: VariableId, value: i64) -> SolverResult<()> {
        if !self.contains(variable, value) {
            return Ok(());
        }
        let (old_size, old_min, old_max) =
            (self.size(variable), self.min(variable), self.max(variable));
        self.variables[variable].domain.remove(value);
        if self.size(variable) == 0 {
            return Err(format!("removing {value} emptied {}", self.label(variable)));
        }
        self.notify_change(variable, old_size, old_min, old_max);
        Ok(())
    }

    pub fn fix(&mut self, variable: VariableId, value: i64) -> SolverResult<()> {
        if !self.contains(variable, value) {
            return Err(format!(
                "cannot fix {} to absent value {value}",
                self.label(variable)
            ));
        }
        if self.is_fixed(variable) {
            return Ok(());
        }
        let (old_size, old_min, old_max) =
            (self.size(variable), self.min(variable), self.max(variable));
        for candidate in self.values(variable) {
            if candidate != value {
                self.variables[variable].domain.remove(candidate);
            }
        }
        self.notify_change(variable, old_size, old_min, old_max);
        Ok(())
    }

    pub fn remove_below(&mut self, variable: VariableId, value: i64) -> SolverResult<()> {
        let (old_size, old_min, old_max) =
            (self.size(variable), self.min(variable), self.max(variable));
        if !self.variables[variable].domain.remove_below(value) {
            return Ok(());
        }
        if self.size(variable) == 0 {
            return Err(format!(
                "removing values below {value} emptied {}",
                self.label(variable)
            ));
        }
        self.notify_change(variable, old_size, old_min, old_max);
        Ok(())
    }

    pub fn remove_above(&mut self, variable: VariableId, value: i64) -> SolverResult<()> {
        let (old_size, old_min, old_max) =
            (self.size(variable), self.min(variable), self.max(variable));
        if !self.variables[variable].domain.remove_above(value) {
            return Ok(());
        }
        if self.size(variable) == 0 {
            return Err(format!(
                "removing values above {value} emptied {}",
                self.label(variable)
            ));
        }
        self.notify_change(variable, old_size, old_min, old_max);
        Ok(())
    }

    fn notify_change(&mut self, variable: VariableId, old_size: usize, old_min: i64, old_max: i64) {
        let mut listeners = self.variables[variable].on_domain_change.values();
        if self.min(variable) != old_min || self.max(variable) != old_max {
            listeners.extend(self.variables[variable].on_bound_change.values());
        }
        if old_size > 1 && self.is_fixed(variable) {
            listeners.extend(self.variables[variable].on_fix.values());
        }
        for constraint in listeners {
            self.schedule(constraint);
        }
    }

    pub fn name(&self, variable: VariableId) -> Option<&str> {
        self.variables[variable].name.as_deref()
    }
    fn label(&self, variable: VariableId) -> &str {
        self.name(variable).unwrap_or("IntVar")
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
            let c = inner.new_not_equal(x, y, 0);
            inner.post(c).unwrap();
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
        let c = inner.new_equal(x, y);
        inner.post(c).unwrap();
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
