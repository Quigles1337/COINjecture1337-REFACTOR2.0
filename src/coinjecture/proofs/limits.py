"""
Module: proofs.limits
Tier-based resource limits for proof generation and verification.

Acts as admission control layer to prevent DoS attacks while maintaining
fairness across hardware classes.
"""

from dataclasses import dataclass
from typing import Dict
from ..types import ProblemTierEnum, TierLimitExceeded
from .interface import ResourceLimits


# ============================================================================
# Tier Limit Constants
# ============================================================================

# Time limits (seconds) - based on production data from v3.17.0
# Mobile devices: lightweight problems, quick solving
TIER_1_MAX_SOLVE_TIME = 60.0  # 1 minute
TIER_1_MAX_VERIFY_TIME = 1.0  # 1 second

# Desktop: moderate problems
TIER_2_MAX_SOLVE_TIME = 300.0  # 5 minutes
TIER_2_MAX_VERIFY_TIME = 2.0  # 2 seconds

# Workstation: heavier computation
TIER_3_MAX_SOLVE_TIME = 900.0  # 15 minutes
TIER_3_MAX_VERIFY_TIME = 5.0  # 5 seconds

# Server: serious computational work
TIER_4_MAX_SOLVE_TIME = 1800.0  # 30 minutes
TIER_4_MAX_VERIFY_TIME = 10.0  # 10 seconds

# Cluster: maximum difficulty
TIER_5_MAX_SOLVE_TIME = 3600.0  # 1 hour
TIER_5_MAX_VERIFY_TIME = 30.0  # 30 seconds

# Memory limits (bytes)
TIER_1_MAX_MEMORY = 256 * 1024 * 1024  # 256 MB
TIER_2_MAX_MEMORY = 1 * 1024 * 1024 * 1024  # 1 GB
TIER_3_MAX_MEMORY = 4 * 1024 * 1024 * 1024  # 4 GB
TIER_4_MAX_MEMORY = 16 * 1024 * 1024 * 1024  # 16 GB
TIER_5_MAX_MEMORY = 64 * 1024 * 1024 * 1024  # 64 GB

# Proof size limits (bytes) - on-wire serialized size
TIER_1_MAX_PROOF_SIZE = 64 * 1024  # 64 KB
TIER_2_MAX_PROOF_SIZE = 256 * 1024  # 256 KB
TIER_3_MAX_PROOF_SIZE = 1 * 1024 * 1024  # 1 MB
TIER_4_MAX_PROOF_SIZE = 4 * 1024 * 1024  # 4 MB
TIER_5_MAX_PROOF_SIZE = 10 * 1024 * 1024  # 10 MB (global max from consensus.py)


# ============================================================================
# Tier Limit Registry
# ============================================================================

_TIER_LIMITS: Dict[ProblemTierEnum, ResourceLimits] = {
    ProblemTierEnum.TIER_1_MOBILE: ResourceLimits(
        max_problem_size=12,  # 8-12 elements
        max_solution_size=12,
        max_solve_time_seconds=TIER_1_MAX_SOLVE_TIME,
        max_verify_time_seconds=TIER_1_MAX_VERIFY_TIME,
        max_memory_bytes=TIER_1_MAX_MEMORY,
        max_proof_bytes=TIER_1_MAX_PROOF_SIZE,
    ),
    ProblemTierEnum.TIER_2_DESKTOP: ResourceLimits(
        max_problem_size=16,  # 12-16 elements
        max_solution_size=16,
        max_solve_time_seconds=TIER_2_MAX_SOLVE_TIME,
        max_verify_time_seconds=TIER_2_MAX_VERIFY_TIME,
        max_memory_bytes=TIER_2_MAX_MEMORY,
        max_proof_bytes=TIER_2_MAX_PROOF_SIZE,
    ),
    ProblemTierEnum.TIER_3_WORKSTATION: ResourceLimits(
        max_problem_size=20,  # 16-20 elements
        max_solution_size=20,
        max_solve_time_seconds=TIER_3_MAX_SOLVE_TIME,
        max_verify_time_seconds=TIER_3_MAX_VERIFY_TIME,
        max_memory_bytes=TIER_3_MAX_MEMORY,
        max_proof_bytes=TIER_3_MAX_PROOF_SIZE,
    ),
    ProblemTierEnum.TIER_4_SERVER: ResourceLimits(
        max_problem_size=24,  # 20-24 elements
        max_solution_size=24,
        max_solve_time_seconds=TIER_4_MAX_SOLVE_TIME,
        max_verify_time_seconds=TIER_4_MAX_VERIFY_TIME,
        max_memory_bytes=TIER_4_MAX_MEMORY,
        max_proof_bytes=TIER_4_MAX_PROOF_SIZE,
    ),
    ProblemTierEnum.TIER_5_CLUSTER: ResourceLimits(
        max_problem_size=32,  # 24-32 elements
        max_solution_size=32,
        max_solve_time_seconds=TIER_5_MAX_SOLVE_TIME,
        max_verify_time_seconds=TIER_5_MAX_VERIFY_TIME,
        max_memory_bytes=TIER_5_MAX_MEMORY,
        max_proof_bytes=TIER_5_MAX_PROOF_SIZE,
    ),
}


