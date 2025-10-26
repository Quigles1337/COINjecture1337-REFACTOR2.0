#!/usr/bin/env python3
"""
COINjecture Bootstrap Node
Serves as the P2P network entry point for other nodes to connect to
"""

import sys
import os
import time
import json
import logging
import signal
import threading
import socket
import requests
from pathlib import Path
from typing import Optional, Dict, Any

# Add src to path
sys.path.append('src')

# Set up logging with file output
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bootstrap_node.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('coinjecture-bootstrap-node')

class BootstrapNode:
    """Bootstrap node for COINjecture P2P network."""
    
    def __init__(self, listen_addr: str = "0.0.0.0:12345"):
        self.listen_addr = listen_addr
        self.running = False
        self.connected_peers = []
        self.server_socket = None
        self.genesis_block = None
        self.blockchain_data = None
        self.network_api_url = "http://167.172.213.70:5000"
        
    def start(self) -> bool:
        """Start the bootstrap node server."""
        try:
            # Load genesis block from network
            if not self._load_genesis_block():
                logger.error("Failed to load genesis block from network")
                return False
            
            host, port = self.listen_addr.split(':')
            port = int(port)
            
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((host, port))
            self.server_socket.listen(10)
            
            self.running = True
            logger.info(f"🌐 Bootstrap node listening on {self.listen_addr}")
            logger.info("📡 Ready to accept P2P connections")
            logger.info("🔗 Other nodes can connect to this bootstrap peer")
            logger.info(f"📊 Genesis block loaded: {self.genesis_block['block_hash'][:16]}...")
            
            # Start accepting connections
            self._accept_connections()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start bootstrap node: {e}")
            return False
    
    def _load_genesis_block(self) -> bool:
        """Load genesis block from the network API."""
        try:
            logger.info("🌐 Loading genesis block from network...")
            response = requests.get(f"{self.network_api_url}/v1/data/block/latest", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    self.genesis_block = data['data']
                    self.blockchain_data = data
                    logger.info(f"✅ Genesis block loaded: {self.genesis_block['block_hash'][:16]}...")
                    logger.info(f"📊 Block index: {self.genesis_block['index']}")
                    logger.info(f"⛏️ Mining capacity: {self.genesis_block['mining_capacity']}")
                    return True
                else:
                    logger.error("Network API returned error status")
                    return False
            else:
                logger.error(f"Failed to fetch genesis block: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error loading genesis block: {e}")
            return False
    
    def _accept_connections(self):
        """Accept incoming P2P connections."""
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                logger.info(f"📡 New peer connected: {address[0]}:{address[1]}")
                
                # Handle peer connection in a separate thread
                peer_thread = threading.Thread(
                    target=self._handle_peer_connection,
                    args=(client_socket, address)
                )
                peer_thread.daemon = True
                peer_thread.start()
                
            except Exception as e:
                if self.running:
                    logger.error(f"Error accepting connection: {e}")
                break
    
    def _handle_peer_connection(self, client_socket: socket.socket, address: tuple):
        """Handle a connected peer."""
        try:
            peer_id = f"{address[0]}:{address[1]}"
            self.connected_peers.append(peer_id)
            
            logger.info(f"🤝 Handling peer connection from {peer_id}")
            
            # Send bootstrap information with actual genesis block
            bootstrap_info = {
                "node_type": "bootstrap",
                "network_id": "coinjecture-mainnet",
                "genesis_block": self.genesis_block['block_hash'],
                "current_height": self.genesis_block['index'],
                "peers": self.connected_peers,
                "genesis_data": self.genesis_block
            }
            
            response = json.dumps(bootstrap_info).encode('utf-8')
            client_socket.send(response)
            logger.info(f"📤 Sent bootstrap info to {peer_id}")
            
            # Keep connection alive and handle requests
            while self.running:
                try:
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    
                    # Handle peer requests
                    request = data.decode('utf-8')
                    if "ping" in request.lower():
                        client_socket.send(b"pong")
                        logger.info(f"📡 Responded to ping from {peer_id}")
                    elif "get_headers" in request.lower():
                        # Send blockchain headers with actual data
                        headers_info = {
                            "headers": [{
                                "hash": self.genesis_block['block_hash'],
                                "height": self.genesis_block['index'],
                                "timestamp": self.genesis_block['timestamp'],
                                "previous_hash": self.genesis_block['previous_hash'],
                                "merkle_root": self.genesis_block['merkle_root']
                            }]
                        }
                        client_socket.send(json.dumps(headers_info).encode('utf-8'))
                        logger.info(f"📤 Sent blockchain headers to {peer_id}")
                    elif "get_genesis" in request.lower():
                        # Send full genesis block
                        client_socket.send(json.dumps(self.genesis_block).encode('utf-8'))
                        logger.info(f"📤 Sent genesis block to {peer_id}")
                    elif "get_blockchain" in request.lower():
                        # Send full blockchain data
                        client_socket.send(json.dumps(self.blockchain_data).encode('utf-8'))
                        logger.info(f"📤 Sent blockchain data to {peer_id}")
                    
                except Exception as e:
                    logger.warning(f"Error handling peer {peer_id}: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Error in peer connection handler: {e}")
        finally:
            try:
                client_socket.close()
                if peer_id in self.connected_peers:
                    self.connected_peers.remove(peer_id)
                logger.info(f"📡 Peer {peer_id} disconnected")
            except:
                pass
    
    def stop(self):
        """Stop the bootstrap node."""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        logger.info("🛑 Bootstrap node stopped")

def main():
    """Main entry point for bootstrap node."""
    logger.info("🚀 Starting COINjecture Bootstrap Node...")
    logger.info("🌐 This node will serve as the P2P network entry point")
    
    bootstrap_node = BootstrapNode("0.0.0.0:12345")
    
    try:
        if bootstrap_node.start():
            logger.info("✅ Bootstrap node started successfully")
            logger.info("🔗 Other nodes can now connect to 0.0.0.0:12345")
            
            # Keep running until interrupted
            while bootstrap_node.running:
                time.sleep(1)
        else:
            logger.error("❌ Failed to start bootstrap node")
            return False
            
    except KeyboardInterrupt:
        logger.info("🛑 Stopping bootstrap node...")
        bootstrap_node.stop()
        return True
        
    except Exception as e:
        logger.error(f"❌ Bootstrap node error: {e}")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
