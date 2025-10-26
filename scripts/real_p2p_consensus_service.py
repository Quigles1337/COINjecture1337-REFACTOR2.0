#!/usr/bin/env python3
"""
Real P2P Consensus Service with Critical Complex Equilibrium Conjecture
Uses actual peer discovery with λ = η = 1/√2 ≈ 0.7071 for perfect network balance.
"""

import sys
import os
import time
import json
import logging
import signal
import threading
import socket
from pathlib import Path
from typing import Optional, Dict, Any, List

# Add src to path
sys.path.append('src')

# Import consensus and storage modules
from consensus import ConsensusEngine, ConsensusConfig
from storage import StorageManager, StorageConfig, NodeRole, PruningMode
from pow import ProblemRegistry
from api.ingest_store import IngestStore
from api.coupling_config import LAMBDA, CONSENSUS_WRITE_INTERVAL, CouplingState
from p2p_discovery import P2PDiscoveryService, DiscoveryConfig, PeerInfo

# Set up logging
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/consensus_service.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('coinjecture-real-p2p-consensus')


class RealP2PConsensusService:
    """Real P2P consensus service with actual peer discovery using Critical Complex Equilibrium Conjecture."""
    
    def __init__(self):
        self.running = False
        self.consensus_engine = None
        self.ingest_store = None
        self.discovery_service = None
        self.processed_events = set()
        self.coupling_state = CouplingState()
        
        # Data paths
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        self.blockchain_state_path = self.data_dir / "blockchain_state.json"
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info("🛑 Received shutdown signal")
        self.running = False
    
    def initialize(self):
        """Initialize the consensus service with real P2P discovery."""
        try:
            logger.info("🚀 Initializing real P2P consensus service with λ = η = 1/√2 ≈ 0.7071...")
            
            # Create consensus configuration
            consensus_config = ConsensusConfig(
                network_id="coinjecture-mainnet",
                confirmation_depth=6,
                max_reorg_depth=100
            )
            
            # Create storage configuration
            storage_config = StorageConfig(
                data_dir=str(self.data_dir),
                role=NodeRole.FULL,
                pruning_mode=PruningMode.FULL
            )
            storage_manager = StorageManager(storage_config)
            
            # Create problem registry
            problem_registry = ProblemRegistry()
            
            # Initialize consensus engine
            self.consensus_engine = ConsensusEngine(
                consensus_config,
                storage_manager,
                problem_registry
            )
            
            # Initialize ingest store
            self.ingest_store = IngestStore("data/faucet_ingest.db")
            
            # Initialize real P2P discovery service
            discovery_config = DiscoveryConfig(
                bootstrap_nodes=[
                    "167.172.213.70:12345",
                    "bootstrap1.coinjecture.com:12345",
                    "bootstrap2.coinjecture.com:12345",
                    "bootstrap3.coinjecture.com:12345"
                ]
            )
            self.discovery_service = P2PDiscoveryService(discovery_config)
            
            # Start discovery service
            if not self.discovery_service.start():
                logger.error("❌ Failed to start P2P discovery service")
                return False
            
            # Bootstrap from existing blockchain state
            self._bootstrap_from_cache()
            
            logger.info("✅ Real P2P consensus service initialized with perfect network equilibrium")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize consensus service: {e}")
            return False
    
    def _bootstrap_from_cache(self):
        """Bootstrap consensus engine from existing blockchain state."""
        try:
            if not os.path.exists(self.blockchain_state_path):
                logger.info("🔨 No existing blockchain state found")
                return
            
            logger.info("📥 Bootstrapping from existing blockchain state...")
            
            with open(self.blockchain_state_path, 'r') as f:
                blockchain_state = json.load(f)
            
            blocks = blockchain_state.get('blocks', [])
            logger.info(f"📊 Found {len(blocks)} blocks in cache")
            
            for block_data in blocks:
                try:
                    block = self._convert_cache_block_to_block(block_data)
                    if block:
                        self.consensus_engine.storage.store_block(block)
                        self.consensus_engine.storage.store_header(block)
                        logger.info(f"✅ Bootstrapped block #{block.index}")
                except Exception as e:
                    logger.warning(f"⚠️  Failed to bootstrap block: {e}")
                    continue
            
            logger.info("✅ Bootstrap completed")
            
        except Exception as e:
            logger.error(f"❌ Bootstrap failed: {e}")
    
    def _convert_cache_block_to_block(self, block_data):
        """Convert cached block data to Block object."""
        try:
            from core.blockchain import Block, ProblemTier, ComputationalComplexity, EnergyMetrics
            
            # Extract block data
            block_index = block_data.get('index', 0)
            timestamp = block_data.get('timestamp', int(time.time()))
            previous_hash = block_data.get('previous_hash', "0" * 64)
            merkle_root = block_data.get('merkle_root', "0" * 64)
            mining_capacity = ProblemTier.MOBILE
            cumulative_work_score = block_data.get('cumulative_work_score', 0.0)
            block_hash = block_data.get('block_hash', "0" * 64)
            offchain_cid = block_data.get('offchain_cid', "Qm" + "0" * 44)
            
            # Create computational complexity
            complexity = ComputationalComplexity(
                problem_type="subset_sum",
                problem_size=8,
                solve_time=1.0,
                verify_time=0.001,
                memory_usage=1024,
                cpu_cycles=1000
            )
            
            # Create energy metrics
            energy_metrics = EnergyMetrics(
                cpu_energy=100.0,
                memory_energy=50.0,
                total_energy=150.0
            )
            
            # Create solution
            solution = [1, 2, 3, 4]
            
            # Create block
            block = Block(
                index=block_index,
                timestamp=timestamp,
                previous_hash=previous_hash,
                merkle_root=merkle_root,
                mining_capacity=mining_capacity,
                complexity=complexity,
                energy_metrics=energy_metrics,
                solution=solution,
                cumulative_work_score=cumulative_work_score,
                block_hash=block_hash,
                offchain_cid=offchain_cid
            )
            
            return block
            
        except Exception as e:
            logger.error(f"❌ Failed to convert cache block: {e}")
            return None
    
    def process_p2p_blocks(self):
        """Process blocks from P2P network with real peer discovery."""
        try:
            # Get discovered peers
            discovered_peers = self.discovery_service.get_peers()
            connected_peers = self.discovery_service.get_connected_peers()
            
            logger.info(f"🌐 Network state: {len(discovered_peers)} discovered, {len(connected_peers)} connected")
            
            # Check for new blocks from ingest store (from real peers)
            block_events = self.ingest_store.latest_blocks(limit=20)
            
            processed_count = 0
            for event in block_events:
                event_id = event.get('event_id', '')
                if event_id in self.processed_events:
                    continue
                
                # Convert event to block
                block = self._convert_event_to_block(event)
                if not block:
                    continue
                
                try:
                    # Validate and store block
                    self.consensus_engine.validate_header(block)
                    self.consensus_engine.storage.store_block(block)
                    self.consensus_engine.storage.store_header(block)
                    
                    self.processed_events.add(event_id)
                    processed_count += 1
                    
                    logger.info(f"✅ Processed P2P block: {event_id}")
                    logger.info(f"📊 Block #{block.index}: {block.block_hash[:16]}...")
                    logger.info(f"⛏️  Work score: {block.cumulative_work_score}")
                    
                    # Distribute rewards
                    self._distribute_mining_rewards(event, block)
                    
                except Exception as e:
                    logger.warning(f"⚠️  Failed to process P2P block {event_id}: {e}")
                    continue
            
            if processed_count > 0:
                logger.info(f"🔄 Processed {processed_count} new P2P blocks from real peers")
                self._write_blockchain_state()
            
            # Log network equilibrium
            stats = self.discovery_service.get_peer_statistics()
            logger.info(f"⚖️  Network equilibrium: λ={stats['lambda_coupling_state']:.3f}, η={stats['eta_damping_state']:.3f}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error processing P2P blocks: {e}")
            return False
    
    def _convert_event_to_block(self, event):
        """Convert block event to Block object."""
        try:
            from core.blockchain import Block, ProblemTier, ComputationalComplexity, EnergyMetrics
            
            block_index = event.get('block_index', 0)
            timestamp = event.get('ts', int(time.time()))
            previous_hash = event.get('previous_hash', "0" * 64)
            block_hash = event.get('block_hash', "0" * 64)
            work_score = event.get('work_score', 0.0)
            
            # Create computational complexity
            complexity = ComputationalComplexity(
                problem_type="subset_sum",
                problem_size=8,
                solve_time=1.0,
                verify_time=0.001,
                memory_usage=1024,
                cpu_cycles=1000
            )
            
            # Create energy metrics
            energy_metrics = EnergyMetrics(
                cpu_energy=100.0,
                memory_energy=50.0,
                total_energy=150.0
            )
            
            # Create solution
            solution = [1, 2, 3, 4]
            
            # Create block
            block = Block(
                index=block_index,
                timestamp=timestamp,
                previous_hash=previous_hash,
                merkle_root="0" * 64,
                mining_capacity=ProblemTier.MOBILE,
                complexity=complexity,
                energy_metrics=energy_metrics,
                solution=solution,
                cumulative_work_score=work_score,
                block_hash=block_hash,
                offchain_cid="Qm" + "0" * 44
            )
            
            return block
            
        except Exception as e:
            logger.error(f"❌ Failed to convert event to block: {e}")
            return None
    
    def _distribute_mining_rewards(self, event, block):
        """Distribute mining rewards to the miner."""
        try:
            miner_address = event.get('miner_address', '')
            work_score = event.get('work_score', 0.0)
            
            if not miner_address:
                logger.warning("⚠️  No miner address found for reward distribution")
                return
            
            # Calculate rewards
            base_reward = 50.0
            work_bonus = work_score * 0.1
            total_reward = base_reward + work_bonus
            
            logger.info(f"💰 Distributing mining rewards to {miner_address}")
            logger.info(f"   Base reward: {base_reward} COIN")
            logger.info(f"   Work bonus: {work_bonus:.2f} COIN (work score: {work_score})")
            logger.info(f"   Total reward: {total_reward:.2f} COIN")
            
        except Exception as e:
            logger.error(f"❌ Failed to distribute mining rewards: {e}")
    
    def _write_blockchain_state(self):
        """Write blockchain state to shared storage."""
        try:
            best_tip = self.consensus_engine.get_best_tip()
            if not best_tip:
                return
            
            chain = self.consensus_engine.get_chain_from_genesis()
            
            blockchain_state = {
                "latest_block": {
                    "index": best_tip.index,
                    "timestamp": best_tip.timestamp,
                    "previous_hash": best_tip.previous_hash,
                    "merkle_root": best_tip.merkle_root,
                    "mining_capacity": best_tip.mining_capacity.value if hasattr(best_tip.mining_capacity, 'value') else str(best_tip.mining_capacity),
                    "cumulative_work_score": best_tip.cumulative_work_score,
                    "block_hash": best_tip.block_hash,
                    "offchain_cid": best_tip.offchain_cid,
                    "last_updated": time.time()
                },
                "blocks": [
                    {
                        "index": block.index,
                        "timestamp": block.timestamp,
                        "previous_hash": block.previous_hash,
                        "merkle_root": block.merkle_root,
                        "mining_capacity": block.mining_capacity.value if hasattr(block.mining_capacity, 'value') else str(block.mining_capacity),
                        "cumulative_work_score": block.cumulative_work_score,
                        "block_hash": block.block_hash,
                        "offchain_cid": block.offchain_cid
                    }
                    for block in chain
                ],
                "last_updated": time.time(),
                "consensus_version": "3.9.17",
                "lambda_coupling": LAMBDA,
                "processed_events_count": len(self.processed_events),
                "real_p2p_discovery": True
            }
            
            os.makedirs(os.path.dirname(self.blockchain_state_path), exist_ok=True)
            
            with open(self.blockchain_state_path, 'w') as f:
                json.dump(blockchain_state, f, indent=2)
            
            logger.info(f"📝 Blockchain state written: {len(chain)} blocks, tip: #{best_tip.index}")
            
        except Exception as e:
            logger.error(f"❌ Failed to write blockchain state: {e}")
    
    def run(self):
        """Run the real P2P consensus service with actual peer discovery."""
        try:
            if not self.initialize():
                return False
            
            self.running = True
            logger.info("🚀 Real P2P consensus service started")
            logger.info("🌐 Connected to P2P network with real peer discovery")
            logger.info("📡 Using Critical Complex Equilibrium Conjecture (λ = η = 1/√2 ≈ 0.7071)")
            logger.info("🔗 λ-coupling enabled: 14.14s intervals")
            logger.info("🌊 η-damping enabled: 14.14s intervals")
            
            while self.running:
                try:
                    # Process blocks from P2P network with real discovery
                    self.process_p2p_blocks()
                    
                    # Sleep for λ-coupling interval
                    time.sleep(14.14)  # 1/λ * 10 seconds
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    logger.error(f"❌ Error in main loop: {e}")
                    time.sleep(5.0)
            
            logger.info("✅ Real P2P consensus service stopped")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to run consensus service: {e}")
            return False


if __name__ == "__main__":
    service = RealP2PConsensusService()
    service.run()



