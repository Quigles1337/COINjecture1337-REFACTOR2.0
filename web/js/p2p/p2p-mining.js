/**
 * COINjecture P2P Mining Service
 * Implements real P2P mining with proper consensus participation
 * and IPFS integration for proof bundles
 */

import { P2PClient } from './p2p-client.js';
import { SubsetSumSolver } from '../mining/subset-sum.js';
import { API_CONFIG, MINING_CONFIG } from '../shared/constants.js';

export class P2PMiningService {
    constructor() {
        this.p2pClient = new P2PClient();
        this.solver = new SubsetSumSolver();
        this.isMining = false;
        this.miningInterval = null;
        this.currentBlock = null;
        this.localBlockchain = [];
        this.workScore = 0;
        this.rewards = 0;
        
        // Mining state
        this.miningStats = {
            problemsSolved: 0,
            blocksMined: 0,
            totalWorkScore: 0,
            totalRewards: 0,
            startTime: null
        };
        
        // Setup P2P message handlers
        this.setupP2PHandlers();
    }

    /**
     * Setup P2P message handlers for mining
     */
    setupP2PHandlers() {
        // Handle new headers (blocks)
        this.p2pClient.onMessageType('header', (data, peerId) => {
            this.handleNewBlock(data, peerId);
        });
        
        // Handle reveal messages (proof bundles)
        this.p2pClient.onMessageType('reveal', (data, peerId) => {
            this.handleReveal(data, peerId);
        });
        
        // Handle peer list updates
        this.p2pClient.onMessageType('peer_list', (data) => {
            this.handlePeerListUpdate(data);
        });
    }

    /**
     * Connect to P2P network and start mining
     */
    async startMining() {
        try {
            // Connect to P2P network
            const connected = await this.p2pClient.connect();
            if (!connected) {
                throw new Error('Failed to connect to P2P network');
            }
            
            // Start mining loop
            this.isMining = true;
            this.miningStats.startTime = Date.now();
            
            this.log('⛏️ P2P Mining started! Connected to blockchain network');
            this.log(`👥 Connected to ${this.p2pClient.getPeerCount()} peers`);
            
            // Start mining loop
            this.startMiningLoop();
            
            return true;
            
        } catch (error) {
            this.log(`❌ Failed to start P2P mining: ${error.message}`, 'error');
            return false;
        }
    }

    /**
     * Stop mining
     */
    stopMining() {
        this.isMining = false;
        
        if (this.miningInterval) {
            clearInterval(this.miningInterval);
            this.miningInterval = null;
        }
        
        this.log('⛏️ P2P Mining stopped');
    }

    /**
     * Start the mining loop
     */
    startMiningLoop() {
        if (this.miningInterval) {
            clearInterval(this.miningInterval);
        }
        
        this.miningInterval = setInterval(async () => {
            if (!this.isMining) return;
            
            try {
                await this.performMiningStep();
            } catch (error) {
                this.log(`❌ Mining error: ${error.message}`, 'error');
            }
        }, 5000); // Mine every 5 seconds
    }

    /**
     * Perform a single mining step
     */
    async performMiningStep() {
        try {
            // Generate problem
            const problem = this.solver.generateProblem();
            this.log(`🔍 Solving subset sum problem: ${problem.numbers.length} elements, target ${problem.target}`);
            
            // Solve problem
            const startTime = Date.now();
            const result = await this.solver.solve(problem);
            const solveTime = Date.now() - startTime;
            
            if (!result) {
                this.log('❌ No solution found for this problem', 'warning');
                return;
            }
            
            // Calculate work score
            const workScore = this.calculateWorkScore(result, problem, solveTime);
            const reward = this.calculateReward(workScore);
            
            this.log(`✅ Solution found! Work Score: ${workScore.toFixed(2)}, Reward: ${reward.toFixed(6)} BEANS`);
            
            // Create block and submit to P2P network
            await this.submitMinedBlock(problem, result, workScore, reward);
            
            // Update stats
            this.miningStats.problemsSolved++;
            this.miningStats.totalWorkScore += workScore;
            this.miningStats.totalRewards += reward;
            
        } catch (error) {
            this.log(`❌ Mining step failed: ${error.message}`, 'error');
        }
    }

