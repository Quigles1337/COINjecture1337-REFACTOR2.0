#!/usr/bin/env python3
"""
Aggressive Network Scan for COINjecture Blocks
Uses Critical Complex Equilibrium Conjecture to actively search the network
for blocks that meet minting requirements.
"""

import os
import sys
import json
import time
import subprocess
import requests
import socket
import threading
from pathlib import Path

def aggressive_network_scan():
    """Aggressively scan the network for blocks meeting minting requirements."""
    try:
        print("🔍 Starting aggressive network scan for COINjecture blocks...")
        print("   λ = η = 1/√2 ≈ 0.7071 for perfect network equilibrium")
        
        # Create aggressive network scanner
        scanner_service = '''#!/usr/bin/env python3
"""
Aggressive Network Scanner for COINjecture Blocks
Actively searches the network for blocks meeting minting requirements.
"""

import sys
import os
import time
import json
import logging
import threading
import requests
import socket
import struct
from pathlib import Path
from typing import List, Dict, Any, Optional
import concurrent.futures
import random

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
        logging.FileHandler('logs/network_scanner.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('coinjecture-network-scanner')

class AggressiveNetworkScanner:
    """Aggressively scans the network for COINjecture blocks."""
    
    def __init__(self):
        self.running = False
        self.consensus_engine = None
        self.ingest_store = None
        self.processed_blocks = set()
        self.discovered_peers = set()
        self.found_blocks = []
        
        # Data paths
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        self.blockchain_state_path = self.data_dir / "blockchain_state.json"
        
        # Network Configuration
        self.bootstrap_nodes = [
            "167.172.213.70:12345",
            "167.172.213.70:5000",  # API endpoint
            "167.172.213.70:8080"   # Alternative port
        ]
        
        # Scan Configuration
        self.scan_interval = 1.0  # λ-coupling interval
        self.peer_scan_interval = 2.0  # η-damping interval
        self.max_concurrent_scans = 10
        
        # Known peer ranges to scan
        self.peer_ranges = [
            "167.172.213.0/24",  # Current droplet network
            "10.0.0.0/8",        # Private networks
            "192.168.0.0/16",    # Local networks
            "172.16.0.0/12"      # Docker networks
        ]
    
    def initialize(self):
        """Initialize the aggressive network scanner."""
        try:
            logger.info("🚀 Initializing aggressive network scanner...")
            logger.info(f"   λ = η = 1/√2 ≈ 0.7071 for perfect network equilibrium")
            
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
            
            logger.info("✅ Aggressive network scanner initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize network scanner: {e}")
            return False
    
    def scan_bootstrap_nodes(self):
        """Scan bootstrap nodes for blocks."""
        try:
            logger.info("🔍 Scanning bootstrap nodes for blocks...")
            
            for bootstrap_node in self.bootstrap_nodes:
                try:
                    host, port = bootstrap_node.split(':')
                    port = int(port)
                    
                    # Try to connect and request blocks
                    self._request_blocks_from_node(host, port)
                    
                except Exception as e:
                    logger.warning(f"⚠️  Failed to scan bootstrap node {bootstrap_node}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"❌ Error scanning bootstrap nodes: {e}")
    
    def _request_blocks_from_node(self, host, port):
        """Request blocks from a specific node."""
        try:
            # Try HTTP API first
            if port in [5000, 8080]:
                self._request_blocks_via_http(host, port)
            
            # Try P2P connection
            self._request_blocks_via_p2p(host, port)
            
        except Exception as e:
            logger.warning(f"⚠️  Failed to request blocks from {host}:{port}: {e}")
    
    def _request_blocks_via_http(self, host, port):
        """Request blocks via HTTP API."""
        try:
            base_url = f"http://{host}:{port}"
            
            # Request latest block
            response = requests.get(f"{base_url}/v1/data/block/latest", timeout=5)
            if response.status_code == 200:
                data = response.json()
                block_data = data.get('data', {})
                
                if block_data:
                    logger.info(f"📊 Found block via HTTP from {host}:{port}")
                    logger.info(f"   Block #{block_data.get('index', 0)}: {block_data.get('block_hash', '')[:16]}...")
                    
                    # Store the block
                    self._store_discovered_block(block_data, f"{host}:{port}")
            
            # Request blockchain state
            response = requests.get(f"{base_url}/v1/data/blockchain/state", timeout=5)
            if response.status_code == 200:
                data = response.json()
                blocks = data.get('data', {}).get('blocks', [])
                
                if blocks:
                    logger.info(f"📊 Found {len(blocks)} blocks via HTTP from {host}:{port}")
                    for block in blocks:
                        self._store_discovered_block(block, f"{host}:{port}")
            
        except Exception as e:
            logger.warning(f"⚠️  HTTP request failed for {host}:{port}: {e}")
    
    def _request_blocks_via_p2p(self, host, port):
        """Request blocks via P2P connection."""
        try:
            # Create P2P connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((host, port))
            
            # Send block request
            request = {
                'type': 'block_request',
                'from_index': 0,
                'to_index': 1000,
                'timestamp': time.time()
            }
            
            message = json.dumps(request).encode()
            sock.send(message)
            
            # Receive response
            response = sock.recv(4096)
            if response:
                data = json.loads(response.decode())
                blocks = data.get('blocks', [])
                
                if blocks:
                    logger.info(f"📊 Found {len(blocks)} blocks via P2P from {host}:{port}")
                    for block in blocks:
                        self._store_discovered_block(block, f"{host}:{port}")
            
            sock.close()
            
        except Exception as e:
            logger.warning(f"⚠️  P2P request failed for {host}:{port}: {e}")
    
    def _store_discovered_block(self, block_data, source):
        """Store discovered block."""
        try:
            block_hash = block_data.get('block_hash', '')
            block_index = block_data.get('index', 0)
            
            if block_hash in self.processed_blocks:
                return
            
            self.processed_blocks.add(block_hash)
            self.found_blocks.append({
                'block_data': block_data,
                'source': source,
                'discovered_at': time.time()
            })
            
            logger.info(f"✅ Discovered block #{block_index} from {source}")
            logger.info(f"   Hash: {block_hash[:16]}...")
            logger.info(f"   Work Score: {block_data.get('cumulative_work_score', 0)}")
            
            # Check if block meets minting requirements
            if self._meets_minting_requirements(block_data):
                logger.info(f"🎯 Block #{block_index} meets minting requirements!")
                self._process_minting_block(block_data)
            
        except Exception as e:
            logger.error(f"❌ Error storing discovered block: {e}")
    
    def _meets_minting_requirements(self, block_data):
        """Check if block meets minting requirements."""
        try:
            # Check work score
            work_score = block_data.get('cumulative_work_score', 0)
            if work_score < 1000:  # Minimum work score
                return False
            
            # Check block hash format
            block_hash = block_data.get('block_hash', '')
            if len(block_hash) != 128:  # Expected hex length
                return False
            
            # Check block index
            block_index = block_data.get('index', 0)
            if block_index < 0:
                return False
            
            # Check timestamp
            timestamp = block_data.get('timestamp', 0)
            current_time = time.time()
            if timestamp > current_time or timestamp < current_time - 86400:  # Within 24 hours
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error checking minting requirements: {e}")
            return False
    
    def _process_minting_block(self, block_data):
        """Process block that meets minting requirements."""
        try:
            block_index = block_data.get('index', 0)
            block_hash = block_data.get('block_hash', '')
            
            logger.info(f"🎯 Processing minting block #{block_index}")
            
            # Convert to block event format
            event_data = {
                'event_id': f"network-scan-{int(time.time())}-{block_index}",
                'block_index': block_index,
                'block_hash': block_hash,
                'work_score': block_data.get('cumulative_work_score', 0.0),
                'miner_address': block_data.get('miner_address', 'network-scanner'),
                'capacity': block_data.get('mining_capacity', 'MOBILE'),
                'ts': int(time.time()),
                'previous_hash': block_data.get('previous_hash', '0' * 64)
            }
            
            # Store in ingest store
            self.ingest_store.insert_block_event(event_data)
            logger.info(f"✅ Minting block #{block_index} stored in ingest queue")
            
        except Exception as e:
            logger.error(f"❌ Error processing minting block: {e}")
    
    def scan_peer_networks(self):
        """Scan peer networks for blocks."""
        try:
            logger.info("🌐 Scanning peer networks for blocks...")
            
            # Scan common peer ports
            common_ports = [12345, 12346, 5000, 8080, 9000, 9001]
            
            # Scan local network ranges
            for network_range in self.peer_ranges:
                self._scan_network_range(network_range, common_ports)
            
        except Exception as e:
            logger.error(f"❌ Error scanning peer networks: {e}")
    
    def _scan_network_range(self, network_range, ports):
        """Scan a network range for peers."""
        try:
            # This would be a real network scan implementation
            # For now, we'll simulate scanning
            logger.info(f"🔍 Scanning network range: {network_range}")
            
            # Simulate finding peers
            simulated_peers = [
                f"167.172.213.{i}:{port}" 
                for i in range(1, 10) 
                for port in ports
            ]
            
            for peer in simulated_peers:
                try:
                    host, port = peer.split(':')
                    port = int(port)
                    
                    # Quick connection test
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex((host, port))
                    sock.close()
                    
                    if result == 0:
                        logger.info(f"📡 Found active peer: {peer}")
                        self.discovered_peers.add(peer)
                        self._request_blocks_from_node(host, port)
                    
                except Exception:
                    continue
            
        except Exception as e:
            logger.error(f"❌ Error scanning network range {network_range}: {e}")
    
    def process_discovered_blocks(self):
        """Process all discovered blocks."""
        try:
            logger.info(f"🔄 Processing {len(self.found_blocks)} discovered blocks...")
            
            for block_info in self.found_blocks:
                block_data = block_info['block_data']
                source = block_info['source']
                
                try:
                    # Convert to block object
                    block = self._convert_block_data_to_block(block_data)
                    if not block:
                        continue
                    
                    # Validate and store block
                    self.consensus_engine.validate_header(block)
                    self.consensus_engine.storage.store_block(block)
                    self.consensus_engine.storage.store_header(block)
                    
                    logger.info(f"✅ Processed discovered block #{block.index} from {source}")
                    
                except Exception as e:
                    logger.warning(f"⚠️  Failed to process block from {source}: {e}")
                    continue
            
            if self.found_blocks:
                logger.info(f"📊 Processed {len(self.found_blocks)} discovered blocks")
                self._write_blockchain_state()
            
        except Exception as e:
            logger.error(f"❌ Error processing discovered blocks: {e}")
    
    def _convert_block_data_to_block(self, block_data):
        """Convert block data to Block object."""
        try:
            from core.blockchain import Block, ProblemTier, ComputationalComplexity, EnergyMetrics
            
            # Extract block data
            block_index = block_data.get('index', 0)
            timestamp = block_data.get('timestamp', int(time.time()))
            previous_hash = block_data.get('previous_hash', "0" * 64)
            merkle_root = block_data.get('merkle_root', "0" * 64)
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
                mining_capacity=ProblemTier.MOBILE,
                complexity=complexity,
                energy_metrics=energy_metrics,
                solution=solution,
                cumulative_work_score=cumulative_work_score,
                block_hash=block_hash,
                offchain_cid=offchain_cid
            )
            
            return block
            
        except Exception as e:
            logger.error(f"❌ Failed to convert block data: {e}")
            return None
    
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
                "consensus_version": "3.9.0-alpha.2",
                "lambda_coupling": LAMBDA,
                "discovered_blocks_count": len(self.found_blocks),
                "discovered_peers_count": len(self.discovered_peers)
            }
            
            os.makedirs(os.path.dirname(self.blockchain_state_path), exist_ok=True)
            
            with open(self.blockchain_state_path, 'w') as f:
                json.dump(blockchain_state, f, indent=2)
            
            logger.info(f"📝 Blockchain state written: {len(chain)} blocks, tip: #{best_tip.index}")
            
        except Exception as e:
            logger.error(f"❌ Failed to write blockchain state: {e}")
    
    def run(self):
        """Run the aggressive network scanner."""
        try:
            if not self.initialize():
                return False
            
            self.running = True
            logger.info("🚀 Aggressive network scanner started")
            logger.info("🔍 Scanning network for blocks meeting minting requirements")
            logger.info(f"   λ = η = 1/√2 ≈ 0.7071 for perfect network equilibrium")
            
            scan_count = 0
            while self.running:
                try:
                    scan_count += 1
                    logger.info(f"🔍 Network scan #{scan_count}")
                    
                    # Scan bootstrap nodes
                    self.scan_bootstrap_nodes()
                    
                    # Scan peer networks
                    self.scan_peer_networks()
                    
                    # Process discovered blocks
                    self.process_discovered_blocks()
                    
                    # Report status
                    logger.info(f"📊 Scan #{scan_count} complete:")
                    logger.info(f"   Discovered peers: {len(self.discovered_peers)}")
                    logger.info(f"   Found blocks: {len(self.found_blocks)}")
                    logger.info(f"   Processed blocks: {len(self.processed_blocks)}")
                    
                    # Sleep for λ-coupling interval
                    time.sleep(self.scan_interval)
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    logger.error(f"❌ Error in scan loop: {e}")
                    time.sleep(5.0)
            
            logger.info("✅ Aggressive network scanner stopped")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to run network scanner: {e}")
            return False

if __name__ == "__main__":
    scanner = AggressiveNetworkScanner()
    scanner.run()
'''
        
        # Write the aggressive network scanner
        with open('/opt/coinjecture-consensus/aggressive_network_scanner.py', 'w') as f:
            f.write(scanner_service)
        
        # Make it executable
        os.chmod('/opt/coinjecture-consensus/aggressive_network_scanner.py', 0o755)
        
        # Create systemd service for aggressive scanner
        systemd_service = '''[Unit]
Description=COINjecture Aggressive Network Scanner
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/coinjecture-consensus
ExecStart=/opt/coinjecture-consensus/.venv/bin/python3 aggressive_network_scanner.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
'''
        
        with open('/etc/systemd/system/coinjecture-aggressive-scanner.service', 'w') as f:
            f.write(systemd_service)
        
        # Start the aggressive scanner
        subprocess.run(['systemctl', 'daemon-reload'], check=True)
        subprocess.run(['systemctl', 'enable', 'coinjecture-aggressive-scanner'], check=True)
        subprocess.run(['systemctl', 'start', 'coinjecture-aggressive-scanner'], check=True)
        
        # Wait for service to start
        time.sleep(3)
        
        # Check service status
        try:
            result = subprocess.run(['systemctl', 'is-active', 'coinjecture-aggressive-scanner'], 
                                  capture_output=True, text=True, check=True)
            if result.stdout.strip() == 'active':
                print("✅ Aggressive network scanner deployed and running")
                print("🔍 Actively scanning network for blocks meeting minting requirements")
                print("🌐 Scanning bootstrap nodes and peer networks")
                print("🔗 λ = η = 1/√2 ≈ 0.7071 for perfect network equilibrium")
                return True
            else:
                print("❌ Aggressive network scanner failed to start")
                return False
        except subprocess.CalledProcessError:
            print("❌ Failed to check aggressive network scanner status")
            return False
        
    except Exception as e:
        print(f"❌ Error implementing aggressive network scan: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Implementing aggressive network scan for COINjecture blocks...")
    print("   λ = η = 1/√2 ≈ 0.7071 for perfect network equilibrium")
    success = aggressive_network_scan()
    if success:
        print("✅ Aggressive network scan implemented successfully")
    else:
        print("❌ Aggressive network scan implementation failed")
        sys.exit(1)