# ============================================================================
# Public API
# ============================================================================

def get_tier_limits(tier: ProblemTierEnum) -> ResourceLimits:
    """
    Get resource limits for given tier.

    Args:
        tier: Problem tier

    Returns:
        ResourceLimits for this tier

    Raises:
        ValueError: If tier is unknown
    """
    if tier not in _TIER_LIMITS:
        raise ValueError(f"Unknown tier: {tier}. Valid tiers: {list(_TIER_LIMITS.keys())}")

    return _TIER_LIMITS[tier]


def validate_problem_size(tier: ProblemTierEnum, problem_size: int) -> None:
    """
    Validate that problem size is within tier limits.

    Args:
        tier: Problem tier
        problem_size: Size of problem (n)

    Raises:
        TierLimitExceeded: If problem size exceeds tier limit
    """
    limits = get_tier_limits(tier)

    if problem_size > limits.max_problem_size:
        raise TierLimitExceeded(
            f"Problem size {problem_size} exceeds {tier.value} limit of {limits.max_problem_size}"
        )


def validate_solution_size(tier: ProblemTierEnum, solution_size: int) -> None:
    """
    Validate that solution size is within tier limits.

    Args:
        tier: Problem tier
        solution_size: Size of solution (number of elements)

    Raises:
        TierLimitExceeded: If solution size exceeds tier limit
    """
    limits = get_tier_limits(tier)

    if solution_size > limits.max_solution_size:
        raise TierLimitExceeded(
            f"Solution size {solution_size} exceeds {tier.value} limit of {limits.max_solution_size}"
        )


def validate_solve_time(tier: ProblemTierEnum, solve_time_seconds: float) -> None:
    """
    Validate that solve time is within tier limits.

    Args:
        tier: Problem tier
        solve_time_seconds: Measured solve time

    Raises:
        TierLimitExceeded: If solve time exceeds tier limit
    """
    limits = get_tier_limits(tier)

    if solve_time_seconds > limits.max_solve_time_seconds:
        raise TierLimitExceeded(
            f"Solve time {solve_time_seconds:.2f}s exceeds {tier.value} limit of {limits.max_solve_time_seconds:.2f}s"
        )


def validate_verify_time(tier: ProblemTierEnum, verify_time_seconds: float) -> None:
    """
    Validate that verification time is within tier limits.

    Args:
        tier: Problem tier
        verify_time_seconds: Measured verification time

    Raises:
        TierLimitExceeded: If verification time exceeds tier limit
    """
    limits = get_tier_limits(tier)

    if verify_time_seconds > limits.max_verify_time_seconds:
        raise TierLimitExceeded(
            f"Verify time {verify_time_seconds:.2f}s exceeds {tier.value} limit of {limits.max_verify_time_seconds:.2f}s"
        )


def validate_memory_usage(tier: ProblemTierEnum, memory_bytes: int) -> None:
    """
    Validate that memory usage is within tier limits.

    Args:
        tier: Problem tier
        memory_bytes: Measured memory usage

    Raises:
        TierLimitExceeded: If memory usage exceeds tier limit
    """
    limits = get_tier_limits(tier)

    if memory_bytes > limits.max_memory_bytes:
        memory_mb = memory_bytes / (1024 * 1024)
        limit_mb = limits.max_memory_bytes / (1024 * 1024)
        raise TierLimitExceeded(
            f"Memory usage {memory_mb:.2f} MB exceeds {tier.value} limit of {limit_mb:.2f} MB"
        )