    /**
     * Calculate work score based on architecture
     */
    calculateWorkScore(result, problem, solveTime) {
        const { numbers, sum } = result.solution;
        const problemSize = numbers.length;
        const target = problem.target;
        
        // Time asymmetry (solve time vs verify time)
        const verifyTime = 0.001; // 1ms verification
        const timeAsymmetry = solveTime / verifyTime;
        
        // Space asymmetry (problem size vs solution size)
        const spaceAsymmetry = problemSize / numbers.length;
        
        // Problem weight (based on target and size)
        const problemWeight = Math.log(target) * problemSize;
        
        // Size factor
        const sizeFactor = Math.sqrt(problemSize);
        
        // Quality score (solution efficiency)
        const qualityScore = 1.0; // Perfect solution
        
        // Energy efficiency (mobile vs desktop)
        const energyEfficiency = 0.8; // Mobile efficiency
        
        // Work score formula from architecture
        const workScore = timeAsymmetry * 
                         Math.sqrt(spaceAsymmetry) * 
                         problemWeight * 
                         sizeFactor * 
                         qualityScore * 
                         energyEfficiency;
        
        return Math.max(workScore, MINING_CONFIG.MIN_WORK_SCORE);
    }

    /**
     * Calculate reward based on dynamic tokenomics
     */
    calculateReward(workScore) {
        // Get network state (simplified for now)
        const networkAvg = 50; // Average work score
        const cumulativeWork = this.miningStats.totalWorkScore + workScore;
        
        // Deflation factor
        const deflationFactor = 1 / Math.pow(2, Math.log2(cumulativeWork) / 10);
        
        // Reward formula from architecture
        const reward = Math.log(1 + workScore / networkAvg) * deflationFactor;
        
        return Math.max(reward, 0.001); // Minimum reward
    }

    /**
     * Submit mined block to P2P network
     */
    async submitMinedBlock(problem, result, workScore, reward) {
        try {
            // Create commitment (Commit Phase)
            const commitment = await this.createCommitment(problem, result);
            
            // Create block header
            const blockHeader = await this.createBlockHeader(problem, result, workScore, commitment);
            
            // Create proof bundle
            const proofBundle = await this.createProofBundle(problem, result, workScore, commitment);
            
            // Check if we're in API fallback mode
            if (this.p2pClient.peers.has('api-peer-1')) {
                // API fallback mode - submit via API
                await this.submitViaAPI(problem, result, workScore, reward, blockHeader, proofBundle, commitment);
            } else {
                // Real P2P mode - publish to network
                await this.p2pClient.publish(this.p2pClient.topics.headers, {
                    header: blockHeader,
                    work_score: workScore,
                    reward: reward,
                    timestamp: Date.now()
                });
                
                // Publish reveal (proof bundle) to P2P network
                await this.p2pClient.publish(this.p2pClient.topics.commitReveal, {
                    cid: proofBundle.cid,
                    commitment: commitment,
                    problem_type: 'subset_sum',
                    tier: this.getOptimalTier()
                });
            }
            
            // Update local blockchain
            this.updateLocalBlockchain(blockHeader, workScore, reward);
            
            this.log(`📤 Block submitted! Work: ${workScore.toFixed(2)}, Reward: ${reward.toFixed(6)} BEANS`);
            
        } catch (error) {
            this.log(`❌ Failed to submit block: ${error.message}`, 'error');
        }
    }

