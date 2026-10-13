use super::ConstraintKind;
use crate::algorithms::supported_all_different_edges;
use crate::solver::{ConstraintId, Solver, SolverResult, VariableId};

impl Solver {
    pub fn new_all_different(&mut self, variables: Vec<VariableId>) -> SolverResult<ConstraintId> {
        if variables.is_empty() {
            return Err("all-different requires at least one variable".into());
        }
        Ok(self.new_constraint(ConstraintKind::AllDifferent { variables }))
    }
}

pub(super) fn post(
    solver: &mut Solver,
    constraint: ConstraintId,
    variables: &[VariableId],
) -> SolverResult<()> {
    for variable in variables {
        solver.variables[*variable]
            .on_domain_change
            .push(constraint);
    }
    propagate(solver, constraint, variables)
}

pub(super) fn propagate(
    solver: &mut Solver,
    constraint: ConstraintId,
    variables: &[VariableId],
) -> SolverResult<()> {
    let adjacency: Vec<_> = variables
        .iter()
        .map(|variable| solver.values(*variable))
        .collect();
    let supported = supported_all_different_edges(&adjacency)
        .ok_or_else(|| "all-different has no matching".to_string())?;
    for (variable, supported_values) in variables.iter().zip(supported) {
        for value in solver.values(*variable) {
            if !supported_values.contains(&value) {
                solver.remove(*variable, value)?;
            }
        }
    }
    if variables.iter().all(|variable| solver.is_fixed(*variable)) {
        solver.deactivate(constraint);
    }
    Ok(())
}
