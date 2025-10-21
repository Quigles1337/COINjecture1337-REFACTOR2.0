#!/usr/bin/env python3
"""
Full Blockchain Sync Script
Downloads the complete blockchain history from the API server
and syncs the local blockchain state.
"""

import requests
import json
import time
import os
from pathlib import Path

def sync_full_blockchain():
    """Sync the complete blockchain from API server."""
    print("🔄 Full Blockchain Sync")
    print("=" * 50)
    
    api_base = "http://167.172.213.70:5000"
    
    try:
        # Get latest block info
        print("📡 Getting latest block information...")
        response = requests.get(f"{api_base}/v1/data/block/latest", timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Failed to get latest block: {response.status_code}")
            return False
            
        latest_data = response.json()
        latest_block = latest_data['data']
        latest_index = latest_block['index']
        
        print(f"✅ Network latest block: #{latest_index}")
        print(f"🔗 Latest hash: {latest_block['block_hash']}")
        
        # Download blocks in batches
        print(f"📥 Downloading blockchain history...")
        all_blocks = []
        batch_size = 100
        
        for start in range(0, latest_index + 1, batch_size):
            end = min(start + batch_size - 1, latest_index)
            
            try:
                print(f"📥 Downloading blocks {start}-{end}...")
                response = requests.get(
                    f"{api_base}/v1/data/blocks?start={start}&end={end}",
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if 'data' in data and 'blocks' in data['data']:
                        blocks = data['data']['blocks']
                        all_blocks.extend(blocks)
                        print(f"✅ Downloaded {len(blocks)} blocks")
                    else:
                        print(f"⚠️  No blocks in response for range {start}-{end}")
                else:
                    print(f"❌ Failed to download blocks {start}-{end}: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Error downloading blocks {start}-{end}: {e}")
                continue
                
            # Small delay to avoid overwhelming the server
            time.sleep(0.1)
        
        print(f"📊 Total blocks downloaded: {len(all_blocks)}")
        
        if not all_blocks:
            print("❌ No blocks downloaded")
            return False
            
        # Sort blocks by index
        all_blocks.sort(key=lambda x: x.get('index', 0))
        
        # Create updated blockchain state
        blockchain_state = {
            "latest_block": all_blocks[-1] if all_blocks else {},
            "blocks": all_blocks,
            "last_updated": time.time(),
            "sync_source": "api_server",
            "total_blocks": len(all_blocks)
        }
        
        # Save to local blockchain state
        blockchain_file = Path("data/blockchain_state.json")
        blockchain_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(blockchain_file, 'w') as f:
            json.dump(blockchain_state, f, indent=2)
            
        print(f"✅ Blockchain state saved to {blockchain_file}")
        print(f"📊 Local blockchain now has {len(all_blocks)} blocks")
        
        # Update cache
        cache_file = Path("data/cache/latest_block.json")
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(cache_file, 'w') as f:
            json.dump(all_blocks[-1], f, indent=2)
            
        print(f"✅ Cache updated with latest block")
        
        return True
        
    except Exception as e:
        print(f"❌ Sync failed: {e}")
        return False

def connect_to_bootstrap():
    """Connect to bootstrap node for peer discovery."""
    print("\n🌐 Connecting to Bootstrap Node")
    print("=" * 50)
    
    try:
        import sys
        sys.path.append('src')
        from p2p_discovery import P2PDiscoveryService, DiscoveryConfig
        
        # Configure bootstrap connection
        config = DiscoveryConfig()
        config.bootstrap_nodes = ['167.172.213.70:12345']
        
        discovery = P2PDiscoveryService(config)
        
        print("🔍 Starting P2P discovery...")
        if discovery.start():
            print("✅ P2P discovery started")
            
            # Let it discover peers
            time.sleep(10)
            
            stats = discovery.get_peer_statistics()
            print(f"📊 Discovery Results:")
            print(f"   Total discovered peers: {stats['total_discovered']}")
            print(f"   Connected peers: {stats['connected']}")
            
            discovery.stop()
            return True
        else:
            print("❌ Failed to start P2P discovery")
            return False
            
    except Exception as e:
        print(f"❌ Bootstrap connection failed: {e}")
        return False

def main():
    """Main sync process."""
    print("🚀 COINjecture Full Blockchain Sync")
    print("=" * 50)
    
    # Step 1: Sync blockchain
    if sync_full_blockchain():
        print("\n✅ Blockchain sync completed")
    else:
        print("\n❌ Blockchain sync failed")
        return
    
    # Step 2: Connect to bootstrap
    if connect_to_bootstrap():
        print("\n✅ Bootstrap connection established")
    else:
        print("\n⚠️  Bootstrap connection failed, but blockchain is synced")
    
    print("\n🎉 Sync process completed!")
    print("📊 Your local node should now be fully synced with the network")

if __name__ == "__main__":
    main()
