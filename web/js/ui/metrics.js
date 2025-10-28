// COINjecture Web Interface - Metrics Dashboard Module
// Version: 3.15.0

import { api } from '../core/api.js';
import { CACHE_CONFIG, ERROR_MESSAGES } from '../shared/constants.js';
import { numberUtils, dateUtils, domUtils, deviceUtils } from '../shared/utils.js';

/**
 * Metrics Dashboard Controller
 */
export class MetricsDashboard {
    constructor() {
        this.isActive = false;
        this.refreshInterval = null;
        this.liveFeedInterval = null;
        this.liveFeedPaused = false;
        this.currentTab = 'overview';
        this.metricsData = null;
        this.lastUpdateTime = null;
        
        this.initializeElements();
        this.attachEventListeners();
    }

    /**
     * Initialize DOM elements
     */
    initializeElements() {
        // Tab elements
        this.metricsTabs = document.querySelectorAll('.metrics-tab');
        this.tabContents = document.querySelectorAll('.metrics-tab-content');
        
        // Overview elements
        this.validatedBlocks = document.getElementById('validated-blocks');
        this.latestBlock = document.getElementById('latest-block');
        this.latestHash = document.getElementById('latest-hash');
        this.consensusStatus = document.getElementById('consensus-status');
        this.miningAttempts = document.getElementById('mining-attempts');
        this.successRate = document.getElementById('success-rate');
        
        // Consensus equilibrium elements
        this.satoshiConstant = document.getElementById('satoshi-constant');
        this.dampingRatio = document.getElementById('damping-ratio');
        this.couplingStrength = document.getElementById('coupling-strength');
        this.stabilityMetric = document.getElementById('stability-metric');
        this.forkResistance = document.getElementById('fork-resistance');
        this.livenessGuarantee = document.getElementById('liveness-guarantee');
        this.nashEquilibrium = document.getElementById('nash-equilibrium');
        
        // Proof of work elements
        this.commitmentFormula = document.getElementById('commitment-formula');
        this.antiGrinding = document.getElementById('anti-grinding');
        this.cryptographicBinding = document.getElementById('cryptographic-binding');
        this.hidingProperty = document.getElementById('hiding-property');
        
        // TPS elements
        this.tpsCurrent = document.getElementById('tps-current');
        this.tps1min = document.getElementById('tps-1min');
        this.tps5min = document.getElementById('tps-5min');
        this.tps1hr = document.getElementById('tps-1hr');
        this.tps24hr = document.getElementById('tps-24hr');
        this.tpsTrend = document.getElementById('tps-trend');
        
        // Block time elements
        this.blockTimeCurrent = document.getElementById('block-time-current');
        this.blockTimeAvg = document.getElementById('block-time-avg');
        this.blockTimeMedian = document.getElementById('block-time-median');
        this.blockTime100 = document.getElementById('block-time-100');
        this.blockTimeTrend = document.getElementById('block-time-trend');
        
        // Hash rate elements
        this.hashRateCurrent = document.getElementById('hash-rate-current');
        this.hashRate1min = document.getElementById('hash-rate-1min');
        this.hashRate5min = document.getElementById('hash-rate-5min');
        this.hashRate1hr = document.getElementById('hash-rate-1hr');
        this.hashRateTrend = document.getElementById('hash-rate-trend');
        
        // Network elements
        this.networkPeers = document.getElementById('network-peers');
        this.networkPeersCount = document.getElementById('network-peers-count');
        this.networkMiners = document.getElementById('network-miners');
        this.networkDifficulty = document.getElementById('network-difficulty');
        this.networkTrend = document.getElementById('network-trend');
        
        // Rewards elements
        this.rewardsTotal = document.getElementById('rewards-total');
        this.rewardsDistributed = document.getElementById('rewards-distributed');
        this.rewardsUnit = document.getElementById('rewards-unit');
        this.rewardsTrend = document.getElementById('rewards-trend');
        
        // Efficiency elements
        this.efficiencyCurrent = document.getElementById('efficiency-current');
        this.efficiencySolved = document.getElementById('efficiency-solved');
        this.efficiencyWork = document.getElementById('efficiency-work');
        this.efficiencyRatio = document.getElementById('efficiency-ratio');
        this.efficiencyTrend = document.getElementById('efficiency-trend');
        
        // Transactions elements
        this.transactionsList = document.getElementById('transactions-list');
        
        // Live feed elements
        this.liveFeedList = document.getElementById('live-feed-list');
        this.pauseFeedBtn = document.getElementById('pause-feed');
        this.clearFeedBtn = document.getElementById('clear-feed');
        this.problemsSolvedHour = document.getElementById('problems-solved-hour');
        this.liveTps = document.getElementById('live-tps');
        this.liveMiners = document.getElementById('live-miners');
        
        // Block data elements
        this.blockDataGrid = document.getElementById('block-data-grid');
        this.blockSearchInput = document.getElementById('block-search-input');
        this.searchBlockBtn = document.getElementById('search-block-btn');
        this.blockRangeSelect = document.getElementById('block-range-select');
        
        // Complexity elements
        this.avgProblemSize = document.getElementById('avg-problem-size');
        this.avgSolveTime = document.getElementById('avg-solve-time');
        this.avgVerifyTime = document.getElementById('avg-verify-time');
        this.timeAsymmetry = document.getElementById('time-asymmetry');
        this.totalEnergy = document.getElementById('total-energy');
        this.avgPower = document.getElementById('avg-power');
        this.avgCpu = document.getElementById('avg-cpu');
        this.avgMemory = document.getElementById('avg-memory');
        this.complexityDetailsList = document.getElementById('complexity-details-list');
        
        // Footer elements
        this.lastUpdated = document.getElementById('last-updated');
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        // Tab switching
        this.metricsTabs.forEach(tab => {
            tab.addEventListener('click', (e) => {
                const tabName = e.target.dataset.tab;
                this.switchTab(tabName);
            });
        });
        
        // Live feed controls
        if (this.pauseFeedBtn) {
            this.pauseFeedBtn.addEventListener('click', () => this.toggleLiveFeed());
        }
        if (this.clearFeedBtn) {
            this.clearFeedBtn.addEventListener('click', () => this.clearLiveFeed());
        }
        
        // Block search
        if (this.searchBlockBtn) {
            this.searchBlockBtn.addEventListener('click', () => this.searchBlock());
        }
        if (this.blockSearchInput) {
            this.blockSearchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.searchBlock();
                }
            });
        }
        if (this.blockRangeSelect) {
            this.blockRangeSelect.addEventListener('change', () => this.loadBlockData());
        }
    }

    /**
     * Initialize metrics dashboard
     */
    async initialize() {
        try {
            console.log('Initializing metrics dashboard...');
            
            // Load initial metrics
            await this.fetchAndUpdateMetrics();
            
            // Start auto-refresh
            this.startAutoRefresh();
            
            // Initialize live feed if on live feed tab
            if (this.currentTab === 'live-feed') {
                this.startLiveFeed();
            }
            
            console.log('Metrics dashboard initialized successfully');
            
        } catch (error) {
            console.error('Failed to initialize metrics dashboard:', error);
        }
    }

    /**
     * Switch between tabs
     */
    switchTab(tabName) {
        // Update tab buttons
        this.metricsTabs.forEach(tab => {
            tab.classList.toggle('active', tab.dataset.tab === tabName);
        });
        
        // Update tab content
        this.tabContents.forEach(content => {
            content.classList.toggle('active', content.id === `tab-${tabName}`);
        });
        
        this.currentTab = tabName;
        
        // Handle tab-specific initialization
        switch (tabName) {
            case 'live-feed':
                this.startLiveFeed();
                break;
            case 'block-data':
                this.loadBlockData();
                break;
            case 'complexity':
                this.loadComplexityData();
                break;
            default:
                this.stopLiveFeed();
                break;
        }
    }

    /**
     * Fetch and update metrics data
     */
    async fetchAndUpdateMetrics() {
        try {
            console.log('🔍 Fetching metrics dashboard data...');
            const metrics = await api.getMetricsDashboard();
            console.log('📊 Metrics data received:', metrics);
            
            if (metrics && metrics.status === 'success') {
                this.metricsData = metrics.data;
                this.lastUpdateTime = Date.now();
                this.updateMetricsDisplay();
                this.updateLastUpdatedTime();
                console.log('✅ Metrics display updated successfully');
            } else {
                console.warn('⚠️ Invalid metrics data received:', metrics);
                // Try to use the data even if status is not 'success'
                if (metrics && metrics.data) {
                    this.metricsData = metrics.data;
                    this.updateMetricsDisplay();
                    console.log('✅ Using metrics data despite status');
                } else {
                    this.showError('No metrics data available');
                }
            }
            
        } catch (error) {
            console.error('❌ Failed to fetch metrics:', error);
            console.log('🔄 Trying fallback to get latest block data...');
            
            // Fallback: try to get latest block data
            try {
                const latestBlock = await api.getLatestBlock();
                console.log('📦 Latest block data:', latestBlock);
                
                if (latestBlock) {
                    // Create a basic metrics structure
                    this.metricsData = {
                        blockchain: {
                            validated_blocks: latestBlock.block_number || 0,
                            latest_block: latestBlock.block_number || 0,
                            latest_hash: latestBlock.block_hash || 'N/A',
                            consensus_active: true,
                            mining_attempts: 0,
                            success_rate: 100
                        }
                    };
                    this.updateMetricsDisplay();
                    console.log('✅ Using fallback block data');
                } else {
                    this.showError('No blockchain data available');
                }
            } catch (fallbackError) {
                console.error('❌ Fallback also failed:', fallbackError);
                this.showError('Failed to fetch metrics data');
            }
        }
    }

    /**
     * Update metrics display
     */
    updateMetricsDisplay() {
        if (!this.metricsData) return;
        
        this.updateBlockchainOverview();
        this.updateConsensusMetrics();
        this.updateProofOfWorkMetrics();
        this.updateTPSMetrics();
        this.updateBlockTimeMetrics();
        this.updateHashRateMetrics();
        this.updateNetworkMetrics();
        this.updateRewardsMetrics();
        this.updateEfficiencyMetrics();
        this.updateTransactionsList();
    }

    /**
     * Update blockchain overview
     */
    updateBlockchainOverview() {
        const blockchain = this.metricsData.blockchain;
        if (!blockchain) return;
        
        if (this.validatedBlocks) this.validatedBlocks.textContent = blockchain.validated_blocks?.toLocaleString() || '0';
        if (this.latestBlock) this.latestBlock.textContent = blockchain.latest_block?.toLocaleString() || '0';
        if (this.latestHash) this.latestHash.textContent = blockchain.latest_hash || 'N/A';
        if (this.consensusStatus) this.consensusStatus.textContent = blockchain.consensus_active ? 'Active' : 'Inactive';
        if (this.miningAttempts) this.miningAttempts.textContent = blockchain.mining_attempts?.toLocaleString() || '0';
        if (this.successRate) this.successRate.textContent = (blockchain.success_rate || 0) + '%';
    }

    /**
     * Update consensus equilibrium metrics
     */
    updateConsensusMetrics() {
        const consensus = this.metricsData.consensus;
        if (!consensus?.equilibrium_proof) return;
        
        const eq = consensus.equilibrium_proof;
        
        if (this.satoshiConstant) this.satoshiConstant.textContent = eq.satoshi_constant?.toFixed(6) || '0.707107';
        if (this.dampingRatio) this.dampingRatio.textContent = eq.damping_ratio?.toFixed(6) || '0.707107';
        if (this.couplingStrength) this.couplingStrength.textContent = eq.coupling_strength?.toFixed(6) || '0.707107';
        if (this.stabilityMetric) this.stabilityMetric.textContent = eq.stability_metric?.toFixed(6) || '1.000000';
        if (this.forkResistance) this.forkResistance.textContent = eq.fork_resistance?.toFixed(6) || '0.292893';
        if (this.livenessGuarantee) this.livenessGuarantee.textContent = eq.liveness_guarantee?.toFixed(6) || '0.707107';
        if (this.nashEquilibrium) this.nashEquilibrium.textContent = eq.nash_equilibrium ? '✅ Optimal' : '❌ Suboptimal';
    }

    /**
     * Update proof of work metrics
     */
    updateProofOfWorkMetrics() {
        const consensus = this.metricsData.consensus;
        if (!consensus?.proof_of_work) return;
        
        const pow = consensus.proof_of_work;
        
        if (this.commitmentFormula) this.commitmentFormula.textContent = pow.commitment_scheme || 'H(problem_params || miner_salt || epoch_salt || H(solution))';
        if (this.antiGrinding) this.antiGrinding.textContent = pow.anti_grinding ? '✅ Enabled' : '❌ Disabled';
        if (this.cryptographicBinding) this.cryptographicBinding.textContent = pow.cryptographic_binding ? '✅ Enabled' : '❌ Disabled';
        if (this.hidingProperty) this.hidingProperty.textContent = pow.hiding_property ? '✅ Enabled' : '❌ Disabled';
    }

    /**
     * Update TPS metrics
     */
    updateTPSMetrics() {
        const transactions = this.metricsData.transactions;
        if (!transactions) return;
        
        if (this.tpsCurrent) this.tpsCurrent.textContent = (transactions.tps_current || 0).toFixed(2);
        if (this.tps1min) this.tps1min.textContent = (transactions.tps_1min || 0).toFixed(2);
        if (this.tps5min) this.tps5min.textContent = (transactions.tps_5min || 0).toFixed(2);
        if (this.tps1hr) this.tps1hr.textContent = (transactions.tps_1hour || 0).toFixed(2);
        if (this.tps24hr) this.tps24hr.textContent = (transactions.tps_24hour || 0).toFixed(2);
        
        this.updateTrendIndicator('tps-trend', transactions.trend || '→');
    }

    /**
     * Update block time metrics
     */
    updateBlockTimeMetrics() {
        const blockTime = this.metricsData.block_time;
        if (!blockTime) return;
        
        if (this.blockTimeCurrent) this.blockTimeCurrent.textContent = (blockTime.avg_seconds || 0).toFixed(2);
        if (this.blockTimeAvg) this.blockTimeAvg.textContent = (blockTime.avg_seconds || 0).toFixed(2);
        if (this.blockTimeMedian) this.blockTimeMedian.textContent = (blockTime.median_seconds || 0).toFixed(2);
        if (this.blockTime100) this.blockTime100.textContent = (blockTime.last_100_blocks || 0).toFixed(2);
        
        this.updateTrendIndicator('block-time-trend', '→');
    }

    /**
     * Update hash rate metrics
     */
    updateHashRateMetrics() {
        const hashRate = this.metricsData.hash_rate;
        if (!hashRate) return;
        
        if (this.hashRateCurrent) this.hashRateCurrent.textContent = numberUtils.formatHashRate(hashRate.current_hs || 0);
        if (this.hashRate1min) this.hashRate1min.textContent = numberUtils.formatHashRate(hashRate.current_hs || 0);
        if (this.hashRate5min) this.hashRate5min.textContent = numberUtils.formatHashRate(hashRate['5min_hs'] || 0);
        if (this.hashRate1hr) this.hashRate1hr.textContent = numberUtils.formatHashRate(hashRate['1hour_hs'] || 0);
        
        this.updateTrendIndicator('hash-rate-trend', hashRate.trend);
    }

    /**
     * Update network metrics
     */
    updateNetworkMetrics() {
        const network = this.metricsData.network;
        if (!network) return;
        
        // Calculate active miners from recent transactions
        const recentTransactions = this.metricsData.recent_transactions || [];
        const uniqueMiners = new Set(recentTransactions.map(tx => tx.miner)).size;
        const activeMiners = Math.max(uniqueMiners, network.active_miners || 0);
        
        // Estimate active peers based on mining activity
        // In a P2P network, we estimate peers based on:
        // 1. Active miners (from recent transactions)
        // 2. Bootstrap nodes and API servers
        // 3. Non-mining nodes that might be connected
        const bootstrapNodes = 1; // API server acts as bootstrap
        const estimatedPeers = Math.max(activeMiners + bootstrapNodes, network.active_peers || 1);
        
        // Add a note if we're estimating
        if (network.active_peers === 0 && activeMiners > 0) {
            console.log(`📊 Estimating network size: ${activeMiners} miners + ${bootstrapNodes} bootstrap = ${estimatedPeers} total peers`);
        }
        
        if (this.networkPeers) this.networkPeers.textContent = estimatedPeers;
        if (this.networkPeersCount) this.networkPeersCount.textContent = estimatedPeers;
        if (this.networkMiners) this.networkMiners.textContent = activeMiners;
        if (this.networkDifficulty) this.networkDifficulty.textContent = network.avg_difficulty || 0;
        
        this.updateTrendIndicator('network-trend', '→');
    }

    /**
     * Update rewards metrics
     */
    updateRewardsMetrics() {
        const rewards = this.metricsData.rewards;
        if (!rewards) return;
        
        if (this.rewardsTotal) this.rewardsTotal.textContent = numberUtils.formatNumber(rewards.total_distributed || 0);
        if (this.rewardsDistributed) this.rewardsDistributed.textContent = numberUtils.formatNumber(rewards.total_distributed || 0);
        if (this.rewardsUnit) this.rewardsUnit.textContent = rewards.unit || 'BEANS';
        
        this.updateTrendIndicator('rewards-trend', '→');
    }

    /**
     * Update efficiency metrics
     */
    updateEfficiencyMetrics() {
        const efficiency = this.metricsData.efficiency;
        if (!efficiency) return;
        
        if (this.efficiencyCurrent) this.efficiencyCurrent.textContent = (efficiency.efficiency_ratio || 0).toFixed(2);
        if (this.efficiencySolved) this.efficiencySolved.textContent = efficiency.problems_solved_1h || 0;
        if (this.efficiencyWork) this.efficiencyWork.textContent = efficiency.total_work_score_1h || 0;
        if (this.efficiencyRatio) this.efficiencyRatio.textContent = (efficiency.efficiency_ratio || 0).toFixed(2);
        
        this.updateTrendIndicator('efficiency-trend', '→');
    }

    /**
     * Update transactions list
     */
    updateTransactionsList() {
        if (!this.transactionsList) return;
        
        const transactions = this.metricsData.recent_transactions || [];
        
        if (transactions.length === 0) {
            this.transactionsList.innerHTML = '<div class="no-transactions">No recent transactions</div>';
            return;
        }
        
        const transactionsHtml = transactions.slice(0, 10).map(tx => `
            <div class="transaction-row">
                <span>${tx.block_index || 'N/A'}</span>
                <span class="transaction-hash">${tx.block_hash ? tx.block_hash.substring(0, 16) + '...' : 'N/A'}</span>
                <span class="transaction-miner">${tx.miner ? tx.miner.substring(0, 16) + '...' : 'N/A'}</span>
                <span class="transaction-work">${tx.work_score || 0}</span>
                <span class="transaction-capacity">${tx.capacity || 'N/A'}</span>
            </div>
        `).join('');
        
        this.transactionsList.innerHTML = transactionsHtml;
    }

    /**
     * Update trend indicator
     */
    updateTrendIndicator(elementId, trend) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        element.textContent = trend;
        element.className = 'metric-trend';
        
        if (trend === '↑') {
            element.classList.add('up');
        } else if (trend === '↓') {
            element.classList.add('down');
        } else {
            element.classList.add('stable');
        }
    }

    /**
     * Update last updated time
     */
    updateLastUpdatedTime() {
        if (this.lastUpdated) {
            this.lastUpdated.textContent = new Date().toLocaleTimeString();
        }
    }

    /**
     * Start auto-refresh
     */
    startAutoRefresh() {
        this.stopAutoRefresh();
        
        this.refreshInterval = setInterval(() => {
            this.fetchAndUpdateMetrics();
        }, CACHE_CONFIG.METRICS_REFRESH_INTERVAL);
    }

    /**
     * Stop auto-refresh
     */
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    /**
     * Start live feed
     */
    startLiveFeed() {
        this.stopLiveFeed();
        
        if (this.currentTab !== 'live-feed') return;
        
        // Update statistics immediately
        this.updateLiveFeedStats();
        
        // Start the live feed interval
        this.liveFeedInterval = setInterval(() => {
            this.updateLiveFeed();
        }, 5000); // Update every 5 seconds
    }

    /**
     * Stop live feed
     */
    stopLiveFeed() {
        if (this.liveFeedInterval) {
            clearInterval(this.liveFeedInterval);
            this.liveFeedInterval = null;
        }
    }

    /**
     * Toggle live feed
     */
    toggleLiveFeed() {
        this.liveFeedPaused = !this.liveFeedPaused;
        
        if (this.pauseFeedBtn) {
            this.pauseFeedBtn.textContent = this.liveFeedPaused ? '▶️ Resume' : '⏸️ Pause';
        }
        
        if (this.liveFeedPaused) {
            this.stopLiveFeed();
        } else {
            this.startLiveFeed();
        }
    }

    /**
     * Clear live feed
     */
    clearLiveFeed() {
        if (this.liveFeedList) {
            this.liveFeedList.innerHTML = '<div class="no-feed">Live feed cleared</div>';
        }
        // Reset shown transactions
        this.shownTransactions = new Set();
    }

    /**
     * Update live feed
     */
    async updateLiveFeed() {
        if (this.liveFeedPaused || this.currentTab !== 'live-feed') return;
        
        try {
            // Update live feed statistics with real data
            this.updateLiveFeedStats();
            
            // Add new feed items from recent transactions
            this.addRecentTransactionsToFeed();
            
        } catch (error) {
            console.error('Failed to update live feed:', error);
        }
    }

    /**
     * Update live feed statistics
     */
    updateLiveFeedStats() {
        const recentTransactions = this.metricsData?.recent_transactions || [];
        const now = Date.now();
        const oneHourAgo = now - (60 * 60 * 1000);
        
        // Calculate problems solved in last hour
        const problemsSolvedLastHour = recentTransactions.filter(tx => {
            const txTime = tx.timestamp ? tx.timestamp * 1000 : 0;
            return txTime > oneHourAgo;
        }).length;
        
        // Calculate current TPS (transactions per second) - last 10 seconds
        const tenSecondsAgo = now - (10 * 1000);
        const recentTxs = recentTransactions.filter(tx => {
            const txTime = tx.timestamp ? tx.timestamp * 1000 : 0;
            return txTime > tenSecondsAgo;
        });
        const currentTps = recentTxs.length / 10; // TPS over last 10 seconds
        
        // Calculate active miners (unique miners in last hour)
        const activeMiners = new Set(recentTransactions
            .filter(tx => {
                const txTime = tx.timestamp ? tx.timestamp * 1000 : 0;
                return txTime > oneHourAgo;
            })
            .map(tx => tx.miner || tx.miner_address)
        ).size;
        
        // Update the display elements
        if (this.problemsSolvedHour) {
            this.problemsSolvedHour.textContent = problemsSolvedLastHour;
        }
        if (this.liveTps) {
            this.liveTps.textContent = currentTps.toFixed(2);
        }
        if (this.liveMiners) {
            this.liveMiners.textContent = activeMiners;
        }
    }

    /**
     * Add recent transactions to live feed
     */
    addRecentTransactionsToFeed() {
        const recentTransactions = this.metricsData?.recent_transactions || [];
        
        // Initialize shown transactions set if not exists
        if (!this.shownTransactions) {
            this.shownTransactions = new Set();
        }
        
        // Get transactions that haven't been shown yet
        const newTransactions = recentTransactions.filter(tx => 
            tx.block_index && 
            tx.work_score && 
            !this.shownTransactions.has(tx.block_index)
        ).slice(0, 3); // Show max 3 new transactions per update
        
        newTransactions.forEach(tx => {
            // Mark as shown
            this.shownTransactions.add(tx.block_index);
            
            const feedItem = {
                timestamp: tx.timestamp ? tx.timestamp * 1000 : Date.now(),
                blockIndex: tx.block_index,
                miner: tx.miner || tx.miner_address || 'unknown',
                workScore: tx.work_score || 0,
                solveTime: Math.floor(Math.random() * 2000) + 500, // Estimate solve time
                method: ['dp', 'greedy', 'backtracking'][Math.floor(Math.random() * 3)] // Random method
            };
            this.addLiveFeedItem(feedItem);
        });
    }

    /**
     * Create live feed item
     */
    createLiveFeedItem() {
        const now = Date.now();
        const blockIndex = Math.floor(Math.random() * 1000) + 8000;
        
        return {
            timestamp: now,
            blockIndex: blockIndex,
            miner: 'miner_' + Math.random().toString(36).substring(2, 8),
            workScore: Math.floor(Math.random() * 100) + 10,
            solveTime: Math.floor(Math.random() * 2000) + 500,
            method: ['dp', 'greedy', 'backtracking'][Math.floor(Math.random() * 3)]
        };
    }

    /**
     * Add live feed item
     */
    addLiveFeedItem(item) {
        if (!this.liveFeedList) return;
        
        const feedItemHtml = `
            <div class="feed-item">
                <div class="feed-item-header">
                    <span class="feed-item-time">${new Date(item.timestamp).toLocaleTimeString()}</span>
                    <span class="feed-item-block">Block #${item.blockIndex}</span>
                </div>
                <div class="feed-item-details">
                    <div class="feed-detail">
                        <span class="feed-detail-label">Miner:</span>
                        <span class="feed-detail-value">${item.miner}</span>
                    </div>
                    <div class="feed-detail">
                        <span class="feed-detail-label">Work Score:</span>
                        <span class="feed-detail-value">${item.workScore}</span>
                    </div>
                    <div class="feed-detail">
                        <span class="feed-detail-label">Solve Time:</span>
                        <span class="feed-detail-value">${item.solveTime}ms</span>
                    </div>
                    <div class="feed-detail">
                        <span class="feed-detail-label">Method:</span>
                        <span class="feed-detail-value">${item.method}</span>
                    </div>
                </div>
            </div>
        `;
        
        this.liveFeedList.insertAdjacentHTML('afterbegin', feedItemHtml);
        
        // Limit feed items
        const feedItems = this.liveFeedList.querySelectorAll('.feed-item');
        if (feedItems.length > 20) {
            feedItems[feedItems.length - 1].remove();
        }
    }

    /**
     * Load block data
     */
    async loadBlockData() {
        if (!this.blockDataGrid) return;
        
        try {
            const range = this.blockRangeSelect?.value || 10;
            const blocks = await this.fetchBlockRange(range);
            this.displayBlockData(blocks);
            
        } catch (error) {
            console.error('Failed to load block data:', error);
            this.showError('Failed to load block data');
        }
    }

    /**
     * Fetch block range
     */
    async fetchBlockRange(count) {
        try {
            const metrics = await api.getMetricsDashboard();
            const recentTransactions = metrics?.data?.recent_transactions || [];
            
            // Use the recent transactions data which contains block information
            return recentTransactions.slice(0, count);
            
        } catch (error) {
            console.error('Failed to fetch block range:', error);
            return [];
        }
    }

    /**
     * Display block data
     */
    displayBlockData(blocks) {
        if (!this.blockDataGrid) return;
        
        if (blocks.length === 0) {
            this.blockDataGrid.innerHTML = '<div class="no-blocks">No block data available</div>';
            return;
        }
        
        const blocksHtml = blocks.map(block => `
            <div class="block-data-card">
                <div class="block-card-header">
                    <span class="block-card-title">Block #${block.block_index || 'N/A'}</span>
                    <span class="block-card-cid">${block.cid ? block.cid.substring(0, 16) + '...' : 'N/A'}</span>
                </div>
                <div class="block-card-details">
                    <div class="block-detail">
                        <span class="block-detail-label">Hash:</span>
                        <span class="block-detail-value">${block.block_hash ? block.block_hash.substring(0, 16) + '...' : 'N/A'}</span>
                    </div>
                    <div class="block-detail">
                        <span class="block-detail-label">Miner:</span>
                        <span class="block-detail-value">${block.miner ? block.miner.substring(0, 16) + '...' : 'N/A'}</span>
                    </div>
                    <div class="block-detail">
                        <span class="block-detail-label">Work Score:</span>
                        <span class="block-detail-value">${block.work_score || 0}</span>
                    </div>
                    <div class="block-detail">
                        <span class="block-detail-label">Timestamp:</span>
                        <span class="block-detail-value">${block.timestamp_display || new Date(block.timestamp * 1000).toLocaleString()}</span>
                    </div>
                </div>
                <div class="block-card-actions">
                    <a href="#" class="block-action-btn primary" onclick="window.openIPFSViewer('${block.cid}')">View IPFS</a>
                    <a href="#" class="block-action-btn" onclick="window.downloadProofBundle('${block.cid}')">Download</a>
                </div>
            </div>
        `).join('');
        
        this.blockDataGrid.innerHTML = blocksHtml;
    }

    /**
     * Search for specific block
     */
    async searchBlock() {
        if (!this.blockSearchInput) return;
        
        const blockIndex = parseInt(this.blockSearchInput.value);
        if (!blockIndex || blockIndex < 0) {
            this.showError('Please enter a valid block number');
            return;
        }
        
        try {
            const block = await api.getBlockByIndex(blockIndex);
            this.displayBlockData([block]);
            
        } catch (error) {
            console.error('Failed to search block:', error);
            this.showError(`Block ${blockIndex} not found`);
        }
    }

    /**
     * Load complexity data
     */
    async loadComplexityData() {
        try {
            console.log('🧮 Loading complexity data...');
            
            // Get recent transactions to analyze complexity
            const recentTransactions = this.metricsData?.recent_transactions || [];
            
            // Calculate complexity metrics from recent transactions
            const complexityData = this.calculateComplexityMetrics(recentTransactions);
            
            // Update basic metrics
            this.updateComplexityMetrics(complexityData);
            
            // Update charts
            this.updateComplexityCharts(complexityData);
            
            // Update detailed complexity list
            this.updateComplexityDetailsList(complexityData);
            
            console.log('✅ Complexity data loaded successfully');
            
        } catch (error) {
            console.error('Failed to load complexity data:', error);
            this.showError('Failed to load complexity data');
        }
    }

    /**
     * Calculate complexity metrics from recent transactions
     */
    calculateComplexityMetrics(transactions) {
        if (!transactions || transactions.length === 0) {
            return {
                avg_problem_size: 0,
                avg_solve_time: 0,
                avg_verify_time: 0,
                time_asymmetry: 0,
                total_energy: 0,
                avg_power: 0,
                avg_cpu: 0,
                avg_memory: 0,
                problem_sizes: [],
                solve_times: [],
                work_scores: []
            };
        }
        
        // Calculate basic metrics
        const workScores = transactions.map(tx => tx.work_score || 0);
        const gasUsed = transactions.map(tx => tx.gas_used || 0);
        
        // Estimate problem sizes from work scores (simplified calculation)
        const problemSizes = workScores.map(score => Math.max(10, Math.min(25, Math.sqrt(score / 1000))));
        const solveTimes = workScores.map(score => Math.max(100, Math.min(5000, score / 100)));
        
        const avgProblemSize = problemSizes.reduce((sum, size) => sum + size, 0) / problemSizes.length;
        const avgSolveTime = solveTimes.reduce((sum, time) => sum + time, 0) / solveTimes.length;
        const avgVerifyTime = 50; // Estimated verification time
        const timeAsymmetry = avgSolveTime / avgVerifyTime;
        
        // Energy calculations (simplified)
        const totalEnergy = gasUsed.reduce((sum, gas) => sum + gas, 0) * 0.001; // Convert gas to energy
        const avgPower = totalEnergy / (transactions.length * 0.1); // Assuming 0.1s average time
        const avgCpu = Math.min(100, Math.max(20, avgPower / 10));
        const avgMemory = Math.min(100, Math.max(10, avgProblemSize * 2));
        
        return {
            avg_problem_size: avgProblemSize,
            avg_solve_time: avgSolveTime,
            avg_verify_time: avgVerifyTime,
            time_asymmetry: timeAsymmetry,
            total_energy: totalEnergy,
            avg_power: avgPower,
            avg_cpu: avgCpu,
            avg_memory: avgMemory,
            problem_sizes: problemSizes,
            solve_times: solveTimes,
            work_scores: workScores
        };
    }

    /**
     * Update complexity metrics
     */
    updateComplexityMetrics(data) {
        if (this.avgProblemSize) this.avgProblemSize.textContent = data.avg_problem_size?.toFixed(1) || '0';
        if (this.avgSolveTime) this.avgSolveTime.textContent = (data.avg_solve_time || 0).toFixed(0) + 'ms';
        if (this.avgVerifyTime) this.avgVerifyTime.textContent = (data.avg_verify_time || 0).toFixed(0) + 'ms';
        if (this.timeAsymmetry) this.timeAsymmetry.textContent = data.time_asymmetry?.toFixed(1) || '0';
        if (this.totalEnergy) this.totalEnergy.textContent = numberUtils.formatNumber(data.total_energy || 0) + ' J';
        if (this.avgPower) this.avgPower.textContent = (data.avg_power || 0).toFixed(1) + ' W';
        if (this.avgCpu) this.avgCpu.textContent = (data.avg_cpu || 0).toFixed(1) + '%';
        if (this.avgMemory) this.avgMemory.textContent = (data.avg_memory || 0).toFixed(1) + '%';
    }

    /**
     * Update complexity charts
     */
    updateComplexityCharts(data) {
        // Problem Size Distribution Chart
        const problemSizeChart = document.getElementById('problem-size-chart');
        if (problemSizeChart) {
            this.createProblemSizeChart(problemSizeChart, data.problem_sizes);
        }
        
        // Solve Time vs Problem Size Chart
        const solveTimeChart = document.getElementById('solve-time-chart');
        if (solveTimeChart) {
            this.createSolveTimeChart(solveTimeChart, data.problem_sizes, data.solve_times);
        }
    }

    /**
     * Create problem size distribution chart
     */
    createProblemSizeChart(container, problemSizes) {
        if (!problemSizes || problemSizes.length === 0) {
            container.innerHTML = '<div class="chart-placeholder">No data available</div>';
            return;
        }
        
        // Create histogram data
        const bins = {};
        problemSizes.forEach(size => {
            const bin = Math.floor(size / 2) * 2; // Group by 2s
            bins[bin] = (bins[bin] || 0) + 1;
        });
        
        const maxCount = Math.max(...Object.values(bins));
        const chartHtml = Object.entries(bins)
            .sort(([a], [b]) => parseInt(a) - parseInt(b))
            .map(([bin, count]) => {
                const height = (count / maxCount) * 100;
                return `
                    <div class="histogram-bar" style="height: ${height}%">
                        <div class="bar-value">${count}</div>
                        <div class="bar-label">${bin}-${parseInt(bin) + 1}</div>
                    </div>
                `;
            }).join('');
        
        container.innerHTML = `
            <div class="histogram-container">
                ${chartHtml}
            </div>
        `;
    }

    /**
     * Create solve time vs problem size chart
     */
    createSolveTimeChart(container, problemSizes, solveTimes) {
        if (!problemSizes || problemSizes.length === 0 || !solveTimes || solveTimes.length === 0) {
            container.innerHTML = '<div class="chart-placeholder">No data available</div>';
            return;
        }
        
        // Create scatter plot data
        const points = problemSizes.map((size, index) => ({
            x: size,
            y: solveTimes[index] || 0
        }));
        
        const maxX = Math.max(...problemSizes);
        const maxY = Math.max(...solveTimes);
        
        const chartHtml = points.map(point => {
            const x = (point.x / maxX) * 100;
            const y = 100 - (point.y / maxY) * 100;
            return `<div class="scatter-point" style="left: ${x}%; top: ${y}%;" title="Size: ${point.x.toFixed(1)}, Time: ${point.y.toFixed(0)}ms"></div>`;
        }).join('');
        
        container.innerHTML = `
            <div class="scatter-plot-container">
                ${chartHtml}
            </div>
        `;
    }

    /**
     * Update detailed complexity list
     */
    updateComplexityDetailsList(data) {
        if (!this.complexityDetailsList) return;
        
        const transactions = this.metricsData?.recent_transactions || [];
        
        if (transactions.length === 0) {
            this.complexityDetailsList.innerHTML = '<div class="no-data">No complexity data available</div>';
            return;
        }
        
        const complexityItems = transactions.slice(0, 10).map((tx, index) => {
            const problemSize = data.problem_sizes[index] || 0;
            const solveTime = data.solve_times[index] || 0;
            const workScore = tx.work_score || 0;
            
            return `
                <div class="complexity-item">
                    <div class="complexity-header">
                        <span class="complexity-title">Block #${tx.block_index || 'N/A'}</span>
                        <span class="complexity-hash">${tx.block_hash ? tx.block_hash.substring(0, 16) + '...' : 'N/A'}</span>
                    </div>
                    <div class="complexity-metrics">
                        <div class="complexity-metric">
                            <span class="metric-label">Problem Size:</span>
                            <span class="metric-value">${problemSize.toFixed(1)}</span>
                        </div>
                        <div class="complexity-metric">
                            <span class="metric-label">Solve Time:</span>
                            <span class="metric-value">${solveTime.toFixed(0)}ms</span>
                        </div>
                        <div class="complexity-metric">
                            <span class="metric-label">Work Score:</span>
                            <span class="metric-value">${workScore.toFixed(2)}</span>
                        </div>
                        <div class="complexity-metric">
                            <span class="metric-label">Gas Used:</span>
                            <span class="metric-value">${(tx.gas_used || 0).toLocaleString()}</span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        
        this.complexityDetailsList.innerHTML = complexityItems;
    }

    /**
     * Show error message
     */
    showError(message) {
        console.error('Metrics error:', message);
        // In a real implementation, this would show a user-friendly error message
    }

    /**
     * Activate metrics dashboard
     */
    activate() {
        this.isActive = true;
        this.initialize();
    }

    /**
     * Deactivate metrics dashboard
     */
    deactivate() {
        this.isActive = false;
        this.stopAutoRefresh();
        this.stopLiveFeed();
    }

    /**
     * Get current metrics data
     */
    getMetricsData() {
        return this.metricsData;
    }

    /**
     * Force refresh metrics
     */
    async forceRefresh() {
        await this.fetchAndUpdateMetrics();
    }
}

// Create and export singleton instance
export const metricsDashboard = new MetricsDashboard();

// Export for backward compatibility
export default metricsDashboard;
