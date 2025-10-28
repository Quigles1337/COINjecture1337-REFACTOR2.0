// COINjecture Web Interface - Mining Validation Module
// Version: 3.15.0

import { MINING_CONFIG } from '../shared/constants.js';
import { validationUtils, numberUtils } from '../shared/utils.js';

/**
 * Mining validation module for COINjecture blockchain
 */
export class MiningValidator {
  constructor() {
    this.validationRules = {
      minWorkScore: MINING_CONFIG.MIN_WORK_SCORE,
      maxAttempts: MINING_CONFIG.MAX_ATTEMPTS,
      maxProblemSize: 25,
      minProblemSize: 5,
      maxTargetValue: 100000,
      minTargetValue: 1
    };
  }

  /**
   * Validate problem structure
   */
  validateProblem(problem) {
    const errors = [];
    const warnings = [];

    // Check if problem exists
    if (!problem) {
      errors.push('Problem is null or undefined');
      return { isValid: false, errors, warnings };
    }

    // Validate numbers array
    if (!Array.isArray(problem.numbers)) {
      errors.push('Problem numbers must be an array');
    } else {
      if (problem.numbers.length < this.validationRules.minProblemSize) {
        errors.push(`Problem size too small (minimum: ${this.validationRules.minProblemSize})`);
      }
      
      if (problem.numbers.length > this.validationRules.maxProblemSize) {
        errors.push(`Problem size too large (maximum: ${this.validationRules.maxProblemSize})`);
      }

      // Validate individual numbers
      problem.numbers.forEach((num, index) => {
        if (!Number.isInteger(num) || num <= 0) {
          errors.push(`Invalid number at index ${index}: ${num}`);
        }
        
        if (num > this.validationRules.maxTargetValue) {
          warnings.push(`Large number at index ${index}: ${num}`);
        }
      });
    }

    // Validate target
    if (!Number.isInteger(problem.target) || problem.target <= 0) {
      errors.push('Target must be a positive integer');
    } else {
      if (problem.target < this.validationRules.minTargetValue) {
        errors.push(`Target too small (minimum: ${this.validationRules.minTargetValue})`);
      }
      
      if (problem.target > this.validationRules.maxTargetValue) {
        errors.push(`Target too large (maximum: ${this.validationRules.maxTargetValue})`);
      }
    }

    // Validate timestamp
    if (!problem.timestamp || !Number.isInteger(problem.timestamp)) {
      errors.push('Invalid timestamp');
    } else {
      const now = Date.now();
      const age = now - problem.timestamp;
      
      if (age < 0) {
        errors.push('Timestamp is in the future');
      } else if (age > 300000) { // 5 minutes
        warnings.push('Problem is older than 5 minutes');
      }
    }

    return {
      isValid: errors.length === 0,
      errors,
      warnings
    };
  }

  /**
   * Validate solution structure
   */
  validateSolution(solution) {
    const errors = [];
    const warnings = [];

    // Check if solution exists
    if (!solution) {
      errors.push('Solution is null or undefined');
      return { isValid: false, errors, warnings };
    }

    // Validate success flag
    if (typeof solution.success !== 'boolean') {
      errors.push('Solution success flag must be boolean');
    }

    if (!solution.success) {
      // If solution failed, check if error message exists
      if (!solution.error) {
        warnings.push('Failed solution should include error message');
      }
      return { isValid: errors.length === 0, errors, warnings };
    }

    // Validate solution data
    if (!solution.solution) {
      errors.push('Solution data is missing');
    } else {
      const sol = solution.solution;

      // Validate indices
      if (!Array.isArray(sol.indices)) {
        errors.push('Solution indices must be an array');
      } else {
        sol.indices.forEach((index, i) => {
          if (!Number.isInteger(index) || index < 0) {
            errors.push(`Invalid index at position ${i}: ${index}`);
          }
        });
      }

      // Validate numbers
      if (!Array.isArray(sol.numbers)) {
        errors.push('Solution numbers must be an array');
      } else {
        sol.numbers.forEach((num, i) => {
          if (!Number.isInteger(num) || num <= 0) {
            errors.push(`Invalid number at position ${i}: ${num}`);
          }
        });
      }

      // Validate sum
      if (!Number.isInteger(sol.sum) || sol.sum <= 0) {
        errors.push('Solution sum must be a positive integer');
      }

      // Validate method
      if (!sol.method || typeof sol.method !== 'string') {
        errors.push('Solution method must be a string');
      } else {
        const validMethods = ['dp', 'greedy', 'backtracking'];
        if (!validMethods.includes(sol.method)) {
          warnings.push(`Unknown solution method: ${sol.method}`);
        }
      }
    }

    // Validate work score
    if (!Number.isInteger(solution.workScore) || solution.workScore < 0) {
      errors.push('Work score must be a non-negative integer');
    } else {
      if (solution.workScore < this.validationRules.minWorkScore) {
        warnings.push(`Low work score: ${solution.workScore}`);
      }
    }

    // Validate solve time
    if (!Number.isInteger(solution.solveTime) || solution.solveTime < 0) {
      errors.push('Solve time must be a non-negative integer');
    } else {
      if (solution.solveTime > 10000) { // 10 seconds
        warnings.push(`Long solve time: ${solution.solveTime}ms`);
      }
    }

    // Validate timestamp
    if (!solution.timestamp || !Number.isInteger(solution.timestamp)) {
      errors.push('Invalid solution timestamp');
    }

    return {
      isValid: errors.length === 0,
      errors,
      warnings
    };
  }

