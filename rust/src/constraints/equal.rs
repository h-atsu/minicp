use std::collections::HashSet;

use super::ConstraintKind;
use crate::solver::{ConstraintId, Solver, SolverResult, VariableId};

impl Solver {
    pub fn new_equal(&mut self, x: VariableId, y: VariableId) -> ConstraintId {
        self.new_constraint(ConstraintKind::Equal { x, y })
    }
}

pub(super) fn post(
    solver: &mut Solver,
    constraint: ConstraintId,
    x: VariableId,
    y: VariableId,
) -> SolverResult<()> {
    if !solver.is_fixed(x) && !solver.is_fixed(y) {
        solver.variables[x].on_domain_change.push(constraint);
        solver.variables[y].on_domain_change.push(constraint);
    }
    propagate(solver, constraint, x, y)
}

pub(super) fn propagate(
    solver: &mut Solver,
    constraint: ConstraintId,
    x: VariableId,
    y: VariableId,
) -> SolverResult<()> {
    if solver.is_fixed(x) {
        solver.fix(y, solver.value(x)?)?;
        solver.deactivate(constraint);
        return Ok(());
    }
    if solver.is_fixed(y) {
        solver.fix(x, solver.value(y)?)?;
        solver.deactivate(constraint);
        return Ok(());
    }
    let right: HashSet<_> = solver.values(y).into_iter().collect();
    for value in solver.values(x) {
        if !right.contains(&value) {
            solver.remove(x, value)?;
        }
    }
    let left: HashSet<_> = solver.values(x).into_iter().collect();
    for value in solver.values(y) {
        if !left.contains(&value) {
            solver.remove(y, value)?;
        }
    }
    if solver.is_fixed(x) {
        solver.fix(y, solver.value(x)?)?;
        solver.deactivate(constraint);
    } else if solver.is_fixed(y) {
        solver.fix(x, solver.value(y)?)?;
        solver.deactivate(constraint);
    }
    Ok(())
}
