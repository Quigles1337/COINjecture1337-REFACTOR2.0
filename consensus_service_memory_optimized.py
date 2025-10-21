#!/usr/bin/env python3
"""
Memory-Efficient Consensus Service
Applies conjecture about balancing memory and processing
"""

import os
import sys
import json
import time
import gc
import psutil
import logging
from pathlib import Path

# Add src to path
sys.path.append('src')

# Import consensus and storage modules
from consensus import ConsensusEngine, ConsensusConfig
from storage import StorageManager, StorageConfig, NodeRole, PruningMode
from pow import ProblemRegistry
from api.ingest_store import IngestStore
from api.coupling_config import LAMBDA, CONSENSUS_WRITE_INTERVAL, CouplingState

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

logger = logging.getLogger('coinjecture-consensus-service')

class MemoryEfficientConsensusService:
    def __init__(self):
        self.blockchain_state_path = "/opt/coinjecture-consensus/data/blockchain_state.json"
        self.max_memory_mb = 256  # 256MB limit
        self.chunk_size = 10  # Process 10 blocks at a time
        self.memory_check_interval = 5  # Check memory every 5 seconds
        self.last_memory_check = 0
        
        # Initialize components
        self.consensus_engine = None
        self.ingest_store = None
        self.running = False
        
        # Initialize P2P discovery for automatic blockchain growth
        try:
            from p2p_discovery import P2PDiscoveryService, DiscoveryConfig
            
            discovery_config = DiscoveryConfig(
                listen_port=12346,
                bootstrap_nodes=[
                    "167.172.213.70:12346",
                    "167.172.213.70:12345",
                    "167.172.213.70:5000"
                ],
                max_peers=100
            )
            
            self.p2p_discovery = P2PDiscoveryService(discovery_config)
            logger.info("🌐 P2P Discovery initialized for automatic blockchain growth")
        except Exception as e:
            logger.warning(f"⚠️  P2P Discovery not available: {e}")
            self.p2p_discovery = None
        
    def check_memory_usage(self):
        """Check current memory usage and trigger cleanup if needed"""
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            if memory_mb > self.max_memory_mb:
                logger.warning(f"Memory usage {memory_mb:.1f}MB exceeds limit {self.max_memory_mb}MB")
                self.cleanup_memory()
                return False
            return True
        except Exception as e:
            logger.error(f"Error checking memory usage: {e}")
            return True
    
    def cleanup_memory(self):
        """Clean up memory by forcing garbage collection"""
        try:
            gc.collect()
            logger.info("Performed memory cleanup")
        except Exception as e:
            logger.error(f"Error during memory cleanup: {e}")
    
    def initialize(self):
        """Initialize the consensus service with memory management"""
        try:
            logger.info("🚀 Initializing memory-efficient consensus service")
            
            # Check memory before initialization
            if not self.check_memory_usage():
                logger.error("Memory usage too high, cannot initialize")
                return False
            
            # Initialize consensus engine with memory limits
            consensus_config = ConsensusConfig(
                
                
            )
            
            storage_config = StorageConfig("/opt/coinjecture-consensus/data", 
                role=NodeRole.FULL,
                pruning_mode=PruningMode.FULL
            )
            
            storage_manager = StorageManager(storage_config)
            problem_registry = ProblemRegistry()
            
            self.consensus_engine = ConsensusEngine(
                consensus_config,
                storage_manager,
                problem_registry
            )
            
            # Initialize ingest store
            self.ingest_store = IngestStore("/opt/coinjecture-consensus/data/faucet_ingest.db")
            
            # Bootstrap from existing blockchain state with memory management
            if not self.bootstrap_from_cache_memory_efficient():
                logger.warning("Bootstrap failed, starting fresh")
            
            # Start P2P discovery for automatic blockchain growth
            if self.p2p_discovery and self.p2p_discovery.start():
                logger.info("✅ P2P Discovery started - discovering ALL network peers for blockchain growth")
                time.sleep(5)  # Wait for initial discovery
                
                stats = self.p2p_discovery.get_peer_statistics()
                logger.info(f"📊 Discovered {stats['total_discovered']} peers for automatic blockchain growth")
            else:
                logger.warning("⚠️  P2P Discovery failed to start - blockchain may not grow automatically")
            
            logger.info("✅ Memory-efficient consensus service initialized with P2P discovery")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize consensus service: {e}")
            return False
    
    def bootstrap_from_cache_memory_efficient(self):
        """Bootstrap from cache with memory management"""
        try:
            if not os.path.exists(self.blockchain_state_path):
                logger.warning("Blockchain state file not found")
                return False
            
            with open(self.blockchain_state_path, 'r') as f:
                blockchain_data = json.load(f)
            
            blocks = blockchain_data.get('blocks', [])
            logger.info(f"📊 Found {len(blocks)} blocks in blockchain state")
            
            # Process blocks in memory-efficient chunks
            for i in range(0, len(blocks), self.chunk_size):
                chunk = blocks[i:i + self.chunk_size]
                
                # Check memory before processing chunk
                if not self.check_memory_usage():
                    logger.warning("Memory limit reached, pausing bootstrap")
                    time.sleep(1)
                    continue
                
                # Process chunk
                for block in chunk:
                    try:
                        self.consensus_engine._add_block_to_tree(self._dict_to_block(block), time.time())
                        if block['index'] % 100 == 0:
                            logger.info(f"📦 Bootstrapped block #{block['index']} ({i + chunk.index(block) + 1}/{len(blocks)})")
                    except Exception as e:
                        logger.error(f"Error processing block {block.get('index', 'unknown')}: {e}")
                        continue
                
                # Small delay between chunks
                time.sleep(0.1)
            
            logger.info(f"✅ Successfully bootstrapped {len(blocks)} blocks")
            return True
            
        except Exception as e:
            logger.error(f"Error during bootstrap: {e}")
            return False
    
    def run(self):
        """Run the consensus service with memory management"""
        if not self.initialize():
            return False
        
        self.running = True
        logger.info("🔄 Starting consensus service main loop")
        
        try:
            while self.running:
                # Check memory usage periodically
                current_time = time.time()
                if current_time - self.last_memory_check > self.memory_check_interval:
                    self.check_memory_usage()
                    self.last_memory_check = current_time
                
                # Process events with memory management
                self.process_events_memory_efficient()
                
                # Process new mining submissions for blockchain growth
                self.process_new_mining_submissions()
                
                # Small delay to prevent excessive CPU usage
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("🛑 Consensus service stopped by user")
        except Exception as e:
            logger.error(f"❌ Consensus service error: {e}")
        finally:
            self.running = False
        
        return True
    
    def _dict_to_block(self, block_dict):
        """Convert dictionary to Block object."""
        from core.blockchain import Block, ComputationalComplexity, ProblemTier
        
        # Create proper complexity object from block data
        work_score = block_dict.get("work_score", 0.0)
        capacity = block_dict.get("capacity", "mobile")
        
        # Map capacity string to ProblemTier
        capacity_map = {
            'mobile': ProblemTier.TIER_1_MOBILE,
            'desktop': ProblemTier.TIER_2_DESKTOP,
            'workstation': ProblemTier.TIER_3_WORKSTATION,
            'server': ProblemTier.TIER_4_SERVER,
            'cluster': ProblemTier.TIER_5_CLUSTER
        }
        
        tier = capacity_map.get(capacity.lower(), ProblemTier.TIER_1_MOBILE)
        
        # Estimate problem size from work score
        problem_size = int(work_score.bit_length()) if work_score > 0 and isinstance(work_score, int) else 8
        
        # Create proper complexity object with correct parameters
        complexity = ComputationalComplexity(
            time_solve_O="O(n^2)",
            time_solve_Omega="Ω(n)",
            time_solve_Theta="Θ(n^2)",
            time_verify_O="O(1)",
            time_verify_Omega="Ω(1)",
            time_verify_Theta="Θ(1)",
            space_solve_O="O(n)",
            space_solve_Omega="Ω(n)",
            space_solve_Theta="Θ(n)",
            space_verify_O="O(1)",
            space_verify_Omega="Ω(1)",
            space_verify_Theta="Θ(1)",
            problem_class="NP",
            problem_size=problem_size,
            solution_size=problem_size,
            epsilon_approximation=None,
            asymmetry_time=work_score / 1000.0,
            asymmetry_space=1.0,
            measured_solve_time=work_score / 1000.0,
            measured_verify_time=0.001,
            measured_solve_space=1000000,
            measured_verify_space=10000,
            energy_metrics=EnergyMetrics(
                solve_energy_joules=work_score * 0.1,
                verify_energy_joules=0.01,
                solve_power_watts=100.0,
                verify_power_watts=10.0,
                solve_time_seconds=work_score / 1000.0,
                verify_time_seconds=0.001,
                cpu_utilization=80.0,
                memory_utilization=60.0,
                gpu_utilization=0.0
            )
        )
        
        # Create Block object with required fields
        block = Block(
            index=block_dict.get("index", 0),
            timestamp=block_dict.get("timestamp", 0),
            previous_hash=block_dict.get("previous_hash", ""),
            transactions=block_dict.get("transactions", []),
            merkle_root=block_dict.get("merkle_root", ""),
            problem=block_dict.get("problem", {}),
            solution=block_dict.get("solution", []),
            complexity=complexity,  # Proper ComputationalComplexity object
            mining_capacity=tier,  # Use ProblemTier instead of string
            cumulative_work_score=block_dict.get("cumulative_work_score", 0),
            block_hash=block_dict.get("block_hash", "")
        )
        block.index = block_dict.get("index", 0)
        block.timestamp = block_dict.get("timestamp", 0)
        block.previous_hash = block_dict.get("previous_hash", "")
        block.merkle_root = block_dict.get("merkle_root", "")
        block.transactions = block_dict.get("transactions", [])
        block.problem = block_dict.get("problem", {})
        block.solution = block_dict.get("solution", [])
        
        return block
    def process_events_memory_efficient(self):
        """Process events with memory management"""
        try:
            # Get events from ingest store
            events = self.ingest_store.latest_blocks(limit=100)
            
            if not events:
                return
            
            # Process events in small chunks
            for i in range(0, len(events), self.chunk_size):
                chunk = events[i:i + self.chunk_size]
                
                # Check memory before processing chunk
                if not self.check_memory_usage():
                    logger.warning("Memory limit reached, pausing event processing")
                    break
                
                # Process chunk
                for event in chunk:
                    try:
                        self.consensus_engine._add_block_to_tree(self._dict_to_block(event), time.time()) if isinstance(event, dict) else None
                    except Exception as e:
                        logger.error(f"Error processing event: {e}")
                        continue
                
                # Small delay between chunks
                time.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Error processing events: {e}")
    
    def process_new_mining_submissions(self):
        """Process new mining submissions and create blocks for blockchain growth"""
        try:
            # Get recent mining submissions from ingest store
            recent_events = self.ingest_store.latest_blocks(limit=10)
            
            for event in recent_events:
                if event.get('work_score', 0) > 0:  # Only process valid mining submissions
                    self.create_new_block_from_mining(event)
                    
        except Exception as e:
            logger.error(f"Error processing new mining submissions: {e}")
    
    def create_new_block_from_mining(self, mining_event):
        """Create a new block from mining submission to grow the blockchain"""
        try:
            # Get current blockchain height
            with open(self.blockchain_state_path, 'r') as f:
                blockchain_data = json.load(f)
            
            current_height = len(blockchain_data.get('blocks', []))
            new_height = current_height + 1
            
            # Create new block
            new_block = {
                "index": new_height,
                "timestamp": time.time(),
                "previous_hash": blockchain_data.get('latest_block', {}).get('block_hash', '0' * 64),
                "miner_address": mining_event.get('miner_address', 'unknown'),
                "work_score": mining_event.get('work_score', 0.0),
                "capacity": mining_event.get('capacity', 'mobile'),
                "block_hash": f"block_{new_height}_{int(time.time())}",
                "merkle_root": "0" * 64,
                "transactions": []
            }
            
            # Add block to blockchain state
            blockchain_data['blocks'].append(new_block)
            blockchain_data['latest_block'] = new_block
            blockchain_data['total_blocks'] = new_height
            
            # Write updated blockchain state
            with open(self.blockchain_state_path, 'w') as f:
                json.dump(blockchain_data, f, indent=2)
            
            logger.info(f"🆕 Created new block #{new_height} from mining submission by {mining_event.get('miner_address', 'unknown')}")
            
        except Exception as e:
            logger.error(f"Error creating new block from mining: {e}")
    
    def _distribute_mining_rewards(self, event, block):
        """Distribute mining rewards using dynamic tokenomics."""
        try:
            from src.tokenomics.dynamic_tokenomics import DynamicWorkScoreTokenomics
            
            if not hasattr(self, 'tokenomics'):
                self.tokenomics = DynamicWorkScoreTokenomics()
            
            # Create complexity object from event
            complexity = self._create_complexity_from_event(event)
            
            # Calculate reward using dynamic tokenomics
            reward = self.tokenomics.calculate_block_reward(block, complexity)
            
            # Record in tokenomics system
            miner_address = event.get('miner_address', '')
            self.tokenomics.record_block(block, complexity, reward, miner_address)
            
            # Update database
            self._update_rewards_database(miner_address, reward, event.get('work_score', 0.0))
            
            logger.info(f"💰 Dynamic reward: {reward:.6f} BEANS to {miner_address}")
            logger.info(f"   Deflation factor: {self.tokenomics._calculate_deflation_factor():.6f}")
            logger.info(f"   Cumulative work: {self.tokenomics.cumulative_work_score:,.0f}")
            
        except Exception as e:
            logger.error(f"❌ Failed to distribute mining rewards: {e}")
    
    def _create_complexity_from_event(self, event):
        """Create ComputationalComplexity object from mining event."""
        from src.core.blockchain import ComputationalComplexity, ProblemTier, EnergyMetrics
        
        work_score = event.get('work_score', 0.0)
        capacity = event.get('capacity', 'mobile')
        
        # Map capacity string to ProblemTier
        capacity_map = {
            'mobile': ProblemTier.TIER_1_MOBILE,
            'desktop': ProblemTier.TIER_2_DESKTOP,
            'workstation': ProblemTier.TIER_3_WORKSTATION,
            'server': ProblemTier.TIER_4_SERVER,
            'cluster': ProblemTier.TIER_5_CLUSTER
        }
        
        tier = capacity_map.get(capacity.lower(), ProblemTier.TIER_1_MOBILE)
        
        # Estimate problem size from work score
        problem_size = int(work_score.bit_length()) if work_score > 0 and isinstance(work_score, int) else 8
        
        # Create energy metrics object
        energy_metrics = EnergyMetrics(
            solve_energy_joules=work_score * 0.1,
            verify_energy_joules=0.01,
            solve_power_watts=100.0,
            verify_power_watts=10.0,
            solve_time_seconds=work_score / 1000.0,
            verify_time_seconds=0.001,
            cpu_utilization=80.0,
            memory_utilization=60.0,
            gpu_utilization=0.0
        )
        
        # Create complexity object with correct parameters
        complexity = ComputationalComplexity(
            time_solve_O="O(n^2)",
            time_solve_Omega="Ω(n)",
            time_solve_Theta="Θ(n^2)",
            time_verify_O="O(1)",
            time_verify_Omega="Ω(1)",
            time_verify_Theta="Θ(1)",
            space_solve_O="O(n)",
            space_solve_Omega="Ω(n)",
            space_solve_Theta="Θ(n)",
            space_verify_O="O(1)",
            space_verify_Omega="Ω(1)",
            space_verify_Theta="Θ(1)",
            problem_class="NP",
            problem_size=problem_size,
            solution_size=problem_size,
            epsilon_approximation=None,
            asymmetry_time=work_score / 1000.0,
            asymmetry_space=1.0,
            measured_solve_time=work_score / 1000.0,
            measured_verify_time=0.001,
            measured_solve_space=1000000,
            measured_verify_space=10000,
            energy_metrics=energy_metrics
        )
        
        return complexity
    
    def _update_rewards_database(self, miner_address, reward, work_score):
        """Update rewards database with new reward."""
        try:
            import sqlite3
            
            # Connect to database
            conn = sqlite3.connect('/opt/coinjecture-consensus/data/faucet_ingest.db')
            cursor = conn.cursor()
            
            # Check if miner exists
            cursor.execute('SELECT total_rewards, blocks_mined, total_work_score FROM work_based_rewards WHERE miner_address = ?', (miner_address,))
            result = cursor.fetchone()
            
            if result:
                # Update existing miner
                total_rewards, blocks_mined, total_work_score = result
                new_total_rewards = total_rewards + reward
                new_blocks_mined = blocks_mined + 1
                new_total_work_score = total_work_score + work_score
                new_average_reward = new_total_rewards / new_blocks_mined
                new_average_work_score = new_total_work_score / new_blocks_mined
                
                cursor.execute('''
                    UPDATE work_based_rewards 
                    SET total_rewards = ?, blocks_mined = ?, total_work_score = ?, 
                        average_reward = ?, average_work_score = ?, last_updated = ?
                    WHERE miner_address = ?
                ''', (new_total_rewards, new_blocks_mined, new_total_work_score, 
                      new_average_reward, new_average_work_score, time.time(), miner_address))
            else:
                # Insert new miner
                cursor.execute('''
                    INSERT INTO work_based_rewards 
                    (miner_address, total_rewards, blocks_mined, total_work_score, 
                     average_reward, average_work_score, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (miner_address, reward, 1, work_score, reward, work_score, time.time()))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Failed to update rewards database: {e}")

def main():
    """Main function"""
    service = MemoryEfficientConsensusService()
    
    try:
        success = service.run()
        if success:
            logger.info("Consensus service completed successfully")
            sys.exit(0)
        else:
            logger.error("Consensus service failed")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

