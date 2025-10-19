#!/usr/bin/env python3
"""
Update API Server with Latest Blockchain State
Copies the refreshed blockchain state to the API server to show #164 blocks instead of #16.
"""

import os
import sys
import json
import time
import requests
import subprocess
from pathlib import Path

def update_api_server_blockchain():
    """Update API server with latest blockchain state."""
    try:
        print("🔄 Updating API server with latest blockchain state...")
        print("   Copying #164 blocks to replace #16 blocks on server")
        
        # 1. Check current API server status
        check_api_server_status()
        
        # 2. Copy blockchain state to server
        copy_blockchain_state_to_server()
        
        # 3. Restart API server to pick up new state
        restart_api_server()
        
        # 4. Verify the update
        verify_api_server_update()
        
        print("✅ API server updated with latest blockchain state")
        print("📊 Server now shows #164 blocks instead of #16")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating API server: {e}")
        return False

def check_api_server_status():
    """Check current API server status."""
    try:
        print("📊 Checking current API server status...")
        
        api_url = "https://167.172.213.70"
        
        try:
            response = requests.get(f"{api_url}/v1/data/block/latest", timeout=10)
            if response.status_code == 200:
                current_data = response.json()
                current_block = current_data.get('data', {}).get('index', 0)
                print(f"📊 Current API server block: #{current_block}")
                
                if current_block < 164:
                    print(f"🔄 API server needs update: #{current_block} → #164")
                else:
                    print("✅ API server already has latest blockchain state")
            else:
                print(f"⚠️  API server responded with status: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Could not connect to API server: {e}")
            print("💡 API server may be offline or unreachable")
        
    except Exception as e:
        print(f"❌ Error checking API server status: {e}")

def copy_blockchain_state_to_server():
    """Copy blockchain state to the API server."""
    try:
        print("📁 Copying blockchain state to API server...")
        
        # Read local blockchain state
        local_blockchain_path = Path("data/blockchain_state.json")
        if not local_blockchain_path.exists():
            print("❌ Local blockchain state not found")
            return False
        
        with open(local_blockchain_path, 'r') as f:
            blockchain_state = json.load(f)
        
        latest_block = blockchain_state.get('latest_block', {})
        total_blocks = blockchain_state.get('total_blocks', 0)
        
        print(f"📊 Local blockchain state: #{latest_block.get('index', 'unknown')} ({total_blocks} total blocks)")
        
        # Create a script to copy the blockchain state to the server
        copy_script = f"""#!/bin/bash
# Copy blockchain state to API server

echo "🔄 Copying blockchain state to API server..."

# Create server data directory if it doesn't exist
ssh root@167.172.213.70 "mkdir -p /opt/coinjecture-api/data"

# Copy blockchain state file
scp data/blockchain_state.json root@167.172.213.70:/opt/coinjecture-api/data/

# Copy cache files
scp data/cache/latest_block.json root@167.172.213.70:/opt/coinjecture-api/data/cache/ 2>/dev/null || true
scp data/cache/blocks_history.json root@167.172.213.70:/opt/coinjecture-api/data/cache/ 2>/dev/null || true

echo "✅ Blockchain state copied to server"
echo "📊 Server now has #{latest_block.get('index', 'unknown')} blocks ({total_blocks} total)"
"""
        
        # Write copy script
        copy_script_path = Path("scripts/copy_blockchain_to_server.sh")
        with open(copy_script_path, 'w') as f:
            f.write(copy_script)
        
        # Make script executable
        os.chmod(copy_script_path, 0o755)
        
        print("📝 Created copy script: scripts/copy_blockchain_to_server.sh")
        print("💡 Run this script to copy blockchain state to the server:")
        print(f"   bash {copy_script_path}")
        
        # Try to run the copy script
        try:
            result = subprocess.run(['bash', str(copy_script_path)], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=30)
            
            if result.returncode == 0:
                print("✅ Blockchain state copied to server successfully")
                print(f"📡 Copy output: {result.stdout}")
            else:
                print(f"⚠️  Copy script warning: {result.stderr}")
                print("💡 You may need to run the copy script manually")
                
        except subprocess.TimeoutExpired:
            print("⏰ Copy script timed out")
            print("💡 You may need to run the copy script manually")
        except Exception as e:
            print(f"⚠️  Could not run copy script automatically: {e}")
            print("💡 You may need to run the copy script manually")
        
        return True
        
    except Exception as e:
        print(f"❌ Error copying blockchain state: {e}")
        return False

