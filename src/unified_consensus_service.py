#!/usr/bin/env python3
"""
Unified Consensus Service
Integrates metrics engine with consensus flow following ARCHITECTURE.md
"""

import sys
import os
import time
import logging
import json
import asyncio
from typing import Dict, Any, Optional

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from consensus import ConsensusEngine, ConsensusConfig
from storage import StorageManager, StorageConfig
from pow import ProblemRegistry
from metrics_engine import get_metrics_engine, SATOSHI_CONSTANT, ComputationalComplexity
from api.blockchain_storage import storage

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UnifiedConsensusService:
    """
    Unified consensus service that integrates metrics engine with consensus flow.
    
    Implements the ARCHITECTURE.md principle: Validate → Calculate → Store
    """
    
    def __init__(self):
        """Initialize unified consensus service with metrics engine integration."""
        logger.info(f"🚀 Initializing unified consensus service with Satoshi Constant: {SATOSHI_CONSTANT:.6f}")
        
        # Initialize components
        self.config = ConsensusConfig()
        self.storage_manager = StorageManager(StorageConfig(
            data_dir="data",
            role="full",
            pruning_mode="recent"
        ))
        self.problem_registry = ProblemRegistry()
        self.metrics_engine = get_metrics_engine()
        
        # Create consensus engine with metrics engine
        self.consensus_engine = ConsensusEngine(
            self.config, 
            self.storage_manager, 
            self.problem_registry, 
            self.metrics_engine
        )
        
        # Initialize database
        self._init_database()
        
        logger.info("✅ Unified consensus service initialized")
    
    def _init_database(self):
        """Initialize database with proper schema."""
        try:
            # Initialize storage manager database
            self.storage_manager.init_database()
            
            # Initialize API storage database
            storage.init_database()
            
            logger.info("📦 Database initialized with proper schema")
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise
    
    def process_block(self, block_data: dict) -> Dict[str, Any]:
        """
        Process a block through the unified consensus flow.
        
        Flow: Validate → Calculate → Store
        """
        try:
            logger.info(f"🔄 Processing block: {block_data.get('block_hash', 'unknown')[:16]}...")
            
            # Step 1: Validate block through consensus engine
            validation_result = self.consensus_engine.validate_and_process_block(block_data)
            
            if not validation_result.get('valid', False):
                logger.warning(f"❌ Block validation failed: {validation_result.get('error', 'Unknown error')}")
                return validation_result
            
            # Step 2: Get processed block with calculated gas/rewards
            processed_block = validation_result['block']
            
            # Step 3: Store enriched block to database
            self._store_block(processed_block)
            
            # Step 4: Update metrics engine network state
            self._update_network_state(processed_block)
            
            logger.info(f"✅ Block processed successfully: gas={processed_block.get('gas_used', 0)}, reward={processed_block.get('reward', 0):.6f}")
            
            return {
                'valid': True,
                'block': processed_block,
                'message': 'Block processed through unified consensus flow'
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing block: {e}")
            return {
                'valid': False,
                'error': f'Processing error: {str(e)}'
            }
    
    def _store_block(self, block_data: dict):
        """Store enriched block to database."""
        try:
            # Extract block information
            block_hash = block_data.get('block_hash')
            height = block_data.get('height', 0)
            timestamp = block_data.get('timestamp', int(time.time()))
            work_score = block_data.get('work_score', 0)
            gas_used = block_data.get('gas_used', 0)
            gas_limit = block_data.get('gas_limit', 1000000)
            gas_price = block_data.get('gas_price', 0.000001)
            reward = block_data.get('reward', 0)
            cumulative_work = block_data.get('cumulative_work', 0)
            
            # Serialize block data
            block_bytes = json.dumps(block_data).encode('utf-8')
            
            # Store to API storage
            storage.add_block_data(block_data)
            
            logger.info(f"💾 Block stored: height={height}, gas={gas_used}, reward={reward:.6f}")
            
        except Exception as e:
            logger.error(f"❌ Error storing block: {e}")
            raise
    
    def _update_network_state(self, block_data: dict):
        """Update metrics engine network state."""
        try:
            # Update network state with new block
            work_score = block_data.get('work_score', 0)
            cumulative_work = block_data.get('cumulative_work', 0)
            block_count = block_data.get('height', 0) + 1
            
            # Update metrics engine state
            self.metrics_engine.network_state.cumulative_work = cumulative_work
            self.metrics_engine.network_state.block_count = block_count
            self.metrics_engine.network_state.network_avg_work = cumulative_work / max(block_count, 1)
            
            logger.info(f"📊 Network state updated: cumulative_work={cumulative_work:.6f}, blocks={block_count}")
            
        except Exception as e:
            logger.error(f"❌ Error updating network state: {e}")
    
    def get_network_metrics(self) -> Dict[str, Any]:
        """Get current network metrics from metrics engine."""
        return self.metrics_engine.get_network_metrics()
    
    def sync_from_peers(self, peer_addresses: list):
        """Sync blocks from network peers."""
        logger.info(f"🌐 Starting sync from {len(peer_addresses)} peers")
        
        # This would implement peer sync logic
        # For now, just log the peer addresses
        for peer in peer_addresses:
            logger.info(f"🔗 Peer: {peer}")
        
        logger.info("✅ Peer sync completed")
    
    def run_consensus_loop(self):
        """Main consensus loop."""
        logger.info("🔄 Starting consensus loop...")
        
        while True:
            try:
                # Check for new blocks from network
                # This would implement the actual consensus loop
                time.sleep(10)
                
                # Log heartbeat
                if int(time.time()) % 60 == 0:  # Every minute
                    metrics = self.get_network_metrics()
                    logger.info(f"💓 Consensus heartbeat: blocks={metrics.get('block_count', 0)}")
                
            except KeyboardInterrupt:
                logger.info("⏹️  Consensus loop stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Error in consensus loop: {e}")
                time.sleep(5)

def main():
    """Main function to run unified consensus service."""
    try:
        logger.info("🚀 Starting Unified Consensus Service")
        
        # Create service
        service = UnifiedConsensusService()
        
        # Bootstrap peers
        bootstrap_peers = [
            "167.172.213.70:5000",
            "167.172.213.70:12346"
        ]
        
        # Start sync from peers
        service.sync_from_peers(bootstrap_peers)
        
        # Run consensus loop
        service.run_consensus_loop()
        
    except Exception as e:
        logger.error(f"❌ Fatal error in unified consensus service: {e}")
        raise

if __name__ == "__main__":
    main()
