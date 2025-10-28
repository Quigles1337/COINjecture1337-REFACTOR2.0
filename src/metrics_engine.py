#!/usr/bin/env python3
"""
COINjecture Metrics Engine
Implements comprehensive metrics calculation with Satoshi Constant for critical damping.
"""

import time
import math
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger('coinjecture-metrics')

# Satoshi Constant for Critical Complex Equilibrium
# Derived from eigenvalue proof: η = λ = √2/2 ≈ 0.7071
# Ensures |μ| = 1 for bounded oscillations and convergence
SATOSHI_CONSTANT = math.sqrt(2) / 2  # 0.707107...

@dataclass
class ComputationalComplexity:
    """Computational complexity metrics for work score calculation."""
    time_asymmetry: float  # solve_time / verify_time
    space_asymmetry: float  # memory_used / problem_size
    problem_weight: float   # problem difficulty multiplier
    size_factor: float     # problem size factor
    quality_score: float   # solution quality (0-1)
    energy_efficiency: float  # work_per_energy_unit

@dataclass
class NetworkState:
    """Current network state for reward calculation."""
    cumulative_work: float
    network_avg_work: float
    total_supply: float
    block_count: int
    avg_block_time: float
    network_growth_rate: float
    damping_ratio: float = SATOSHI_CONSTANT  # Critical damping
    coupling_strength: float = SATOSHI_CONSTANT  # Critical coupling

