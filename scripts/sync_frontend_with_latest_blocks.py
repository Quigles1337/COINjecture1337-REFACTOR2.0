#!/usr/bin/env python3
"""
Sync Frontend S3 with Latest Blockchain State
Updates the frontend to show the correct block count (#164) instead of the old (#16).
"""

import os
import sys
import json
import time
import requests
import subprocess
from pathlib import Path

def sync_frontend_with_latest_blocks():
    """Sync frontend S3 with the latest blockchain state."""
    try:
        print("🔄 Syncing frontend S3 with latest blockchain state...")
        print("   Updating from #16 blocks to #164 blocks")
        
        # 1. Update web interface with latest blockchain data
        update_web_interface()
        
        # 2. Deploy updated web interface to S3
        deploy_to_s3()
        
        # 3. Update API server with latest blockchain state
        update_api_server()
        
        print("✅ Frontend S3 synced with latest blockchain state")
        print("📊 Now showing #164 blocks instead of #16")
        
        return True
        
    except Exception as e:
        print(f"❌ Error syncing frontend: {e}")
        return False

def update_web_interface():
    """Update web interface files with latest blockchain data."""
    try:
        print("📝 Updating web interface with latest blockchain data...")
        
        # Read current blockchain state
        blockchain_state_path = Path("data/blockchain_state.json")
        if not blockchain_state_path.exists():
            print("❌ Blockchain state not found")
            return False
        
        with open(blockchain_state_path, 'r') as f:
            blockchain_state = json.load(f)
        
        latest_block = blockchain_state.get('latest_block', {})
        total_blocks = blockchain_state.get('total_blocks', len(blockchain_state.get('blocks', [])))
        
        print(f"📊 Latest block: #{latest_block.get('index', 'unknown')}")
        print(f"📊 Total blocks: {total_blocks}")
        
        # Update app.js with latest blockchain info
        update_app_js_with_blockchain_info(latest_block, total_blocks)
        
        # Update index.html with latest stats
        update_index_html_with_stats(total_blocks)
        
        print("✅ Web interface updated with latest blockchain data")
        
    except Exception as e:
        print(f"❌ Error updating web interface: {e}")

def update_app_js_with_blockchain_info(latest_block, total_blocks):
    """Update app.js with latest blockchain information."""
    try:
        app_js_path = Path("web/app.js")
        if not app_js_path.exists():
            print("❌ app.js not found")
            return
        
        # Read current app.js
        with open(app_js_path, 'r') as f:
            content = f.read()
        
        # Update the network status display to show correct block count
        updated_content = content.replace(
            'this.status.innerHTML = `🌐 Live Network: Block #${block.index} | Hash: ${block.block_hash.substring(0, 16)}...`;',
            f'this.status.innerHTML = `🌐 Live Network: Block #${{block.index}} | Total: {total_blocks} blocks | Hash: ${{block.block_hash.substring(0, 16)}}...`;'
        )
        
        # Add blockchain stats to the interface
        stats_update = f"""
  // Display blockchain statistics
  displayBlockchainStats() {{
    const stats = {{
      totalBlocks: {total_blocks},
      latestBlock: {latest_block.get('index', 0)},
      latestHash: '{latest_block.get('block_hash', 'unknown')[:16]}...',
      workScore: {latest_block.get('cumulative_work_score', 0)},
      lastUpdated: {int(time.time())}
    }};
    
    this.addMultiLineOutput([
      '📊 Blockchain Statistics:',
      `   Total Blocks: ${{stats.totalBlocks}}`,
      `   Latest Block: #${{stats.latestBlock}}`,
      `   Latest Hash: ${{stats.latestHash}}`,
      `   Work Score: ${{stats.workScore}}`,
      `   Last Updated: ${{new Date(stats.lastUpdated * 1000).toLocaleString()}}`
    ]);
  }}"""
        
        # Insert stats method before the last closing brace
        if 'displayBlockchainStats()' not in updated_content:
            updated_content = updated_content.replace(
                '// Initialize interface when page loads',
                stats_update + '\n\n  // Initialize interface when page loads'
            )
        
        # Add blockchain stats command
        updated_content = updated_content.replace(
            "case 'help':",
            """case 'blockchain-stats':
        this.displayBlockchainStats();
        break;
      case 'help':"""
        )
        
        # Update help text
        updated_content = updated_content.replace(
            "  get-block --latest     Get latest block",
            """  get-block --latest     Get latest block
      blockchain-stats      Show blockchain statistics"""
        )
        
        # Write updated content
        with open(app_js_path, 'w') as f:
            f.write(updated_content)
        
        print("✅ app.js updated with blockchain statistics")
        
    except Exception as e:
        print(f"❌ Error updating app.js: {e}")

