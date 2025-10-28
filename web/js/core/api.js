// COINjecture Web Interface - Core API Module
// Version: 3.15.0

import { API_CONFIG, API_ENDPOINTS, CACHE_CONFIG, ERROR_MESSAGES } from '../shared/constants.js';
import { urlUtils } from '../shared/utils.js';

/**
 * Core API class for handling all API communications
 */
export class COINjectureAPI {
  constructor() {
    this.apiBase = API_CONFIG.BASE_URL;
    this.fallbackBase = API_CONFIG.FALLBACK_URL;
    this.timeout = API_CONFIG.TIMEOUT;
    this.retryAttempts = API_CONFIG.RETRY_ATTEMPTS;
  }

  /**
   * Enhanced fetch with fallback, retry, and error handling
   */
  async fetchWithFallback(endpoint, options = {}) {
    // For HTTPS pages, only use the main API to avoid mixed content errors
    const urls = window.location.protocol === 'https:' 
      ? [`${this.apiBase}${endpoint}`]
      : [`${this.apiBase}${endpoint}`, `${this.fallbackBase}${endpoint}`];

    let lastError = null;

    for (let attempt = 0; attempt < this.retryAttempts; attempt++) {
      for (const url of urls) {
        try {
          const response = await this.fetchWithTimeout(url, options);
          
          if (response.ok) {
            return response;
          }
          
          // Try to get the error message from response body
          let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
          try {
            const errorData = await response.json();
            if (errorData.message) {
              errorMessage = errorData.message;
            }
          } catch (e) {
            // If we can't parse JSON, use the status text
          }
          
          // If response is not ok, try next URL
          lastError = new Error(errorMessage);
        } catch (error) {
          lastError = error;
          console.warn(`API request failed for ${url}:`, error.message);
        }
      }
      
      // Wait before retry
      if (attempt < this.retryAttempts - 1) {
        await this.delay(1000 * (attempt + 1));
      }
    }

    throw new Error(`All API endpoints failed. Last error: ${lastError?.message || 'Unknown error'}`);
  }

