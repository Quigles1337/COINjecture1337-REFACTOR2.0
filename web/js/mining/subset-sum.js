// COINjecture Web Interface - Mobile-Optimized Subset Sum Solver
// Version: 3.15.0

import { MINING_CONFIG } from '../shared/constants.js';
import { deviceUtils, numberUtils } from '../shared/utils.js';

/**
 * Mobile-optimized subset sum solver with adaptive problem sizing
 */
export class SubsetSumSolver {
  constructor() {
    this.isMobile = deviceUtils.isMobile();
    this.maxProblemSize = this.isMobile ? 
      MINING_CONFIG.MOBILE_MAX_PROBLEM_SIZE : 
      MINING_CONFIG.DESKTOP_MAX_PROBLEM_SIZE;
    this.maxSolveTime = this.isMobile ? 
      MINING_CONFIG.MOBILE_MAX_SOLVE_TIME : 
      MINING_CONFIG.DESKTOP_MAX_SOLVE_TIME;
  }

  /**
   * Generate a subset sum problem
   */
  generateProblem(size = null) {
    const problemSize = size || this.getOptimalProblemSize();
    const numbers = this.generateNumbers(problemSize);
    const target = this.generateTarget(numbers);
    
    return {
      numbers,
      target,
      size: problemSize,
      timestamp: Date.now(),
      device: deviceUtils.getDeviceType()
    };
  }

  /**
   * Get optimal problem size based on device
   */
  getOptimalProblemSize() {
    if (this.isMobile) {
      // Mobile: 10-15 items for fast solving
      return Math.floor(Math.random() * 6) + 10;
    } else {
      // Desktop: 15-25 items for more complex problems
      return Math.floor(Math.random() * 11) + 15;
    }
  }

  /**
   * Generate random numbers for the problem
   */
  generateNumbers(size) {
    const numbers = [];
    const maxValue = this.isMobile ? 50 : 100; // Much smaller numbers for solvability
    
    for (let i = 0; i < size; i++) {
      numbers.push(Math.floor(Math.random() * maxValue) + 1);
    }
    
    return numbers;
  }

  /**
   * Generate a target sum that has a solution
   */
  generateTarget(numbers) {
    // Select a subset of numbers to ensure there's a solution
    const subsetSize = Math.floor(numbers.length / 2) + 1;
    const subset = this.selectRandomSubset(numbers, subsetSize);
    return subset.reduce((sum, num) => sum + num, 0);
  }

  /**
   * Select a random subset of numbers
   */
  selectRandomSubset(numbers, size) {
    const shuffled = [...numbers].sort(() => Math.random() - 0.5);
    return shuffled.slice(0, size);
  }

  /**
   * Solve subset sum problem with multiple strategies
   */
  async solve(problem) {
    const startTime = Date.now();
    const timeout = this.maxSolveTime;
    
    try {
      // Try dynamic programming first (most efficient)
      let solution = await this.solveWithDP(problem, startTime, timeout);
      
      if (solution) {
        return this.createSolutionResult(solution, startTime, 'dp');
      }
      
      // Fallback to greedy approach
      solution = await this.solveWithGreedy(problem, startTime, timeout);
      
      if (solution) {
        return this.createSolutionResult(solution, startTime, 'greedy');
      }
      
      // Final fallback to backtracking
      solution = await this.solveWithBacktracking(problem, startTime, timeout);
      
      if (solution) {
        return this.createSolutionResult(solution, startTime, 'backtracking');
      }
      
      return this.createNoSolutionResult(startTime);
      
    } catch (error) {
      console.error('Subset sum solving error:', error);
      return this.createErrorResult(error, startTime);
    }
  }

  /**
   * Solve using dynamic programming (most efficient)
   */
  async solveWithDP(problem, startTime, timeout) {
    const { numbers, target } = problem;
    const n = numbers.length;
    
    // Use 2D DP array to track which numbers are used
    const dp = Array(n + 1).fill().map(() => Array(target + 1).fill(false));
    const parent = Array(n + 1).fill().map(() => Array(target + 1).fill(-1));
    
    // Base case: sum 0 can always be achieved with empty set
    for (let i = 0; i <= n; i++) {
      dp[i][0] = true;
    }
    
    for (let i = 1; i <= n; i++) {
      // Check timeout
      if (Date.now() - startTime > timeout) {
        throw new Error('Timeout');
      }
      
      const num = numbers[i - 1];
      
      for (let j = 0; j <= target; j++) {
        // Don't use current number
        if (dp[i - 1][j]) {
          dp[i][j] = true;
          parent[i][j] = parent[i - 1][j];
        }
        
        // Use current number
        if (j >= num && dp[i - 1][j - num]) {
          dp[i][j] = true;
          parent[i][j] = i - 1; // Store the index of the number used
        }
      }
      
      // If we found the target, break early
      if (dp[i][target]) {
        break;
      }
    }
    
    if (!dp[n][target]) {
      return null;
    }
    
    // Reconstruct solution by backtracking
    const solution = [];
    let i = n;
    let j = target;
    
    while (i > 0 && j > 0) {
      if (parent[i][j] === i - 1) {
        // This number was used
        solution.push(i - 1);
        j -= numbers[i - 1];
      }
      i--;
    }
    
    return {
      indices: solution,
      numbers: solution.map(i => numbers[i]),
      sum: target,
      method: 'dp'
    };
  }

