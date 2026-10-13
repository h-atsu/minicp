use super::ConstraintKind;
use crate::algorithms::supported_all_different_edges;
use crate::solver::{ConstraintId, Solver, SolverResult, VariableId};
use crate::variable::VariableView;

impl Solver {
    pub fn new_all_different(&mut self, variables: Vec<VariableId>) -> SolverResult<ConstraintId> {
        self.new_all_different_views(variables.into_iter().map(VariableView::identity).collect())
    }

    pub fn new_all_different_views(
        &mut self,
        variables: Vec<VariableView>,
    ) -> SolverResult<ConstraintId> {
        if variables.is_empty() {
            return Err("all-different requires at least one variable".into());
        }
        Ok(self.new_constraint(ConstraintKind::AllDifferent { variables }))
    }
}

pub(super) fn post(
    solver: &mut Solver,
    constraint: ConstraintId,
    variables: &[VariableView],
) -> SolverResult<()> {
    for view in variables {
        solver.variables[view.variable]
            .on_domain_change
            .push(constraint);
    }
    propagate(solver, constraint, variables)
}

pub(super) fn propagate(
    solver: &mut Solver,
    constraint: ConstraintId,
    variables: &[VariableView],
) -> SolverResult<()> {
    let adjacency: SolverResult<Vec<_>> = variables
        .iter()
        .map(|view| {
            solver
                .values(view.variable)
                .into_iter()
                .map(|value| {
                    value
                        .checked_add(view.offset)
                        .ok_or_else(|| "all-different offset view overflowed i64".to_string())
                })
                .collect()
        })
        .collect();
    let supported = supported_all_different_edges(&adjacency?)
        .ok_or_else(|| "all-different has no matching".to_string())?;
    for (view, supported_values) in variables.iter().zip(supported) {
        for value in solver.values(view.variable) {
            let viewed_value = value
                .checked_add(view.offset)
                .ok_or_else(|| "all-different offset view overflowed i64".to_string())?;
            if !supported_values.contains(&viewed_value) {
                solver.remove(view.variable, value)?;
            }
        }
    }
    if variables.iter().all(|view| solver.is_fixed(view.variable)) {
        solver.deactivate(constraint);
    }
    Ok(())
}
