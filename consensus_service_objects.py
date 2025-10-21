#!/usr/bin/env python3
"""
Object-Oriented COINjecture Consensus Service
All components are proper objects with clear interfaces and responsibilities.

Optimized with Critical Complex Equilibrium Conjecture (λ = η = 1/√2 ≈ 0.7071)
for optimal processing time and network stability.
"""
import time
import json
import logging
import sqlite3
import math
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod

# ============================================
# CRITICAL COUPLING CONSTANTS (0.707 OPTIMIZATION)
# ============================================

# Mathematical proof: λ = η at marginal stability boundary
# With unit norm: λ² + η² = 1 → λ = η = 1/√2 ≈ 0.7071
SQRT2 = math.sqrt(2)
LAMBDA = 1.0 / SQRT2  # ≈ 0.7071 - Consensus coupling constant
ETA = 1.0 / SQRT2     # ≈ 0.7071 - Damping constant

# Optimal processing intervals based on critical damping
BASE_PROCESSING_INTERVAL = 2.0  # Base processing interval (seconds)
OPTIMAL_PROCESSING_INTERVAL = BASE_PROCESSING_INTERVAL / LAMBDA  # ~2.83s with 0.7071

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('coinjecture-consensus-service')

@dataclass
class MiningEvent:
    """Represents a mining event with all necessary data."""
    event_id: str
    block_index: int
    block_hash: str
    cid: str
    miner_address: str
    capacity: str
    work_score: float
    timestamp: float
    previous_hash: str
    merkle_root: str
    signature: str
    public_key: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MiningEvent':
        """Create MiningEvent from dictionary."""
        return cls(
            event_id=data.get('event_id', ''),
            block_index=data.get('block_index', 0),
            block_hash=data.get('block_hash', ''),
            cid=data.get('cid', ''),
            miner_address=data.get('miner_address', ''),
            capacity=data.get('capacity', 'mobile'),
            work_score=data.get('work_score', 0.0),
            timestamp=data.get('ts', time.time()),
            previous_hash=data.get('previous_hash', ''),
            merkle_root=data.get('merkle_root', ''),
            signature=data.get('signature', ''),
            public_key=data.get('public_key', '')
        )

@dataclass
class BlockchainBlock:
    """Represents a blockchain block with all necessary data."""
    index: int
    timestamp: float
    previous_hash: str
    miner_address: str
    work_score: float
    capacity: str
    block_hash: str
    merkle_root: str
    transactions: List[Dict[str, Any]]

    @classmethod
    def from_mining_event(cls, event: MiningEvent) -> 'BlockchainBlock':
        """Create BlockchainBlock from MiningEvent."""
        return cls(
            index=event.block_index,
            timestamp=event.timestamp,
            previous_hash=event.previous_hash,
            miner_address=event.miner_address,
            work_score=event.work_score,
            capacity=event.capacity,
            block_hash=event.block_hash,
            merkle_root=event.merkle_root,
            transactions=[]
        )

class ComplexityFactory:
    """Factory for creating ComputationalComplexity objects."""
    
    @staticmethod
    def create_from_mining_event(event: MiningEvent):
        """Create ComputationalComplexity from MiningEvent."""
        from src.core.blockchain import ComputationalComplexity, ProblemTier, EnergyMetrics
        
        work_score = event.work_score
        capacity = event.capacity
        
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
        
        # Create complexity object with all required parameters
        return ComputationalComplexity(
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
            energy_metrics=energy_metrics,
            problem=None,  # Add missing problem parameter
            solution_quality=1.0  # Add missing solution_quality parameter
        )

