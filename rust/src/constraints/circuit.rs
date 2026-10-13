use super::ConstraintKind;
use crate::solver::{ConstraintId, Solver, SolverResult, VariableId};
use crate::state::StateInt;

impl Solver {
    pub fn new_circuit(&mut self, variables: Vec<VariableId>) -> SolverResult<ConstraintId> {
        if variables.len() < 2 {
            return Err("circuit requires at least two successors".into());
        }
        let count = variables.len();
        let make = |values: Vec<i64>| {
            values
                .into_iter()
                .map(|value| StateInt::new(self.state_manager.clone(), value))
                .collect()
        };
        Ok(self.new_constraint(ConstraintKind::Circuit {
            variables,
            destination: make((0..count as i64).collect()),
            origin: make((0..count as i64).collect()),
            length: make(vec![0; count]),
            processed: make(vec![0; count]),
        }))
    }
}

pub(super) fn post(
    solver: &mut Solver,
    constraint: ConstraintId,
    variables: Vec<VariableId>,
) -> SolverResult<()> {
    let count = variables.len() as i64;
    for (node, variable) in variables.iter().copied().enumerate() {
        solver.remove_below(variable, 0)?;
        solver.remove_above(variable, count - 1)?;
        solver.remove(variable, node as i64)?;
        solver.variables[variable].on_fix.push(constraint);
    }
    let all_different = solver.new_all_different(variables)?;
    solver.post(all_different)?;
    let kind = solver.constraints[constraint].kind.clone();
    if let ConstraintKind::Circuit {
        variables,
        destination,
        origin,
        length,
        processed,
    } = kind
    {
        propagate(
            solver,
            constraint,
            &variables,
            &destination,
            &origin,
            &length,
            &processed,
        )
    } else {
        unreachable!()
    }
}

pub(super) fn propagate(
    solver: &mut Solver,
    constraint: ConstraintId,
    variables: &[VariableId],
    destination: &[StateInt],
    origin: &[StateInt],
    length: &[StateInt],
    processed: &[StateInt],
) -> SolverResult<()> {
    for (node, variable) in variables.iter().copied().enumerate() {
        if solver.is_fixed(variable) && processed[node].value() == 0 {
            let successor = solver.value(variable)? as usize;
            let path_origin = origin[node].value() as usize;
            let path_destination = destination[successor].value() as usize;
            let path_length = length[path_origin].value() + length[successor].value() + 1;
            destination[path_origin].set(path_destination as i64);
            origin[path_destination].set(path_origin as i64);
            length[path_origin].set(path_length);
            processed[node].set(1);
            if path_length < variables.len() as i64 - 1 {
                solver.remove(variables[path_destination], path_origin as i64)?;
            }
        }
    }
    if variables.iter().all(|variable| solver.is_fixed(*variable)) {
        solver.deactivate(constraint);
    }
    Ok(())
}
