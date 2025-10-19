#!/usr/bin/env python3
"""
Apply Conjecture Final Solution
Balances memory and processing to prevent OOM killer
"""

import os
import sys
import json
import subprocess
import logging
import time
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/coinjecture-consensus/logs/conjecture_final.log'),
        logging.StreamHandler()
    ]
)

class ConjectureFinalSolution:
    def __init__(self):
        self.base_path = Path('/opt/coinjecture-consensus')
        self.blockchain_state_path = self.base_path / 'data' / 'blockchain_state.json'
        
        # Memory management parameters based on conjecture
        self.max_memory_mb = 256  # 256MB limit (much lower)
        self.chunk_size = 10  # Process only 10 blocks at a time
        self.memory_check_interval = 5  # Check memory every 5 seconds
        
    def apply_conjecture_solution(self):
        """Apply the final conjecture solution"""
        logging.info("=== Applying Conjecture Final Solution ===")
        
        # 1. Update systemd service with strict memory limits
        self.update_systemd_service()
        
        # 2. Create memory-efficient consensus service
        self.create_memory_efficient_service()
        
        # 3. Set up memory monitoring
        self.setup_memory_monitoring()
        
        # 4. Restart services
        self.restart_services()
        
        logging.info("=== Conjecture Final Solution Applied ===")
        return True
    
    def update_systemd_service(self):
        """Update systemd service with strict memory limits"""
        logging.info("Updating systemd service with strict memory limits")
        
        service_content = f"""[Unit]
Description=COINjecture Consensus Service (Memory Optimized)
After=network.target

[Service]
Type=simple
User=coinjecture
Group=coinjecture
WorkingDirectory=/opt/coinjecture-consensus
ExecStart=/opt/coinjecture-consensus/.venv/bin/python3 consensus_service_memory_optimized.py
Restart=always
RestartSec=30

# Strict memory limits
MemoryLimit={self.max_memory_mb}M
MemoryAccounting=true
MemoryHigh={self.max_memory_mb}M

# Process limits
LimitNOFILE=65536
LimitNPROC=4096

# Environment
Environment=PYTHONPATH=/opt/coinjecture-consensus
Environment=PYTHONUNBUFFERED=1
Environment=PYTHONHASHSEED=0

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=coinjecture-consensus

[Install]
WantedBy=multi-user.target
"""
        
        try:
            with open('/etc/systemd/system/coinjecture-consensus.service', 'w') as f:
                f.write(service_content)
            
            subprocess.run(['systemctl', 'daemon-reload'], check=True)
            logging.info("Systemd service updated with strict memory limits")
            return True
            
        except Exception as e:
            logging.error(f"Error updating systemd service: {e}")
            return False
    
    def create_memory_efficient_service(self):
        """Create memory-efficient consensus service"""
        logging.info("Creating memory-efficient consensus service")
        
        service_content = '''#!/usr/bin/env python3
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
                lambda_param=LAMBDA,
                write_interval=CONSENSUS_WRITE_INTERVAL
            )
            
            storage_config = StorageConfig(
                node_role=NodeRole.CONSENSUS,
                pruning_mode=PruningMode.CONSENSUS
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
            
            logger.info("✅ Memory-efficient consensus service initialized")
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
                        self.consensus_engine.add_block(block)
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
                
                # Small delay to prevent excessive CPU usage
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("🛑 Consensus service stopped by user")
        except Exception as e:
            logger.error(f"❌ Consensus service error: {e}")
        finally:
            self.running = False
        
        return True
    
    def process_events_memory_efficient(self):
        """Process events with memory management"""
        try:
            # Get events from ingest store
            events = self.ingest_store.get_pending_events()
            
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
                        self.consensus_engine.process_event(event)
                    except Exception as e:
                        logger.error(f"Error processing event: {e}")
                        continue
                
                # Small delay between chunks
                time.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Error processing events: {e}")

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
'''
        
        try:
            with open('/opt/coinjecture-consensus/consensus_service_memory_optimized.py', 'w') as f:
                f.write(service_content)
            
            os.chmod('/opt/coinjecture-consensus/consensus_service_memory_optimized.py', 0o755)
            logging.info("Memory-efficient consensus service created")
            return True
            
        except Exception as e:
            logging.error(f"Error creating memory-efficient service: {e}")
            return False
    
    def setup_memory_monitoring(self):
        """Set up memory monitoring"""
        logging.info("Setting up memory monitoring")
        
        try:
            # Install psutil if not already installed
            subprocess.run(['pip3', 'install', 'psutil'], check=True)
            logging.info("Memory monitoring tools installed")
            return True
            
        except subprocess.CalledProcessError as e:
            logging.error(f"Error installing memory monitoring tools: {e}")
            return False
    
    def restart_services(self):
        """Restart services"""
        logging.info("Restarting services")
        
        try:
            # Stop current service
            subprocess.run(['systemctl', 'stop', 'coinjecture-consensus'], check=True)
            
            # Start new service
            subprocess.run(['systemctl', 'start', 'coinjecture-consensus'], check=True)
            
            # Wait for service to start
            time.sleep(10)
            
            # Check service status
            result = subprocess.run(['systemctl', 'is-active', 'coinjecture-consensus'], 
                                  capture_output=True, text=True)
            
            if result.stdout.strip() == 'active':
                logging.info("✅ Consensus service is running")
                return True
            else:
                logging.error("❌ Consensus service failed to start")
                return False
                
        except Exception as e:
            logging.error(f"Error restarting services: {e}")
            return False

def main():
    """Main function"""
    solution = ConjectureFinalSolution()
    
    try:
        success = solution.apply_conjecture_solution()
        if success:
            print("Conjecture final solution applied successfully")
            sys.exit(0)
        else:
            print("Conjecture final solution failed")
            sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
