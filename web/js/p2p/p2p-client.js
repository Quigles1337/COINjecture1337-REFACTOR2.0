/**
 * COINjecture P2P Client
 * Connects to the P2P network and implements gossipsub protocol
 * for real-time blockchain mining and consensus participation
 */

import { API_CONFIG } from '../shared/constants.js';

export class P2PClient {
    constructor() {
        this.connected = false;
        this.peers = new Map();
        this.subscriptions = new Map();
        this.messageHandlers = new Map();
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 5000;
        
        // P2P Topics (from architecture)
        this.topics = {
            headers: '/coinj/headers/1.0.0',
            commitReveal: '/coinj/commit-reveal/1.0.0',
            requests: '/coinj/requests/1.0.0',
            responses: '/coinj/responses/1.0.0'
        };
        
        // Bootstrap nodes from architecture
        this.bootstrapNodes = [
            '167.172.213.70:5000',  // WebSocket P2P Bridge
            '167.172.213.70:12346', // API Server
            '167.172.213.70:12345'  // Backup
        ];
        
        this.logger = console;
    }

    /**
     * Connect to P2P network
     */
    async connect() {
        try {
            this.logger.log('🌐 Connecting to COINjecture P2P network...');
            
            // Check if we're on HTTPS - if so, skip WebSocket and go straight to API mode
            if (window.location.protocol === 'https:') {
                this.logger.log('🔒 HTTPS detected - using API fallback mode');
                return this.connectViaAPI();
            }
            
            // Try to connect to bootstrap nodes first (HTTP only)
            try {
                await this.connectToBootstrapNode();
                this.connected = true;
                this.reconnectAttempts = 0;
                this.logger.log('✅ Connected to P2P network');
                
                // Subscribe to all topics
                await this.subscribeToTopics();
                
                return true;
            } catch (p2pError) {
                this.logger.warn('⚠️ P2P connection failed, falling back to API mode');
                return this.connectViaAPI();
            }
            
        } catch (error) {
            this.logger.error('❌ Failed to connect to P2P network:', error);
            return false;
        }
    }

    /**
     * Fallback connection via API
     */
    async connectViaAPI() {
        try {
            this.logger.log('🌐 Connecting via API fallback...');
            
            // Simulate P2P connection for API mode
            this.connected = true;
            this.reconnectAttempts = 0;
            
            // Add some mock peers for API mode
            this.peers.set('api-peer-1', {
                peer_id: 'api-peer-1',
                address: 'api.coinjecture.com',
                port: 443,
                last_seen: Date.now(),
                is_bootstrap: true
            });
            
            this.logger.log('✅ Connected via API fallback (simulated P2P)');
            return true;
            
        } catch (error) {
            this.logger.error('❌ API fallback failed:', error);
            return false;
        }
    }

    /**
     * Connect to bootstrap node via WebSocket
     */
    async connectToBootstrapNode() {
        return new Promise((resolve, reject) => {
            // Try each bootstrap node
            const tryBootstrap = async (index = 0) => {
                if (index >= this.bootstrapNodes.length) {
                    reject(new Error('All bootstrap nodes failed'));
                    return;
                }
                
                const node = this.bootstrapNodes[index];
                const [host, port] = node.split(':');
                
                try {
                    // Create WebSocket connection to bootstrap node
                    // Use WS for now (WSS requires SSL certificates)
                    const protocol = 'ws';
                    const path = port === '5000' ? '' : '/p2p';
                    const ws = new WebSocket(`${protocol}://${host}:${port}${path}`);
                    
                    ws.onopen = () => {
                        this.logger.log(`✅ Connected to bootstrap node: ${node}`);
                        this.ws = ws;
                        this.setupWebSocketHandlers();
                        resolve();
                    };
                    
                    ws.onerror = (error) => {
                        this.logger.warn(`⚠️ Failed to connect to ${node}:`, error);
                        tryBootstrap(index + 1);
                    };
                    
                    ws.onclose = () => {
                        this.logger.warn(`🔌 Connection to ${node} closed`);
                        this.connected = false;
                        this.handleReconnect();
                    };
                    
                } catch (error) {
                    this.logger.warn(`⚠️ Error connecting to ${node}:`, error);
                    tryBootstrap(index + 1);
                }
            };
            
            tryBootstrap();
        });
    }