class RewardsCalculator:
    """Handles reward calculations using dynamic tokenomics."""
    
    def __init__(self):
        self.tokenomics = None
        self._initialize_tokenomics()
    
    def _initialize_tokenomics(self):
        """Initialize the tokenomics system."""
        try:
            from src.tokenomics.dynamic_tokenomics import DynamicWorkScoreTokenomics
            self.tokenomics = DynamicWorkScoreTokenomics()
            logger.info("✅ Dynamic tokenomics system initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize tokenomics: {e}")
            self.tokenomics = None
    
    def calculate_reward(self, event: MiningEvent, block: BlockchainBlock) -> float:
        """Calculate reward for a mining event."""
        if not self.tokenomics:
            # Fallback to simple calculation
            return 50.0 + event.work_score * 0.1
        
        try:
            # Create complexity object
            complexity = ComplexityFactory.create_from_mining_event(event)
            
            # Create Block object for tokenomics
            from src.core.blockchain import Block, ProblemTier
            
            capacity_map = {
                'mobile': ProblemTier.TIER_1_MOBILE,
                'desktop': ProblemTier.TIER_2_DESKTOP,
                'workstation': ProblemTier.TIER_3_WORKSTATION,
                'server': ProblemTier.TIER_4_SERVER,
                'cluster': ProblemTier.TIER_5_CLUSTER
            }
            
            tier = capacity_map.get(event.capacity.lower(), ProblemTier.TIER_1_MOBILE)
            
            block_obj = Block(
                index=block.index,
                timestamp=block.timestamp,
                previous_hash=block.previous_hash,
                transactions=block.transactions,
                merkle_root=block.merkle_root,
                problem=None,
                solution=None,
                complexity=complexity,
                mining_capacity=tier,
                cumulative_work_score=event.work_score,
                block_hash=block.block_hash
            )
            
            # Calculate reward using dynamic tokenomics
            reward = self.tokenomics.calculate_block_reward(block_obj, complexity)
            
            # Record in tokenomics system
            self.tokenomics.record_block(block_obj, complexity, reward, event.miner_address)
            
            return reward
            
        except Exception as e:
            logger.error(f"❌ Failed to calculate reward: {e}")
            return 50.0 + event.work_score * 0.1