  /**
   * Validate block data
   */
  validateBlock(block) {
    const errors = [];
    const warnings = [];

    // Check if block exists
    if (!block) {
      errors.push('Block is null or undefined');
      return { isValid: false, errors, warnings };
    }

    // Validate block index
    if (!Number.isInteger(block.index) || block.index < 0) {
      errors.push('Block index must be a non-negative integer');
    }

    // Validate timestamp
    if (!Number.isInteger(block.timestamp) || block.timestamp <= 0) {
      errors.push('Block timestamp must be a positive integer');
    } else {
      const now = Date.now();
      const age = now - block.timestamp;
      
      if (age < 0) {
        errors.push('Block timestamp is in the future');
      } else if (age > 60000) { // 1 minute
        warnings.push('Block timestamp is more than 1 minute old');
      }
    }

    // Validate previous hash
    if (!block.previousHash || typeof block.previousHash !== 'string') {
      errors.push('Previous hash must be a string');
    } else {
      if (block.previousHash.length !== 64) {
        warnings.push('Previous hash length is not 64 characters');
      }
    }

    // Validate miner address
    if (!block.miner || typeof block.miner !== 'string') {
      errors.push('Miner address must be a string');
    } else {
      if (!validationUtils.isValidAddress(block.miner)) {
        errors.push('Invalid miner address format');
      }
    }

    // Validate problem
    const problemValidation = this.validateProblem(block.problem);
    if (!problemValidation.isValid) {
      errors.push(...problemValidation.errors.map(e => `Problem: ${e}`));
    }
    warnings.push(...problemValidation.warnings.map(w => `Problem: ${w}`));

    // Validate solution
    const solutionValidation = this.validateSolution(block.solution);
    if (!solutionValidation.isValid) {
      errors.push(...solutionValidation.errors.map(e => `Solution: ${e}`));
    }
    warnings.push(...solutionValidation.warnings.map(w => `Solution: ${w}`));

    // Validate work score
    if (!Number.isInteger(block.workScore) || block.workScore < 0) {
      errors.push('Block work score must be a non-negative integer');
    }

    // Validate nonce
    if (!Number.isInteger(block.nonce) || block.nonce < 0) {
      errors.push('Block nonce must be a non-negative integer');
    }

    // Validate difficulty
    if (!Number.isInteger(block.difficulty) || block.difficulty < 1) {
      errors.push('Block difficulty must be a positive integer');
    }

    // Validate hash
    if (!block.hash || typeof block.hash !== 'string') {
      errors.push('Block hash must be a string');
    } else {
      if (block.hash.length !== 64) {
        warnings.push('Block hash length is not 64 characters');
      }
    }

    return {
      isValid: errors.length === 0,
      errors,
      warnings
    };
  }