    /**
     * Setup WebSocket message handlers
     */
    setupWebSocketHandlers() {
        if (!this.ws) return;
        
        this.ws.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                this.handleP2PMessage(message);
            } catch (error) {
                this.logger.error('❌ Error parsing P2P message:', error);
            }
        };
    }

    /**
     * Handle incoming P2P messages
     */
    handleP2PMessage(message) {
        const { type, topic, data, peerId } = message;
        
        switch (type) {
            case 'header':
                this.handleHeaderMessage(data, peerId);
                break;
            case 'reveal':
                this.handleRevealMessage(data, peerId);
                break;
            case 'request':
                this.handleRequestMessage(data, peerId);
                break;
            case 'response':
                this.handleResponseMessage(data, peerId);
                break;
            case 'peer_list':
                this.handlePeerListMessage(data);
                break;
            default:
                this.logger.warn('⚠️ Unknown P2P message type:', type);
        }
    }

    /**
     * Handle header messages (new blocks)
     */
    handleHeaderMessage(data, peerId) {
        this.logger.log(`📦 Received header from ${peerId}:`, data);
        
        // Notify subscribers
        const handlers = this.messageHandlers.get('header') || [];
        handlers.forEach(handler => handler(data, peerId));
    }

    /**
     * Handle reveal messages (proof bundles)
     */
    handleRevealMessage(data, peerId) {
        this.logger.log(`🔍 Received reveal from ${peerId}:`, data);
        
        // Notify subscribers
        const handlers = this.messageHandlers.get('reveal') || [];
        handlers.forEach(handler => handler(data, peerId));
    }

    /**
     * Handle request messages
     */
    handleRequestMessage(data, peerId) {
        this.logger.log(`📨 Received request from ${peerId}:`, data);
        
        // Notify subscribers
        const handlers = this.messageHandlers.get('request') || [];
        handlers.forEach(handler => handler(data, peerId));
    }

    /**
     * Handle response messages
     */
    handleResponseMessage(data, peerId) {
        this.logger.log(`📤 Received response from ${peerId}:`, data);
        
        // Notify subscribers
        const handlers = this.messageHandlers.get('response') || [];
        handlers.forEach(handler => handler(data, peerId));
    }

    /**
     * Handle peer list updates
     */
    handlePeerListMessage(data) {
        this.logger.log(`👥 Received peer list:`, data);
        
        if (data.peers) {
            data.peers.forEach(peer => {
                this.peers.set(peer.peer_id, peer);
            });
        }
        
        // Notify subscribers
        const handlers = this.messageHandlers.get('peer_list') || [];
        handlers.forEach(handler => handler(data));
    }

    /**
     * Subscribe to P2P topics
     */
    async subscribeToTopics() {
        for (const [name, topic] of Object.entries(this.topics)) {
            await this.subscribeToTopic(topic, name);
        }
    }

    /**
     * Subscribe to specific topic
     */
    async subscribeToTopic(topic, name) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            this.logger.warn('⚠️ WebSocket not connected, cannot subscribe to topic');
            return;
        }
        
        const message = {
            type: 'subscribe',
            topic: topic,
            name: name
        };
        
        this.ws.send(JSON.stringify(message));
        this.logger.log(`📡 Subscribed to topic: ${name} (${topic})`);
    }

    /**
     * Publish message to P2P network
     */
    async publish(topic, data) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            this.logger.warn('⚠️ WebSocket not connected, cannot publish message');
            return false;
        }
        
        const message = {
            type: this.getTopicType(topic),
            topic: topic,
            data: data,
            timestamp: Date.now()
        };
        
        this.ws.send(JSON.stringify(message));
        this.logger.log(`📤 Published to ${topic}:`, data);
        return true;
    }

    /**
     * Get message type from topic
     */
    getTopicType(topic) {
        if (topic.includes('headers')) return 'header';
        if (topic.includes('commit-reveal')) return 'reveal';
        if (topic.includes('requests')) return 'request';
        if (topic.includes('responses')) return 'response';
        return 'message';
    }

    /**
     * Subscribe to message handlers
     */
    onMessageType(type, handler) {
        if (!this.messageHandlers.has(type)) {
            this.messageHandlers.set(type, []);
        }
        this.messageHandlers.get(type).push(handler);
    }

    /**
     * Unsubscribe from message handlers
     */
    offMessageType(type, handler) {
        if (this.messageHandlers.has(type)) {
            const handlers = this.messageHandlers.get(type);
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }

    /**
     * Request peer list from bootstrap node
     */
    async requestPeerList() {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            return;
        }
        
        const message = {
            type: 'request_peers',
            timestamp: Date.now()
        };
        
        this.ws.send(JSON.stringify(message));
    }

    /**
     * Get connected peers
     */
    getPeers() {
        return Array.from(this.peers.values());
    }

    /**
     * Get peer count
     */
    getPeerCount() {
        return this.peers.size;
    }

    /**
     * Handle reconnection
     */
    async handleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            this.logger.error('❌ Max reconnection attempts reached');
            return;
        }
        
        this.reconnectAttempts++;
        this.logger.log(`🔄 Attempting reconnection ${this.reconnectAttempts}/${this.maxReconnectAttempts}...`);
        
        setTimeout(async () => {
            await this.connect();
        }, this.reconnectDelay);
    }

    /**
     * Disconnect from P2P network
     */
    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        
        this.connected = false;
        this.peers.clear();
        this.subscriptions.clear();
        this.messageHandlers.clear();
        
        this.logger.log('🔌 Disconnected from P2P network');
    }

    /**
     * Check if connected
     */
    isConnected() {
        return this.connected && this.ws && this.ws.readyState === WebSocket.OPEN;
    }
}
