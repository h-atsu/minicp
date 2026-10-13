use super::ConstraintKind;
use crate::solver::{ConstraintId, Solver, SolverResult, VariableId};
use std::collections::HashSet;

impl Solver {
    pub fn new_element(&mut self, values: Vec<i64>, index: VariableId) -> SolverResult<VariableId> {
        if values.is_empty() {
            return Err("element requires at least one value".into());
        }
        let result = self.new_variable(
            *values.iter().min().unwrap(),
            *values.iter().max().unwrap(),
            None,
        )?;
        let constraint = self.new_constraint(ConstraintKind::Element {
            values,
            index,
            result,
        });
        self.post(constraint)?;
        Ok(result)
    }
}

pub(super) fn post(
    solver: &mut Solver,
    constraint: ConstraintId,
    values: &[i64],
    index: VariableId,
    result: VariableId,
) -> SolverResult<()> {
    solver.variables[index].on_domain_change.push(constraint);
    solver.variables[result].on_domain_change.push(constraint);
    solver.remove_below(index, 0)?;
    solver.remove_above(index, values.len() as i64 - 1)?;
    propagate(solver, constraint, values, index, result)
}

pub(super) fn propagate(
    solver: &mut Solver,
    constraint: ConstraintId,
    values: &[i64],
    index: VariableId,
    result: VariableId,
) -> SolverResult<()> {
    if solver.is_fixed(index) {
        solver.fix(result, values[solver.value(index)? as usize])?;
        solver.deactivate(constraint);
        return Ok(());
    }
    for position in solver.values(index) {
        if !solver.contains(result, values[position as usize]) {
            solver.remove(index, position)?;
        }
    }
    if solver.is_fixed(index) {
        solver.fix(result, values[solver.value(index)? as usize])?;
        solver.deactivate(constraint);
        return Ok(());
    }
    let supported: HashSet<_> = solver
        .values(index)
        .into_iter()
        .map(|position| values[position as usize])
        .collect();
    for value in solver.values(result) {
        if !supported.contains(&value) {
            solver.remove(result, value)?;
        }
    }
    if solver.is_fixed(result) {
        solver.deactivate(constraint);
    }
    Ok(())
}