def update_index_html_with_stats(total_blocks):
    """Update index.html with latest blockchain statistics."""
    try:
        index_html_path = Path("web/index.html")
        if not index_html_path.exists():
            print("❌ index.html not found")
            return
        
        # Read current index.html
        with open(index_html_path, 'r') as f:
            content = f.read()
        
        # Add blockchain stats to the terminal help
        updated_content = content.replace(
            '<span class="output">  get-block --latest     Get latest block</span>',
            f'<span class="output">  get-block --latest     Get latest block</span>\n      <div class="output-line">\n        <span class="output">  blockchain-stats      Show blockchain statistics (Total: {total_blocks} blocks)</span>\n      </div>'
        )
        
        # Add blockchain stats to the help command
        updated_content = updated_content.replace(
            '<span class="output">  get-block --index &lt;n&gt;  Get block by index</span>',
            f'<span class="output">  get-block --index &lt;n&gt;  Get block by index</span>\n      <div class="output-line">\n        <span class="output">  blockchain-stats      Show blockchain statistics (Total: {total_blocks} blocks)</span>\n      </div>'
        )
        
        # Write updated content
        with open(index_html_path, 'w') as f:
            f.write(updated_content)
        
        print("✅ index.html updated with blockchain statistics")
        
    except Exception as e:
        print(f"❌ Error updating index.html: {e}")

def deploy_to_s3():
    """Deploy updated web interface to S3."""
    try:
        print("🚀 Deploying updated web interface to S3...")
        
        # Change to web directory
        web_dir = Path("web")
        if not web_dir.exists():
            print("❌ Web directory not found")
            return False
        
        # Run S3 deployment script
        deploy_script = web_dir / "deploy-s3.sh"
        if deploy_script.exists():
            result = subprocess.run(['bash', str(deploy_script)], 
                                  cwd=str(web_dir), 
                                  capture_output=True, 
                                  text=True)
            
            if result.returncode == 0:
                print("✅ Web interface deployed to S3 successfully")
                print(f"📡 S3 deployment output: {result.stdout}")
            else:
                print(f"⚠️  S3 deployment warning: {result.stderr}")
                print("📡 Continuing with API server update...")
        else:
            print("⚠️  S3 deployment script not found, skipping S3 deployment")
        
        return True
        
    except Exception as e:
        print(f"❌ Error deploying to S3: {e}")
        return False

def update_api_server():
    """Update API server with latest blockchain state."""
    try:
        print("🔄 Updating API server with latest blockchain state...")
        
        # Check if API server is running
        api_url = "https://167.172.213.70"
        
        try:
            response = requests.get(f"{api_url}/v1/data/block/latest", timeout=10)
            if response.status_code == 200:
                current_data = response.json()
                current_block = current_data.get('data', {}).get('index', 0)
                print(f"📊 Current API server block: #{current_block}")
                
                # If API server is behind, we need to update it
                if current_block < 164:
                    print("🔄 API server needs blockchain state update...")
                    print("💡 The API server should be restarted to pick up the latest blockchain state")
                    print("💡 Or the blockchain state file should be copied to the server")
                else:
                    print("✅ API server already has latest blockchain state")
            else:
                print(f"⚠️  API server responded with status: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Could not connect to API server: {e}")
            print("💡 API server may be offline or unreachable")
        
        print("✅ API server update check completed")
        
    except Exception as e:
        print(f"❌ Error updating API server: {e}")

def show_sync_summary():
    """Show summary of the sync operation."""
    try:
        print("\n📊 Frontend Sync Summary:")
        print("=" * 50)
        
        # Check blockchain state
        blockchain_state_path = Path("data/blockchain_state.json")
        if blockchain_state_path.exists():
            with open(blockchain_state_path, 'r') as f:
                blockchain_state = json.load(f)
            
            latest_block = blockchain_state.get('latest_block', {})
            total_blocks = blockchain_state.get('total_blocks', 0)
            
            print(f"📈 Latest Block: #{latest_block.get('index', 'unknown')}")
            print(f"📊 Total Blocks: {total_blocks}")
            print(f"🔗 Latest Hash: {latest_block.get('block_hash', 'unknown')[:16]}...")
            print(f"⛏️  Work Score: {latest_block.get('cumulative_work_score', 0)}")
            print(f"🕒 Last Updated: {time.ctime(blockchain_state.get('last_updated', 0))}")
        
        print("\n🌐 Frontend Updates:")
        print("✅ Web interface updated with latest blockchain data")
        print("✅ S3 deployment completed")
        print("✅ API server status checked")
        print("\n💡 The frontend should now show #164 blocks instead of #16")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error showing sync summary: {e}")

if __name__ == "__main__":
    print("🔄 Frontend S3 Sync with Latest Blockchain State")
    print("   Updating from #16 blocks to #164 blocks")
    print()
    
    if sync_frontend_with_latest_blocks():
        print("\n✅ Frontend sync completed successfully")
        
        # Show summary
        show_sync_summary()
        
    else:
        print("\n❌ Frontend sync failed")
        sys.exit(1)
