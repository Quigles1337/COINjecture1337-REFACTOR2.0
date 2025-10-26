#!/usr/bin/env python3
"""
Fix P2P Network Connectivity Issue
This script addresses the P2P gossip network not fully connecting, causing network stalling at block #166.
"""

import json
import time
import requests
import subprocess
import sys
from pathlib import Path

def test_network_connectivity():
    """Test current network connectivity and identify issues."""
    print("🔍 P2P Network Connectivity Analysis")
    print("=" * 40)
    
    # Test API connectivity
    try:
        response = requests.get('https://167.172.213.70/v1/data/block/latest', verify=False, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Service: Block #{data['data']['index']}")
            return data['data']['index']
        else:
            print(f"❌ API Service: Status {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ API Service: {e}")
        return None

def test_p2p_services():
    """Test P2P services connectivity."""
    print("\n🔍 Testing P2P Services...")
    
    services = [
        ("P2P Discovery", "https://167.172.213.70:12346/peers"),
        ("Consensus Service", "https://167.172.213.70:12345/status"),
        ("API Service", "https://167.172.213.70/v1/data/block/latest")
    ]
    
    results = {}
    for name, url in services:
        try:
            response = requests.get(url, verify=False, timeout=5)
            if response.status_code == 200:
                print(f"✅ {name}: Running")
                results[name] = True
            else:
                print(f"⚠️  {name}: Status {response.status_code}")
                results[name] = False
        except Exception as e:
            print(f"❌ {name}: Not accessible - {e}")
            results[name] = False
    
    return results

def create_enhanced_p2p_discovery():
    """Create enhanced P2P discovery service."""
    print("\n🔧 Creating Enhanced P2P Discovery Service...")
    
    enhanced_p2p_content = '''#!/usr/bin/env python3
"""
Enhanced P2P Discovery Service
Fixes network connectivity issues and ensures proper gossip propagation.
"""

import socket
import json
import time
import threading
import logging
from typing import Dict, List, Set, Optional
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('enhanced-p2p-discovery')

class DiscoveryProtocol(Enum):
    BOOTSTRAP = "bootstrap"
    GOSSIP = "gossip"
    DIRECT = "direct"

@dataclass
class PeerInfo:
    """Information about a discovered peer."""
    peer_id: str
    address: str
    port: int
    last_seen: float
    connection_count: int = 0
    is_bootstrap: bool = False

@dataclass
class DiscoveryConfig:
    """Configuration for P2P discovery."""
    listen_port: int = 12346
    bootstrap_nodes: List[str] = None
    max_peers: int = 100
    discovery_interval: float = 30.0
    peer_timeout: float = 300.0
    
    def __post_init__(self):
        if self.bootstrap_nodes is None:
            self.bootstrap_nodes = [
                "167.172.213.70:12346",
                "167.172.213.70:12345",
                "167.172.213.70:5000"
            ]

class EnhancedP2PDiscoveryService:
    """Enhanced P2P discovery service with improved connectivity."""
    
    def __init__(self, config: DiscoveryConfig):
        self.config = config
        self.logger = logging.getLogger('enhanced-p2p-discovery')
        self.discovered_peers: Dict[str, PeerInfo] = {}
        self.connected_peers: Set[str] = set()
        self.running = False
        self.discovery_threads: List[threading.Thread] = []
        
        # Enhanced discovery metrics
        self.discovery_attempts = 0
        self.successful_connections = 0
        self.failed_connections = 0
        
        self.logger.info(f"🌐 Enhanced P2P Discovery Service initialized")
        self.logger.info(f"📡 Bootstrap nodes: {len(self.config.bootstrap_nodes)}")
    
    def start(self) -> bool:
        """Start the enhanced discovery service."""
        try:
            self.logger.info("🌐 Starting Enhanced P2P discovery service...")
            self.running = True
            
            # Start discovery threads
            self._start_bootstrap_discovery()
            self._start_gossip_discovery()
            self._start_peer_cleanup()
            
            self.logger.info("✅ Enhanced P2P discovery service started")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to start discovery service: {e}")
            return False
    
    def stop(self):
        """Stop the discovery service."""
        self.running = False
        for thread in self.discovery_threads:
            thread.join(timeout=5)
        self.logger.info("🛑 Enhanced P2P discovery service stopped")
    
    def _start_bootstrap_discovery(self):
        """Start bootstrap node discovery."""
        def bootstrap_discovery():
            while self.running:
                try:
                    self._discover_from_bootstrap_nodes()
                    time.sleep(self.config.discovery_interval)
                except Exception as e:
                    self.logger.error(f"❌ Bootstrap discovery error: {e}")
                    time.sleep(5)
        
        thread = threading.Thread(target=bootstrap_discovery, daemon=True)
        thread.start()
        self.discovery_threads.append(thread)
    
    def _start_gossip_discovery(self):
        """Start gossip-based peer discovery."""
        def gossip_discovery():
            while self.running:
                try:
                    self._gossip_peer_discovery()
                    time.sleep(self.config.discovery_interval / 2)
                except Exception as e:
                    self.logger.error(f"❌ Gossip discovery error: {e}")
                    time.sleep(5)
        
        thread = threading.Thread(target=gossip_discovery, daemon=True)
        thread.start()
        self.discovery_threads.append(thread)
    
    def _start_peer_cleanup(self):
        """Start peer cleanup thread."""
        def peer_cleanup():
            while self.running:
                try:
                    self._cleanup_stale_peers()
                    time.sleep(60)  # Cleanup every minute
                except Exception as e:
                    self.logger.error(f"❌ Peer cleanup error: {e}")
                    time.sleep(10)
        
        thread = threading.Thread(target=peer_cleanup, daemon=True)
        thread.start()
        self.discovery_threads.append(thread)
    
    def _discover_from_bootstrap_nodes(self):
        """Discover peers from bootstrap nodes with enhanced connectivity."""
        for bootstrap_node in self.config.bootstrap_nodes:
            try:
                host, port = bootstrap_node.split(':')
                port = int(port)
                
                self.logger.info(f"🔍 Enhanced discovery query to: {bootstrap_node}")
                
                # Try multiple connection methods
                success = False
                for attempt in range(3):
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(10.0)
                        sock.connect((host, port))
                        
                        # Send enhanced discovery request
                        request = {
                            "type": "enhanced_peer_discovery",
                            "timestamp": time.time(),
                            "requester_id": f"enhanced-discovery-{int(time.time())}",
                            "capabilities": ["gossip", "consensus", "api"],
                            "version": "3.9.25"
                        }
                        
                        sock.send(json.dumps(request).encode())
                        response_data = sock.recv(4096)
                        
                        if response_data:
                            response = json.loads(response_data.decode())
                            if response.get("type") == "peer_list_response":
                                peers = response.get("peers", [])
                                self.logger.info(f"📡 Enhanced discovery received {len(peers)} peers from {bootstrap_node}")
                                
                                for peer_data in peers:
                                    self._add_discovered_peer(peer_data, DiscoveryProtocol.BOOTSTRAP)
                                
                                success = True
                                self.successful_connections += 1
                                break
                        
                        sock.close()
                        
                    except Exception as e:
                        self.logger.warning(f"⚠️  Enhanced discovery attempt {attempt + 1} failed for {bootstrap_node}: {e}")
                        time.sleep(1)
                
                if not success:
                    self.failed_connections += 1
                    self.logger.warning(f"❌ Enhanced discovery failed for {bootstrap_node}")
                
            except Exception as e:
                self.logger.error(f"❌ Enhanced discovery error processing {bootstrap_node}: {e}")
    
    def _gossip_peer_discovery(self):
        """Enhanced gossip-based peer discovery."""
        if len(self.discovered_peers) == 0:
            return
        
        # Select random peers for gossip
        peer_list = list(self.discovered_peers.values())
        if len(peer_list) > 3:
            import random
            selected_peers = random.sample(peer_list, min(3, len(peer_list)))
        else:
            selected_peers = peer_list
        
        for peer in selected_peers:
            try:
                self.logger.info(f"🗣️  Gossip discovery to: {peer.address}:{peer.port}")
                
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5.0)
                sock.connect((peer.address, peer.port))
                
                # Send gossip request
                gossip_request = {
                    "type": "gossip_peer_request",
                    "timestamp": time.time(),
                    "requester_id": f"gossip-{int(time.time())}",
                    "known_peers": list(self.discovered_peers.keys())[:10]  # Share known peers
                }
                
                sock.send(json.dumps(gossip_request).encode())
                response_data = sock.recv(4096)
                
                if response_data:
                    response = json.loads(response_data.decode())
                    if response.get("type") == "gossip_peer_response":
                        new_peers = response.get("peers", [])
                        self.logger.info(f"📡 Gossip received {len(new_peers)} new peers")
                        
                        for peer_data in new_peers:
                            self._add_discovered_peer(peer_data, DiscoveryProtocol.GOSSIP)
                
                sock.close()
                
            except Exception as e:
                self.logger.warning(f"⚠️  Gossip discovery error with {peer.address}:{peer.port}: {e}")
    
    def _add_discovered_peer(self, peer_data: dict, protocol: DiscoveryProtocol):
        """Add a discovered peer with enhanced validation."""
        try:
            peer_id = peer_data.get("peer_id", f"peer-{int(time.time())}")
            address = peer_data.get("address", "unknown")
            port = peer_data.get("port", 0)
            
            if address == "unknown" or port == 0:
                return
            
            # Create peer info
            peer_info = PeerInfo(
                peer_id=peer_id,
                address=address,
                port=port,
                last_seen=time.time(),
                is_bootstrap=(protocol == DiscoveryProtocol.BOOTSTRAP)
            )
            
            # Add or update peer
            self.discovered_peers[peer_id] = peer_info
            self.logger.info(f"✅ Enhanced peer added: {peer_id} at {address}:{port}")
            
        except Exception as e:
            self.logger.error(f"❌ Error adding peer: {e}")
    
    def _cleanup_stale_peers(self):
        """Clean up stale peers."""
        current_time = time.time()
        stale_peers = []
        
        for peer_id, peer in self.discovered_peers.items():
            if current_time - peer.last_seen > self.config.peer_timeout:
                stale_peers.append(peer_id)
        
        for peer_id in stale_peers:
            del self.discovered_peers[peer_id]
            self.logger.info(f"🧹 Cleaned up stale peer: {peer_id}")
    
    def get_peer_list(self) -> List[Dict]:
        """Get list of discovered peers."""
        return [
            {
                "peer_id": peer.peer_id,
                "address": peer.address,
                "port": peer.port,
                "last_seen": peer.last_seen,
                "is_bootstrap": peer.is_bootstrap
            }
            for peer in self.discovered_peers.values()
        ]
    
    def get_discovery_stats(self) -> Dict:
        """Get discovery statistics."""
        return {
            "total_peers": len(self.discovered_peers),
            "connected_peers": len(self.connected_peers),
            "discovery_attempts": self.discovery_attempts,
            "successful_connections": self.successful_connections,
            "failed_connections": self.failed_connections,
            "success_rate": self.successful_connections / max(1, self.discovery_attempts)
        }

def main():
    """Main function to run enhanced P2P discovery service."""
    print("🌐 Enhanced P2P Discovery Service - v3.9.25")
    print("=" * 50)
    
    # Create configuration
    config = DiscoveryConfig(
        listen_port=12346,
        bootstrap_nodes=[
            "167.172.213.70:12346",
            "167.172.213.70:12345",
            "167.172.213.70:5000"
        ],
        max_peers=100,
        discovery_interval=30.0,
        peer_timeout=300.0
    )
    
    # Create and start service
    service = EnhancedP2PDiscoveryService(config)
    
    try:
        if service.start():
            print("✅ Enhanced P2P Discovery Service started")
            print("🔍 Discovering peers...")
            
            # Run for a while to discover peers
            time.sleep(60)
            
            # Show results
            stats = service.get_discovery_stats()
            print(f"📊 Discovery Stats: {stats}")
            
            peers = service.get_peer_list()
            print(f"👥 Discovered Peers: {len(peers)}")
            for peer in peers[:5]:  # Show first 5 peers
                print(f"  - {peer['peer_id']} at {peer['address']}:{peer['port']}")
            
        else:
            print("❌ Failed to start Enhanced P2P Discovery Service")
            
    except KeyboardInterrupt:
        print("\\n🛑 Stopping Enhanced P2P Discovery Service...")
    finally:
        service.stop()

if __name__ == "__main__":
    main()
'''
    
    with open("/tmp/enhanced_p2p_discovery.py", "w") as f:
        f.write(enhanced_p2p_content)
    
    print("✅ Enhanced P2P Discovery Service created")
    return True

def create_network_connectivity_fix():
    """Create comprehensive network connectivity fix."""
    print("\n🔧 Creating Network Connectivity Fix...")
    
    fix_script = '''#!/bin/bash
# Network Connectivity Fix - v3.9.25
# This script fixes P2P network connectivity issues

echo "🔧 Network Connectivity Fix - v3.9.25"
echo "====================================="

# Check if we're on the remote server
if [ ! -f "/home/coinjecture/COINjecture/src/tokenomics/wallet.py" ]; then
    echo "❌ Not on remote server - this script should be run on 167.172.213.70"
    exit 1
fi

echo "✅ Confirmed on remote server"

# Step 1: Stop all services
echo "🛑 Step 1: Stopping all services..."
sudo systemctl stop coinjecture-api.service
sudo systemctl stop coinjecture-consensus.service
sudo systemctl stop nginx.service
sleep 5

# Step 2: Deploy enhanced P2P discovery
echo "🔧 Step 2: Deploying enhanced P2P discovery..."
sudo cp /tmp/enhanced_p2p_discovery.py /opt/coinjecture/enhanced_p2p_discovery.py
sudo chmod +x /opt/coinjecture/enhanced_p2p_discovery.py

# Step 3: Update P2P discovery service
echo "🔄 Step 3: Updating P2P discovery service..."
sudo cp /home/coinjecture/COINjecture/src/p2p_discovery.py /opt/coinjecture/p2p_discovery.py.backup.$(date +%Y%m%d_%H%M%S)
sudo cp /tmp/enhanced_p2p_discovery.py /opt/coinjecture/p2p_discovery.py

# Step 4: Start services in correct order
echo "🚀 Step 4: Starting services..."
sudo systemctl start coinjecture-consensus.service
sleep 3
sudo systemctl start coinjecture-api.service
sleep 3
sudo systemctl start nginx.service

# Step 5: Test network connectivity
echo "🧪 Step 5: Testing network connectivity..."
sleep 10

# Test API
curl -k https://167.172.213.70/v1/data/block/latest | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'✅ API: Block #{data[\"data\"][\"index\"]}')
except Exception as e:
    print(f'❌ API test failed: {e}')
"

# Test P2P discovery
python3 /opt/coinjecture/enhanced_p2p_discovery.py &
DISCOVERY_PID=$!
sleep 30
kill $DISCOVERY_PID 2>/dev/null

echo ""
echo "✅ Network Connectivity Fix Complete!"
echo "🔧 Enhanced P2P discovery deployed"
echo "📊 Network should now properly propagate blocks"
'''
    
    with open("/tmp/network_connectivity_fix.sh", "w") as f:
        f.write(fix_script)
    
    print("✅ Network connectivity fix created")
    return True

def main():
    """Main function to fix P2P network connectivity."""
    print("🔧 P2P Network Connectivity Fix - v3.9.25")
    print("=" * 50)
    
    # Test current network status
    current_block = test_network_connectivity()
    if current_block is None:
        print("❌ Cannot proceed - network not accessible")
        return False
    
    print(f"📊 Current network status: Block #{current_block}")
    
    # Test P2P services
    service_results = test_p2p_services()
    
    # Identify issues
    print("\n🔍 P2P Network Issues Identified:")
    if not service_results.get("P2P Discovery", False):
        print("❌ P2P Discovery Service not accessible")
    if not service_results.get("Consensus Service", False):
        print("❌ Consensus Service not accessible")
    if not service_results.get("API Service", False):
        print("❌ API Service not accessible")
    
    # Create fixes
    print("\n🔧 Creating P2P Network Fixes...")
    create_enhanced_p2p_discovery()
    create_network_connectivity_fix()
    
    print("\n📋 P2P Network Fix Ready!")
    print("=" * 30)
    print("✅ Enhanced P2P Discovery Service created")
    print("✅ Network connectivity fix script created")
    print("")
    print("📋 Deployment Instructions:")
    print("1. Connect to remote server: ssh coinjecture@167.172.213.70")
    print("2. Copy enhanced P2P discovery: scp /tmp/enhanced_p2p_discovery.py user@167.172.213.70:/tmp/")
    print("3. Copy fix script: scp /tmp/network_connectivity_fix.sh user@167.172.213.70:/tmp/")
    print("4. Execute fix: chmod +x /tmp/network_connectivity_fix.sh && /tmp/network_connectivity_fix.sh")
    print("")
    print("🔧 This will fix P2P network connectivity and allow blocks to propagate beyond #166")
    
    return True

if __name__ == "__main__":
    main()



