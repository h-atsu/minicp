//! Constraint arena entries and propagation dispatch.

mod all_different;
mod circuit;
mod element;
mod equal;
mod not_equal;
mod sum;

use crate::solver::{ConstraintId, Solver, SolverResult, VariableId};
use crate::state::StateInt;

#[derive(Clone)]
pub(crate) enum ConstraintKind {
    NotEqual {
        x: VariableId,
        y: VariableId,
        offset: i64,
    },
    Equal {
        x: VariableId,
        y: VariableId,
    },
    AllDifferent {
        variables: Vec<VariableId>,
    },
    Circuit {
        variables: Vec<VariableId>,
        destination: Vec<StateInt>,
        origin: Vec<StateInt>,
        length: Vec<StateInt>,
        processed: Vec<StateInt>,
    },
    Element {
        values: Vec<i64>,
        index: VariableId,
        result: VariableId,
    },
    Sum {
        terms: Vec<(VariableId, i64)>,
    },
}

pub(crate) struct Constraint {
    pub(crate) kind: ConstraintKind,
    pub(crate) active: StateInt,
    pub(crate) scheduled: bool,
    pub(crate) posted: bool,
}

impl Solver {
    pub fn post(&mut self, constraint: ConstraintId) -> SolverResult<()> {
        if self.constraints[constraint].posted {
            return Err("constraint has already been posted".into());
        }
        self.constraints[constraint].posted = true;
        match self.constraints[constraint].kind.clone() {
            ConstraintKind::NotEqual { x, y, offset } => {
                not_equal::post(self, constraint, x, y, offset)?
            }
            ConstraintKind::Equal { x, y } => equal::post(self, constraint, x, y)?,
            ConstraintKind::AllDifferent { variables } => {
                all_different::post(self, constraint, &variables)?
            }
            ConstraintKind::Circuit { variables, .. } => {
                circuit::post(self, constraint, variables)?
            }
            ConstraintKind::Element {
                values,
                index,
                result,
            } => element::post(self, constraint, &values, index, result)?,
            ConstraintKind::Sum { terms } => sum::post(self, constraint, &terms)?,
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
                not_equal::propagate(self, constraint, x, y, offset)
            }
            ConstraintKind::Equal { x, y } => equal::propagate(self, constraint, x, y),
            ConstraintKind::AllDifferent { variables } => {
                all_different::propagate(self, constraint, &variables)
            }
            ConstraintKind::Circuit {
                variables,
                destination,
                origin,
                length,
                processed,
            } => circuit::propagate(
                self,
                constraint,
                &variables,
                &destination,
                &origin,
                &length,
                &processed,
            ),
            ConstraintKind::Element {
                values,
                index,
                result,
            } => element::propagate(self, constraint, &values, index, result),
            ConstraintKind::Sum { terms } => sum::propagate(self, constraint, &terms),
        }
    }
}