class DatabaseManager:
    """Manages database operations for rewards and blockchain state."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def update_miner_rewards(self, miner_address: str, reward: float, work_score: float):
        """Update miner rewards in database."""
        try:
            conn = sqlite3.connect(self.db_path)
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
    
    def get_latest_blocks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get latest blocks from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM block_events 
                ORDER BY ts DESC 
                LIMIT ?
            ''', (limit,))
            
            columns = [description[0] for description in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            conn.close()
            return results
            
        except Exception as e:
            logger.error(f"❌ Failed to get latest blocks: {e}")
            return []

class BlockchainManager:
    """Manages blockchain state and operations."""
    
    def __init__(self, blockchain_path: str):
        self.blockchain_path = blockchain_path
    
    def load_blockchain_state(self) -> Dict[str, Any]:
        """Load blockchain state from file."""
        try:
            with open(self.blockchain_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"❌ Failed to load blockchain state: {e}")
            return {"blocks": [], "latest_block": {}, "total_blocks": 0}
    
    def save_blockchain_state(self, blockchain_data: Dict[str, Any]):
        """Save blockchain state to file."""
        try:
            with open(self.blockchain_path, 'w') as f:
                json.dump(blockchain_data, f, indent=2)
        except Exception as e:
            logger.error(f"❌ Failed to save blockchain state: {e}")
    
    def add_block(self, block: BlockchainBlock):
        """Add a new block to the blockchain."""
        try:
            blockchain_data = self.load_blockchain_state()
            
            # Create block data
            block_data = {
                "index": block.index,
                "timestamp": block.timestamp,
                "previous_hash": block.previous_hash,
                "miner_address": block.miner_address,
                "work_score": block.work_score,
                "capacity": block.capacity,
                "block_hash": block.block_hash,
                "merkle_root": block.merkle_root,
                "transactions": block.transactions
            }
            
            # Add to blocks list
            blockchain_data['blocks'].append(block_data)
            blockchain_data['latest_block'] = block_data
            blockchain_data['total_blocks'] = len(blockchain_data['blocks'])
            
            # Save updated state
            self.save_blockchain_state(blockchain_data)
            
            logger.info(f"🆕 Added block #{block.index} to blockchain")
            
        except Exception as e:
            logger.error(f"❌ Failed to add block to blockchain: {e}")

class P2PDiscoveryManager:
    """Manages P2P network discovery."""
    
    def __init__(self):
        self.discovery_service = None
        self._initialize_discovery()
    
    def _initialize_discovery(self):
        """Initialize P2P discovery service."""
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
            
            self.discovery_service = P2PDiscoveryService(discovery_config)
            logger.info("🌐 P2P Discovery initialized")
        except Exception as e:
            logger.warning(f"⚠️  P2P Discovery not available: {e}")
            self.discovery_service = None
    
    def start_discovery(self) -> bool:
        """Start P2P discovery service."""
        if self.discovery_service:
            return self.discovery_service.start()
        return False
    
    def get_peer_statistics(self) -> Dict[str, Any]:
        """Get peer discovery statistics."""
        if self.discovery_service:
            return self.discovery_service.get_peer_statistics()
        return {"total_discovered": 0, "active_peers": 0}

class CouplingState:
    """
    Track coupling state for 0.707 optimization.
    Implements critical damping with λ = η = 1/√2 ≈ 0.7071
    """
    
    def __init__(self):
        # Initialize with old timestamps to prevent immediate processing
        current_time = time.time()
        self.last_processing = current_time - OPTIMAL_PROCESSING_INTERVAL - 1.0
        self.processing_count = 0
        self.lambda_state = LAMBDA
        self.eta_state = ETA
        
    def can_process(self) -> bool:
        """Check if consensus can process (λ-coupled timing)."""
        current_time = time.time()
        return current_time - self.last_processing >= OPTIMAL_PROCESSING_INTERVAL
    
    def record_processing(self):
        """Record consensus processing with coupling timing."""
        self.last_processing = time.time()
        self.processing_count += 1
    
    def get_coupling_metrics(self) -> dict:
        """Get current coupling metrics."""
        current_time = time.time()
        time_since_processing = current_time - self.last_processing
        
        return {
            'optimal_processing_interval': OPTIMAL_PROCESSING_INTERVAL,
            'time_since_last_processing': time_since_processing,
            'processing_count': self.processing_count,
            'lambda': self.lambda_state,
            'eta': self.eta_state,
            'critical_damping_active': True
        }

class ObjectOrientedConsensusService:
    """Main consensus service using object-oriented architecture."""
    
    def __init__(self):
        self.running = False
        self.rewards_calculator = RewardsCalculator()
        self.database_manager = DatabaseManager("/opt/coinjecture-consensus/data/faucet_ingest.db")
        self.blockchain_manager = BlockchainManager("/opt/coinjecture-consensus/data/blockchain_state.json")
        self.p2p_discovery = P2PDiscoveryManager()
        self.coupling_state = CouplingState()  # 0.707 optimization
        
        logger.info("🚀 Object-oriented consensus service initialized with λ = η = 1/√2 ≈ 0.7071")
    
    def initialize(self) -> bool:
        """Initialize the consensus service with genesis block and P2P discovery."""
        try:
            # Load existing blockchain state
            blockchain_data = self.blockchain_manager.load_blockchain_state()
            existing_blocks = blockchain_data.get('blocks', [])
            
            if existing_blocks:
                logger.info(f"🔗 Found {len(existing_blocks)} existing blocks in blockchain state")
                logger.info(f"📊 Genesis block: #{existing_blocks[0].get('index', 0)}")
                logger.info(f"📊 Latest block: #{existing_blocks[-1].get('index', 0)}")
            else:
                logger.warning("⚠️  No existing blockchain state found")
            
            # Start P2P discovery to find all network blocks
            if self.p2p_discovery.start_discovery():
                logger.info("✅ P2P Discovery started")
                time.sleep(10)  # Wait for discovery to find all peers
                
                stats = self.p2p_discovery.get_peer_statistics()
                logger.info(f"📊 Discovered {stats['total_discovered']} peers")
                
                # Process all discovered blocks from P2P network
                self._process_network_blocks()
            else:
                logger.warning("⚠️  P2P Discovery failed to start")
            
            logger.info("✅ Object-oriented consensus service initialized with genesis anchor")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize consensus service: {e}")
            return False
    
    def _process_network_blocks(self):
        """Process all blocks discovered from P2P network."""
        try:
            # Get all blocks from database that aren't in current blockchain state
            all_events = self.database_manager.get_latest_blocks(limit=50000)  # Get all blocks
            
            logger.info(f"🔄 Processing {len(all_events)} blocks from P2P network...")
            
            processed_count = 0
            for event_data in all_events:
                if event_data.get('work_score', 0) > 0:
                    # Create objects from data
                    event = MiningEvent.from_dict(event_data)
                    block = BlockchainBlock.from_mining_event(event)
                    
                    # Calculate reward using dynamic tokenomics
                    reward = self.rewards_calculator.calculate_reward(event, block)
                    
                    # Update database with proper rewards
                    self.database_manager.update_miner_rewards(event.miner_address, reward, event.work_score)
                    
                    processed_count += 1
                    
                    if processed_count % 1000 == 0:
                        logger.info(f"   Processed {processed_count}/{len(all_events)} blocks...")
            
            logger.info(f"✅ Processed {processed_count} blocks from P2P network")
            
        except Exception as e:
            logger.error(f"❌ Failed to process network blocks: {e}")
    
    def process_mining_event(self, event_data: Dict[str, Any]):
        """Process a mining event."""
        try:
            # Create objects from data
            event = MiningEvent.from_dict(event_data)
            block = BlockchainBlock.from_mining_event(event)
            
            # Calculate reward
            reward = self.rewards_calculator.calculate_reward(event, block)
            
            # Update database
            self.database_manager.update_miner_rewards(event.miner_address, reward, event.work_score)
            
            # Add to blockchain
            self.blockchain_manager.add_block(block)
            
            logger.info(f"💰 Processed mining event: {reward:.6f} BEANS to {event.miner_address}")
            
        except Exception as e:
            logger.error(f"❌ Failed to process mining event: {e}")
    
    def get_coupling_metrics(self) -> dict:
        """Get current coupling metrics for monitoring."""
        return self.coupling_state.get_coupling_metrics()
    
    def run(self):
        """Main service loop with 0.707 critical damping optimization."""
        self.running = True
        logger.info("🔄 Starting object-oriented consensus service with λ = η = 1/√2 ≈ 0.7071")
        
        try:
            # First, ensure we have the full blockchain state loaded
            blockchain_data = self.blockchain_manager.load_blockchain_state()
            existing_blocks = blockchain_data.get('blocks', [])
            
            # Sort blocks by index for proper sequential processing
            existing_blocks.sort(key=lambda x: x.get('index', 0))
            total_blocks = len(existing_blocks)
            logger.info(f"📊 Blockchain state loaded: {total_blocks} blocks")
            
            if total_blocks > 0:
                logger.info(f"🔗 Genesis block: #{existing_blocks[0].get('index', 0)}")
                logger.info(f"🔗 Latest block: #{existing_blocks[-1].get('index', 0)}")
            
            # Process all blocks in proper order
            self._process_all_blocks_sequentially()
            
            while self.running:
                # Use 0.707 critical damping for optimal processing timing
                if self.coupling_state.can_process():
                    # Process new mining events only
                    recent_events = self.database_manager.get_latest_blocks(limit=5)
                    
                    for event_data in recent_events:
                        if event_data.get('work_score', 0) > 0:
                            # Check if this block is already processed
                            block_index = event_data.get('block_index', 0)
                            if not self._is_block_processed(block_index):
                                self.process_mining_event(event_data)
                    
                    # Record processing with coupling timing
                    self.coupling_state.record_processing()
                    
                    # Update blockchain state periodically
                    current_data = self.blockchain_manager.load_blockchain_state()
                    current_blocks = len(current_data.get('blocks', []))
                    if current_blocks != total_blocks:
                        logger.info(f"📈 Blockchain height updated: {current_blocks} blocks")
                        total_blocks = current_blocks
                        
                        # Log coupling metrics every 100 blocks
                        if current_blocks % 100 == 0:
                            metrics = self.coupling_state.get_coupling_metrics()
                            logger.info(f"⚖️  Critical damping: λ={metrics['lambda']:.3f}, η={metrics['eta']:.3f}, "
                                      f"interval={metrics['optimal_processing_interval']:.2f}s")
                
                # Optimal delay based on critical damping (λ = η = 1/√2)
                time.sleep(0.1)  # Check every 100ms, but process only at optimal intervals
                
        except KeyboardInterrupt:
            logger.info("🛑 Consensus service stopped by user")
        except Exception as e:
            logger.error(f"❌ Consensus service error: {e}")
        finally:
            self.running = False
        
        return True
    
    def _process_all_blocks_sequentially(self):
        """Process all blocks in proper sequential order."""
        try:
            # Get all blocks from database
            all_events = self.database_manager.get_latest_blocks(limit=50000)
            
            # Sort by block index for proper sequential processing
            all_events.sort(key=lambda x: x.get('block_index', 0))
            
            logger.info(f"🔄 Processing {len(all_events)} blocks in sequential order...")
            
            processed_count = 0
            for event_data in all_events:
                if event_data.get('work_score', 0) > 0:
                    # Create objects from data
                    event = MiningEvent.from_dict(event_data)
                    block = BlockchainBlock.from_mining_event(event)
                    
                    # Calculate reward using dynamic tokenomics
                    reward = self.rewards_calculator.calculate_reward(event, block)
                    
                    # Update database with proper rewards
                    self.database_manager.update_miner_rewards(event.miner_address, reward, event.work_score)
                    
                    processed_count += 1
                    
                    if processed_count % 1000 == 0:
                        logger.info(f"   Processed {processed_count}/{len(all_events)} blocks...")
            
            logger.info(f"✅ Processed {processed_count} blocks in sequential order")
            
        except Exception as e:
            logger.error(f"❌ Failed to process blocks sequentially: {e}")
    
    def _is_block_processed(self, block_index: int) -> bool:
        """Check if a block has already been processed."""
        try:
            blockchain_data = self.blockchain_manager.load_blockchain_state()
            existing_blocks = blockchain_data.get('blocks', [])
            
            for block in existing_blocks:
                if block.get('index') == block_index:
                    return True
            return False
        except Exception:
            return False

def main():
    """Main function"""
    service = ObjectOrientedConsensusService()
    
    if service.initialize():
        service.run()
    else:
        logger.error("❌ Failed to initialize consensus service")
        return False
    
    return True

if __name__ == "__main__":
    main()
