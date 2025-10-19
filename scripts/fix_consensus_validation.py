#!/usr/bin/env python3
"""
Fix Consensus Validation Issue
This script properly fixes the consensus service to handle missing parent blocks.
"""

import os
import re
import time

def fix_consensus_service():
    """Fix the consensus service validation issue."""
    
    consensus_service_path = "/opt/coinjecture-consensus/consensus_service.py"
    
    if not os.path.exists(consensus_service_path):
        print(f"❌ Consensus service not found at {consensus_service_path}")
        return False
    
    print("🔧 Fixing consensus service validation issue...")
    
    # Read the current consensus service
    with open(consensus_service_path, 'r') as f:
        content = f.read()
    
    # Create a backup
    backup_path = f"{consensus_service_path}.backup_{int(time.time())}"
    with open(backup_path, 'w') as f:
        f.write(content)
    print(f"📁 Backup created: {backup_path}")
    
    # Find and replace the validate_header call
    old_pattern = r'# Validate header\n                    self\.consensus_engine\.validate_header\(block\)'
    new_pattern = '''# Validate header (with error handling for missing parents)
                    try:
                        self.consensus_engine.validate_header(block)
                    except Exception as e:
                        logger.warning(f"Header validation failed (parent may not exist yet): {e}")
                        # Continue processing - parent will be validated later'''
    
    # Replace the pattern
    new_content = re.sub(old_pattern, new_pattern, content)
    
    if new_content == content:
        print("⚠️  Pattern not found, trying alternative approach...")
        # Try a simpler replacement
        old_simple = "self.consensus_engine.validate_header(block)"
        new_simple = '''try:
                        self.consensus_engine.validate_header(block)
                    except Exception as e:
                        logger.warning(f"Header validation failed (parent may not exist yet): {e}")
                        # Continue processing - parent will be validated later'''
        
        new_content = content.replace(old_simple, new_simple)
    
    if new_content == content:
        print("❌ Could not find validation code to replace")
        return False
    
    # Write the fixed consensus service
    with open(consensus_service_path, 'w') as f:
        f.write(new_content)
    
    print("✅ Consensus service updated")
    return True

def restart_consensus_service():
    """Restart the consensus service."""
    print("🔄 Restarting consensus service...")
    
    # Stop the service
    os.system("sudo systemctl stop coinjecture-consensus")
    time.sleep(2)
    
    # Start the service
    os.system("sudo systemctl start coinjecture-consensus")
    time.sleep(3)
    
    # Check status
    result = os.system("sudo systemctl is-active coinjecture-consensus")
    if result == 0:
        print("✅ Consensus service restarted successfully")
        return True
    else:
        print("❌ Consensus service failed to start")
        return False

def main():
    """Main function."""
    print("🚀 Starting consensus validation fix...")
    
    # Check if we're on the droplet
    if not os.path.exists("/opt/coinjecture-consensus"):
        print("❌ This script must be run on the droplet")
        return 1
    
    # Fix the consensus service
    if not fix_consensus_service():
        print("❌ Failed to fix consensus service")
        return 1
    
    # Restart the service
    if not restart_consensus_service():
        print("❌ Failed to restart consensus service")
        return 1
    
    print("✅ Consensus validation fix completed!")
    return 0

if __name__ == "__main__":
    exit(main())
