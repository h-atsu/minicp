use std::error::Error;
use std::fmt::{Display, Formatter};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SparseSetError {
    InvalidBounds,
    DomainTooLarge,
}

impl Display for SparseSetError {
    fn fmt(&self, formatter: &mut Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::InvalidBounds => {
                write!(formatter, "minimum must be less than or equal to maximum")
            }
            Self::DomainTooLarge => write!(formatter, "domain is too large"),
        }
    }
}

impl Error for SparseSetError {}

pub struct SparseSet {
    values: Vec<usize>,
    indices: Vec<usize>,
    size: usize,
    min: usize,
    max: usize,
    offset: i64,
}

impl SparseSet {
    pub fn new(minimum: i64, maximum: i64) -> Result<Self, SparseSetError> {
        if minimum > maximum {
            return Err(SparseSetError::InvalidBounds);
        }

        let length = i128::from(maximum) - i128::from(minimum) + 1;
        let size = usize::try_from(length).map_err(|_| SparseSetError::DomainTooLarge)?;
        let values = (0..size).collect();
        let indices = (0..size).collect();

        Ok(Self {
            values,
            indices,
            size,
            min: 0,
            max: size - 1,
            offset: minimum,
        })
    }

    pub fn size(&self) -> usize {
        self.size
    }

    pub fn min(&self) -> Option<i64> {
        (self.size > 0).then(|| self.denormalize(self.min))
    }

    pub fn max(&self) -> Option<i64> {
        (self.size > 0).then(|| self.denormalize(self.max))
    }

    pub fn contains(&self, value: i64) -> bool {
        let Some(value) = self.normalize(value) else {
            return false;
        };
        self.contains_normalized(value)
    }

    pub fn remove(&mut self, value: i64) -> bool {
        let Some(value) = self.normalize(value) else {
            return false;
        };
        if !self.contains_normalized(value) {
            return false;
        }

        let last = self.values[self.size - 1];
        self.exchange_positions(value, last);
        self.size -= 1;

        if self.size > 0 {
            if value == self.min {
                self.min = (value + 1..=self.max)
                    .find(|candidate| self.contains_normalized(*candidate))
                    .expect("a non-empty set has a minimum");
            }
            if value == self.max {
                self.max = (self.min..value)
                    .rev()
                    .find(|candidate| self.contains_normalized(*candidate))
                    .expect("a non-empty set has a maximum");
            }
        }

        true
    }

    pub fn values(&self) -> impl Iterator<Item = i64> + '_ {
        self.values[..self.size]
            .iter()
            .map(|value| self.denormalize(*value))
    }

    fn normalize(&self, value: i64) -> Option<usize> {
        let normalized = value.checked_sub(self.offset)?;
        let normalized = usize::try_from(normalized).ok()?;
        (normalized < self.values.len()).then_some(normalized)
    }

    fn denormalize(&self, value: usize) -> i64 {
        let value = i128::try_from(value).expect("usize always fits in i128");
        i64::try_from(value + i128::from(self.offset))
            .expect("normalized domain values originated as i64")
    }

    fn contains_normalized(&self, value: usize) -> bool {
        self.indices[value] < self.size
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
    use super::{SparseSet, SparseSetError};

    #[test]
    fn rejects_invalid_bounds() {
        let result = SparseSet::new(2, 1);

        assert!(matches!(result, Err(SparseSetError::InvalidBounds)));
    }

    #[test]
    fn removes_values_and_updates_bounds() {
        let mut sparse_set = SparseSet::new(2, 6).unwrap();

        assert!(sparse_set.remove(2));
        assert!(sparse_set.remove(4));
        assert!(sparse_set.remove(6));

        assert_eq!(sparse_set.size(), 2);
        assert_eq!(sparse_set.min(), Some(3));
        assert_eq!(sparse_set.max(), Some(5));
        assert_eq!(sparse_set.values().collect::<Vec<_>>(), vec![5, 3]);
    }

    #[test]
    fn empty_set_has_no_bounds() {
        let mut sparse_set = SparseSet::new(-1, -1).unwrap();

        assert!(sparse_set.remove(-1));

        assert_eq!(sparse_set.min(), None);
        assert_eq!(sparse_set.max(), None);
    }
}
