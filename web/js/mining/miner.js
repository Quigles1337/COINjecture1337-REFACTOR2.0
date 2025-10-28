// COINjecture Web Interface - Mining Module
// Version: 3.15.0

import { api } from '../core/api.js';
import { subsetSumSolver } from './subset-sum.js';
import { MINING_CONFIG, SUCCESS_MESSAGES, ERROR_MESSAGES } from '../shared/constants.js';
import { validationUtils, numberUtils, dateUtils } from '../shared/utils.js';

/**
 * Mining module for COINjecture blockchain
 */
export class COINjectureMiner {
  constructor() {
    this.isMining = false;
    this.miningStats = {
      attempts: 0,
      successes: 0,
      totalWorkScore: 0,
      startTime: null,
      lastMineTime: null
    };
    this.currentProblem = null;
    this.wallet = null;
  }

  /**
   * Set wallet for mining
   */
  setWallet(wallet) {
    this.wallet = wallet;
  }

  /**
   * Start mining process
   */
  async startMining(options = {}) {
    if (this.isMining) {
      throw new Error('Mining is already in progress');
    }

    if (!this.wallet) {
      throw new Error('Wallet not set. Please set a wallet before mining.');
    }

    this.isMining = true;
    this.miningStats.startTime = Date.now();
    this.miningStats.attempts = 0;
    this.miningStats.successes = 0;
    this.miningStats.totalWorkScore = 0;

    try {
      // Generate initial problem
      this.currentProblem = subsetSumSolver.generateProblem();
      
      // Start mining loop
      await this.miningLoop(options);
      
    } catch (error) {
      this.isMining = false;
      throw error;
    }
  }

  /**
   * Stop mining process
   */
  stopMining() {
    this.isMining = false;
    this.miningStats.lastMineTime = Date.now();
  }

  /**
   * Main mining loop
   */
  async miningLoop(options = {}) {
    const maxAttempts = options.maxAttempts || MINING_CONFIG.MAX_ATTEMPTS;
    const onProgress = options.onProgress || (() => {});
    const onSuccess = options.onSuccess || (() => {});
    const onError = options.onError || (() => {});

    while (this.isMining && this.miningStats.attempts < maxAttempts) {
      try {
        // Generate new problem if needed
        if (!this.currentProblem) {
          this.currentProblem = subsetSumSolver.generateProblem();
        }

        // Solve the problem
        const solution = await subsetSumSolver.solve(this.currentProblem);
        this.miningStats.attempts++;

        // Update progress
        onProgress({
          attempt: this.miningStats.attempts,
          maxAttempts,
          problem: this.currentProblem,
          solution,
          stats: this.getMiningStats()
        });

        if (solution.success) {
          // Submit solution to blockchain
          const blockResult = await this.submitSolution(solution);
          
          if (blockResult.success) {
            this.miningStats.successes++;
            this.miningStats.totalWorkScore += solution.workScore;
            this.miningStats.lastMineTime = Date.now();
            
            onSuccess({
              solution,
              blockResult,
              stats: this.getMiningStats()
            });
            
            // Generate new problem for next attempt
            this.currentProblem = subsetSumSolver.generateProblem();
          }
        }

        // Small delay to prevent overwhelming the system
        await this.delay(100);

      } catch (error) {
        console.error('Mining loop error:', error);
        onError(error);
        
        // Continue mining unless it's a critical error
        if (error.message.includes('Wallet') || error.message.includes('Network')) {
          throw error;
        }
      }
    }

    this.isMining = false;
  }

  /**
   * Submit solution to blockchain
   */
  async submitSolution(solution) {
    if (!this.wallet) {
      throw new Error('Wallet not set');
    }

    if (!this.currentProblem) {
      throw new Error('No current problem');
    }

    // Create block data
    const blockData = {
      index: await this.getNextBlockIndex(),
      timestamp: Date.now(),
      previousHash: await this.getPreviousHash(),
      miner: this.wallet.address,
      problem: this.currentProblem,
      solution: solution,
      workScore: solution.workScore,
      nonce: this.generateNonce(),
      difficulty: await this.getCurrentDifficulty()
    };

    // Calculate block hash
    blockData.hash = await this.calculateBlockHash(blockData);

    try {
      // Submit to blockchain
      const result = await api.submitMiningBlock(blockData);
      
      return {
        success: true,
        block: blockData,
        result,
        timestamp: Date.now()
      };

    } catch (error) {
      console.error('Failed to submit mining block:', error);
      return {
        success: false,
        error: error.message,
        block: blockData,
        timestamp: Date.now()
      };
    }
  }

  /**
   * Get next block index
   */
  async getNextBlockIndex() {
    try {
      const metrics = await api.getMetricsDashboard();
      return (metrics.latestBlock || 0) + 1;
    } catch (error) {
      console.warn('Failed to get latest block index, using fallback');
      return Math.floor(Date.now() / 1000); // Fallback
    }
  }

  /**
   * Get previous block hash
   */
  async getPreviousHash() {
    try {
      const latestBlock = await api.getLatestBlock();
      return latestBlock.hash || '0'.repeat(64);
    } catch (error) {
      console.warn('Failed to get previous hash, using fallback');
      return '0'.repeat(64); // Fallback
    }
  }

