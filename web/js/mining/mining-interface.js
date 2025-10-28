// COINjecture Web Interface - Mining Interface Controller
// Version: 3.15.0

import { miner } from './miner.js';
import { subsetSumSolver } from './subset-sum.js';
import { miningValidator } from './validation.js';
import { api } from '../core/api.js';
import { deviceUtils, numberUtils, dateUtils, domUtils, storageUtils, clipboardUtils } from '../shared/utils.js';
import { SUCCESS_MESSAGES, ERROR_MESSAGES } from '../shared/constants.js';

/**
 * Mining Interface Controller
 */
class MiningInterface {
    constructor() {
        this.wallet = null;
        this.isInitialized = false;
        this.logEntries = [];
        this.maxLogEntries = 100;
        
        this.initializeElements();
        this.attachEventListeners();
        this.initializeInterface();
    }

    /**
     * Initialize DOM elements
     */
    initializeElements() {
        // Wallet elements
        this.createWalletBtn = document.getElementById('create-wallet-btn');
        this.loadWalletBtn = document.getElementById('load-wallet-btn');
        this.walletInfo = document.getElementById('wallet-info');
        this.walletAddress = document.getElementById('wallet-address');
        this.walletBalance = document.getElementById('wallet-balance');
        this.copyAddressBtn = document.getElementById('copy-address-btn');

        // Mining control elements
        this.maxAttemptsInput = document.getElementById('max-attempts');
        this.autoMiningCheckbox = document.getElementById('auto-mining');
        this.startMiningBtn = document.getElementById('start-mining-btn');
        this.stopMiningBtn = document.getElementById('stop-mining-btn');
        this.testMiningBtn = document.getElementById('test-mining-btn');

        // Problem elements
        this.problemDisplay = document.getElementById('problem-display');
        this.generateProblemBtn = document.getElementById('generate-problem-btn');
        this.solveProblemBtn = document.getElementById('solve-problem-btn');

        // Statistics elements
        this.miningStatus = document.getElementById('mining-status');
        this.miningAttempts = document.getElementById('mining-attempts');
        this.miningSuccesses = document.getElementById('mining-successes');
        this.miningSuccessRate = document.getElementById('mining-success-rate');
        this.miningHashRate = document.getElementById('mining-hash-rate');
        this.miningWorkScore = document.getElementById('mining-work-score');
        this.miningDuration = document.getElementById('mining-duration');
        this.miningDevice = document.getElementById('mining-device');

        // Log elements
        this.miningLog = document.getElementById('mining-log');
        this.clearLogBtn = document.getElementById('clear-log-btn');
        this.exportLogBtn = document.getElementById('export-log-btn');
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        // Wallet events
        this.createWalletBtn.addEventListener('click', () => this.createWallet());
        this.loadWalletBtn.addEventListener('click', () => this.loadWallet());
        this.copyAddressBtn.addEventListener('click', () => this.copyWalletAddress());

        // Mining control events
        this.startMiningBtn.addEventListener('click', () => this.startMining());
        this.stopMiningBtn.addEventListener('click', () => this.stopMining());
        this.testMiningBtn.addEventListener('click', () => this.testMiningSetup());

        // Problem events
        this.generateProblemBtn.addEventListener('click', () => this.generateNewProblem());
        this.solveProblemBtn.addEventListener('click', () => this.solveCurrentProblem());

        // Log events
        this.clearLogBtn.addEventListener('click', () => this.clearLog());
        this.exportLogBtn.addEventListener('click', () => this.exportLog());

        // Auto-save settings
        this.maxAttemptsInput.addEventListener('change', () => this.saveSettings());
        this.autoMiningCheckbox.addEventListener('change', () => this.saveSettings());
    }

    /**
     * Initialize the interface
     */
    async initializeInterface() {
        try {
            this.addLogEntry('info', 'Initializing mining interface...');
            
            // Load saved settings
            this.loadSettings();
            
            // Load saved wallet
            await this.loadSavedWallet();
            
            // Update device information
            this.updateDeviceInfo();
            
            // Initialize miner
            if (this.wallet) {
                miner.setWallet(this.wallet);
            }
            
            this.isInitialized = true;
            this.addLogEntry('success', 'Mining interface initialized successfully');
            
        } catch (error) {
            console.error('Failed to initialize mining interface:', error);
            this.addLogEntry('error', `Initialization failed: ${error.message}`);
        }
    }

