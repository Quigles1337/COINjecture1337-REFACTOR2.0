#!/usr/bin/env python3
"""
Update Gas Calculations for Existing Blocks
Recalculates gas values based on IPFS proof data and computational complexity
"""

import sys
import os
import json
import time
import logging
from typing import Dict, Any, Optional

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from api.blockchain_storage import COINjectureStorage, PruningMode
from metrics_engine import MetricsEngine, ComputationalComplexity, NetworkState
from storage import StorageManager, StorageConfig, NodeRole

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GasCalculator:
    def __init__(self, data_dir: str = "/opt/coinjecture/data"):
        self.storage = COINjectureStorage(data_dir=data_dir, pruning_mode=PruningMode.ARCHIVE)
        self.metrics_engine = MetricsEngine()
        
        # Initialize storage manager for IPFS access
        storage_config = StorageConfig(
            data_dir=data_dir,
            role=NodeRole.ARCHIVE,
            pruning_mode=PruningMode.ARCHIVE,
            ipfs_api_url="http://localhost:5001"
        )
        self.storage_manager = StorageManager(storage_config)

    def calculate_complexity_from_proof_data(self, proof_data: Dict[str, Any]) -> ComputationalComplexity:
        """Calculate complexity metrics from IPFS proof data."""
        try:
            problem = proof_data.get('problem', {})
            complexity = proof_data.get('complexity', {})
            energy_metrics = proof_data.get('energy_metrics', {})
            
            # Extract metrics
            problem_size = problem.get('size', 10)
            solve_time = complexity.get('measured_solve_time', 0.001)
            verify_time = complexity.get('measured_verify_time', 0.0001)
            energy_joules = energy_metrics.get('solve_energy_joules', 1.0)
            
            # Calculate complexity metrics
            time_asymmetry = solve_time / verify_time if verify_time > 0 else 1.0
            space_asymmetry = problem_size * 0.1  # Memory usage factor
            problem_weight = min(problem_size / 10.0, 3.0)  # Difficulty factor
            size_factor = problem_size / 20.0  # Size scaling
            quality_score = 0.9  # Assume high quality solutions
            energy_efficiency = 1.0 / max(energy_joules, 0.1)  # Efficiency factor
            
            return ComputationalComplexity(
                time_asymmetry=time_asymmetry,
                space_asymmetry=space_asymmetry,
                problem_weight=problem_weight,
                size_factor=size_factor,
                quality_score=quality_score,
                energy_efficiency=energy_efficiency
            )
            
        except Exception as e:
            logger.error(f"Error calculating complexity: {e}")
            # Return default complexity
            return ComputationalComplexity(
                time_asymmetry=1.0,
                space_asymmetry=1.0,
                problem_weight=1.0,
                size_factor=1.0,
                quality_score=0.9,
                energy_efficiency=1.0
            )

    def get_proof_data_from_ipfs(self, cid: str) -> Optional[Dict[str, Any]]:
        """Get proof data from IPFS by CID."""
        try:
            if not self.storage_manager.ipfs_client.health_check():
                logger.warning("IPFS daemon not available")
                return None
            
            bundle_bytes = self.storage_manager.ipfs_client.get(cid)
            if bundle_bytes:
                return json.loads(bundle_bytes.decode('utf-8'))
            return None
            
        except Exception as e:
            logger.error(f"Error fetching IPFS data for CID {cid}: {e}")
            return None

    def calculate_dynamic_gas(self, block_data: Dict[str, Any]) -> int:
        """Calculate dynamic gas based on IPFS proof data."""
        try:
            cid = block_data.get('cid')
            if not cid:
                logger.warning(f"No CID found for block {block_data.get('height', 'unknown')}")
                return 11000  # Default fallback
            
            # Get proof data from IPFS
            proof_data = self.get_proof_data_from_ipfs(cid)
            if not proof_data:
                logger.warning(f"No IPFS data found for CID {cid}")
                return 11000  # Default fallback
            
            # Calculate complexity metrics
            complexity = self.calculate_complexity_from_proof_data(proof_data)
            
            # Calculate gas cost
            gas_cost = self.metrics_engine.calculate_gas_cost('mining', complexity)
            
            logger.info(f"Block {block_data.get('height', 'unknown')}: Gas {gas_cost} (was {block_data.get('gas_used', 0)})")
            return gas_cost
            
        except Exception as e:
            logger.error(f"Error calculating gas for block {block_data.get('height', 'unknown')}: {e}")
            return block_data.get('gas_used', 11000)  # Keep existing value

    def update_all_blocks(self):
        """Update gas calculations for all blocks in the database."""
        try:
            latest_height = self.storage.get_latest_height()
            logger.info(f"Updating gas calculations for {latest_height + 1} blocks...")
            
            updated_count = 0
            failed_count = 0
            
            for height in range(latest_height + 1):
                try:
                    # Get block data
                    block_data = self.storage.get_block_data(height)
                    if not block_data:
                        logger.warning(f"No data found for block {height}")
                        failed_count += 1
                        continue
                    
                    # Calculate new gas value
                    new_gas = self.calculate_dynamic_gas(block_data)
                    
                    # Update database
                    self.storage.update_block_gas(block_data['block_hash'], new_gas)
                    updated_count += 1
                    
                    if height % 10 == 0:
                        logger.info(f"Updated {height + 1}/{latest_height + 1} blocks...")
                        
                except Exception as e:
                    logger.error(f"Error updating block {height}: {e}")
                    failed_count += 1
            
            logger.info(f"✅ Gas calculation update complete!")
            logger.info(f"   Updated: {updated_count} blocks")
            logger.info(f"   Failed: {failed_count} blocks")
            
            return updated_count, failed_count
            
        except Exception as e:
            logger.error(f"Error updating blocks: {e}")
            return 0, 0

def main():
    calculator = GasCalculator()
    
    logger.info("🚀 Starting gas calculation update...")
    logger.info("This will recalculate gas values based on IPFS proof data")
    
    # Auto-confirm for server deployment
    logger.info("Auto-confirming update (server deployment mode)")
    
    updated_count, failed_count = calculator.update_all_blocks()
    
    if updated_count > 0:
        logger.info("✅ Gas calculations updated successfully!")
        logger.info("The frontend should now show dynamic gas values based on computational complexity")
        return 0
    else:
        logger.error("❌ No blocks were updated")
        return 1

if __name__ == "__main__":
    sys.exit(main())
