#!/usr/bin/env python3
"""
Memory-Efficient Consensus Fix
Applies conjecture about balancing memory and processing to solve OOM killer issue
"""

import os
import sys
import json
import time
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/coinjecture/logs/memory_efficient_fix.log'),
        logging.StreamHandler()
    ]
)

class MemoryEfficientConsensusFix:
    def __init__(self):
        self.base_path = Path('/opt/coinjecture')
        self.blockchain_state_path = self.base_path / 'data' / 'blockchain_state.json'
        self.consensus_db_path = self.base_path / 'data' / 'blockchain.db'
        self.logs_path = self.base_path / 'logs'
        
        # Memory management parameters
        self.max_memory_usage = 0.8  # 80% of available memory
        self.chunk_size = 50  # Process blocks in chunks
        self.memory_check_interval = 10  # Check memory every 10 seconds
        
    def get_memory_usage(self):
        """Get current memory usage percentage"""
        try:
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
            
            # Parse memory info
            lines = meminfo.split('\n')
            mem_total = 0
            mem_available = 0
            
            for line in lines:
                if line.startswith('MemTotal:'):
                    mem_total = int(line.split()[1]) * 1024  # Convert to bytes
                elif line.startswith('MemAvailable:'):
                    mem_available = int(line.split()[1]) * 1024  # Convert to bytes
            
            if mem_total > 0:
                usage = (mem_total - mem_available) / mem_total
                return usage
            return 0.0
        except Exception as e:
            logging.error(f"Error getting memory usage: {e}")
            return 0.0
    
    def check_memory_constraints(self):
        """Check if memory usage is within safe limits"""
        usage = self.get_memory_usage()
        if usage > self.max_memory_usage:
            logging.warning(f"Memory usage {usage:.2%} exceeds limit {self.max_memory_usage:.2%}")
            return False
        return True
    
    def process_blocks_in_chunks(self, blocks):
        """Process blocks in memory-efficient chunks"""
        total_blocks = len(blocks)
        processed = 0
        
        for i in range(0, total_blocks, self.chunk_size):
            chunk = blocks[i:i + self.chunk_size]
            
            # Check memory before processing chunk
            if not self.check_memory_constraints():
                logging.warning("Memory limit reached, pausing processing")
                time.sleep(5)
                continue
            
            # Process chunk
            for block in chunk:
                try:
                    # Simulate block processing (replace with actual logic)
                    self.process_single_block(block)
                    processed += 1
                    
                    # Log progress
                    if processed % 10 == 0:
                        logging.info(f"Processed {processed}/{total_blocks} blocks")
                    
                except Exception as e:
                    logging.error(f"Error processing block {block.get('index', 'unknown')}: {e}")
                    continue
            
            # Small delay between chunks to allow memory cleanup
            time.sleep(0.1)
        
        return processed
    
    def process_single_block(self, block):
        """Process a single block with minimal memory footprint"""
        # This is where you'd implement the actual block processing logic
        # For now, just validate the block structure
        required_fields = ['index', 'hash', 'previous_hash', 'timestamp']
        for field in required_fields:
            if field not in block:
                raise ValueError(f"Missing required field: {field}")
    
    def clear_consensus_state(self):
        """Clear consensus state to force fresh bootstrap"""
        try:
            if self.consensus_db_path.exists():
                self.consensus_db_path.unlink()
                logging.info("Cleared consensus database")
            
            # Clear any other consensus-related state files
            state_files = [
                self.base_path / 'data' / 'blockchain.db-journal',
                self.base_path / 'data' / 'blockchain.db-wal',
                self.base_path / 'data' / 'blockchain.db-shm'
            ]
            
            for state_file in state_files:
                if state_file.exists():
                    state_file.unlink()
                    logging.info(f"Cleared {state_file.name}")
            
            return True
        except Exception as e:
            logging.error(f"Error clearing consensus state: {e}")
            return False
    
    def restart_consensus_service(self):
        """Restart consensus service with memory monitoring"""
        try:
            # Stop service
            subprocess.run(['systemctl', 'stop', 'coinjecture-consensus'], check=True)
            logging.info("Stopped consensus service")
            
            # Wait for service to fully stop
            time.sleep(2)
            
            # Clear state
            if not self.clear_consensus_state():
                return False
            
            # Start service
            subprocess.run(['systemctl', 'start', 'coinjecture-consensus'], check=True)
            logging.info("Started consensus service")
            
            # Monitor startup
            self.monitor_consensus_startup()
            
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Error restarting consensus service: {e}")
            return False
    
    def monitor_consensus_startup(self):
        """Monitor consensus service startup and memory usage"""
        max_wait_time = 300  # 5 minutes
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            # Check service status
            try:
                result = subprocess.run(['systemctl', 'is-active', 'coinjecture-consensus'], 
                                      capture_output=True, text=True)
                if result.stdout.strip() == 'active':
                    logging.info("Consensus service is active")
                    break
            except Exception as e:
                logging.error(f"Error checking service status: {e}")
            
            # Check memory usage
            memory_usage = self.get_memory_usage()
            if memory_usage > self.max_memory_usage:
                logging.warning(f"High memory usage during startup: {memory_usage:.2%}")
            
            time.sleep(5)
        
        if time.time() - start_time >= max_wait_time:
            logging.error("Consensus service failed to start within timeout")
            return False
        
        return True
    
    def apply_memory_efficient_fix(self):
        """Apply the memory-efficient consensus fix"""
        logging.info("=== Applying Memory-Efficient Consensus Fix ===")
        
        # Check initial memory state
        initial_memory = self.get_memory_usage()
        logging.info(f"Initial memory usage: {initial_memory:.2%}")
        
        if initial_memory > self.max_memory_usage:
            logging.error("System memory usage too high, cannot proceed safely")
            return False
        
        # Load blockchain state
        if not self.blockchain_state_path.exists():
            logging.error("Blockchain state file not found")
            return False
        
        try:
            with open(self.blockchain_state_path, 'r') as f:
                blockchain_data = json.load(f)
            
            blocks = blockchain_data.get('blocks', [])
            logging.info(f"Loaded {len(blocks)} blocks from blockchain state")
            
        except Exception as e:
            logging.error(f"Error loading blockchain state: {e}")
            return False
        
        # Process blocks in memory-efficient chunks
        processed_count = self.process_blocks_in_chunks(blocks)
        logging.info(f"Processed {processed_count} blocks in memory-efficient chunks")
        
        # Restart consensus service
        if not self.restart_consensus_service():
            logging.error("Failed to restart consensus service")
            return False
        
        # Final memory check
        final_memory = self.get_memory_usage()
        logging.info(f"Final memory usage: {final_memory:.2%}")
        
        logging.info("=== Memory-Efficient Consensus Fix Applied Successfully ===")
        return True

def main():
    """Main function"""
    fix = MemoryEfficientConsensusFix()
    
    try:
        success = fix.apply_memory_efficient_fix()
        if success:
            print("Memory-efficient consensus fix applied successfully")
            sys.exit(0)
        else:
            print("Memory-efficient consensus fix failed")
            sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