def validate_proof_size(tier: ProblemTierEnum, proof_bytes: int) -> None:
    """
    Validate that serialized proof size is within tier limits.

    Args:
        tier: Problem tier
        proof_bytes: Serialized proof size

    Raises:
        TierLimitExceeded: If proof size exceeds tier limit
    """
    limits = get_tier_limits(tier)

    if proof_bytes > limits.max_proof_bytes:
        proof_kb = proof_bytes / 1024
        limit_kb = limits.max_proof_bytes / 1024
        raise TierLimitExceeded(
            f"Proof size {proof_kb:.2f} KB exceeds {tier.value} limit of {limit_kb:.2f} KB"
        )


def validate_all_limits(
    tier: ProblemTierEnum,
    problem_size: int,
    solution_size: int,
    solve_time_seconds: float,
    verify_time_seconds: float,
    memory_bytes: int,
    proof_bytes: int,
) -> None:
    """
    Validate all resource limits for a proof.

    Convenience function that runs all validation checks.

    Args:
        tier: Problem tier
        problem_size: Size of problem
        solution_size: Size of solution
        solve_time_seconds: Measured solve time
        verify_time_seconds: Measured verification time
        memory_bytes: Measured memory usage
        proof_bytes: Serialized proof size

    Raises:
        TierLimitExceeded: If any limit is exceeded
    """
    validate_problem_size(tier, problem_size)
    validate_solution_size(tier, solution_size)
    validate_solve_time(tier, solve_time_seconds)
    validate_verify_time(tier, verify_time_seconds)
    validate_memory_usage(tier, memory_bytes)
    validate_proof_size(tier, proof_bytes)


# ============================================================================
# Tier Recommendation
# ============================================================================

def recommend_tier_for_hardware(
    cpu_cores: int,
    memory_gb: float,
    is_mobile: bool = False,
    has_gpu: bool = False,
) -> ProblemTierEnum:
    """
    Recommend appropriate tier based on hardware capabilities.

    Args:
        cpu_cores: Number of CPU cores
        memory_gb: Available RAM in GB
        is_mobile: True if mobile/battery-powered device
        has_gpu: True if GPU is available

    Returns:
        Recommended ProblemTierEnum
    """
    # Mobile devices always use TIER_1
    if is_mobile:
        return ProblemTierEnum.TIER_1_MOBILE

    # Tier based on CPU cores and memory
    if cpu_cores >= 64 and memory_gb >= 64:
        return ProblemTierEnum.TIER_5_CLUSTER
    elif cpu_cores >= 16 and memory_gb >= 16:
        return ProblemTierEnum.TIER_4_SERVER
    elif cpu_cores >= 8 and memory_gb >= 8:
        return ProblemTierEnum.TIER_3_WORKSTATION
    elif cpu_cores >= 4 and memory_gb >= 4:
        return ProblemTierEnum.TIER_2_DESKTOP
    else:
        return ProblemTierEnum.TIER_1_MOBILE


def estimate_work_score_range(tier: ProblemTierEnum) -> tuple[float, float]:
    """
    Estimate expected work score range for given tier.

    Based on historical data from v3.17.0 production analysis.

    Args:
        tier: Problem tier

    Returns:
        (min_work_score, max_work_score) tuple
    """
    # Approximate work score ranges based on 2^n complexity
    # These are rough estimates - actual scores vary based on specific problem
    work_score_ranges = {
        ProblemTierEnum.TIER_1_MOBILE: (256.0, 4096.0),  # 2^8 to 2^12
        ProblemTierEnum.TIER_2_DESKTOP: (4096.0, 65536.0),  # 2^12 to 2^16
        ProblemTierEnum.TIER_3_WORKSTATION: (65536.0, 1048576.0),  # 2^16 to 2^20
        ProblemTierEnum.TIER_4_SERVER: (1048576.0, 16777216.0),  # 2^20 to 2^24
        ProblemTierEnum.TIER_5_CLUSTER: (16777216.0, 4294967296.0),  # 2^24 to 2^32
    }

    return work_score_ranges[tier]


__all__ = [
    "get_tier_limits",
    "validate_problem_size",
    "validate_solution_size",
    "validate_solve_time",
    "validate_verify_time",
    "validate_memory_usage",
    "validate_proof_size",
    "validate_all_limits",
    "recommend_tier_for_hardware",
    "estimate_work_score_range",
]