    /**
     * Create a new wallet
     */
    async createWallet() {
        try {
            this.addLogEntry('info', 'Creating new wallet...');
            
            // Check if Ed25519 library is available
            if (!window.nobleEd25519 && window.ed25519Fallback !== 'webcrypto') {
                throw new Error('Ed25519 library not available');
            }

            // Generate wallet
            const wallet = await this.generateWallet();
            
            // Save wallet
            storageUtils.save('mining_wallet', wallet);
            
            // Set wallet
            this.setWallet(wallet);
            
            this.addLogEntry('success', 'New wallet created successfully');
            
        } catch (error) {
            console.error('Failed to create wallet:', error);
            this.addLogEntry('error', `Wallet creation failed: ${error.message}`);
        }
    }

    /**
     * Load existing wallet
     */
    async loadWallet() {
        try {
            const walletData = prompt('Enter wallet private key or address:');
            if (!walletData) return;

            // Try to parse as JSON first (full wallet data)
            let wallet;
            try {
                wallet = JSON.parse(walletData);
            } catch {
                // If not JSON, treat as private key
                wallet = await this.importWalletFromPrivateKey(walletData);
            }

            // Save wallet
            storageUtils.save('mining_wallet', wallet);
            
            // Set wallet
            this.setWallet(wallet);
            
            this.addLogEntry('success', 'Wallet loaded successfully');
            
        } catch (error) {
            console.error('Failed to load wallet:', error);
            this.addLogEntry('error', `Wallet loading failed: ${error.message}`);
        }
    }

    /**
     * Load saved wallet from storage
     */
    async loadSavedWallet() {
        try {
            const savedWallet = storageUtils.load('mining_wallet');
            if (savedWallet) {
                this.setWallet(savedWallet);
                this.addLogEntry('info', 'Saved wallet loaded');
            }
        } catch (error) {
            console.error('Failed to load saved wallet:', error);
        }
    }

    /**
     * Generate a new wallet
     */
    async generateWallet() {
        if (window.nobleEd25519) {
            // Use Noble Ed25519 library
            const privateKey = window.nobleEd25519.utils.randomPrivateKey();
            const publicKey = window.nobleEd25519.getPublicKey(privateKey);
            const address = this.publicKeyToAddress(publicKey);
            
            return {
                privateKey: Array.from(privateKey).map(b => b.toString(16).padStart(2, '0')).join(''),
                publicKey: Array.from(publicKey).map(b => b.toString(16).padStart(2, '0')).join(''),
                address: address,
                created: Date.now()
            };
        } else if (window.crypto && window.crypto.subtle) {
            // Use Web Crypto API fallback
            const keyPair = await window.crypto.subtle.generateKey(
                {
                    name: 'Ed25519',
                    namedCurve: 'Ed25519'
                },
                true,
                ['sign', 'verify']
            );
            
            const publicKeyBuffer = await window.crypto.subtle.exportKey('raw', keyPair.publicKey);
            const address = this.publicKeyToAddress(new Uint8Array(publicKeyBuffer));
            
            return {
                publicKey: Array.from(new Uint8Array(publicKeyBuffer)).map(b => b.toString(16).padStart(2, '0')).join(''),
                address: address,
                created: Date.now(),
                type: 'webcrypto'
            };
        } else {
            // Demo wallet fallback
            const demoAddress = 'demo_' + Math.random().toString(36).substring(2, 15);
            return {
                address: demoAddress,
                created: Date.now(),
                type: 'demo'
            };
        }
    }

    /**
     * Import wallet from private key
     */
    async importWalletFromPrivateKey(privateKeyHex) {
        if (window.nobleEd25519) {
            const privateKey = new Uint8Array(privateKeyHex.match(/.{1,2}/g).map(byte => parseInt(byte, 16)));
            const publicKey = window.nobleEd25519.getPublicKey(privateKey);
            const address = this.publicKeyToAddress(publicKey);
            
            return {
                privateKey: privateKeyHex,
                publicKey: Array.from(publicKey).map(b => b.toString(16).padStart(2, '0')).join(''),
                address: address,
                imported: Date.now()
            };
        } else {
            throw new Error('Ed25519 library not available for import');
        }
    }

    /**
     * Convert public key to address
     */
    publicKeyToAddress(publicKey) {
        // Simple hash-based address generation
        const hash = Array.from(publicKey).reduce((acc, byte) => acc + byte, 0);
        return 'addr_' + hash.toString(16).padStart(8, '0') + '_' + Date.now().toString(36);
    }

    /**
     * Set wallet and update UI
     */
    setWallet(wallet) {
        this.wallet = wallet;
        miner.setWallet(wallet);
        
        // Update UI
        this.walletAddress.textContent = wallet.address;
        this.walletInfo.style.display = 'block';
        this.startMiningBtn.disabled = false;
        this.testMiningBtn.disabled = false;
        
        // Load wallet balance
        this.loadWalletBalance();
        
        this.addLogEntry('info', `Wallet set: ${wallet.address.substring(0, 20)}...`);
    }

