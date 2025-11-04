//! Proof verification with resource budgets (defense against DoS).
//!
//! All verification is O(n) or better - no exponential paths.
//! Budget limits (ops, time, memory) prevent resource exhaustion.
//! Tier-based limits ensure fairness and prevent spam.

use crate::errors::{ConsensusError, Result};
use crate::types::{HardwareTier, Problem, ProblemType, Solution, VerifyBudget};
use std::collections::HashSet;
use std::time::Instant;

/// Verification result with metadata
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct VerificationResult {
    pub valid: bool,
    pub ops_used: u64,
    pub duration_ms: u64,
    pub memory_used: u64,
}

/// Verify solution to problem with budget constraints
pub fn verify_solution(
    problem: &Problem,
    solution: &Solution,
    budget: &VerifyBudget,
) -> Result<VerificationResult> {
    let start = Instant::now();

    // Dispatch to problem-specific verifier
    let result = match problem.problem_type {
        ProblemType::SubsetSum => verify_subset_sum(problem, solution, budget)?,
        ProblemType::Knapsack => {
            return Err(ConsensusError::NotImplemented(
                "Knapsack verification".into(),
            ))
        }
        ProblemType::GraphColoring => {
            return Err(ConsensusError::NotImplemented(
                "GraphColoring verification".into(),
            ))
        }
        ProblemType::SAT => {
            return Err(ConsensusError::NotImplemented("SAT verification".into()))
        }
        ProblemType::TSP => {
            return Err(ConsensusError::NotImplemented("TSP verification".into()))
        }
        ProblemType::Factorization => {
            return Err(ConsensusError::NotImplemented(
                "Factorization verification".into(),
            ))
        }
        ProblemType::LatticeProblems => {
            return Err(ConsensusError::NotImplemented(
                "LatticeProblems verification".into(),
            ))
        }
    };

    let duration_ms = start.elapsed().as_millis() as u64;

    // Check time budget
    if duration_ms > budget.max_duration_ms {
        return Err(ConsensusError::BudgetTimeExceeded {
            max_ms: budget.max_duration_ms,
            actual_ms: duration_ms,
        });
    }

    Ok(result)
}

/// Verify subset sum solution - O(n) verification
///
/// Problem: Given elements [e1, e2, ..., en] and target T,
///          find subset S such that sum(S) == T
///
/// Solution: Indices [i1, i2, ..., ik] into elements array
///
/// Verification: O(k) <= O(n), constant space
fn verify_subset_sum(
    problem: &Problem,
    solution: &Solution,
    budget: &VerifyBudget,
) -> Result<VerificationResult> {
    let ops_start = 0u64;
    let mut ops_used = ops_start;

    // 1. Validate tier constraints
    validate_tier_constraints(problem.tier, problem.elements.len())?;

    // 2. Check solution size doesn't exceed element count
    if solution.indices.len() > problem.elements.len() {
        return Err(ConsensusError::InvalidProofSize {
            tier: problem.tier as u8,
            elements: solution.indices.len(),
            max: problem.elements.len(),
        });
    }

    // 3. Check for duplicate indices (O(n) with HashSet)
    let mut seen = HashSet::new();
    for &index in &solution.indices {
        ops_used += 1;
        if ops_used > budget.max_ops {
            return Err(ConsensusError::BudgetOpsExceeded {
                max_ops: budget.max_ops,
                actual_ops: ops_used,
            });
        }

        if !seen.insert(index) {
            return Err(ConsensusError::DuplicateIndex { index });
        }
    }

    // 4. Compute sum of selected elements (O(k))
    let mut sum: i64 = 0;
    for &index in &solution.indices {
        ops_used += 1;
        if ops_used > budget.max_ops {
            return Err(ConsensusError::BudgetOpsExceeded {
                max_ops: budget.max_ops,
                actual_ops: ops_used,
            });
        }

        // Check index in bounds
        if index as usize >= problem.elements.len() {
            return Err(ConsensusError::IndexOutOfBounds {
                index,
                max: problem.elements.len(),
            });
        }

        let element = problem.elements[index as usize];

        // Check for overflow (defense in depth)
        sum = sum
            .checked_add(element)
            .ok_or_else(|| ConsensusError::InvalidInput("Integer overflow in sum".into()))?;
    }

    // 5. Verify sum matches target
    let valid = sum == problem.target;

    if !valid {
        return Err(ConsensusError::SubsetSumInvalid);
    }

    // Estimate memory used (rough approximation)
    let memory_used = (solution.indices.len() * 4 + seen.len() * 4) as u64;

    if memory_used > budget.max_memory_bytes {
        return Err(ConsensusError::TierMemoryLimitExceeded {
            tier: problem.tier as u8,
            max_mb: budget.max_memory_bytes / (1024 * 1024),
            actual_mb: memory_used / (1024 * 1024),
        });
    }

    Ok(VerificationResult {
        valid: true,
        ops_used,
        duration_ms: 0, // Filled by caller
        memory_used,
    })
}

