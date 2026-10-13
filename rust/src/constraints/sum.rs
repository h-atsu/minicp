use super::ConstraintKind;
use crate::solver::{ConstraintId, Solver, SolverResult, VariableId};

impl Solver {
    pub fn new_sum_variable(&mut self, variables: Vec<VariableId>) -> SolverResult<VariableId> {
        if variables.is_empty() {
            return Err("sum requires at least one variable".into());
        }
        let result = self.new_variable(
            variables.iter().map(|variable| self.min(*variable)).sum(),
            variables.iter().map(|variable| self.max(*variable)).sum(),
            None,
        )?;
        let mut terms: Vec<_> = variables
            .into_iter()
            .map(|variable| (variable, 1))
            .collect();
        terms.push((result, -1));
        let constraint = self.new_constraint(ConstraintKind::Sum { terms });
        self.post(constraint)?;
        Ok(result)
    }
}

pub(super) fn post(
    solver: &mut Solver,
    constraint: ConstraintId,
    terms: &[(VariableId, i64)],
) -> SolverResult<()> {
    for (variable, _) in terms {
        solver.variables[*variable].on_bound_change.push(constraint);
    }
    propagate(solver, constraint, terms)
}

pub(super) fn propagate(
    solver: &mut Solver,
    constraint: ConstraintId,
    terms: &[(VariableId, i64)],
) -> SolverResult<()> {
    let ranges: Vec<_> = terms
        .iter()
        .map(|(variable, coefficient)| {
            if *coefficient == 1 {
                (solver.min(*variable), solver.max(*variable))
            } else {
                (-solver.max(*variable), -solver.min(*variable))
            }
        })
        .collect();
    let sum_min: i64 = ranges.iter().map(|range| range.0).sum();
    let sum_max: i64 = ranges.iter().map(|range| range.1).sum();
    if sum_min > 0 || sum_max < 0 {
        return Err("sum cannot reach its target".into());
    }
    for ((variable, coefficient), (term_min, term_max)) in terms.iter().zip(ranges) {
        let required_min = -(sum_max - term_max);
        let required_max = -(sum_min - term_min);
        if *coefficient == 1 {
            solver.remove_below(*variable, required_min)?;
            solver.remove_above(*variable, required_max)?;
        } else {
            solver.remove_below(*variable, -required_max)?;
            solver.remove_above(*variable, -required_min)?;
        }
    }
    if terms.iter().all(|(variable, _)| solver.is_fixed(*variable)) {
        solver.deactivate(constraint);
    }
    Ok(())
}