  /**
   * Get current difficulty
   */
  async getCurrentDifficulty() {
    try {
      const metrics = await api.getMetricsDashboard();
      return metrics.difficulty || 1;
    } catch (error) {
      console.warn('Failed to get difficulty, using fallback');
      return 1; // Fallback
    }
  }

  /**
   * Generate nonce for block
   */
  generateNonce() {
    return Math.floor(Math.random() * 1000000);
  }

  /**
   * Calculate block hash
   */
  async calculateBlockHash(blockData) {
    const dataString = JSON.stringify({
      index: blockData.index,
      timestamp: blockData.timestamp,
      previousHash: blockData.previousHash,
      miner: blockData.miner,
      problem: blockData.problem,
      solution: blockData.solution,
      workScore: blockData.workScore,
      nonce: blockData.nonce,
      difficulty: blockData.difficulty
    });

    // Use Web Crypto API for hashing
    const encoder = new TextEncoder();
    const data = encoder.encode(dataString);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    
    return hashHex;
  }

  /**
   * Get mining statistics
   */
  getMiningStats() {
    const now = Date.now();
    const duration = this.miningStats.startTime ? 
      now - this.miningStats.startTime : 0;
    
    return {
      isMining: this.isMining,
      attempts: this.miningStats.attempts,
      successes: this.miningStats.successes,
      successRate: this.miningStats.attempts > 0 ? 
        (this.miningStats.successes / this.miningStats.attempts) * 100 : 0,
      totalWorkScore: this.miningStats.totalWorkScore,
      averageWorkScore: this.miningStats.successes > 0 ? 
        this.miningStats.totalWorkScore / this.miningStats.successes : 0,
      duration: duration,
      durationFormatted: dateUtils.formatDuration(duration),
      hashRate: this.calculateHashRate(),
      lastMineTime: this.miningStats.lastMineTime,
      currentProblem: this.currentProblem
    };
  }

  /**
   * Calculate hash rate (attempts per second)
   */
  calculateHashRate() {
    if (!this.miningStats.startTime) return 0;
    
    const duration = (Date.now() - this.miningStats.startTime) / 1000; // seconds
    return duration > 0 ? this.miningStats.attempts / duration : 0;
  }

  /**
   * Get mining efficiency metrics
   */
  getEfficiencyMetrics() {
    const stats = this.getMiningStats();
    
    return {
      hashRate: stats.hashRate,
      hashRateFormatted: numberUtils.formatHashRate(stats.hashRate),
      successRate: stats.successRate,
      successRateFormatted: numberUtils.formatPercentage(stats.successRate / 100),
      averageWorkScore: stats.averageWorkScore,
      totalWorkScore: stats.totalWorkScore,
      efficiency: this.calculateEfficiency(),
      device: subsetSumSolver.getStats().device
    };
  }

  /**
   * Calculate mining efficiency
   */
  calculateEfficiency() {
    const stats = this.getMiningStats();
    
    if (stats.attempts === 0) return 0;
    
    // Efficiency based on success rate and work score
    const successFactor = stats.successRate / 100;
    const workFactor = Math.min(stats.averageWorkScore / 100, 1);
    
    return (successFactor * 0.7 + workFactor * 0.3) * 100;
  }

  /**
   * Validate mining setup
   */
  validateMiningSetup() {
    const errors = [];
    
    if (!this.wallet) {
      errors.push('Wallet not set');
    } else if (!validationUtils.isValidAddress(this.wallet.address)) {
      errors.push('Invalid wallet address');
    }
    
    if (!subsetSumSolver) {
      errors.push('Subset sum solver not available');
    }
    
    return {
      isValid: errors.length === 0,
      errors
    };
  }

  /**
   * Reset mining statistics
   */
  resetStats() {
    this.miningStats = {
      attempts: 0,
      successes: 0,
      totalWorkScore: 0,
      startTime: null,
      lastMineTime: null
    };
  }

  /**
   * Delay utility
   */
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Get current problem
   */
  getCurrentProblem() {
    return this.currentProblem;
  }

  /**
   * Generate new problem
   */
  generateNewProblem() {
    this.currentProblem = subsetSumSolver.generateProblem();
    return this.currentProblem;
  }

  /**
   * Test mining setup
   */
  async testMiningSetup() {
    try {
      // Validate setup
      const validation = this.validateMiningSetup();
      if (!validation.isValid) {
        throw new Error(`Mining setup invalid: ${validation.errors.join(', ')}`);
      }

      // Test problem generation
      const problem = subsetSumSolver.generateProblem();
      if (!problem || !problem.numbers || !problem.target) {
        throw new Error('Problem generation failed');
      }

      // Test problem solving
      const solution = await subsetSumSolver.solve(problem);
      if (!solution) {
        throw new Error('Problem solving failed');
      }

      // Test API connection
      await api.healthCheck();

      return {
        success: true,
        message: 'Mining setup test passed',
        problem,
        solution,
        timestamp: Date.now()
      };

    } catch (error) {
      return {
        success: false,
        message: error.message,
        timestamp: Date.now()
      };
    }
  }
}

// Create and export singleton instance
export const miner = new COINjectureMiner();

// Export for backward compatibility
export default miner;
