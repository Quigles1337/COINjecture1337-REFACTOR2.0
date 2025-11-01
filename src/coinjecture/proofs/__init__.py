"""Proof-of-work solver interfaces and resource limits."""

from .interface import (
    Solver,
    SubsetSumSolver,
    ProofInstance,
    ProofSolution,
    ProofVerificationResult,
    ResourceLimits,
    get_solver,
    register_solver,
)
from .limits import (
    get_tier_limits,
    validate_all_limits,
    recommend_tier_for_hardware,
    estimate_work_score_range,
)

__all__ = [
    "Solver",
    "SubsetSumSolver",
    "ProofInstance",
    "ProofSolution",
    "ProofVerificationResult",
    "ResourceLimits",
    "get_solver",
    "register_solver",
    "get_tier_limits",
    "validate_all_limits",
    "recommend_tier_for_hardware",
    "estimate_work_score_range",
]