  /**
   * Fetch with timeout
   */
  async fetchWithTimeout(url, options = {}) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(urlUtils.addCacheBuster(url), {
        ...options,
        signal: controller.signal,
        cache: 'no-cache',
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0',
          ...options.headers
        }
      });

      clearTimeout(timeoutId);
      return response;
    } catch (error) {
      clearTimeout(timeoutId);
      throw error;
    }
  }

  /**
   * Delay utility
   */
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Get metrics dashboard data
   */
  async getMetricsDashboard() {
    try {
      const response = await this.fetchWithFallback(API_ENDPOINTS.METRICS_DASHBOARD);
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch metrics dashboard:', error);
      throw new Error(ERROR_MESSAGES.API_ERROR);
    }
  }

  /**
   * Get latest block data
   */
  async getLatestBlock() {
    try {
      const response = await this.fetchWithFallback(API_ENDPOINTS.BLOCK_LATEST);
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch latest block:', error);
      throw new Error(ERROR_MESSAGES.API_ERROR);
    }
  }

  /**
   * Get block by index
   */
  async getBlockByIndex(index) {
    try {
      const response = await this.fetchWithFallback(API_ENDPOINTS.BLOCK_BY_INDEX(index));
      return await response.json();
    } catch (error) {
      console.error(`Failed to fetch block ${index}:`, error);
      throw new Error(ERROR_MESSAGES.API_ERROR);
    }
  }

  /**
   * Submit mining block
   */
  async submitMiningBlock(blockData) {
    try {
      const response = await this.fetchWithFallback(API_ENDPOINTS.INGEST_BLOCK, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(blockData)
      });
      return await response.json();
    } catch (error) {
      console.error('Failed to submit mining block:', error);
      throw new Error(ERROR_MESSAGES.MINING_ERROR);
    }
  }

  /**
   * Get user rewards
   */
  async getUserRewards(address) {
    try {
      const response = await this.fetchWithFallback(API_ENDPOINTS.REWARDS_USER(address));
      return await response.json();
    } catch (error) {
      console.error(`Failed to fetch rewards for ${address}:`, error);
      throw new Error(ERROR_MESSAGES.API_ERROR);
    }
  }

  /**
   * Get rewards leaderboard
   */
  async getRewardsLeaderboard() {
    try {
      const response = await this.fetchWithFallback(API_ENDPOINTS.REWARDS_LEADERBOARD);
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch rewards leaderboard:', error);
      throw new Error(ERROR_MESSAGES.API_ERROR);
    }
  }

  /**
   * Register wallet
   */
  async registerWallet(walletData) {
    try {
      const response = await this.fetchWithFallback(API_ENDPOINTS.WALLET_REGISTER, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(walletData)
      });
      return await response.json();
    } catch (error) {
      console.error('Failed to register wallet:', error);
      throw new Error(ERROR_MESSAGES.WALLET_ERROR);
    }
  }

  /**
   * Get wallet balance
   */
  async getWalletBalance(address) {
    try {
      const response = await this.fetchWithFallback(API_ENDPOINTS.WALLET_BALANCE(address));
      return await response.json();
    } catch (error) {
      console.error(`Failed to fetch balance for ${address}:`, error);
      throw new Error(ERROR_MESSAGES.WALLET_ERROR);
    }
  }

  /**
   * Get wallet transactions
   */
  async getWalletTransactions(address) {
    try {
      const response = await this.fetchWithFallback(API_ENDPOINTS.WALLET_TRANSACTIONS(address));
      return await response.json();
    } catch (error) {
      console.error(`Failed to fetch transactions for ${address}:`, error);
      throw new Error(ERROR_MESSAGES.WALLET_ERROR);
    }
  }

  /**
   * Get IPFS user data
   */
  async getIPFSUserData(address) {
    try {
      const response = await this.fetchWithFallback(API_ENDPOINTS.IPFS_USER(address));
      return await response.json();
    } catch (error) {
      console.error(`Failed to fetch IPFS data for ${address}:`, error);
      throw new Error(ERROR_MESSAGES.API_ERROR);
    }
  }

  /**
   * Get IPFS statistics
   */
  async getIPFSStats(address) {
    try {
      const response = await this.fetchWithFallback(API_ENDPOINTS.IPFS_STATS(address));
      return await response.json();
    } catch (error) {
      console.error(`Failed to fetch IPFS stats for ${address}:`, error);
      throw new Error(ERROR_MESSAGES.API_ERROR);
    }
  }

  /**
   * Download IPFS data
   */
  downloadIPFSData(address, format = 'json') {
    const downloadUrl = `${this.apiBase}${API_ENDPOINTS.IPFS_DOWNLOAD(address)}?format=${format}`;
    window.open(downloadUrl, '_blank');
  }

  /**
   * Submit problem
   */
  async submitProblem(problemData) {
    try {
      const response = await this.fetchWithFallback(API_ENDPOINTS.PROBLEM_SUBMIT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(problemData)
      });
      return await response.json();
    } catch (error) {
      console.error('Failed to submit problem:', error);
      throw new Error(ERROR_MESSAGES.API_ERROR);
    }
  }

  /**
   * Get problem list
   */
  async getProblemList() {
    try {
      const response = await this.fetchWithFallback(API_ENDPOINTS.PROBLEM_LIST);
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch problem list:', error);
      throw new Error(ERROR_MESSAGES.API_ERROR);
    }
  }

  /**
   * Get problem status
   */
  async getProblemStatus(submissionId) {
    try {
      const response = await this.fetchWithFallback(API_ENDPOINTS.PROBLEM_STATUS(submissionId));
      return await response.json();
    } catch (error) {
      console.error(`Failed to fetch problem status for ${submissionId}:`, error);
      throw new Error(ERROR_MESSAGES.API_ERROR);
    }
  }

  /**
   * Register user
   */
  async registerUser(userData) {
    try {
      const response = await this.fetchWithFallback(API_ENDPOINTS.USER_REGISTER, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(userData)
      });
      return await response.json();
    } catch (error) {
      console.error('Failed to register user:', error);
      throw new Error(ERROR_MESSAGES.API_ERROR);
    }
  }

  /**
   * Get user profile
   */
  async getUserProfile(address) {
    try {
      const response = await this.fetchWithFallback(API_ENDPOINTS.USER_PROFILE(address));
      return await response.json();
    } catch (error) {
      console.error(`Failed to fetch user profile for ${address}:`, error);
      throw new Error(ERROR_MESSAGES.API_ERROR);
    }
  }

  /**
   * Send transaction
   */
  async sendTransaction(transactionData) {
    try {
      const response = await this.fetchWithFallback(API_ENDPOINTS.TRANSACTION_SEND, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(transactionData)
      });
      return await response.json();
    } catch (error) {
      console.error('Failed to send transaction:', error);
      throw new Error(ERROR_MESSAGES.API_ERROR);
    }
  }

  /**
   * Get telemetry data
   */
  async getTelemetryData() {
    try {
      const response = await this.fetchWithFallback(API_ENDPOINTS.TELEMETRY_LATEST);
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch telemetry data:', error);
      throw new Error(ERROR_MESSAGES.API_ERROR);
    }
  }

  /**
   * Get IPFS content
   */
  async getIPFSContent(cid) {
    try {
      const response = await this.fetchWithFallback(API_ENDPOINTS.IPFS_CONTENT(cid));
      return await response.json();
    } catch (error) {
      console.error(`Failed to fetch IPFS content for ${cid}:`, error);
      throw new Error(ERROR_MESSAGES.API_ERROR);
    }
  }

  /**
   * Get block proof
   */
  async getBlockProof(cid) {
    try {
      const response = await this.fetchWithFallback(API_ENDPOINTS.BLOCK_PROOF(cid));
      return await response.json();
    } catch (error) {
      console.error(`Failed to fetch block proof for ${cid}:`, error);
      throw new Error(ERROR_MESSAGES.API_ERROR);
    }
  }

  /**
   * Get proof data (alias for getBlockProof)
   */
  async getProofData(cid) {
    return this.getBlockProof(cid);
  }

  /**
   * Get user rewards
   */
  async getUserRewards(address) {
    try {
      const response = await this.fetchWithFallback(API_ENDPOINTS.REWARDS_USER(address));
      return await response.json();
    } catch (error) {
      console.error(`Failed to fetch user rewards for ${address}:`, error);
      throw new Error(ERROR_MESSAGES.API_ERROR);
    }
  }

  /**
   * Health check
   */
  async healthCheck() {
    try {
      const response = await this.fetchWithFallback(API_ENDPOINTS.HEALTH);
      return await response.json();
    } catch (error) {
      console.error('Health check failed:', error);
      throw new Error(ERROR_MESSAGES.API_ERROR);
    }
  }

  /**
   * Submit mined block to blockchain
   */
    async submitMinedBlock(blockData) {
      try {
        // Use the existing ingest/block endpoint
        const response = await this.fetchWithFallback('/v1/ingest/block', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(blockData)
        });
        return await response.json();
      } catch (error) {
        console.error('Error submitting mined block:', error);
        return {
          success: false,
          error: error.message
        };
      }
    }
}

// Create and export singleton instance
export const api = new COINjectureAPI();

// Export for backward compatibility
export default api;
