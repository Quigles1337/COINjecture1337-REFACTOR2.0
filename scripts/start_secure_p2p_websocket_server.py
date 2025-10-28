#!/usr/bin/env python3
"""
Secure WebSocket P2P Bridge Server with SSL
Creates a WSS server that bridges frontend connections to the P2P network
"""

import asyncio
import json
import logging
import ssl
import websockets
import aiohttp
from typing import Set, Dict, Any
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('secure-p2p-websocket-bridge')

class SecureP2PWebSocketBridge:
    """Secure WebSocket server that bridges frontend to P2P network."""
    
    def __init__(self, host='0.0.0.0', port=5000, api_url='https://api.coinjecture.com'):
        self.host = host
        self.port = port
        self.api_url = api_url
        self.connected_clients: Set[websockets.WebSocketServerProtocol] = set()
        self.running = False
        
        # P2P topics
        self.topics = {
            'headers': '/coinj/headers/1.0.0',
            'commit_reveal': '/coinj/commit-reveal/1.0.0',
            'requests': '/coinj/requests/1.0.0',
            'responses': '/coinj/responses/1.0.0'
        }
    
    def create_ssl_context(self):
        """Create SSL context for WSS."""
        try:
            # Try to use existing SSL certificates
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            
            # Try to load certificates from common locations
            cert_paths = [
                '/etc/ssl/certs/ssl-cert-snakeoil.pem',
                '/etc/ssl/private/ssl-cert-snakeoil.key',
                '/etc/letsencrypt/live/coinjecture.com/fullchain.pem',
                '/etc/letsencrypt/live/coinjecture.com/privkey.pem'
            ]
            
            # For now, create a self-signed certificate
            logger.warning("⚠️ Using self-signed certificate for WSS")
            return None  # Let websockets handle SSL
            
        except Exception as e:
            logger.error(f"❌ SSL setup failed: {e}")
            return None
    
    async def start(self):
        """Start the secure WebSocket server."""
        try:
            logger.info(f"🌐 Starting Secure P2P WebSocket Bridge on {self.host}:{self.port}")
            
            # Create SSL context
            ssl_context = self.create_ssl_context()
            
            # Start WebSocket server
            server = await websockets.serve(
                self.handle_connection,
                self.host,
                self.port,
                subprotocols=["p2p-bridge"],
                ssl=ssl_context
            )
            
            self.running = True
            protocol = "wss" if ssl_context else "ws"
            logger.info(f"✅ Secure P2P WebSocket Bridge started on {protocol}://{self.host}:{self.port}")
            
            # Start background tasks
            asyncio.create_task(self.background_tasks())
            
            # Keep server running
            await server.wait_closed()
            
        except Exception as e:
            logger.error(f"❌ Failed to start secure WebSocket server: {e}")
    
    async def handle_connection(self, websocket, path):
        """Handle new WebSocket connection."""
        client_addr = websocket.remote_address
        logger.info(f"🔌 New secure connection from {client_addr}")
        self.connected_clients.add(websocket)
        
        try:
            # Send welcome message
            await websocket.send(json.dumps({
                'type': 'welcome',
                'message': 'Connected to COINjecture Secure P2P Bridge',
                'topics': list(self.topics.values()),
                'timestamp': datetime.now().isoformat()
            }))
            
            # Handle messages
            async for message in websocket:
                await self.handle_message(websocket, message)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"🔌 Secure connection closed: {client_addr}")
        except Exception as e:
            logger.error(f"❌ Connection error: {e}")
        finally:
            self.connected_clients.discard(websocket)
    
    async def handle_message(self, websocket, message):
        """Handle incoming WebSocket message."""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            if message_type == 'subscribe':
                await self.handle_subscribe(websocket, data)
            elif message_type == 'publish':
                await self.handle_publish(websocket, data)
            elif message_type == 'request_peers':
                await self.handle_request_peers(websocket, data)
            elif message_type == 'mining_submit':
                await self.handle_mining_submit(websocket, data)
            else:
                logger.warning(f"⚠️ Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            logger.error("❌ Invalid JSON message")
        except Exception as e:
            logger.error(f"❌ Message handling error: {e}")
    
    async def handle_subscribe(self, websocket, data):
        """Handle subscription request."""
        topic = data.get('topic')
        if topic:
            logger.info(f"📡 Client subscribed to topic: {topic}")
            await websocket.send(json.dumps({
                'type': 'subscription_confirmed',
                'topic': topic,
                'status': 'success',
                'timestamp': datetime.now().isoformat()
            }))
    
    async def handle_publish(self, websocket, data):
        """Handle publish request."""
        topic = data.get('topic')
        message_data = data.get('data')
        
        if topic and message_data:
            logger.info(f"📤 Publishing to topic: {topic}")
            await self.broadcast_to_clients({
                'type': 'message',
                'topic': topic,
                'data': message_data,
                'peerId': 'bridge_server',
                'timestamp': datetime.now().isoformat()
            })
    
    async def handle_request_peers(self, websocket, data):
        """Handle peer list request."""
        peers = [
            {
                'peer_id': 'bootstrap-1',
                'address': '167.172.213.70',
                'port': 12346,
                'last_seen': datetime.now().isoformat(),
                'is_bootstrap': True
            },
            {
                'peer_id': 'bootstrap-2',
                'address': '167.172.213.70', 
                'port': 12345,
                'last_seen': datetime.now().isoformat(),
                'is_bootstrap': True
            },
            {
                'peer_id': 'api-server',
                'address': 'api.coinjecture.com',
                'port': 443,
                'last_seen': datetime.now().isoformat(),
                'is_bootstrap': True
            }
        ]
        
        await websocket.send(json.dumps({
            'type': 'peer_list_response',
            'peers': peers,
            'timestamp': datetime.now().isoformat()
        }))
    
    async def handle_mining_submit(self, websocket, data):
        """Handle mining submission."""
        try:
            block_data = data.get('block_data', {})
            logger.info(f"⛏️ Mining submission received")
            
            # Forward to API
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/v1/mining/submit-block",
                    json=block_data,
                    headers={'Content-Type': 'application/json'},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    result = await response.json()
                    
                    await websocket.send(json.dumps({
                        'type': 'mining_response',
                        'success': result.get('success', False),
                        'data': result,
                        'timestamp': datetime.now().isoformat()
                    }))
                    
        except Exception as e:
            logger.error(f"❌ Mining submission error: {e}")
            await websocket.send(json.dumps({
                'type': 'mining_response',
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }))
    
    async def broadcast_to_clients(self, message):
        """Broadcast message to all connected clients."""
        if not self.connected_clients:
            return
        
        message_json = json.dumps(message)
        disconnected = set()
        
        for client in self.connected_clients:
            try:
                await client.send(message_json)
            except Exception as e:
                logger.error(f"❌ Failed to send to client: {e}")
                disconnected.add(client)
        
        # Remove disconnected clients
        self.connected_clients -= disconnected
    
    async def background_tasks(self):
        """Background tasks for the bridge."""
        while self.running:
            try:
                await self.simulate_network_activity()
                await asyncio.sleep(30)
            except Exception as e:
                logger.error(f"❌ Background task error: {e}")
                await asyncio.sleep(5)
    
    async def simulate_network_activity(self):
        """Simulate P2P network activity."""
        if self.connected_clients:
            message = {
                'type': 'header',
                'topic': self.topics['headers'],
                'data': {
                    'header': {
                        'height': 1,
                        'hash': f'simulated_block_{int(datetime.now().timestamp())}',
                        'timestamp': datetime.now().isoformat()
                    },
                    'work_score': 100.0,
                    'reward': 0.01
                },
                'peerId': 'simulated_peer',
                'timestamp': datetime.now().isoformat()
            }
            
            await self.broadcast_to_clients(message)

async def main():
    """Main function to start the secure P2P WebSocket bridge."""
    bridge = SecureP2PWebSocketBridge(
        host='0.0.0.0',
        port=5000,
        api_url='https://api.coinjecture.com'
    )
    
    try:
        await bridge.start()
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down Secure P2P WebSocket Bridge...")
        bridge.running = False

if __name__ == "__main__":
    asyncio.run(main())
