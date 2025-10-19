#!/usr/bin/env python3
"""
Optimize Consensus Service Memory Usage
Applies conjecture about balancing memory and processing to prevent OOM killer
"""

import os
import sys
import json
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/coinjecture-consensus/logs/memory_optimization.log'),
        logging.StreamHandler()
    ]
)

class ConsensusMemoryOptimizer:
    def __init__(self):
        self.base_path = Path('/opt/coinjecture-consensus')
        self.consensus_service_path = self.base_path / 'consensus_service.py'
        self.systemd_service_path = Path('/etc/systemd/system/coinjecture-consensus.service')
        
        # Memory optimization parameters
        self.max_memory_mb = 512  # 512MB limit
        self.chunk_size = 25  # Process 25 blocks at a time
        self.memory_check_interval = 30  # Check memory every 30 seconds
        
    def optimize_consensus_service(self):
        """Optimize consensus service for memory efficiency"""
        logging.info("=== Optimizing Consensus Service Memory Usage ===")
        
        # Read current consensus service
        if not self.consensus_service_path.exists():
            logging.error("Consensus service file not found")
            return False
        
        try:
            with open(self.consensus_service_path, 'r') as f:
                content = self.consensus_service_path.read_text()
            
            # Apply memory optimizations
            optimized_content = self.apply_memory_optimizations(content)
            
            # Write optimized version
            with open(self.consensus_service_path, 'w') as f:
                f.write(optimized_content)
            
            logging.info("Applied memory optimizations to consensus service")
            return True
            
        except Exception as e:
            logging.error(f"Error optimizing consensus service: {e}")
            return False
    
    def apply_memory_optimizations(self, content):
        """Apply memory optimizations to consensus service code"""
        optimizations = [
            # Add memory monitoring
            ('import os', 'import os\nimport psutil\nimport gc'),
            
            # Add memory check method
            ('class ConsensusService:', '''class ConsensusService:
    def __init__(self):
        # ... existing init code ...
        self.max_memory_mb = 512  # 512MB limit
        self.memory_check_interval = 30  # Check every 30 seconds
        self.last_memory_check = 0
    
    def check_memory_usage(self):
        """Check current memory usage and trigger cleanup if needed"""
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            if memory_mb > self.max_memory_mb:
                logging.warning(f"Memory usage {memory_mb:.1f}MB exceeds limit {self.max_memory_mb}MB")
                self.cleanup_memory()
                return False
            return True
        except Exception as e:
            logging.error(f"Error checking memory usage: {e}")
            return True
    
    def cleanup_memory(self):
        """Clean up memory by forcing garbage collection"""
        try:
            gc.collect()
            logging.info("Performed memory cleanup")
        except Exception as e:
            logging.error(f"Error during memory cleanup: {e}'''),
            
            # Optimize block processing
            ('def process_block_events(self, events):', '''def process_block_events(self, events):
        """Process block events with memory optimization"""
        # Check memory before processing
        if not self.check_memory_usage():
            logging.warning("Memory limit reached, skipping block processing")
            return
        
        # Process events in smaller chunks
        chunk_size = 25
        for i in range(0, len(events), chunk_size):
            chunk = events[i:i + chunk_size]
            self.process_block_chunk(chunk)
            
            # Check memory after each chunk
            if not self.check_memory_usage():
                break
    
    def process_block_chunk(self, events):
        """Process a chunk of block events"""
        for event in events:
            try:
                self.process_single_block_event(event)
            except Exception as e:
                logging.error(f"Error processing block event: {e}")
                continue'''),
            
            # Add memory monitoring to main loop
            ('while True:', '''while True:
            # Check memory usage periodically
            current_time = time.time()
            if current_time - self.last_memory_check > self.memory_check_interval:
                self.check_memory_usage()
                self.last_memory_check = current_time'''),
        ]
        
        # Apply optimizations
        for old, new in optimizations:
            if old in content:
                content = content.replace(old, new)
                logging.info(f"Applied optimization: {old[:50]}...")
        
        return content
    
    def update_systemd_service(self):
        """Update systemd service with memory limits"""
        logging.info("=== Updating Systemd Service with Memory Limits ===")
        
        # Create optimized systemd service
        service_content = f"""[Unit]
Description=COINjecture Consensus Service (Memory Optimized)
After=network.target

[Service]
Type=simple
User=coinjecture
Group=coinjecture
WorkingDirectory=/opt/coinjecture-consensus
ExecStart=/opt/coinjecture-consensus/.venv/bin/python3 consensus_service.py
Restart=always
RestartSec=10

# Memory limits
MemoryLimit={self.max_memory_mb}M
MemoryAccounting=true

# Process limits
LimitNOFILE=65536
LimitNPROC=4096

# Environment
Environment=PYTHONPATH=/opt/coinjecture-consensus
Environment=PYTHONUNBUFFERED=1

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=coinjecture-consensus

[Install]
WantedBy=multi-user.target
"""
        
        try:
            # Write new service file
            with open(self.systemd_service_path, 'w') as f:
                f.write(service_content)
            
            # Reload systemd
            subprocess.run(['systemctl', 'daemon-reload'], check=True)
            logging.info("Updated systemd service with memory limits")
            return True
            
        except Exception as e:
            logging.error(f"Error updating systemd service: {e}")
            return False
    
    def install_memory_monitoring(self):
        """Install memory monitoring tools"""
        logging.info("=== Installing Memory Monitoring Tools ===")
        
        try:
            # Install psutil if not already installed
            subprocess.run(['pip3', 'install', 'psutil'], check=True)
            logging.info("Installed psutil for memory monitoring")
            return True
            
        except subprocess.CalledProcessError as e:
            logging.error(f"Error installing psutil: {e}")
            return False
    
    def apply_memory_optimizations(self):
        """Apply all memory optimizations"""
        logging.info("=== Applying Memory Optimizations ===")
        
        # Install monitoring tools
        if not self.install_memory_monitoring():
            return False
        
        # Optimize consensus service
        if not self.optimize_consensus_service():
            return False
        
        # Update systemd service
        if not self.update_systemd_service():
            return False
        
        logging.info("=== Memory Optimizations Applied Successfully ===")
        return True

def main():
    """Main function"""
    optimizer = ConsensusMemoryOptimizer()
    
    try:
        success = optimizer.apply_memory_optimizations()
        if success:
            print("Memory optimizations applied successfully")
            sys.exit(0)
        else:
            print("Memory optimizations failed")
            sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
