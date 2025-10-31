#!/usr/bin/env python3
"""
Equilibrium Service
Standalone service that runs equilibrium gossip loops
Works independently of API server to maintain network equilibrium
"""

import os
import sys
import time
import logging
import threading
from typing import Optional

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from storage import StorageManager, StorageConfig, NodeRole, PruningMode
from consensus import ConsensusEngine, ConsensusConfig
from pow import ProblemRegistry
from network import NetworkProtocol

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('equilibrium-service')


class EquilibriumService:
    """Standalone equilibrium gossip service."""
    
    def __init__(self, data_dir: str = "data", ipfs_url: str = "http://localhost:5001"):
        self.data_dir = data_dir
        self.ipfs_url = ipfs_url
        self.network = None
        self.running = False
        
    def start(self):
        """Start equilibrium service."""
        logger.info("⚖️  Starting Equilibrium Service...")
        
        try:
            # Initialize storage
            storage_config = StorageConfig(
                data_dir=self.data_dir,
                role=NodeRole.FULL,
                pruning_mode=PruningMode.FULL,
                ipfs_api_url=self.ipfs_url
            )
            storage = StorageManager(storage_config)
            
            # Initialize consensus
            consensus_config = ConsensusConfig()
            problem_registry = ProblemRegistry()
            consensus = ConsensusEngine(consensus_config, storage, problem_registry)
            
            # Initialize network protocol
            self.network = NetworkProtocol(
                consensus=consensus,
                storage=storage,
                problem_registry=problem_registry,
                peer_id="equilibrium-service"
            )
            
            # Start equilibrium loops
            self.network.start_equilibrium_loops()
            
            self.running = True
            logger.info("✅ Equilibrium Service started")
            logger.info(f"   λ = {NetworkProtocol.LAMBDA:.4f}")
            logger.info(f"   η = {NetworkProtocol.ETA:.4f}")
            logger.info(f"   Broadcast interval: {NetworkProtocol.BROADCAST_INTERVAL:.2f}s")
            logger.info(f"   Listen interval: {NetworkProtocol.LISTEN_INTERVAL:.2f}s")
            logger.info(f"   Cleanup interval: {NetworkProtocol.CLEANUP_INTERVAL:.2f}s")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start Equilibrium Service: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def stop(self):
        """Stop equilibrium service."""
        logger.info("🛑 Stopping Equilibrium Service...")
        
        if self.network:
            self.network.stop_equilibrium_loops()
        
        self.running = False
        logger.info("✅ Equilibrium Service stopped")
    
    def announce_cid(self, cid: str):
        """Announce a CID for equilibrium gossip (can be called from API)."""
        if self.network:
            self.network.announce_proof(cid)
            logger.debug(f"📬 CID queued for equilibrium broadcast: {cid[:16]}...")
            return True
        else:
            logger.warning(f"⚠️  Network not initialized - CID not queued: {cid[:16]}...")
            return False
    
    def run(self):
        """Run the service (blocking)."""
        if not self.start():
            return
        
        try:
            logger.info("⚖️  Equilibrium Service running...")
            logger.info("   Monitoring network equilibrium...")
            logger.info("   Press Ctrl+C to stop")
            
            while self.running:
                time.sleep(60)  # Check every minute
                
                # Log current equilibrium state
                if self.network:
                    ratio = self.network.lambda_state / max(self.network.eta_state, 0.001)
                    logger.info(
                        f"⚖️  Equilibrium: λ={self.network.lambda_state:.4f}, "
                        f"η={self.network.eta_state:.4f}, ratio={ratio:.4f}, "
                        f"queued={len(self.network.pending_broadcasts)}, "
                        f"peers={len(self.network.peers)}"
                    )
        except KeyboardInterrupt:
            logger.info("\n🛑 Stopping Equilibrium Service...")
        finally:
            self.stop()


# Global instance (can be imported by API server)
_equilibrium_service = None


def get_equilibrium_service() -> Optional[EquilibriumService]:
    """Get or create global equilibrium service instance."""
    global _equilibrium_service
    if _equilibrium_service is None:
        _equilibrium_service = EquilibriumService()
    return _equilibrium_service


def start_equilibrium_service():
    """Start equilibrium service (can be called from API server)."""
    global _equilibrium_service
    if _equilibrium_service is None:
        _equilibrium_service = EquilibriumService()
    return _equilibrium_service.start()


if __name__ == '__main__':
    # Run as standalone service
    service = EquilibriumService()
    service.run()

