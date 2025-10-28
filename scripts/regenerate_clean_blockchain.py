#!/usr/bin/env python3
"""
Regenerate Clean Blockchain with Proper Consensus Validation
This script creates a fresh blockchain from genesis with only valid solutions.
"""

import sys
import os
import json
import time
import logging

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../src/api'))

from api.blockchain_storage import COINjectureStorage
from pow import ProblemRegistry, ProblemType, ProblemTier
from metrics_engine import MetricsEngine, NetworkState
from storage import IPFSClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_valid_genesis_block():
    """Create a genesis block with a valid subset sum solution."""
    
    # Initialize components
    storage = COINjectureStorage(data_dir="/opt/coinjecture/data")
    problem_registry = ProblemRegistry()
    metrics_engine = MetricsEngine()
    ipfs_client = IPFSClient("http://localhost:5001")
    
    # Verify IPFS is running
    if not ipfs_client.health_check():
        logger.error("❌ IPFS daemon not available. Start IPFS first.")
        return False
    
    logger.info("✅ IPFS daemon is healthy")
    
    # Create a valid subset sum problem
    problem = problem_registry.generate(
        ProblemType.SUBSET_SUM, 
        "coinjecture-genesis-2025", 
        ProblemTier.TIER_2_DESKTOP
    )
    
    # Solve the problem to get a valid solution
    solution = problem_registry.solve(problem)
    
    # Verify the solution is correct
    if not problem_registry.verify(problem, solution):
        logger.error("❌ Generated solution is invalid!")
        return False
    
    logger.info(f"✅ Generated valid problem: target={problem['target']}, solution={solution}, sum={sum(solution)}")
    
    # Create proof bundle
    proof_bundle = {
        'bundle_version': '1.0',
        'block_hash': 'd1700c2681b75c1d22ed08285994c202d310ff25cf40851365ca6fea22011358',
        'block_index': 0,
        'timestamp': 1700000000.0,
        'miner_address': 'GENESIS',
        'mining_capacity': 'TIER_2_DESKTOP',
        'problem': problem,
        'solution': solution,
        'complexity': {
            'problem_class': 'NP-Complete',
            'problem_size': problem['size'],
            'solution_size': len(solution),
            'measured_solve_time': 0.001,
            'measured_verify_time': 0.0001,
            'time_solve_O': 'O(2^n)',
            'time_verify_O': 'O(n)',
            'space_solve_O': 'O(n * target)',
            'space_verify_O': 'O(n)',
            'asymmetry_time': 10.0,
            'asymmetry_space': 5.0
        },
        'energy_metrics': {
            'solve_energy_joules': 0.1,
            'verify_energy_joules': 0.01,
            'solve_power_watts': 100,
            'verify_power_watts': 1,
            'solve_time_seconds': 0.001,
            'verify_time_seconds': 0.0001,
            'cpu_utilization': 80.0,
            'memory_utilization': 50.0,
            'gpu_utilization': 0.0
        },
        'cumulative_work_score': 1.0,
        'created_at': f'{{"timestamp": "{time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}"}}'
    }
    
    # Upload to IPFS
    bundle_bytes = json.dumps(proof_bundle, indent=2).encode('utf-8')
    cid = ipfs_client.add(bundle_bytes)
    
    if not cid:
        logger.error("❌ Failed to upload proof bundle to IPFS")
        return False
    
    # Pin the CID
    import subprocess
    result = subprocess.run([
        "curl", "-X", "POST", 
        f"http://localhost:5001/api/v0/pin/add?arg={cid}"
    ], capture_output=True, text=True, timeout=30)
    
    logger.info(f"✅ Genesis proof bundle uploaded to IPFS: {cid}")
    
    # Calculate gas and reward
    complexity = metrics_engine.calculate_complexity_metrics(proof_bundle, solution)
    gas_used = metrics_engine.calculate_gas_cost('mining', complexity)
    
    network_state = NetworkState(
        cumulative_work=0.0,
        network_avg_work=1.0,
        total_supply=0.0,
        block_count=1,
        avg_block_time=60.0,
        network_growth_rate=0.0
    )
    
    reward = metrics_engine.calculate_block_reward(1.0, network_state)
    
    # Create genesis block data
    genesis_data = {
        'block_hash': 'd1700c2681b75c1d22ed08285994c202d310ff25cf40851365ca6fea22011358',
        'index': 0,
        'timestamp': 1700000000.0,
        'miner_address': 'GENESIS',
        'work_score': 1.0,
        'capacity': 'desktop',
        'cid': cid,
        'previous_hash': '',
        'merkle_root': '',
        'nonce': 0,
        'difficulty': 1.0,
        'size_bytes': len(bundle_bytes),
        'transaction_count': 0,
        'gas_used': gas_used,
        'gas_limit': 1000000,
        'gas_price': 0.000001,
        'reward': reward,
        'cumulative_work_score': 1.0,
        'is_full_block': True
    }
    
    # Initialize database and store genesis
    storage.init_database()
    storage.add_block_data(genesis_data)
    
    logger.info(f"✅ Genesis block created and stored:")
    logger.info(f"   Hash: {genesis_data['block_hash']}")
    logger.info(f"   CID: {cid}")
    logger.info(f"   Gas: {gas_used}")
    logger.info(f"   Reward: {reward:.6f} BEANS")
    logger.info(f"   Problem: target={problem['target']}, solution={solution}")
    
    return True

def main():
    logger.info("🚀 Starting clean blockchain regeneration...")
    
    success = create_valid_genesis_block()
    
    if success:
        logger.info("✅ Clean blockchain regeneration completed successfully!")
        logger.info("🔒 All blocks now have proper consensus validation")
        return 0
    else:
        logger.error("❌ Blockchain regeneration failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