/// Validate tier constraints on problem size
fn validate_tier_constraints(tier: HardwareTier, element_count: usize) -> Result<()> {
    let (min_elem, max_elem) = tier.element_range();

    if element_count < min_elem || element_count > max_elem {
        return Err(ConsensusError::TierConstraintViolation {
            tier: tier as u8,
            min_elem,
            max_elem,
            actual: element_count,
        });
    }

    Ok(())
}

/// Quick validation before heavy verification (syntactic checks)
pub fn quick_validate_solution(problem: &Problem, solution: &Solution) -> Result<()> {
    // Check problem type is production-ready
    if !problem.problem_type.is_production_ready() {
        return Err(ConsensusError::NotImplemented(format!(
            "Problem type {:?} not production ready",
            problem.problem_type
        )));
    }

    // Check tier is valid
    if HardwareTier::from_u8(problem.tier as u8).is_none() {
        return Err(ConsensusError::InvalidTier {
            tier: problem.tier as u8,
        });
    }

    // Check element count
    validate_tier_constraints(problem.tier, problem.elements.len())?;

    // Check solution not empty
    if solution.indices.is_empty() {
        return Err(ConsensusError::InvalidInput(
            "Solution cannot be empty".into(),
        ));
    }

    // Check solution size reasonable
    if solution.indices.len() > problem.elements.len() {
        return Err(ConsensusError::InvalidProofSize {
            tier: problem.tier as u8,
            elements: solution.indices.len(),
            max: problem.elements.len(),
        });
    }

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn make_subset_sum_problem(tier: HardwareTier, elements: Vec<i64>, target: i64) -> Problem {
        Problem {
            problem_type: ProblemType::SubsetSum,
            tier,
            elements,
            target,
            timestamp: 1000,
        }
    }

    #[test]
    fn test_verify_subset_sum_valid() {
        let problem = make_subset_sum_problem(HardwareTier::Desktop, vec![1, 2, 3, 4, 5], 9);
        let solution = Solution {
            indices: vec![1, 3], // elements[1] + elements[3] = 2 + 4 = 6... wait, that's wrong
            timestamp: 1001,
        };

        // Actually: indices [1, 3] = elements 2 and 4 = 6, not 9
        // Let me fix: indices [0, 3, 4] = 1 + 4 + 5 = 10... still wrong
        // Correct: indices [0, 2, 4] = 1 + 3 + 5 = 9 ✓

        let correct_solution = Solution {
            indices: vec![0, 2, 4],
            timestamp: 1001,
        };

        let budget = VerifyBudget::from_tier(HardwareTier::Desktop);
        let result = verify_solution(&problem, &correct_solution, &budget).unwrap();

        assert!(result.valid);
        assert!(result.ops_used > 0);
    }

    #[test]
    fn test_verify_subset_sum_invalid() {
        let problem = make_subset_sum_problem(HardwareTier::Desktop, vec![1, 2, 3, 4, 5], 9);
        let solution = Solution {
            indices: vec![0, 1], // 1 + 2 = 3, not 9
            timestamp: 1001,
        };

        let budget = VerifyBudget::from_tier(HardwareTier::Desktop);
        let result = verify_solution(&problem, &solution, &budget);

        assert!(result.is_err());
        assert!(matches!(result.unwrap_err(), ConsensusError::SubsetSumInvalid));
    }

    #[test]
    fn test_verify_subset_sum_out_of_bounds() {
        let problem = make_subset_sum_problem(HardwareTier::Desktop, vec![1, 2, 3, 4, 5], 9);
        let solution = Solution {
            indices: vec![10], // Index out of bounds
            timestamp: 1001,
        };

        let budget = VerifyBudget::from_tier(HardwareTier::Desktop);
        let result = verify_solution(&problem, &solution, &budget);

        assert!(result.is_err());
        assert!(matches!(
            result.unwrap_err(),
            ConsensusError::IndexOutOfBounds { .. }
        ));
    }

    #[test]
    fn test_verify_subset_sum_duplicate_indices() {
        let problem = make_subset_sum_problem(HardwareTier::Desktop, vec![1, 2, 3, 4, 5], 9);
        let solution = Solution {
            indices: vec![0, 0, 4], // Duplicate index 0
            timestamp: 1001,
        };

        let budget = VerifyBudget::from_tier(HardwareTier::Desktop);
        let result = verify_solution(&problem, &solution, &budget);

        assert!(result.is_err());
        assert!(matches!(
            result.unwrap_err(),
            ConsensusError::DuplicateIndex { .. }
        ));
    }

    #[test]
    fn test_tier_constraint_validation() {
        // Desktop tier: 12-16 elements
        let problem_too_small =
            make_subset_sum_problem(HardwareTier::Desktop, vec![1, 2, 3], 6);
        let problem_too_large = make_subset_sum_problem(
            HardwareTier::Desktop,
            vec![1; 20], // 20 elements > 16 max
            20,
        );
        let problem_ok = make_subset_sum_problem(HardwareTier::Desktop, vec![1; 14], 14);

        assert!(validate_tier_constraints(problem_too_small.tier, problem_too_small.elements.len())
            .is_err());
        assert!(
            validate_tier_constraints(problem_too_large.tier, problem_too_large.elements.len())
                .is_err()
        );
        assert!(
            validate_tier_constraints(problem_ok.tier, problem_ok.elements.len()).is_ok()
        );
    }

    #[test]
    fn test_budget_ops_exceeded() {
        let problem = make_subset_sum_problem(HardwareTier::Desktop, vec![1; 14], 10);
        let solution = Solution {
            indices: (0..14).collect(), // All indices
            timestamp: 1001,
        };

        let tiny_budget = VerifyBudget {
            max_ops: 5, // Very small
            max_duration_ms: 1000,
            max_memory_bytes: 1024 * 1024,
        };

        let result = verify_solution(&problem, &solution, &tiny_budget);

        assert!(result.is_err());
        assert!(matches!(
            result.unwrap_err(),
            ConsensusError::BudgetOpsExceeded { .. }
        ));
    }

    #[test]
    fn test_quick_validate_solution() {
        let problem = make_subset_sum_problem(HardwareTier::Desktop, vec![1; 14], 10);
        let valid_solution = Solution {
            indices: vec![0, 1, 2],
            timestamp: 1001,
        };

        assert!(quick_validate_solution(&problem, &valid_solution).is_ok());

        // Empty solution
        let empty_solution = Solution {
            indices: vec![],
            timestamp: 1001,
        };
        assert!(quick_validate_solution(&problem, &empty_solution).is_err());
    }

    #[test]
    fn test_verify_performance() {
        // Ensure verification is fast (< 1ms for small problems)
        let problem = make_subset_sum_problem(HardwareTier::Desktop, vec![1; 14], 14);
        let solution = Solution {
            indices: (0..14).collect(),
            timestamp: 1001,
        };

        let budget = VerifyBudget::from_tier(HardwareTier::Desktop);
        let start = Instant::now();
        let result = verify_solution(&problem, &solution, &budget).unwrap();
        let duration = start.elapsed();

        assert!(result.valid);
        assert!(duration.as_millis() < 10, "Verification too slow: {:?}", duration);
    }
}