  /**
   * Validate mining attempt
   */
  validateMiningAttempt(attempt) {
    const errors = [];
    const warnings = [];

    // Check if attempt exists
    if (!attempt) {
      errors.push('Mining attempt is null or undefined');
      return { isValid: false, errors, warnings };
    }

    // Validate attempt number
    if (!Number.isInteger(attempt.attempt) || attempt.attempt < 1) {
      errors.push('Attempt number must be a positive integer');
    }

    // Validate max attempts
    if (!Number.isInteger(attempt.maxAttempts) || attempt.maxAttempts < 1) {
      errors.push('Max attempts must be a positive integer');
    } else {
      if (attempt.attempt > attempt.maxAttempts) {
        errors.push('Attempt number exceeds max attempts');
      }
    }

    // Validate problem
    const problemValidation = this.validateProblem(attempt.problem);
    if (!problemValidation.isValid) {
      errors.push(...problemValidation.errors.map(e => `Problem: ${e}`));
    }
    warnings.push(...problemValidation.warnings.map(w => `Problem: ${w}`));

    // Validate solution if present
    if (attempt.solution) {
      const solutionValidation = this.validateSolution(attempt.solution);
      if (!solutionValidation.isValid) {
        errors.push(...solutionValidation.errors.map(e => `Solution: ${e}`));
      }
      warnings.push(...solutionValidation.warnings.map(w => `Solution: ${w}`));
    }

    // Validate stats
    if (attempt.stats) {
      if (!Number.isInteger(attempt.stats.attempts) || attempt.stats.attempts < 0) {
        errors.push('Stats attempts must be a non-negative integer');
      }
      
      if (!Number.isInteger(attempt.stats.successes) || attempt.stats.successes < 0) {
        errors.push('Stats successes must be a non-negative integer');
      }
      
      if (attempt.stats.successes > attempt.stats.attempts) {
        errors.push('Successes cannot exceed attempts');
      }
    }

    return {
      isValid: errors.length === 0,
      errors,
      warnings
    };
  }

  /**
   * Validate mining statistics
   */
  validateMiningStats(stats) {
    const errors = [];
    const warnings = [];

    // Check if stats exist
    if (!stats) {
      errors.push('Mining stats are null or undefined');
      return { isValid: false, errors, warnings };
    }

    // Validate attempts
    if (!Number.isInteger(stats.attempts) || stats.attempts < 0) {
      errors.push('Attempts must be a non-negative integer');
    }

    // Validate successes
    if (!Number.isInteger(stats.successes) || stats.successes < 0) {
      errors.push('Successes must be a non-negative integer');
    }

    // Validate success rate
    if (stats.attempts > 0) {
      const expectedSuccessRate = (stats.successes / stats.attempts) * 100;
      if (Math.abs(stats.successRate - expectedSuccessRate) > 0.01) {
        warnings.push('Success rate calculation may be incorrect');
      }
    }

    // Validate work score
    if (!Number.isInteger(stats.totalWorkScore) || stats.totalWorkScore < 0) {
      errors.push('Total work score must be a non-negative integer');
    }

    // Validate average work score
    if (stats.successes > 0) {
      const expectedAverage = stats.totalWorkScore / stats.successes;
      if (Math.abs(stats.averageWorkScore - expectedAverage) > 0.01) {
        warnings.push('Average work score calculation may be incorrect');
      }
    }

    // Validate duration
    if (!Number.isInteger(stats.duration) || stats.duration < 0) {
      errors.push('Duration must be a non-negative integer');
    }

    // Validate hash rate
    if (typeof stats.hashRate !== 'number' || stats.hashRate < 0) {
      errors.push('Hash rate must be a non-negative number');
    }

    return {
      isValid: errors.length === 0,
      errors,
      warnings
    };
  }

  /**
   * Get validation summary
   */
  getValidationSummary(validations) {
    const totalValidations = validations.length;
    const validCount = validations.filter(v => v.isValid).length;
    const invalidCount = totalValidations - validCount;
    
    const allErrors = validations.flatMap(v => v.errors);
    const allWarnings = validations.flatMap(v => v.warnings);
    
    return {
      total: totalValidations,
      valid: validCount,
      invalid: invalidCount,
      successRate: totalValidations > 0 ? (validCount / totalValidations) * 100 : 0,
      errorCount: allErrors.length,
      warningCount: allWarnings.length,
      errors: allErrors,
      warnings: allWarnings
    };
  }

  /**
   * Validate mining configuration
   */
  validateMiningConfig(config) {
    const errors = [];
    const warnings = [];

    // Check if config exists
    if (!config) {
      errors.push('Mining config is null or undefined');
      return { isValid: false, errors, warnings };
    }

    // Validate max attempts
    if (!Number.isInteger(config.maxAttempts) || config.maxAttempts < 1) {
      errors.push('Max attempts must be a positive integer');
    } else {
      if (config.maxAttempts > 10000) {
        warnings.push('Very high max attempts value');
      }
    }

    // Validate timeout
    if (!Number.isInteger(config.timeout) || config.timeout < 1000) {
      errors.push('Timeout must be at least 1000ms');
    }

    // Validate problem size
    if (config.problemSize) {
      if (!Number.isInteger(config.problemSize) || config.problemSize < 5 || config.problemSize > 25) {
        errors.push('Problem size must be between 5 and 25');
      }
    }

    return {
      isValid: errors.length === 0,
      errors,
      warnings
    };
  }
}

// Create and export singleton instance
export const miningValidator = new MiningValidator();

// Export for backward compatibility
export default miningValidator;
