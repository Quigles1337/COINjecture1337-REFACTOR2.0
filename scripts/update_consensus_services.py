#!/usr/bin/env python3
"""
Update consensus services to use proper architecture with metrics engine
"""

import sys
import os
import time
import subprocess

def update_consensus_services():
    """Update consensus services to use metrics engine"""
    print("🔄 Updating consensus services to use proper architecture...")
    
    # Stop existing consensus services
    print("⏹️  Stopping existing consensus services...")
    subprocess.run(["pkill", "-f", "consensus_service"], check=False)
    subprocess.run(["pkill", "-f", "automatic_block_processor"], check=False)
    subprocess.run(["pkill", "-f", "p2p_consensus_service"], check=False)
    time.sleep(3)
    
    # Update consensus services to use metrics engine
    print("📝 Updating consensus service files...")
    
    # Create updated consensus service that uses metrics engine
    consensus_service_content = '''#!/usr/bin/env python3
"""
Updated consensus service with metrics engine integration
"""

import sys
import os
sys.path.append('/opt/coinjecture/src')

from consensus import ConsensusEngine, ConsensusConfig
from storage import StorageManager, StorageConfig
from pow import ProblemRegistry
from metrics_engine import get_metrics_engine, SATOSHI_CONSTANT
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main consensus service with metrics engine integration"""
    logger.info(f"🚀 Starting consensus service with Satoshi Constant: {SATOSHI_CONSTANT:.6f}")
    
    # Initialize components
    config = ConsensusConfig()
    storage = StorageManager(StorageConfig())
    problem_registry = ProblemRegistry()
    metrics_engine = get_metrics_engine()
    
    # Create consensus engine with metrics engine
    consensus = ConsensusEngine(config, storage, problem_registry, metrics_engine)
    
    logger.info("✅ Consensus service initialized with proper architecture")
    
    # Keep running
    while True:
        time.sleep(60)
        logger.info("💓 Consensus service heartbeat")

if __name__ == "__main__":
    main()
'''
    
    # Write updated consensus service
    with open('/opt/coinjecture/consensus_service_updated.py', 'w') as f:
        f.write(consensus_service_content)
    
    # Make it executable
    os.chmod('/opt/coinjecture/consensus_service_updated.py', 0o755)
    
    print("✅ Consensus services updated with metrics engine integration")
    print("🔄 Restarting consensus services...")
    
    # Start updated consensus service
    subprocess.Popen([
        "nohup", "python3", "/opt/coinjecture/consensus_service_updated.py",
        ">", "/opt/coinjecture/logs/consensus.log", "2>&1", "&"
    ], shell=True)
    
    print("✅ Updated consensus service started")

if __name__ == "__main__":
    update_consensus_services()
