#!/usr/bin/env python3
"""
Proper Network Sync - Discover peers and sync blockchain from network
"""

import logging
import time
import requests
import json
import os
import sys
from typing import List, Dict, Any

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.api.blockchain_storage import COINjectureStorage
from src.metrics_engine import MetricsEngine, ComputationalComplexity, NetworkState, SATOSHI_CONSTANT

logger = logging.getLogger('proper-network-sync')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ProperNetworkSync:
    """
    Proper network sync that discovers peers and syncs blockchain data
    """

    def __init__(self):
        logger.info(f"🌐 Initializing proper network sync with Satoshi Constant: {SATOSHI_CONSTANT:.6f}")
        
        # Initialize storage
        self.storage = COINjectureStorage()
        
        # Initialize metrics engine
        self.metrics_engine = MetricsEngine()
        
        # Known bootstrap nodes
        self.bootstrap_nodes = [
            "https://api.coinjecture.com",  # Main bootstrap via nginx
            "http://167.172.213.70:12346",  # Direct API server
        ]
        
        # Discovered peers
        self.peers = []
        
        logger.info("✅ Proper Network Sync initialized")

    def discover_peers(self) -> List[str]:
        """Discover network peers from bootstrap nodes"""
        logger.info("🔍 Discovering network peers...")
        
        discovered_peers = set()
        
        # Try each bootstrap node
        for bootstrap in self.bootstrap_nodes:
            try:
                logger.info(f"Trying bootstrap node: {bootstrap}")
                
                # Try to get peer list
                response = requests.get(f"{bootstrap}/v1/network/peers", timeout=10)
                if response.status_code == 200:
                    peer_data = response.json()
                    if 'peers' in peer_data:
                        for peer in peer_data['peers']:
                            discovered_peers.add(peer)
                        logger.info(f"Found {len(peer_data['peers'])} peers from {bootstrap}")
                
                # Also try to get latest block to see if node is responsive
                response = requests.get(f"{bootstrap}/v1/data/block/latest", timeout=5)
                if response.status_code == 200:
                    block_data = response.json()
                    if 'data' in block_data and 'index' in block_data['data']:
                        height = block_data['data']['index']
                        logger.info(f"Bootstrap {bootstrap} has height: {height}")
                        discovered_peers.add(bootstrap)
                
            except Exception as e:
                logger.warning(f"Could not connect to {bootstrap}: {e}")
        
        # Add some known network nodes (these would be discovered in a real network)
        known_peers = [
            "http://167.172.213.70:5000",
            "http://167.172.213.70:12346",
        ]
        
        for peer in known_peers:
            discovered_peers.add(peer)
        
        self.peers = list(discovered_peers)
        logger.info(f"✅ Discovered {len(self.peers)} peers: {self.peers}")
        return self.peers

    def get_latest_block_from_peers(self) -> Dict[str, Any]:
        """Get the latest block from all peers and find the highest"""
        logger.info("📊 Finding highest block from all peers...")
        
        highest_block = None
        highest_height = -1
        
        for peer in self.peers:
            try:
                response = requests.get(f"{peer}/v1/data/block/latest", timeout=5)
                if response.status_code == 200:
                    block_data = response.json()
                    if 'data' in block_data and 'index' in block_data['data']:
                        height = block_data['data']['index']
                        if height > highest_height:
                            highest_height = height
                            highest_block = block_data['data']
                            logger.info(f"Found higher block at {peer}: height {height}")
            except Exception as e:
                logger.warning(f"Could not get latest block from {peer}: {e}")
        
        if highest_block:
            logger.info(f"✅ Highest block found: height {highest_height}")
        else:
            logger.warning("⚠️  No blocks found from any peer")
        
        return highest_block

    def get_block_from_peer(self, peer: str, height: int) -> Dict[str, Any]:
        """Get a specific block from a peer"""
        try:
            response = requests.get(f"{peer}/v1/data/block/{height}", timeout=5)
            if response.status_code == 200:
                block_data = response.json()
                if 'data' in block_data:
                    return block_data['data']
        except Exception as e:
            logger.debug(f"Could not get block {height} from {peer}: {e}")
        return None

    def sync_blocks_from_network(self):
        """Sync all blocks from the network"""
        logger.info("🔄 Starting blockchain sync from network...")
        
        # Discover peers
        self.discover_peers()
        
        # Get local latest block
        local_latest = self.storage.get_latest_block_data()
        local_height = local_latest.get('index', -1) if local_latest else -1
        logger.info(f"Local blockchain height: {local_height}")
        
        # Get network latest block
        network_latest = self.get_latest_block_from_peers()
        if not network_latest:
            logger.error("❌ Could not get latest block from network")
            return
        
        network_height = network_latest.get('index', -1)
        logger.info(f"Network blockchain height: {network_height}")
        
        if network_height <= local_height:
            logger.info("✅ Local blockchain is up-to-date")
            return
        
        # Sync missing blocks
        logger.info(f"🔄 Syncing blocks from height {local_height + 1} to {network_height}")
        
        synced_count = 0
        for height in range(local_height + 1, network_height + 1):
            block_found = False
            
            # Try each peer for this block
            for peer in self.peers:
                block_data = self.get_block_from_peer(peer, height)
                if block_data:
                    # Calculate proper metrics for this block
                    self._process_block_with_metrics(block_data)
                    synced_count += 1
                    block_found = True
                    
                    if synced_count % 100 == 0:
                        logger.info(f"✅ Synced {synced_count} blocks (height {height})")
                    break
            
            if not block_found:
                logger.warning(f"⚠️  Could not get block {height} from any peer")
        
        logger.info(f"✅ Sync completed: {synced_count} blocks synced")

    def _process_block_with_metrics(self, block_data: Dict[str, Any]):
        """Process a block with proper metrics calculation"""
        try:
            # Get work score from block
            work_score = block_data.get('work_score', 1.0)
            
            # Calculate complexity metrics from actual block data
            complexity = self.metrics_engine.calculate_complexity_metrics(
                block_data.get('problem', {}),
                block_data.get('solution', {})
            )
            
            # Calculate gas cost based on complexity
            gas_used = self.metrics_engine.calculate_gas_cost("block_validation", complexity)
            gas_limit = 1000000
            gas_price = 0.000001
            
            # Calculate reward
            network_state = self.metrics_engine.network_state
            reward = self.metrics_engine.calculate_block_reward(work_score, network_state)
            
            # Update block data with calculated metrics
            block_data['gas_used'] = gas_used
            block_data['gas_limit'] = gas_limit
            block_data['gas_price'] = gas_price
            block_data['reward'] = reward
            
            # Store the block
            self.storage.add_block_data(block_data)
            
            # Update network state
            network_state.cumulative_work += work_score
            network_state.block_count += 1
            
            logger.debug(f"Processed block {block_data.get('index', 'unknown')}: gas={gas_used}, reward={reward:.6f}")
            
        except Exception as e:
            logger.error(f"❌ Error processing block: {e}")

def main():
    """Main sync function"""
    sync = ProperNetworkSync()
    sync.sync_blocks_from_network()

if __name__ == '__main__':
    main()
