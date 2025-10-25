#!/usr/bin/env python3
"""
Network Sync Service
Syncs blocks from network peers using proper consensus validation
"""

import sys
import os
import time
import logging
import json
import requests
from typing import Dict, Any, List, Optional

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from unified_consensus_service import UnifiedConsensusService
from metrics_engine import SATOSHI_CONSTANT

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NetworkSyncService:
    """
    Network sync service that fetches blocks from peers and validates them.
    
    Implements peer discovery and block synchronization.
    """
    
    def __init__(self):
        """Initialize network sync service."""
        logger.info(f"🌐 Initializing network sync service with Satoshi Constant: {SATOSHI_CONSTANT:.6f}")
        
        # Initialize unified consensus service
        self.consensus_service = UnifiedConsensusService()
        
        # Bootstrap peers
        self.bootstrap_peers = [
            "167.172.213.70:5000",
            "167.172.213.70:12346"
        ]
        
        # Discovered peers
        self.discovered_peers = []
        
        logger.info("✅ Network sync service initialized")
    
    def discover_peers(self) -> List[str]:
        """Discover peers from bootstrap nodes."""
        logger.info("🔍 Discovering peers from bootstrap nodes...")
        
        all_peers = set(self.bootstrap_peers)
        
        for bootstrap_peer in self.bootstrap_peers:
            try:
                # Try to get peer list from bootstrap node
                peer_url = f"http://{bootstrap_peer}/v1/network/peers"
                response = requests.get(peer_url, timeout=10)
                
                if response.status_code == 200:
                    peer_data = response.json()
                    if 'peers' in peer_data:
                        for peer in peer_data['peers']:
                            all_peers.add(peer)
                        logger.info(f"📡 Found {len(peer_data['peers'])} peers from {bootstrap_peer}")
                
            except Exception as e:
                logger.warning(f"⚠️  Could not discover peers from {bootstrap_peer}: {e}")
        
        self.discovered_peers = list(all_peers)
        logger.info(f"✅ Discovered {len(self.discovered_peers)} total peers")
        
        return self.discovered_peers
    
    def get_block_from_peer(self, peer: str, block_height: int) -> Optional[Dict[str, Any]]:
        """Get a specific block from a peer."""
        try:
            # Try to get block from peer
            block_url = f"http://{peer}/v1/data/block/{block_height}"
            response = requests.get(block_url, timeout=10)
            
            if response.status_code == 200:
                block_data = response.json()
                if 'data' in block_data:
                    return block_data['data']
            
        except Exception as e:
            logger.debug(f"Could not get block {block_height} from {peer}: {e}")
        
        return None
    
    def get_latest_block_height(self) -> int:
        """Get the latest block height from the network."""
        logger.info("📊 Getting latest block height from network...")
        
        latest_height = 0
        
        for peer in self.discovered_peers:
            try:
                # Try to get latest block info
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
        
        logger.info(f"✅ Latest network height: {latest_height}")
        return latest_height
    
    def sync_blocks_from_network(self, start_height: int = 0, max_blocks: int = 1000):
        """Sync blocks from network starting from given height."""
        logger.info(f"🔄 Starting block sync from height {start_height}")
        
        # Discover peers
        self.discover_peers()
        
        # Get latest height
        latest_height = self.get_latest_block_height()
        
        if latest_height <= start_height:
            logger.info("✅ Already synced to latest height")
            return
        
        # Sync blocks
        synced_count = 0
        failed_count = 0
        
        for height in range(start_height, min(latest_height + 1, start_height + max_blocks)):
            try:
                # Try to get block from multiple peers
                block_data = None
                
                for peer in self.discovered_peers:
                    block_data = self.get_block_from_peer(peer, height)
                    if block_data:
                        break
                
                if not block_data:
                    logger.warning(f"⚠️  Could not get block {height} from any peer")
                    failed_count += 1
                    continue
                
                # Process block through consensus
                result = self.consensus_service.process_block(block_data)
                
                if result.get('valid', False):
                    synced_count += 1
                    if synced_count % 100 == 0:
                        logger.info(f"✅ Synced {synced_count} blocks (height {height})")
                else:
                    logger.warning(f"❌ Block {height} validation failed: {result.get('error', 'Unknown')}")
                    failed_count += 1
                
                # Small delay to avoid overwhelming peers
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"❌ Error syncing block {height}: {e}")
                failed_count += 1
        
        logger.info(f"✅ Sync completed: {synced_count} blocks synced, {failed_count} failed")
    
    def run_sync_loop(self):
        """Run continuous sync loop."""
        logger.info("🔄 Starting continuous sync loop...")
        
        while True:
            try:
                # Get current local height
                current_height = 0  # This would get from local database
                
                # Sync new blocks
                self.sync_blocks_from_network(start_height=current_height, max_blocks=100)
                
                # Wait before next sync
                time.sleep(30)
                
            except KeyboardInterrupt:
                logger.info("⏹️  Sync loop stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Error in sync loop: {e}")
                time.sleep(10)

def main():
    """Main function to run network sync service."""
    try:
        logger.info("🚀 Starting Network Sync Service")
        
        # Create service
        sync_service = NetworkSyncService()
        
        # Initial sync from genesis
        sync_service.sync_blocks_from_network(start_height=0, max_blocks=2000)
        
        # Run continuous sync
        sync_service.run_sync_loop()
        
    except Exception as e:
        logger.error(f"❌ Fatal error in network sync service: {e}")
        raise

if __name__ == "__main__":
    main()
