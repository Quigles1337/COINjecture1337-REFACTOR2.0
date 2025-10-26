#!/usr/bin/env python3
"""
Sync blocks from network and calculate metrics
Simple approach to populate database with network blocks
"""

import sys
import os
import time
import json
import requests
import sqlite3
import logging

# Add src to path
sys.path.append('src')

from metrics_engine import get_metrics_engine, SATOSHI_CONSTANT, ComputationalComplexity
from api.blockchain_storage import storage

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def sync_blocks_from_network():
    """Sync blocks from network and calculate metrics."""
    logger.info(f"🌐 Starting network sync with Satoshi Constant: {SATOSHI_CONSTANT:.6f}")
    
    # Initialize database
    storage.init_database()
    
    # Get metrics engine
    metrics_engine = get_metrics_engine()
    
    # Bootstrap peers
    bootstrap_peers = [
        "167.172.213.70:5000",
        "167.172.213.70:12346"
    ]
    
    # Get latest block height from network
    latest_height = 0
    for peer in bootstrap_peers:
        try:
            metrics_url = f"http://{peer}/v1/metrics/dashboard"
            response = requests.get(metrics_url, timeout=10)
            
            if response.status_code == 200:
                metrics_data = response.json()
                if 'data' in metrics_data and 'blockchain' in metrics_data['data']:
                    peer_height = metrics_data['data']['blockchain'].get('latest_block', 0)
                    if peer_height > latest_height:
                        latest_height = peer_height
                        logger.info(f"📈 Found latest height {peer_height} from {peer}")
        except Exception as e:
            logger.debug(f"Could not get metrics from {peer}: {e}")
    
    logger.info(f"📊 Latest network height: {latest_height}")
    
    # Sync blocks
    synced_count = 0
    cumulative_work = 0.0
    
    for height in range(0, min(latest_height + 1, 2000)):  # Limit to 2000 blocks
        try:
            # Try to get block from multiple peers
            block_data = None
            
            for peer in bootstrap_peers:
                try:
                    block_url = f"http://{peer}/v1/data/block/{height}"
                    response = requests.get(block_url, timeout=10)
                    
                    if response.status_code == 200:
                        block_response = response.json()
                        if 'data' in block_response:
                            block_data = block_response['data']
                            break
                except Exception as e:
                    logger.debug(f"Could not get block {height} from {peer}: {e}")
            
            if not block_data:
                logger.warning(f"⚠️  Could not get block {height} from any peer")
                continue
            
            # Calculate metrics for block
            work_score = block_data.get('work_score', 1.0)
            
            # Calculate complexity metrics from actual block data
            complexity = metrics_engine.calculate_complexity_metrics(
                block_data.get('problem', {}),
                block_data.get('solution', {})
            )
            
            # Calculate gas cost
            gas_used = metrics_engine.calculate_gas_cost("block_validation", complexity)
            gas_limit = 1000000
            gas_price = 0.000001
            
            # Calculate reward
            network_state = metrics_engine.network_state
            network_state.cumulative_work = cumulative_work
            network_state.block_count = height
            
            reward = metrics_engine.calculate_block_reward(work_score, network_state)
            
            # Update cumulative work
            cumulative_work += work_score
            
            # Update block data with calculated metrics
            block_data['gas_used'] = gas_used
            block_data['gas_limit'] = gas_limit
            block_data['gas_price'] = gas_price
            block_data['reward'] = reward
            block_data['cumulative_work_score'] = cumulative_work
            block_data['damping_ratio'] = SATOSHI_CONSTANT
            block_data['stability_metric'] = 1.0
            
            # Store block
            storage.add_block_data(block_data)
            
            synced_count += 1
            if synced_count % 100 == 0:
                logger.info(f"✅ Synced {synced_count} blocks (height {height})")
            
            # Small delay
            time.sleep(0.1)
            
        except Exception as e:
            logger.error(f"❌ Error syncing block {height}: {e}")
            continue
    
    logger.info(f"✅ Sync completed: {synced_count} blocks synced")
    logger.info(f"📊 Final cumulative work: {cumulative_work:.6f}")

def main():
    """Main function."""
    try:
        sync_blocks_from_network()
        return 0
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