class MetricsEngine:
    """
    Comprehensive metrics calculation engine implementing COINjecture architecture.
    
    Implements:
    - Work score calculation with complexity metrics
    - Gas calculation for transaction costs
    - Dynamic reward calculation with deflation
    - Satoshi Constant for critical damping (0.7071)
    """
    
    def __init__(self):
        self.genesis_timestamp = int(time.time())
        self.network_state = NetworkState(
            cumulative_work=0.0,
            network_avg_work=1.0,
            total_supply=0.0,
            block_count=0,
            avg_block_time=60.0,
            network_growth_rate=0.0,
            damping_ratio=SATOSHI_CONSTANT,
            coupling_strength=SATOSHI_CONSTANT
        )
        logger.info(f"✅ Metrics engine initialized with Satoshi Constant: {SATOSHI_CONSTANT:.6f}")
    
    def calculate_work_score(self, complexity: ComputationalComplexity) -> float:
        """
        Calculate work score using the architecture formula:
        work_score = time_asymmetry * sqrt(space_asymmetry) * 
                     problem_weight * size_factor * quality_score * energy_efficiency
        """
        try:
            work_score = (
                complexity.time_asymmetry *
                math.sqrt(complexity.space_asymmetry) *
                complexity.problem_weight *
                complexity.size_factor *
                complexity.quality_score *
                complexity.energy_efficiency
            )
            
            # Apply Satoshi Constant for stability
            work_score = work_score * self.network_state.damping_ratio
            
            # Ensure minimum work score
            work_score = max(work_score, 0.1)
            
            logger.info(f"💰 Calculated work score: {work_score:.6f}")
            return work_score
            
        except Exception as e:
            logger.error(f"❌ Error calculating work score: {e}")
            return 0.1
    
    def calculate_gas_cost(self, operation_type: str, complexity: ComputationalComplexity) -> int:
        """
        Calculate gas cost for operations based on computational complexity.
        
        Base gas costs:
        - block_validation: 1000
        - transaction_processing: 500
        - proof_verification: 2000
        - commitment_verification: 1500
        - merkle_proof: 300
        """
        base_gas = {
            "block_validation": 1000,
            "transaction_processing": 500,
            "proof_verification": 2000,
            "commitment_verification": 1500,
            "merkle_proof": 300,
            "mining": 11000  # Base gas for mining operations
        }
        
        try:
            base_cost = base_gas.get(operation_type, 1000)
            
            # Scale by complexity metrics
            complexity_multiplier = (
                complexity.time_asymmetry * 
                math.sqrt(complexity.space_asymmetry) *
                complexity.problem_weight
            )
            
            gas_cost = base_cost * (1 + complexity_multiplier)
            
            logger.info(f"⛽ Gas cost for {operation_type}: {gas_cost:.2f}")
            return int(gas_cost)
            
        except Exception as e:
            logger.error(f"❌ Error calculating gas cost: {e}")
            return base_gas.get(operation_type, 1000)
    
    def calculate_block_reward(self, work_score: float, network_state: NetworkState) -> float:
        """
        Calculate block reward using dynamic tokenomics:
        reward = log(1 + work_score/network_avg) * deflation_factor * damping_ratio
        
        Includes Satoshi Constant for stability.
        """
        try:
            # Calculate deflation factor
            deflation_factor = self.get_deflation_factor(network_state.cumulative_work)
            
            # Calculate reward with Satoshi Constant damping
            reward = (
                math.log(1 + work_score / network_state.network_avg_work) * 
                deflation_factor * 
                network_state.damping_ratio
            )
            
            # Ensure minimum reward
            reward = max(reward, 0.01)
            
            logger.info(f"🎁 Block reward: {reward:.6f} BEANS (deflation: {deflation_factor:.4f})")
            return reward
            
        except Exception as e:
            logger.error(f"❌ Error calculating block reward: {e}")
            return 0.01
    
    def get_deflation_factor(self, cumulative_work: float) -> float:
        """
        Calculate deflation factor based on cumulative work:
        deflation_factor = 1 / (2^(log2(cumulative_work)/10))
        """
        try:
            if cumulative_work <= 0:
                return 1.0
            
            deflation_factor = 1.0 / (2 ** (math.log2(cumulative_work) / 10))
            deflation_factor = max(0.1, min(1.0, deflation_factor))
            
            return deflation_factor
            
        except Exception as e:
            logger.error(f"❌ Error calculating deflation factor: {e}")
            return 1.0
    
    def calculate_complexity_metrics(self, problem_data: dict, solution_data: dict) -> ComputationalComplexity:
        """Calculate complexity metrics from problem and solution data."""
        try:
            # Handle both direct field access and proof bundle structure
            if isinstance(problem_data, dict) and 'complexity' in problem_data:
                # This is a proof bundle structure
                complexity_data = problem_data.get('complexity', {})
                energy_metrics = problem_data.get('energy_metrics', {})
                
                solve_time = complexity_data.get('measured_solve_time', 1.0)
                verify_time = complexity_data.get('measured_verify_time', 0.1)
                problem_size = complexity_data.get('problem_size', 1.0)
                energy_used = energy_metrics.get('solve_energy_joules', 1.0)
                
                time_asymmetry = complexity_data.get('asymmetry_time', solve_time / max(verify_time, 0.001))
                space_asymmetry = complexity_data.get('asymmetry_space', 1.0)
                problem_weight = problem_data.get('problem', {}).get('difficulty', 1.0)
                size_factor = math.log(problem_size + 1)
                quality_score = 1.0  # Default quality score
                energy_efficiency = 1.0 / max(energy_used, 0.001)
            else:
                # Direct field access (legacy format)
                solve_time = solution_data.get('solve_time', 1.0)
                verify_time = solution_data.get('verify_time', 0.1)
                memory_used = solution_data.get('memory_used', 1.0)
                problem_size = problem_data.get('size', 1.0)
                energy_used = solution_data.get('energy_used', 1.0)
                
                time_asymmetry = solve_time / max(verify_time, 0.001)
                space_asymmetry = memory_used / max(problem_size, 1.0)
                problem_weight = problem_data.get('difficulty', 1.0)
                size_factor = math.log(problem_size + 1)
                quality_score = solution_data.get('quality', 1.0)
                energy_efficiency = (solve_time * problem_size) / max(energy_used, 0.001)
            
            return ComputationalComplexity(
                time_asymmetry=time_asymmetry,
                space_asymmetry=space_asymmetry,
                problem_weight=problem_weight,
                size_factor=size_factor,
                quality_score=quality_score,
                energy_efficiency=energy_efficiency
            )
            
        except Exception as e:
            logger.error(f"❌ Error calculating complexity metrics: {e}")
            return ComputationalComplexity(
                time_asymmetry=1.0,
                space_asymmetry=1.0,
                problem_weight=1.0,
                size_factor=1.0,
                quality_score=1.0,
                energy_efficiency=1.0
            )
    
    def get_network_metrics(self) -> Dict[str, Any]:
        """Get comprehensive network metrics including Satoshi Constant."""
        return {
            "cumulative_work": self.network_state.cumulative_work,
            "network_avg_work": self.network_state.network_avg_work,
            "total_supply": self.network_state.total_supply,
            "block_count": self.network_state.block_count,
            "avg_block_time": self.network_state.avg_block_time,
            "deflation_factor": self.get_deflation_factor(self.network_state.cumulative_work),
            "satoshi_constant": SATOSHI_CONSTANT,
            "damping_ratio": self.network_state.damping_ratio,
            "coupling_strength": self.network_state.coupling_strength,
            "stability_metric": 1.0,  # |μ| = 1 for critical damping
            "fork_resistance": 1.0 - SATOSHI_CONSTANT,  # ≈ 0.293
            "liveness_guarantee": SATOSHI_CONSTANT  # ≈ 0.707
        }

# Global metrics engine instance
_metrics_engine = None

def get_metrics_engine() -> MetricsEngine:
    """Get global metrics engine instance."""
    global _metrics_engine
    if _metrics_engine is None:
        _metrics_engine = MetricsEngine()
    return _metrics_engine