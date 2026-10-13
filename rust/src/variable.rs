//! Reversible integer variables and event notification.

use crate::solver::{ConstraintId, Solver, SolverResult, VariableId};
use crate::state::StateSparseSet;
use crate::state::StateStack;

#[derive(Clone, Copy)]
pub(crate) struct VariableView {
    pub(crate) variable: VariableId,
    pub(crate) offset: i64,
}

impl VariableView {
    pub(crate) fn identity(variable: VariableId) -> Self {
        Self {
            variable,
            offset: 0,
        }
    }
}

pub(crate) struct Variable {
    pub(crate) domain: StateSparseSet,
    pub(crate) name: Option<String>,
    pub(crate) on_fix: StateStack<ConstraintId>,
    pub(crate) on_domain_change: StateStack<ConstraintId>,
    pub(crate) on_bound_change: StateStack<ConstraintId>,
}

impl Solver {
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
        let previous = (self.size(variable), self.min(variable), self.max(variable));
        self.variables[variable].domain.remove(value);
        if self.size(variable) == 0 {
            return Err(format!("removing {value} emptied {}", self.label(variable)));
        }
        self.notify_change(variable, previous);
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
        let previous = (self.size(variable), self.min(variable), self.max(variable));
        for candidate in self.values(variable) {
            if candidate != value {
                self.variables[variable].domain.remove(candidate);
            }
        }
        self.notify_change(variable, previous);
        Ok(())
    }

    pub fn remove_below(&mut self, variable: VariableId, value: i64) -> SolverResult<()> {
        let previous = (self.size(variable), self.min(variable), self.max(variable));
        if !self.variables[variable].domain.remove_below(value) {
            return Ok(());
        }
        if self.size(variable) == 0 {
            return Err(format!(
                "removing values below {value} emptied {}",
                self.label(variable)
            ));
        }
        self.notify_change(variable, previous);
        Ok(())
    }

    pub fn remove_above(&mut self, variable: VariableId, value: i64) -> SolverResult<()> {
        let previous = (self.size(variable), self.min(variable), self.max(variable));
        if !self.variables[variable].domain.remove_above(value) {
            return Ok(());
        }
        if self.size(variable) == 0 {
            return Err(format!(
                "removing values above {value} emptied {}",
                self.label(variable)
            ));
        }
        self.notify_change(variable, previous);
        Ok(())
    }

    fn notify_change(&mut self, variable: VariableId, previous: (usize, i64, i64)) {
        let (old_size, old_min, old_max) = previous;
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