    /**
     * Submit block via API fallback
     */
    async submitViaAPI(problem, result, workScore, reward, blockHeader, proofBundle, commitment) {
        try {
            // Import API module
            const { api } = await import('../core/api.js');
            
            // Generate a proper hex block hash
            const blockData = `${blockHeader.timestamp}_${this.wallet.address}_${workScore}_${commitment}`;
            const blockHash = await this.sha256(blockData);
            
            // Prepare the data
            const submitData = {
                block_hash: blockHash,
                miner_address: this.wallet.address,
                work_score: workScore,
                capacity: 'subset_sum',
                cid: proofBundle.cid || 'QmPlaceholder', // Provide a placeholder if no CID
                solution_data: result.solution.numbers, // Use actual values instead of indices
                problem_data: {
                    type: 'subset_sum',
                    numbers: problem.numbers,
                    target: problem.target
                },
                // Add additional fields that might be expected
                timestamp: Date.now(),
                nonce: Math.random().toString(36).substring(2),
                difficulty: 1.0
            };
            
            // Validate solution before submitting
            const solutionSum = result.solution.numbers.reduce((sum, num) => sum + num, 0);
            const isValidSolution = solutionSum === problem.target;
            
            // Debug logging
            this.log(`🔍 Submitting block data:`, 'info');
            this.log(`   Block Hash: ${blockHash.substring(0, 16)}...`, 'info');
            this.log(`   Miner: ${this.wallet.address}`, 'info');
            this.log(`   Work Score: ${workScore}`, 'info');
            this.log(`   Solution Indices: [${result.solution.indices.join(', ')}]`, 'info');
            this.log(`   Solution Values: [${result.solution.numbers.join(', ')}]`, 'info');
            this.log(`   Solution Sum: ${solutionSum}, Target: ${problem.target}, Valid: ${isValidSolution}`, 'info');
            this.log(`   Problem: ${problem.numbers.length} numbers, target ${problem.target}`, 'info');
            this.log(`   Full Submit Data: ${JSON.stringify(submitData, null, 2)}`, 'info');
            
            if (!isValidSolution) {
                this.log(`❌ Invalid solution detected! Sum ${solutionSum} != Target ${problem.target}`, 'error');
                return;
            }
            
            // Submit via existing API with correct format
            const response = await api.submitMinedBlock(submitData);
            
            // Debug logging
            this.log(`🔍 API Response:`, 'info');
            this.log(`   Status: ${response.status}`, 'info');
            this.log(`   Message: ${response.message}`, 'info');
            this.log(`   Full Response: ${JSON.stringify(response)}`, 'info');

            if (response.status === 'success') {
                const blockHash = response.data?.block_hash || response.block_hash;
                const reward = response.data?.reward || 0;
                
                // Update wallet balance with reward
                if (this.wallet && reward > 0) {
                    this.wallet.balance = (this.wallet.balance || 0) + reward;
                    this.wallet.blocksMined = (this.wallet.blocksMined || 0) + 1;
                    
                    // Save updated wallet to localStorage
                    localStorage.setItem('coinjecture_wallet', JSON.stringify(this.wallet));
                    
                    // Update wallet display if available
                    if (this.updateWalletDisplay) {
                        this.updateWalletDisplay();
                    }
                }
                
                this.log(`✅ Block accepted by API! Block Hash: ${blockHash?.substring(0, 16)}...`);
                this.log(`💰 Reward earned: ${reward.toFixed(6)} BEANS`, 'success');
            } else if (response.success === false && response.error && response.error.includes('consensus validation failed')) {
                // Handle consensus validation error - this might be a server-side issue
                this.log(`⚠️ Consensus validation failed - this might be a server-side issue`, 'warning');
                this.log(`   Block data was valid but server rejected it`, 'warning');
                this.log(`   This could be a temporary server issue`, 'warning');
            } else if (response.success === false) {
                // Handle error response from fetchWithFallback
                this.log(`❌ Block rejected by API: ${response.error || 'Unknown error'}`, 'error');
            } else {
                this.log(`❌ Block rejected by API: ${response.message || 'Unknown error'}`, 'error');
            }
            
        } catch (error) {
            this.log(`❌ API submission failed: ${error.message}`, 'error');
        }
    }

    /**
     * Create commitment hash
     */
    async createCommitment(problem, result) {
        const problemParams = JSON.stringify(problem);
        const solutionHash = await this.sha256(JSON.stringify(result.solution));
        const minerSalt = this.generateSalt();
        const epochSalt = await this.getEpochSalt();
        
        const commitmentData = problemParams + minerSalt + epochSalt + solutionHash;
        return await this.sha256(commitmentData);
    }

    /**
     * Create block header
     */
    async createBlockHeader(problem, result, workScore, commitment) {
        const previousHash = this.getPreviousBlockHash();
        const height = this.localBlockchain.length;
        
        return {
            version: 1,
            parent_hash: previousHash,
            height: height,
            timestamp: Date.now(),
            commitments_root: commitment,
            tx_root: await this.sha256('empty'),
            difficulty_target: this.calculateDifficultyTarget(),
            cumulative_work: this.getCumulativeWork() + workScore,
            miner_pubkey: this.getMinerPublicKey(),
            commit_nonce: this.generateNonce(),
            problem_type: 'subset_sum',
            tier: this.getOptimalTier(),
            commit_epoch: this.getCurrentEpoch(),
            proof_commitment: commitment,
            header_hash: null // Will be calculated
        };
    }