    /**
     * Load wallet balance
     */
    async loadWalletBalance() {
        if (!this.wallet) return;
        
        try {
            const rewards = await api.getUserRewards(this.wallet.address);
            this.walletBalance.textContent = `${rewards.totalRewards || 0} BEANS`;
        } catch (error) {
            console.error('Failed to load wallet balance:', error);
            this.walletBalance.textContent = 'Error loading balance';
        }
    }

    /**
     * Copy wallet address to clipboard
     */
    async copyWalletAddress() {
        if (!this.wallet) return;
        
        const success = await clipboardUtils.copyToClipboard(this.wallet.address);
        if (success) {
            this.addLogEntry('success', 'Wallet address copied to clipboard');
        } else {
            this.addLogEntry('error', 'Failed to copy wallet address');
        }
    }

    /**
     * Start mining
     */
    async startMining() {
        if (!this.wallet) {
            this.addLogEntry('error', 'No wallet set. Please create or load a wallet first.');
            return;
        }

        try {
            this.addLogEntry('info', 'Starting mining...');
            
            const maxAttempts = parseInt(this.maxAttemptsInput.value) || 100;
            
            // Update UI
            this.startMiningBtn.disabled = true;
            this.stopMiningBtn.disabled = false;
            this.miningStatus.textContent = 'Mining';
            this.miningStatus.className = 'stat-value mining';
            
            // Start mining with callbacks
            await miner.startMining({
                maxAttempts: maxAttempts,
                onProgress: (data) => this.handleMiningProgress(data),
                onSuccess: (data) => this.handleMiningSuccess(data),
                onError: (error) => this.handleMiningError(error)
            });
            
        } catch (error) {
            console.error('Failed to start mining:', error);
            this.addLogEntry('error', `Mining start failed: ${error.message}`);
            this.stopMining();
        }
    }

    /**
     * Stop mining
     */
    stopMining() {
        miner.stopMining();
        
        // Update UI
        this.startMiningBtn.disabled = false;
        this.stopMiningBtn.disabled = true;
        this.miningStatus.textContent = 'Stopped';
        this.miningStatus.className = 'stat-value stopped';
        
        this.addLogEntry('info', 'Mining stopped');
    }

    /**
     * Handle mining progress
     */
    handleMiningProgress(data) {
        this.updateMiningStats(data.stats);
        
        if (data.attempt % 10 === 0) { // Log every 10th attempt
            this.addLogEntry('info', `Mining attempt ${data.attempt}/${data.maxAttempts}`);
        }
    }

    /**
     * Handle mining success
     */
    handleMiningSuccess(data) {
        this.addLogEntry('success', `Block mined! Work score: ${data.solution.workScore}`);
        this.updateMiningStats(data.stats);
        this.loadWalletBalance(); // Refresh balance
    }

    /**
     * Handle mining error
     */
    handleMiningError(error) {
        this.addLogEntry('error', `Mining error: ${error.message}`);
    }

    /**
     * Test mining setup
     */
    async testMiningSetup() {
        try {
            this.addLogEntry('info', 'Testing mining setup...');
            
            const testResult = await miner.testMiningSetup();
            
            if (testResult.success) {
                this.addLogEntry('success', 'Mining setup test passed');
                this.addLogEntry('info', `Problem: ${testResult.problem.numbers.length} numbers, target: ${testResult.problem.target}`);
                this.addLogEntry('info', `Solution: ${testResult.solution.method}, time: ${testResult.solution.solveTime}ms`);
            } else {
                this.addLogEntry('error', `Mining setup test failed: ${testResult.message}`);
            }
            
        } catch (error) {
            console.error('Mining setup test failed:', error);
            this.addLogEntry('error', `Test failed: ${error.message}`);
        }
    }

    /**
     * Generate new problem
     */
    generateNewProblem() {
        try {
            const problem = subsetSumSolver.generateProblem();
            this.displayProblem(problem);
            this.solveProblemBtn.disabled = false;
            this.addLogEntry('info', `New problem generated: ${problem.numbers.length} numbers, target: ${problem.target}`);
        } catch (error) {
            console.error('Failed to generate problem:', error);
            this.addLogEntry('error', `Problem generation failed: ${error.message}`);
        }
    }

    /**
     * Solve current problem
     */
    async solveCurrentProblem() {
        if (!this.currentProblem) {
            this.addLogEntry('error', 'No current problem to solve');
            return;
        }

        try {
            this.addLogEntry('info', 'Solving problem...');
            this.solveProblemBtn.disabled = true;
            
            const solution = await subsetSumSolver.solve(this.currentProblem);
            
            if (solution.success) {
                this.addLogEntry('success', `Problem solved! Method: ${solution.method}, time: ${solution.solveTime}ms, work score: ${solution.workScore}`);
                this.displaySolution(solution);
            } else {
                this.addLogEntry('error', `Problem solving failed: ${solution.error}`);
            }
            
            this.solveProblemBtn.disabled = false;
            
        } catch (error) {
            console.error('Failed to solve problem:', error);
            this.addLogEntry('error', `Problem solving failed: ${error.message}`);
            this.solveProblemBtn.disabled = false;
        }
    }

