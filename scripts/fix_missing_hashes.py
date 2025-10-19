#!/usr/bin/env python3
"""
Fix Missing Hash Fields in Blockchain State
Applies conjecture about balancing memory and processing
"""

import os
import sys
import json
import hashlib
import logging
import time
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/coinjecture-consensus/logs/fix_missing_hashes.log'),
        logging.StreamHandler()
    ]
)

class MissingHashFixer:
    def __init__(self):
        self.base_path = Path('/opt/coinjecture-consensus')
        self.blockchain_state_path = self.base_path / 'data' / 'blockchain_state.json'
        
        # Memory management parameters
        self.max_memory_usage = 0.8  # 80% of available memory
        self.chunk_size = 100  # Process 100 blocks at a time
        
    def get_memory_usage(self):
        """Get current memory usage percentage"""
        try:
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
            
            lines = meminfo.split('\n')
            mem_total = 0
            mem_available = 0
            
            for line in lines:
                if line.startswith('MemTotal:'):
                    mem_total = int(line.split()[1]) * 1024
                elif line.startswith('MemAvailable:'):
                    mem_available = int(line.split()[1]) * 1024
            
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
    
    def generate_block_hash(self, block):
        """Generate hash for a block based on its content"""
        try:
            # Create hash from block content
            block_data = {
                'index': block.get('index', 0),
                'previous_hash': block.get('previous_hash', ''),
                'timestamp': block.get('timestamp', ''),
                'data': block.get('data', ''),
                'nonce': block.get('nonce', 0)
            }
            
            # Convert to string and hash
            block_string = json.dumps(block_data, sort_keys=True)
            block_hash = hashlib.sha256(block_string.encode()).hexdigest()
            
            return block_hash
        except Exception as e:
            logging.error(f"Error generating hash for block {block.get('index', 'unknown')}: {e}")
            return None
    
    def fix_blocks_in_chunks(self, blocks):
        """Fix missing hashes in memory-efficient chunks"""
        total_blocks = len(blocks)
        fixed_count = 0
        
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
                    # Check if hash is missing
                    if 'hash' not in block or not block['hash']:
                        # Generate hash
                        block_hash = self.generate_block_hash(block)
                        if block_hash:
                            block['hash'] = block_hash
                            fixed_count += 1
                            
                            # Log progress
                            if fixed_count % 50 == 0:
                                logging.info(f"Fixed {fixed_count} blocks")
                    
                except Exception as e:
                    logging.error(f"Error fixing block {block.get('index', 'unknown')}: {e}")
                    continue
            
            # Small delay between chunks
            time.sleep(0.1)
        
        return fixed_count
    
    def fix_missing_hashes(self):
        """Fix missing hash fields in blockchain state"""
        logging.info("=== Fixing Missing Hash Fields ===")
        
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
        
        # Fix blocks in memory-efficient chunks
        fixed_count = self.fix_blocks_in_chunks(blocks)
        logging.info(f"Fixed {fixed_count} blocks with missing hashes")
        
        # Save updated blockchain state
        try:
            with open(self.blockchain_state_path, 'w') as f:
                json.dump(blockchain_data, f, indent=2)
            logging.info("Saved updated blockchain state")
        except Exception as e:
            logging.error(f"Error saving blockchain state: {e}")
            return False
        
        # Final memory check
        final_memory = self.get_memory_usage()
        logging.info(f"Final memory usage: {final_memory:.2%}")
        
        logging.info("=== Missing Hash Fields Fixed Successfully ===")
        return True

def main():
    """Main function"""
    fixer = MissingHashFixer()
    
    try:
        success = fixer.fix_missing_hashes()
        if success:
            print("Missing hash fields fixed successfully")
            sys.exit(0)
        else:
            print("Failed to fix missing hash fields")
            sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