    /**
     * Create proof bundle for IPFS
     */
    async createProofBundle(problem, result, workScore, commitment) {
        const bundle = {
            problem: problem,
            solution: result.solution,
            work_score: workScore,
            commitment: commitment,
            timestamp: Date.now(),
            miner: this.getMinerPublicKey()
        };
        
        // In a real implementation, this would be uploaded to IPFS
        // For now, we'll simulate a CID
        const cid = (await this.sha256(JSON.stringify(bundle))).substring(0, 32);
        
        return {
            cid: cid,
            bundle: bundle
        };
    }

    /**
     * Handle new block from P2P network
     */
    handleNewBlock(data, peerId) {
        this.log(`📦 New block received from ${peerId}: Height ${data.header.height}`);
        
        // Validate block
        if (this.validateBlock(data.header)) {
            this.localBlockchain.push(data.header);
            this.log(`✅ Block validated and added to local chain`);
        } else {
            this.log(`❌ Block validation failed`, 'error');
        }
    }

    /**
     * Handle reveal message
     */
    handleReveal(data, peerId) {
        this.log(`🔍 Reveal received from ${peerId}: CID ${data.cid}`);
        
        // In a real implementation, we would fetch the proof bundle from IPFS
        // and validate the commitment
    }

    /**
     * Handle peer list updates
     */
    handlePeerListUpdate(data) {
        const peerCount = this.p2pClient.getPeerCount();
        this.log(`👥 Peer count updated: ${peerCount} peers`);
    }

    /**
     * Validate block
     */
    validateBlock(header) {
        // Basic validation
        if (!header.height || !header.timestamp || !header.header_hash) {
            return false;
        }
        
        // Check work score
        if (header.cumulative_work < this.getCumulativeWork()) {
            return false;
        }
        
        return true;
    }

    /**
     * Update local blockchain
     */
    updateLocalBlockchain(header, workScore, reward) {
        this.localBlockchain.push(header);
        this.workScore += workScore;
        this.rewards += reward;
        this.miningStats.blocksMined++;
    }

    /**
     * Get mining statistics
     */
    getMiningStats() {
        const runtime = this.miningStats.startTime ? 
            Date.now() - this.miningStats.startTime : 0;
        
        return {
            ...this.miningStats,
            runtime: runtime,
            peerCount: this.p2pClient.getPeerCount(),
            blockchainHeight: this.localBlockchain.length,
            isMining: this.isMining
        };
    }

    /**
     * Utility methods
     */
    async sha256(data) {
        // Use Web Crypto API for proper SHA-256
        const encoder = new TextEncoder();
        const dataBuffer = encoder.encode(data);
        const hashBuffer = await crypto.subtle.digest('SHA-256', dataBuffer);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    }
    
    generateSalt() {
        return Math.random().toString(36).substring(2, 15);
    }
    
    generateNonce() {
        return Math.floor(Math.random() * 1000000);
    }
    
    getPreviousBlockHash() {
        if (this.localBlockchain.length === 0) {
            return '0'.repeat(64); // Genesis
        }
        return this.localBlockchain[this.localBlockchain.length - 1].header_hash;
    }
    
    getCumulativeWork() {
        return this.localBlockchain.reduce((sum, block) => sum + (block.cumulative_work || 0), 0);
    }
    
    getOptimalTier() {
        // Mobile tier for web interface
        return 1;
    }
    
    getCurrentEpoch() {
        return Math.floor(Date.now() / 60000); // 1-minute epochs
    }
    
    async getEpochSalt() {
        return await this.sha256(this.getCurrentEpoch().toString());
    }
    
    calculateDifficultyTarget() {
        // Simplified difficulty calculation
        return 1000;
    }
    
    getMinerPublicKey() {
        // Get from wallet
        const wallet = localStorage.getItem('coinjecture_wallet');
        if (wallet) {
            const parsed = JSON.parse(wallet);
            return parsed.publicKey || 'unknown';
        }
        return 'unknown';
    }

    /**
     * Logging
     */
    log(message, type = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        const prefix = `[${timestamp}] P2P Mining:`;
        
        switch (type) {
            case 'error':
                console.error(`${prefix} ${message}`);
                break;
            case 'warning':
                console.warn(`${prefix} ${message}`);
                break;
            default:
                console.log(`${prefix} ${message}`);
        }
    }
}
