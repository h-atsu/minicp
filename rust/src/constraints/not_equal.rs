use super::ConstraintKind;
use crate::solver::{ConstraintId, Solver, SolverResult, VariableId};

impl Solver {
    pub fn new_not_equal(&mut self, x: VariableId, y: VariableId, offset: i64) -> ConstraintId {
        self.new_constraint(ConstraintKind::NotEqual { x, y, offset })
    }
}

pub(super) fn post(
    solver: &mut Solver,
    constraint: ConstraintId,
    x: VariableId,
    y: VariableId,
    offset: i64,
) -> SolverResult<()> {
    if solver.is_fixed(x) || solver.is_fixed(y) {
        propagate(solver, constraint, x, y, offset)
    } else {
        solver.variables[x].on_fix.push(constraint);
        solver.variables[y].on_fix.push(constraint);
        Ok(())
    }
}

pub(super) fn propagate(
    solver: &mut Solver,
    constraint: ConstraintId,
    x: VariableId,
    y: VariableId,
    offset: i64,
) -> SolverResult<()> {
    if solver.is_fixed(x) {
        solver.remove(y, solver.value(x)? - offset)?;
        solver.deactivate(constraint);
    } else if solver.is_fixed(y) {
        solver.remove(x, solver.value(y)? + offset)?;
        solver.deactivate(constraint);
    }
    Ok(())
}