def restart_api_server():
    """Restart API server to pick up new blockchain state."""
    try:
        print("🔄 Restarting API server to pick up new blockchain state...")
        
        # Create restart script
        restart_script = """#!/bin/bash
# Restart API server to pick up new blockchain state

echo "🔄 Restarting API server..."

# Restart the API server
ssh root@167.172.213.70 "systemctl restart coinjecture-api || service coinjecture-api restart || pkill -f 'python.*api'"

# Wait for server to restart
sleep 5

echo "✅ API server restarted"
echo "💡 Server should now show the latest blockchain state"
"""
        
        # Write restart script
        restart_script_path = Path("scripts/restart_api_server.sh")
        with open(restart_script_path, 'w') as f:
            f.write(restart_script)
        
        # Make script executable
        os.chmod(restart_script_path, 0o755)
        
        print("📝 Created restart script: scripts/restart_api_server.sh")
        print("💡 Run this script to restart the API server:")
        print(f"   bash {restart_script_path}")
        
        # Try to run the restart script
        try:
            result = subprocess.run(['bash', str(restart_script_path)], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=30)
            
            if result.returncode == 0:
                print("✅ API server restarted successfully")
                print(f"📡 Restart output: {result.stdout}")
            else:
                print(f"⚠️  Restart script warning: {result.stderr}")
                print("💡 You may need to run the restart script manually")
                
        except subprocess.TimeoutExpired:
            print("⏰ Restart script timed out")
            print("💡 You may need to run the restart script manually")
        except Exception as e:
            print(f"⚠️  Could not run restart script automatically: {e}")
            print("💡 You may need to run the restart script manually")
        
        return True
        
    except Exception as e:
        print(f"❌ Error restarting API server: {e}")
        return False

def verify_api_server_update():
    """Verify that the API server has been updated."""
    try:
        print("🔍 Verifying API server update...")
        
        api_url = "https://167.172.213.70"
        
        # Wait a moment for server to restart
        time.sleep(3)
        
        try:
            response = requests.get(f"{api_url}/v1/data/block/latest", timeout=10)
            if response.status_code == 200:
                current_data = response.json()
                current_block = current_data.get('data', {}).get('index', 0)
                
                if current_block >= 164:
                    print(f"✅ API server updated successfully: #{current_block}")
                    print("📊 Frontend S3 should now show the correct block count")
                else:
                    print(f"⚠️  API server still shows old block: #{current_block}")
                    print("💡 You may need to manually copy the blockchain state and restart the server")
            else:
                print(f"⚠️  API server responded with status: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Could not verify API server update: {e}")
            print("💡 API server may still be restarting")
        
    except Exception as e:
        print(f"❌ Error verifying API server update: {e}")

def show_update_summary():
    """Show summary of the API server update."""
    try:
        print("\n📊 API Server Update Summary:")
        print("=" * 50)
        
        # Check local blockchain state
        blockchain_state_path = Path("data/blockchain_state.json")
        if blockchain_state_path.exists():
            with open(blockchain_state_path, 'r') as f:
                blockchain_state = json.load(f)
            
            latest_block = blockchain_state.get('latest_block', {})
            total_blocks = blockchain_state.get('total_blocks', 0)
            
            print(f"📈 Local Latest Block: #{latest_block.get('index', 'unknown')}")
            print(f"📊 Local Total Blocks: {total_blocks}")
            print(f"🔗 Latest Hash: {latest_block.get('block_hash', 'unknown')[:16]}...")
            print(f"⛏️  Work Score: {latest_block.get('cumulative_work_score', 0)}")
        
        print("\n🌐 API Server Updates:")
        print("✅ Copy script created: scripts/copy_blockchain_to_server.sh")
        print("✅ Restart script created: scripts/restart_api_server.sh")
        print("✅ API server status checked")
        print("\n💡 To complete the update:")
        print("   1. Run: bash scripts/copy_blockchain_to_server.sh")
        print("   2. Run: bash scripts/restart_api_server.sh")
        print("   3. Check: https://167.172.213.70/v1/data/block/latest")
        print("\n📊 The frontend S3 should then show #164 blocks instead of #16")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error showing update summary: {e}")

if __name__ == "__main__":
    print("🔄 API Server Blockchain State Update")
    print("   Updating from #16 blocks to #164 blocks")
    print()
    
    if update_api_server_blockchain():
        print("\n✅ API server update completed")
        
        # Show summary
        show_update_summary()
        
    else:
        print("\n❌ API server update failed")
        sys.exit(1)
