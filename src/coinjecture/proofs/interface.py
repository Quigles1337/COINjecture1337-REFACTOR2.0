"""
Module: proofs.interface
Abstract interface for computational proof solvers.

Defines the contract that all proof-of-work solvers must implement,
enabling pluggable solver backends while maintaining verification guarantees.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from ..types import (
    ProblemTierEnum,
    ProofReveal,
    ComplexityMetrics,
    SolutionHash,
    ValidationError,
)


@dataclass
class ProofInstance:
    """
    Specification of a proof-of-work problem instance.
    Solver-agnostic representation.
    """
    problem_type: str  # e.g., "subset_sum", "sat", "graph_coloring"
    problem_params: Dict[str, Any]  # Problem-specific parameters
    problem_size: int  # Primary size parameter (n)
    tier: ProblemTierEnum  # Resource tier for this problem
    epoch_salt: bytes  # Time-locked epoch salt
    parent_hash: bytes  # Parent block hash for chain continuity


@dataclass
class ProofSolution:
    """
    Candidate solution to a proof instance.
    Contains solution data and metadata for verification.
    """
    solution_data: List[int]  # Solution representation (problem-specific)
    solution_hash: SolutionHash  # H(solution) for commitment
    solve_time_seconds: float  # Measured solve time
    solve_space_bytes: int  # Measured memory usage
    miner_salt: bytes  # Unique salt for commitment binding


@dataclass
class ProofVerificationResult:
    """
    Result of proof verification.
    Includes correctness, performance bounds, and complexity attestation.
    """
    is_valid: bool
    error_message: Optional[str]
    verify_time_seconds: float
    verify_space_bytes: int
    complexity_metrics: Optional[ComplexityMetrics]
    asymmetry_ratio: Optional[float]  # solve_time / verify_time


@dataclass
class ResourceLimits:
    """
    Resource constraints for proof generation/verification.
    Enforced by tier system to prevent DoS.
    """
    max_problem_size: int  # Maximum n
    max_solution_size: int  # Maximum solution length
    max_solve_time_seconds: float  # CPU time limit
    max_verify_time_seconds: float  # Verification time limit
    max_memory_bytes: int  # Memory ceiling
    max_proof_bytes: int  # Serialized proof size limit


class Solver(ABC):
    """
    Abstract base class for computational proof solvers.

    Implementing classes provide concrete algorithms for specific
    problem types (Subset Sum, SAT, Graph Coloring, etc.).

    All implementations must guarantee:
    1. Deterministic verification
    2. Efficient verification (polynomial time)
    3. Hard solving (exponential/NP complexity)
    4. Canonical serialization
    """

    @abstractmethod
    def solve(
        self,
        instance: ProofInstance,
        limits: ResourceLimits,
        timeout_seconds: Optional[float] = None,
    ) -> ProofSolution:
        """
        Solve the given proof instance within resource limits.

        Args:
            instance: Problem specification
            limits: Resource constraints (tier-based)
            timeout_seconds: Optional timeout (defaults to tier limit)

        Returns:
            ProofSolution with candidate solution

        Raises:
            TierLimitExceeded: If resource limits are violated
            TimeoutError: If solving exceeds timeout
            ValueError: If instance is malformed
        """
        pass

    @abstractmethod
    def verify(
        self,
        instance: ProofInstance,
        solution: ProofSolution,
        limits: ResourceLimits,
    ) -> ProofVerificationResult:
        """
        Verify that solution correctly solves instance.

        MUST run in polynomial time relative to problem_size.
        MUST be deterministic (same instance + solution = same result).

        Args:
            instance: Problem specification
            solution: Candidate solution
            limits: Resource constraints for verification

        Returns:
            ProofVerificationResult with validity and metrics

        Raises:
            ValidationError: If verification process fails
            TierLimitExceeded: If verification exceeds limits
        """
        pass

    @abstractmethod
    def cost_hint(self, instance: ProofInstance) -> float:
        """
        Estimate computational cost for this instance.

        Used for dynamic fee estimation and work score prediction.

        Args:
            instance: Problem specification

        Returns:
            Estimated cost in abstract work units
            (normalized such that TIER_1_MOBILE baseline = 1.0)
        """
        pass

    @abstractmethod
    def complexity_bound(self, problem_size: int) -> ComplexityMetrics:
        """
        Theoretical complexity bounds for this problem type.

        Args:
            problem_size: Problem size parameter (n)

        Returns:
            ComplexityMetrics with asymptotic bounds
        """
        pass

    @abstractmethod
    def generate_problem(
        self,
        tier: ProblemTierEnum,
        parent_hash: bytes,
        epoch_salt: bytes,
        ensure_solvable: bool = True,
    ) -> ProofInstance:
        """
        Generate a new problem instance for mining.

        MUST be deterministic from parent_hash + epoch_salt to prevent
        grinding attacks.

        Args:
            tier: Difficulty tier
            parent_hash: Parent block hash (for determinism)
            epoch_salt: Epoch salt (for time-locking)
            ensure_solvable: If True, guarantee solution exists

        Returns:
            ProofInstance ready for solving
        """
        pass

    def validate_tier_compliance(
        self,
        instance: ProofInstance,
        solution: ProofSolution,
        tier: ProblemTierEnum,
    ) -> bool:
        """
        Validate that proof complies with tier limits.

        Default implementation checks basic bounds.
        Override for problem-specific validation.

        Args:
            instance: Problem specification
            solution: Candidate solution
            tier: Expected tier

        Returns:
            True if tier-compliant, False otherwise
        """
        from .limits import get_tier_limits

        limits = get_tier_limits(tier)

        # Check problem size
        if instance.problem_size > limits.max_problem_size:
            return False

        # Check solution size
        if len(solution.solution_data) > limits.max_solution_size:
            return False

        # Check solve time
        if solution.solve_time_seconds > limits.max_solve_time_seconds:
            return False

        return True


class SubsetSumSolver(Solver):
    """
    Concrete solver for Subset Sum problems.

    Problem: Given set S = {a1, a2, ..., an} and target T,
             find subset I ⊆ {1..n} such that Σ(a_i for i in I) = T

    Complexity:
    - Solving: O(2^n) exhaustive search or O(n·T) pseudo-polynomial DP
    - Verification: O(n) sum check
    - Asymmetry: Exponential (2^n / n)

    Wire Format:
    - problem_params: {"elements": [int, ...], "target": int}
    - solution_data: [int, ...] (list of selected indices)
    """

    def solve(
        self,
        instance: ProofInstance,
        limits: ResourceLimits,
        timeout_seconds: Optional[float] = None,
    ) -> ProofSolution:
        """Solve Subset Sum using backtracking with pruning."""
        from ...core.blockchain import solve_subset_sum, compute_solution_hash
        import time

        if instance.problem_type != "subset_sum":
            raise ValueError(f"Expected subset_sum, got {instance.problem_type}")

        elements = instance.problem_params["elements"]
        target = instance.problem_params["target"]

        start_time = time.time()

        # Solve using existing implementation
        solution_indices = solve_subset_sum(elements, target)

        solve_time = time.time() - start_time

        # Check timeout
        timeout = timeout_seconds or limits.max_solve_time_seconds
        if solve_time > timeout:
            raise TimeoutError(f"Solving exceeded timeout: {solve_time:.2f}s > {timeout:.2f}s")

        # Compute solution hash
        import hashlib
        import json
        solution_json = json.dumps(solution_indices, sort_keys=True)
        solution_hash = SolutionHash(hashlib.sha256(solution_json.encode()).digest())

        # Estimate memory (rough approximation)
        solve_space = len(elements) * 8 + len(solution_indices) * 8

        # Generate miner salt (in production, this would come from wallet)
        import os
        miner_salt = os.urandom(32)

        return ProofSolution(
            solution_data=solution_indices,
            solution_hash=solution_hash,
            solve_time_seconds=solve_time,
            solve_space_bytes=solve_space,
            miner_salt=miner_salt,
        )

    def verify(
        self,
        instance: ProofInstance,
        solution: ProofSolution,
        limits: ResourceLimits,
    ) -> ProofVerificationResult:
        """Verify Subset Sum solution in O(n) time."""
        import time

        start_time = time.time()

        try:
            elements = instance.problem_params["elements"]
            target = instance.problem_params["target"]
            solution_indices = solution.solution_data

            # Check indices are valid and unique
            if not solution_indices:
                return ProofVerificationResult(
                    is_valid=False,
                    error_message="Empty solution",
                    verify_time_seconds=time.time() - start_time,
                    verify_space_bytes=0,
                    complexity_metrics=None,
                    asymmetry_ratio=None,
                )

            if len(set(solution_indices)) != len(solution_indices):
                return ProofVerificationResult(
                    is_valid=False,
                    error_message="Duplicate indices in solution",
                    verify_time_seconds=time.time() - start_time,
                    verify_space_bytes=0,
                    complexity_metrics=None,
                    asymmetry_ratio=None,
                )

            # Check all indices in range
            if not all(0 <= i < len(elements) for i in solution_indices):
                return ProofVerificationResult(
                    is_valid=False,
                    error_message="Solution index out of range",
                    verify_time_seconds=time.time() - start_time,
                    verify_space_bytes=0,
                    complexity_metrics=None,
                    asymmetry_ratio=None,
                )

            # Verify sum equals target (O(n) check)
            computed_sum = sum(elements[i] for i in solution_indices)

            if computed_sum != target:
                return ProofVerificationResult(
                    is_valid=False,
                    error_message=f"Sum mismatch: {computed_sum} != {target}",
                    verify_time_seconds=time.time() - start_time,
                    verify_space_bytes=0,
                    complexity_metrics=None,
                    asymmetry_ratio=None,
                )

            verify_time = time.time() - start_time
            verify_space = len(elements) * 8

            # Compute complexity metrics
            complexity = self.complexity_bound(instance.problem_size)
            asymmetry = solution.solve_time_seconds / verify_time if verify_time > 0 else 0.0

            return ProofVerificationResult(
                is_valid=True,
                error_message=None,
                verify_time_seconds=verify_time,
                verify_space_bytes=verify_space,
                complexity_metrics=complexity,
                asymmetry_ratio=asymmetry,
            )

        except Exception as e:
            return ProofVerificationResult(
                is_valid=False,
                error_message=f"Verification error: {str(e)}",
                verify_time_seconds=time.time() - start_time,
                verify_space_bytes=0,
                complexity_metrics=None,
                asymmetry_ratio=None,
            )

    def cost_hint(self, instance: ProofInstance) -> float:
        """Estimate cost as 2^n for exponential complexity."""
        n = instance.problem_size
        # Normalize to TIER_1 baseline (n=10): 2^10 = 1024
        baseline = 2**10
        estimated_cost = (2**n) / baseline
        return estimated_cost

    def complexity_bound(self, problem_size: int) -> ComplexityMetrics:
        """Return theoretical complexity bounds for Subset Sum."""
        from ..types import ProblemClassEnum

        return ComplexityMetrics(
            time_solve_O=f"O(2^{problem_size})",
            time_verify_O=f"O({problem_size})",
            space_solve_O=f"O({problem_size})",
            space_verify_O="O(1)",
            problem_class=ProblemClassEnum.NP_COMPLETE,
            problem_size=problem_size,
            solution_size=problem_size,  # Worst case: all elements
            asymmetry_ratio=2**(problem_size - 1),  # Theoretical: 2^n / n
            measured_solve_time=0.0,  # Filled in during actual solving
            measured_verify_time=0.0,  # Filled in during verification
            measured_solve_space=0,
            measured_verify_space=0,
        )

    def generate_problem(
        self,
        tier: ProblemTierEnum,
        parent_hash: bytes,
        epoch_salt: bytes,
        ensure_solvable: bool = True,
    ) -> ProofInstance:
        """Generate deterministic Subset Sum instance."""
        from ...core.blockchain import generate_subset_sum_problem
        import hashlib

        # Derive problem size from tier
        min_size, max_size = tier.get_size_range()

        # Deterministic size selection from parent_hash
        size_seed = int.from_bytes(parent_hash[:4], 'little')
        problem_size = min_size + (size_seed % (max_size - min_size + 1))

        # Generate problem deterministically
        seed_data = parent_hash + epoch_salt
        problem_seed = int.from_bytes(hashlib.sha256(seed_data).digest()[:8], 'little')

        elements, target = generate_subset_sum_problem(problem_size, problem_seed)

        return ProofInstance(
            problem_type="subset_sum",
            problem_params={"elements": elements, "target": target},
            problem_size=problem_size,
            tier=tier,
            epoch_salt=epoch_salt,
            parent_hash=parent_hash,
        )


# Default solver registry
_SOLVER_REGISTRY: Dict[str, type[Solver]] = {
    "subset_sum": SubsetSumSolver,
}


def get_solver(problem_type: str) -> Solver:
    """
    Get solver instance for given problem type.

    Args:
        problem_type: Problem type identifier (e.g., "subset_sum")

    Returns:
        Solver instance

    Raises:
        ValueError: If problem type is not registered
    """
    if problem_type not in _SOLVER_REGISTRY:
        raise ValueError(f"Unknown problem type: {problem_type}. Registered: {list(_SOLVER_REGISTRY.keys())}")

    solver_class = _SOLVER_REGISTRY[problem_type]
    return solver_class()


def register_solver(problem_type: str, solver_class: type[Solver]) -> None:
    """
    Register a new solver implementation.

    Args:
        problem_type: Problem type identifier
        solver_class: Solver class (must extend Solver ABC)
    """
    if not issubclass(solver_class, Solver):
        raise TypeError(f"{solver_class} must extend Solver ABC")

    _SOLVER_REGISTRY[problem_type] = solver_class


__all__ = [
    "ProofInstance",
    "ProofSolution",
    "ProofVerificationResult",
    "ResourceLimits",
    "Solver",
    "SubsetSumSolver",
    "get_solver",
    "register_solver",
]
