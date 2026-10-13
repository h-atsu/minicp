//! Reversible sparse set using reversible size and bounds.

use crate::sparse_set::SparseSetError;
use crate::state::{SharedStateManager, StateInt};

pub struct StateSparseSet {
    values: Vec<usize>,
    indices: Vec<usize>,
    size: StateInt,
    min: StateInt,
    max: StateInt,
    offset: i64,
}

impl StateSparseSet {
    pub fn new(
        manager: SharedStateManager,
        minimum: i64,
        maximum: i64,
    ) -> Result<Self, SparseSetError> {
        if minimum > maximum {
            return Err(SparseSetError::InvalidBounds);
        }

        let length = i128::from(maximum) - i128::from(minimum) + 1;
        let length = usize::try_from(length).map_err(|_| SparseSetError::DomainTooLarge)?;
        let reversible_length =
            i64::try_from(length).map_err(|_| SparseSetError::DomainTooLarge)?;

        Ok(Self {
            values: (0..length).collect(),
            indices: (0..length).collect(),
            size: StateInt::new(manager.clone(), reversible_length),
            min: StateInt::new(manager.clone(), 0),
            max: StateInt::new(manager, reversible_length - 1),
            offset: minimum,
        })
    }

    pub fn size(&self) -> usize {
        usize::try_from(self.size.value()).expect("size is non-negative")
    }

    pub fn min(&self) -> Option<i64> {
        (self.size() > 0).then(|| self.denormalize(self.min.value() as usize))
    }

    pub fn max(&self) -> Option<i64> {
        (self.size() > 0).then(|| self.denormalize(self.max.value() as usize))
    }

    pub fn contains(&self, value: i64) -> bool {
        self.normalize(value)
            .is_some_and(|value| self.contains_normalized(value))
    }

    pub fn remove(&mut self, value: i64) -> bool {
        let Some(value) = self.normalize(value) else {
            return false;
        };
        if !self.contains_normalized(value) {
            return false;
        }

        let old_size = self.size();
        let last = self.values[old_size - 1];
        self.exchange_positions(value, last);
        self.size.set((old_size - 1) as i64);

        if old_size > 1 {
            if value == self.min.value() as usize {
                let max = self.max.value() as usize;
                let new_min = (value + 1..=max)
                    .find(|candidate| self.contains_normalized(*candidate))
                    .expect("a non-empty set has a minimum");
                self.min.set(new_min as i64);
            }
            if value == self.max.value() as usize {
                let min = self.min.value() as usize;
                let new_max = (min..value)
                    .rev()
                    .find(|candidate| self.contains_normalized(*candidate))
                    .expect("a non-empty set has a maximum");
                self.max.set(new_max as i64);
            }
        }
        true
    }

    pub fn remove_below(&mut self, bound: i64) -> bool {
        let candidates: Vec<_> = self.values().collect();
        let mut changed = false;
        for candidate in candidates {
            if candidate < bound {
                changed |= self.remove(candidate);
            }
        }
        changed
    }

    pub fn remove_above(&mut self, bound: i64) -> bool {
        let candidates: Vec<_> = self.values().collect();
        let mut changed = false;
        for candidate in candidates {
            if candidate > bound {
                changed |= self.remove(candidate);
            }
        }
        changed
    }

    pub fn values(&self) -> impl Iterator<Item = i64> + '_ {
        self.values[..self.size()]
            .iter()
            .map(|value| self.denormalize(*value))
    }

    fn normalize(&self, value: i64) -> Option<usize> {
        let normalized = value.checked_sub(self.offset)?;
        let normalized = usize::try_from(normalized).ok()?;
        (normalized < self.values.len()).then_some(normalized)
    }

    fn denormalize(&self, value: usize) -> i64 {
        i64::try_from(value as i128 + i128::from(self.offset))
            .expect("normalized domain values originated as i64")
    }

    fn contains_normalized(&self, value: usize) -> bool {
        self.indices[value] < self.size()
    }

    fn exchange_positions(&mut self, first: usize, second: usize) {
        let first_index = self.indices[first];
        let second_index = self.indices[second];
        self.values.swap(first_index, second_index);
        self.indices[first] = second_index;
        self.indices[second] = first_index;
    }
}

#[cfg(test)]
mod tests {
    use super::StateSparseSet;
    use crate::state::StateManager;

    #[test]
    fn restores_values_and_bounds() {
        let manager = StateManager::shared();
        let mut set = StateSparseSet::new(manager.clone(), 2, 6).unwrap();
        manager.borrow_mut().save();
        set.remove(2);
        set.remove(4);
        set.remove(6);
        manager.borrow_mut().restore().unwrap();

        assert_eq!(set.size(), 5);
        assert_eq!(set.min(), Some(2));
        assert_eq!(set.max(), Some(6));
        assert_eq!(
            set.values().collect::<std::collections::HashSet<_>>(),
            (2..=6).collect()
        );
    }
}