    /**
     * Display problem
     */
    displayProblem(problem) {
        this.currentProblem = problem;
        
        const problemHtml = `
            <div class="problem-info">
                <div class="problem-meta">
                    <span class="problem-size">Size: ${problem.numbers.length}</span>
                    <span class="problem-target">Target: ${problem.target}</span>
                    <span class="problem-device">Device: ${problem.device}</span>
                </div>
                <div class="problem-numbers">
                    <strong>Numbers:</strong> [${problem.numbers.join(', ')}]
                </div>
            </div>
        `;
        
        this.problemDisplay.innerHTML = problemHtml;
    }

    /**
     * Display solution
     */
    displaySolution(solution) {
        const solutionHtml = `
            <div class="solution-info">
                <div class="solution-meta">
                    <span class="solution-method">Method: ${solution.method}</span>
                    <span class="solution-time">Time: ${solution.solveTime}ms</span>
                    <span class="solution-work-score">Work Score: ${solution.workScore}</span>
                </div>
                <div class="solution-details">
                    <div class="solution-indices">
                        <strong>Indices:</strong> [${solution.solution.indices.join(', ')}]
                    </div>
                    <div class="solution-numbers">
                        <strong>Numbers:</strong> [${solution.solution.numbers.join(', ')}]
                    </div>
                    <div class="solution-sum">
                        <strong>Sum:</strong> ${solution.solution.sum}
                    </div>
                </div>
            </div>
        `;
        
        this.problemDisplay.innerHTML += solutionHtml;
    }

    /**
     * Update mining statistics
     */
    updateMiningStats(stats) {
        this.miningAttempts.textContent = stats.attempts;
        this.miningSuccesses.textContent = stats.successes;
        this.miningSuccessRate.textContent = `${stats.successRate.toFixed(1)}%`;
        this.miningHashRate.textContent = numberUtils.formatHashRate(stats.hashRate);
        this.miningWorkScore.textContent = stats.totalWorkScore;
        this.miningDuration.textContent = stats.durationFormatted;
    }

    /**
     * Update device information
     */
    updateDeviceInfo() {
        const deviceType = deviceUtils.getDeviceType();
        this.miningDevice.textContent = deviceType.charAt(0).toUpperCase() + deviceType.slice(1);
    }

    /**
     * Add log entry
     */
    addLogEntry(type, message) {
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = {
            timestamp,
            type,
            message,
            time: Date.now()
        };
        
        this.logEntries.push(logEntry);
        
        // Limit log entries
        if (this.logEntries.length > this.maxLogEntries) {
            this.logEntries.shift();
        }
        
        this.updateLogDisplay();
    }

    /**
     * Update log display
     */
    updateLogDisplay() {
        const logHtml = this.logEntries.map(entry => `
            <div class="log-entry ${entry.type}">
                <span class="log-time">[${entry.timestamp}]</span>
                <span class="log-message">${entry.message}</span>
            </div>
        `).join('');
        
        this.miningLog.innerHTML = logHtml;
        this.miningLog.scrollTop = this.miningLog.scrollHeight;
    }

    /**
     * Clear log
     */
    clearLog() {
        this.logEntries = [];
        this.miningLog.innerHTML = '<div class="log-entry info"><span class="log-time">[00:00:00]</span><span class="log-message">Log cleared.</span></div>';
    }

    /**
     * Export log
     */
    exportLog() {
        const logText = this.logEntries.map(entry => 
            `[${entry.timestamp}] ${entry.type.toUpperCase()}: ${entry.message}`
        ).join('\n');
        
        const blob = new Blob([logText], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `mining-log-${new Date().toISOString().split('T')[0]}.txt`;
        a.click();
        URL.revokeObjectURL(url);
        
        this.addLogEntry('info', 'Log exported');
    }

    /**
     * Save settings
     */
    saveSettings() {
        const settings = {
            maxAttempts: parseInt(this.maxAttemptsInput.value),
            autoMining: this.autoMiningCheckbox.checked
        };
        
        storageUtils.save('mining_settings', settings);
    }

    /**
     * Load settings
     */
    loadSettings() {
        const settings = storageUtils.load('mining_settings', {
            maxAttempts: 100,
            autoMining: true
        });
        
        this.maxAttemptsInput.value = settings.maxAttempts;
        this.autoMiningCheckbox.checked = settings.autoMining;
    }
}

// Initialize the mining interface when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new MiningInterface();
});