  /**
   * Solve using greedy approach (fast but not optimal)
   */
  async solveWithGreedy(problem, startTime, timeout) {
    const { numbers, target } = problem;
    const solution = [];
    let currentSum = 0;
    
    // Sort numbers in descending order for greedy approach
    const sortedIndices = numbers
      .map((num, index) => ({ num, index }))
      .sort((a, b) => b.num - a.num);
    
    for (const { num, index } of sortedIndices) {
      // Check timeout
      if (Date.now() - startTime > timeout) {
        throw new Error('Timeout');
      }
      
      if (currentSum + num <= target) {
        solution.push(index);
        currentSum += num;
        
        if (currentSum === target) {
          return {
            indices: solution,
            numbers: solution.map(i => numbers[i]),
            sum: currentSum,
            method: 'greedy'
          };
        }
      }
    }
    
    return null;
  }

  /**
   * Solve using backtracking (guaranteed to find solution if exists)
   */
  async solveWithBacktracking(problem, startTime, timeout) {
    const { numbers, target } = problem;
    const solution = [];
    
    const backtrack = (index, currentSum) => {
      // Check timeout
      if (Date.now() - startTime > timeout) {
        throw new Error('Timeout');
      }
      
      if (currentSum === target) {
        return true;
      }
      
      if (index >= numbers.length || currentSum > target) {
        return false;
      }
      
      // Try including current number
      solution.push(index);
      if (backtrack(index + 1, currentSum + numbers[index])) {
        return true;
      }
      solution.pop();
      
      // Try excluding current number
      return backtrack(index + 1, currentSum);
    };
    
    if (backtrack(0, 0)) {
      return {
        indices: solution,
        numbers: solution.map(i => numbers[i]),
        sum: target,
        method: 'backtracking'
      };
    }
    
    return null;
  }

  /**
   * Create solution result object
   */
  createSolutionResult(solution, startTime, method) {
    const solveTime = Date.now() - startTime;
    
    return {
      success: true,
      solution,
      solveTime,
      method,
      workScore: this.calculateWorkScore(solution, solveTime),
      device: deviceUtils.getDeviceType(),
      timestamp: Date.now()
    };
  }

  /**
   * Create no solution result
   */
  createNoSolutionResult(startTime) {
    const solveTime = Date.now() - startTime;
    
    return {
      success: false,
      solution: null,
      solveTime,
      method: 'none',
      workScore: 0,
      device: deviceUtils.getDeviceType(),
      timestamp: Date.now(),
      error: 'No solution found'
    };
  }

  /**
   * Create error result
   */
  createErrorResult(error, startTime) {
    const solveTime = Date.now() - startTime;
    
    return {
      success: false,
      solution: null,
      solveTime,
      method: 'error',
      workScore: 0,
      device: deviceUtils.getDeviceType(),
      timestamp: Date.now(),
      error: error.message
    };
  }

  /**
   * Calculate work score based on solution complexity and time
   */
  calculateWorkScore(solution, solveTime) {
    if (!solution) return 0;
    
    const complexity = solution.numbers.length;
    const timeFactor = Math.max(1, solveTime / 100); // Time in 100ms units
    const baseScore = complexity * 10;
    
    return Math.floor(baseScore * timeFactor);
  }

  /**
   * Verify a solution
   */
  verifySolution(problem, solution) {
    if (!solution || !solution.numbers) {
      return false;
    }
    
    const actualSum = solution.numbers.reduce((sum, num) => sum + num, 0);
    return actualSum === problem.target;
  }

  /**
   * Get solver statistics
   */
  getStats() {
    return {
      isMobile: this.isMobile,
      maxProblemSize: this.maxProblemSize,
      maxSolveTime: this.maxSolveTime,
      device: deviceUtils.getDeviceType(),
      timestamp: Date.now()
    };
  }
}

// Create and export singleton instance
export const subsetSumSolver = new SubsetSumSolver();

// Export for backward compatibility
export default subsetSumSolver;
