/**
 * WebSocket P2P Bridge
 * Creates a WebSocket server that bridges frontend connections to the P2P network
 * This runs on the server side to provide WebSocket endpoints for the frontend
 */

import asyncio
import json
import logging
from typing import Dict, Set, Optional
from dataclasses import dataclass

@dataclass
class P2PConfig:
    """Configuration for P2P bridge server."""
    host: str = '0.0.0.0'
    port: int = 5000
    api_url: str = 'https://api.coinjecture.com'
    bootstrap_nodes: list = None
    
    def __post_init__(self):
        if self.bootstrap_nodes is None:
            self.bootstrap_nodes = [
                '167.172.213.70:12346',
                '167.172.213.70:12345',
                '167.172.213.70:5000'
            ]

class WebSocketP2PBridge:
    """WebSocket server that bridges frontend to P2P network."""
    
    def __init__(self, config: P2PConfig):
        self.config = config
        self.logger = logging.getLogger('websocket-p2p-bridge')
        self.connected_clients: Set[WebSocket] = set()
        self.message_handlers: Dict[str, callable] = {}
        self.running = False
        
        # P2P topics
        self.topics = {
            'headers': '/coinj/headers/1.0.0',
            'commit_reveal': '/coinj/commit-reveal/1.0.0',
            'requests': '/coinj/requests/1.0.0',
            'responses': '/coinj/responses/1.0.0'
        }
        
        # Setup message handlers
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup message handlers for different message types."""
        self.message_handlers = {
            'subscribe': self.handle_subscribe,
            'publish': self.handle_publish,
            'request_peers': self.handle_request_peers,
            'mining_submit': self.handle_mining_submit
        }
    
    async def start(self):
        """Start the WebSocket P2P bridge server."""
        try:
            self.logger.info(f"🌐 Starting WebSocket P2P Bridge on {self.config.host}:{self.config.port}")
            
            # In a real implementation, this would start a WebSocket server
            # For now, we'll simulate the server functionality
            self.running = True
            
            # Start background tasks
            asyncio.create_task(self.background_tasks())
            
            self.logger.info("✅ WebSocket P2P Bridge started")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start WebSocket P2P Bridge: {e}")
            return False
    
    async def stop(self):
        """Stop the WebSocket P2P bridge server."""
        self.running = False
        self.logger.info("🛑 WebSocket P2P Bridge stopped")
    
    async def background_tasks(self):
        """Background tasks for the bridge."""
        while self.running:
            try:
                # Simulate P2P network activity
                await self.simulate_network_activity()
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                self.logger.error(f"❌ Background task error: {e}")
                await asyncio.sleep(5)
    
    async def simulate_network_activity(self):
        """Simulate P2P network activity."""
        # In a real implementation, this would:
        # 1. Connect to actual P2P network
        # 2. Listen for new blocks
        # 3. Forward messages to connected clients
        
        # For now, simulate some activity
        if self.connected_clients:
            # Simulate a new block announcement
            message = {
                'type': 'header',
                'topic': self.topics['headers'],
                'data': {
                    'header': {
                        'height': 1,
                        'hash': 'simulated_block_hash',
                        'timestamp': Date.now()
                    },
                    'work_score': 100.0,
                    'reward': 0.01
                },
                'peerId': 'simulated_peer'
            }
            
            await self.broadcast_to_clients(message)
    
    async def handle_websocket_connection(self, websocket, path):
        """Handle new WebSocket connection."""
        self.logger.info(f"🔌 New WebSocket connection from {websocket.remote_address}")
        self.connected_clients.add(websocket)
        
        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        except Exception as e:
            self.logger.error(f"❌ WebSocket error: {e}")
        finally:
            self.connected_clients.discard(websocket)
            self.logger.info(f"🔌 WebSocket connection closed")
    
    async def handle_message(self, websocket, message):
        """Handle incoming WebSocket message."""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            if message_type in self.message_handlers:
                await self.message_handlers[message_type](websocket, data)
            else:
                self.logger.warn(f"⚠️ Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            self.logger.error("❌ Invalid JSON message")
        except Exception as e:
            self.logger.error(f"❌ Message handling error: {e}")
    
    async def handle_subscribe(self, websocket, data):
        """Handle subscription request."""
        topic = data.get('topic')
        if topic:
            self.logger.info(f"📡 Client subscribed to topic: {topic}")
            # In a real implementation, this would subscribe to the P2P topic
            await websocket.send(json.dumps({
                'type': 'subscription_confirmed',
                'topic': topic,
                'status': 'success'
            }))
    
    async def handle_publish(self, websocket, data):
        """Handle publish request."""
        topic = data.get('topic')
        message_data = data.get('data')
        
        if topic and message_data:
            self.logger.info(f"📤 Publishing to topic: {topic}")
            # In a real implementation, this would publish to the P2P network
            await self.broadcast_to_clients({
                'type': 'message',
                'topic': topic,
                'data': message_data,
                'peerId': 'bridge_server'
            })
    
    async def handle_request_peers(self, websocket, data):
        """Handle peer list request."""
        # Simulate peer list
        peers = [
            {
                'peer_id': 'bootstrap-1',
                'address': '167.172.213.70',
                'port': 12346,
                'last_seen': Date.now(),
                'is_bootstrap': True
            },
            {
                'peer_id': 'bootstrap-2', 
                'address': '167.172.213.70',
                'port': 12345,
                'last_seen': Date.now(),
                'is_bootstrap': True
            }
        ]
        
        await websocket.send(json.dumps({
            'type': 'peer_list_response',
            'peers': peers
        }))
    
    async def handle_mining_submit(self, websocket, data):
        """Handle mining submission."""
        try:
            # Forward mining submission to API
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.config.api_url}/v1/mining/submit-block",
                    json=data.get('block_data', {}),
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    result = await response.json()
                    
                    await websocket.send(json.dumps({
                        'type': 'mining_response',
                        'success': result.get('success', False),
                        'data': result
                    }))
                    
        except Exception as e:
            self.logger.error(f"❌ Mining submission error: {e}")
            await websocket.send(json.dumps({
                'type': 'mining_response',
                'success': False,
                'error': str(e)
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
                self.logger.error(f"❌ Failed to send to client: {e}")
                disconnected.add(client)
        
        # Remove disconnected clients
        self.connected_clients -= disconnected

# Server startup function
async def start_p2p_bridge():
    """Start the P2P bridge server."""
    config = P2PConfig(
        host='0.0.0.0',
        port=5000,
        api_url='https://api.coinjecture.com'
    )
    
    bridge = WebSocketP2PBridge(config)
    await bridge.start()
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await bridge.stop()

if __name__ == "__main__":
    asyncio.run(start_p2p_bridge())
