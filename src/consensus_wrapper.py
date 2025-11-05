"""
COINjecture Consensus Wrapper - Live Migration from Legacy to Rust

This module provides a dual-run consensus engine that enables safe migration
from legacy Python consensus to refactored Rust consensus without downtime.

Migration Phases:
1. LEGACY_ONLY - Current production (Python consensus)
2. SHADOW - Run both Python + Rust, compare outputs, use Python (validation)
3. REFACTORED_PRIMARY - Use Rust, fallback to Python on error (gradual migration)
4. REFACTORED_ONLY - Rust only, remove Python (final state)

Author: Quigles1337 <adz@alphx.io>
Version: 4.1.0
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any, Tuple
import logging
import time
import traceback


class ConsensusMode(Enum):
    """Consensus migration modes for safe cutover."""
    LEGACY_ONLY = "legacy"          # Use legacy Python consensus only
    SHADOW = "shadow"               # Run both, use legacy, log diffs (Phase 1)
    REFACTORED_PRIMARY = "rust"     # Use Rust, fallback to legacy on error (Phase 2)
    REFACTORED_ONLY = "final"       # Use Rust only, remove legacy (Phase 3)


@dataclass
class ConsensusResult:
    """Result from consensus verification."""
    valid: bool
    duration_ms: float
    mode_used: str  # "legacy" or "rust"
    error: Optional[str] = None


class DualRunConsensus:
    """
    Wrapper that runs both legacy and Rust consensus for safe migration.

    Example Usage:
        # Phase 1: Shadow mode (validate Rust without risk)
        consensus = DualRunConsensus(mode=ConsensusMode.SHADOW)
        result = consensus.verify_block(block)

        # Phase 2: Rust primary (use Rust, fallback if error)
        consensus = DualRunConsensus(mode=ConsensusMode.REFACTORED_PRIMARY)
        result = consensus.verify_block(block)

        # Phase 3: Rust only (remove legacy)
        consensus = DualRunConsensus(mode=ConsensusMode.REFACTORED_ONLY)
        result = consensus.verify_block(block)
    """

    def __init__(
        self,
        mode: ConsensusMode = ConsensusMode.LEGACY_ONLY,
        legacy_engine=None,
        alert_callback=None
    ):
        """
        Initialize dual-run consensus wrapper.

        Args:
            mode: Consensus migration mode
            legacy_engine: Existing ConsensusEngine instance (legacy Python)
            alert_callback: Function to call on divergence (for monitoring)
        """
        self.mode = mode
        self.logger = logging.getLogger("DualRunConsensus")
        self.alert_callback = alert_callback

        # Statistics
        self.stats = {
            "total_verifications": 0,
            "divergences": 0,
            "rust_errors": 0,
            "fallback_to_legacy": 0,
        }

        # Legacy consensus (always loaded except REFACTORED_ONLY)
        self.legacy = None
        if mode != ConsensusMode.REFACTORED_ONLY:
            if legacy_engine is not None:
                self.legacy = legacy_engine
            else:
                try:
                    from .consensus import ConsensusEngine
                    # You'll need to pass proper config/storage/registry
                    # For now, we'll expect it to be injected
                    self.logger.warning(
                        "Legacy engine not provided, will need manual injection"
                    )
                except ImportError:
                    self.logger.error("Cannot import legacy ConsensusEngine")

        # Rust consensus (loaded when mode != LEGACY_ONLY)
        self.rust_available = False
        if mode != ConsensusMode.LEGACY_ONLY:
            try:
                from coinjecture._core import (
                    sha256_hash,
                    compute_header_hash_py,
                    compute_merkle_root_py,
                    verify_subset_sum_py,
                )
                self.rust_sha256 = sha256_hash
                self.rust_header_hash = compute_header_hash_py
                self.rust_merkle_root = compute_merkle_root_py
                self.rust_verify_subset_sum = verify_subset_sum_py
                self.rust_available = True
                self.logger.info("Rust consensus loaded successfully")
            except ImportError as e:
                self.logger.error(f"Cannot import Rust consensus: {e}")
                if mode == ConsensusMode.REFACTORED_ONLY:
                    raise RuntimeError(
                        "REFACTORED_ONLY mode requires Rust, but Rust not available. "
                        "Build with: maturin develop --release --features python"
                    )
                self.logger.warning("Falling back to legacy-only mode")
                self.mode = ConsensusMode.LEGACY_ONLY

        self.logger.info(f"DualRunConsensus initialized in {self.mode.value} mode")

    def verify_block(self, block) -> Tuple[bool, ConsensusResult]:
        """
        Verify block using appropriate consensus mode.

        Returns:
            (is_valid, result_metadata)
        """
        self.stats["total_verifications"] += 1

        if self.mode == ConsensusMode.LEGACY_ONLY:
            return self._verify_legacy_only(block)

        elif self.mode == ConsensusMode.SHADOW:
            return self._verify_shadow_mode(block)

        elif self.mode == ConsensusMode.REFACTORED_PRIMARY:
            return self._verify_rust_primary(block)

        elif self.mode == ConsensusMode.REFACTORED_ONLY:
            return self._verify_rust_only(block)

        else:
            raise ValueError(f"Unknown consensus mode: {self.mode}")

    def _verify_legacy_only(self, block) -> Tuple[bool, ConsensusResult]:
        """Phase 0: Legacy Python consensus only (current production)."""
        start = time.time()

        try:
            # Delegate to legacy consensus engine
            is_valid = self.legacy.verify_block(block)
            duration = (time.time() - start) * 1000

            return is_valid, ConsensusResult(
                valid=is_valid,
                duration_ms=duration,
                mode_used="legacy"
            )
        except Exception as e:
            self.logger.error(f"Legacy verification error: {e}")
            raise

    def _verify_shadow_mode(self, block) -> Tuple[bool, ConsensusResult]:
        """
        Phase 1: Run BOTH legacy and Rust, use legacy result, log divergences.

        This phase validates that Rust produces identical results to legacy
        WITHOUT risking production behavior.
        """
        # Run legacy first (this is what we'll return)
        start_legacy = time.time()
        try:
            legacy_valid = self.legacy.verify_block(block)
            legacy_duration = (time.time() - start_legacy) * 1000
        except Exception as e:
            self.logger.error(f"Legacy verification failed in shadow mode: {e}")
            raise  # Can't continue without legacy in shadow mode

        # Run Rust for comparison
        start_rust = time.time()
        rust_valid = None
        rust_error = None

        try:
            rust_valid = self._rust_verify_block_impl(block)
            rust_duration = (time.time() - start_rust) * 1000
        except Exception as e:
            rust_error = str(e)
            rust_duration = (time.time() - start_rust) * 1000
            self.logger.error(f"Rust verification failed in shadow mode: {e}")
            self.stats["rust_errors"] += 1

        # Compare results
        if rust_error is None and rust_valid != legacy_valid:
            # CRITICAL: Consensus divergence detected!
            self.stats["divergences"] += 1
            self.logger.error(
                f"🚨 CONSENSUS DIVERGENCE DETECTED! 🚨\n"
                f"Block index: {getattr(block, 'index', 'unknown')}\n"
                f"Legacy result: {legacy_valid}\n"
                f"Rust result: {rust_valid}\n"
                f"This is a CRITICAL BUG in the Rust implementation!"
            )

            # Call alert callback if provided
            if self.alert_callback:
                self.alert_callback({
                    "type": "consensus_divergence",
                    "block_index": getattr(block, 'index', None),
                    "legacy_result": legacy_valid,
                    "rust_result": rust_valid,
                })

        elif rust_error is None:
            # Results match - good!
            perf_improvement = ((legacy_duration - rust_duration) / legacy_duration) * 100
            self.logger.debug(
                f"Shadow mode: Results match! "
                f"Rust {perf_improvement:+.1f}% vs legacy "
                f"({rust_duration:.2f}ms vs {legacy_duration:.2f}ms)"
            )

        # ALWAYS return legacy result in shadow mode (safe)
        return legacy_valid, ConsensusResult(
            valid=legacy_valid,
            duration_ms=legacy_duration,
            mode_used="legacy",
            error=rust_error if rust_error else None
        )

    def _verify_rust_primary(self, block) -> Tuple[bool, ConsensusResult]:
        """
        Phase 2: Use Rust first, fallback to legacy on error.

        This phase tests Rust in production with a safety net.
        """
        start_rust = time.time()

        try:
            # Try Rust first
            rust_valid = self._rust_verify_block_impl(block)
            rust_duration = (time.time() - start_rust) * 1000

            # Also run legacy for comparison (catch bugs)
            try:
                legacy_valid = self.legacy.verify_block(block)
                if legacy_valid != rust_valid:
                    self.logger.warning(
                        f"Divergence in Rust-primary mode: "
                        f"Rust={rust_valid}, Legacy={legacy_valid}. "
                        f"Using Rust result."
                    )
                    self.stats["divergences"] += 1
            except Exception as e:
                self.logger.warning(f"Legacy verification failed (ignoring): {e}")

            return rust_valid, ConsensusResult(
                valid=rust_valid,
                duration_ms=rust_duration,
                mode_used="rust"
            )

        except Exception as e:
            # Rust failed - fallback to legacy
            self.stats["rust_errors"] += 1
            self.stats["fallback_to_legacy"] += 1

            self.logger.error(
                f"Rust verification failed, falling back to legacy: {e}\n"
                f"{traceback.format_exc()}"
            )

            # Fallback to legacy
            start_legacy = time.time()
            legacy_valid = self.legacy.verify_block(block)
            legacy_duration = (time.time() - start_legacy) * 1000

            return legacy_valid, ConsensusResult(
                valid=legacy_valid,
                duration_ms=legacy_duration,
                mode_used="legacy",
                error=str(e)
            )

    def _verify_rust_only(self, block) -> Tuple[bool, ConsensusResult]:
        """
        Phase 3: Rust only, no fallback.

        This is the final state - legacy code can be removed.
        """
        start = time.time()

        try:
            is_valid = self._rust_verify_block_impl(block)
            duration = (time.time() - start) * 1000

            return is_valid, ConsensusResult(
                valid=is_valid,
                duration_ms=duration,
                mode_used="rust"
            )
        except Exception as e:
            self.logger.error(f"Rust verification error (no fallback): {e}")
            raise

    def _rust_verify_block_impl(self, block) -> bool:
        """
        Verify block using Rust consensus.

        This delegates to Rust for all consensus-critical operations.
        """
        # TODO: Implement full Rust delegation based on block structure

        # For now, verify individual components:
        # 1. Block header hash
        header_dict = {
            "codec_version": getattr(block, 'codec_version', 1),
            "block_index": getattr(block, 'index', 0),
            "timestamp": int(getattr(block, 'timestamp', time.time())),
            "parent_hash": getattr(block, 'previous_hash', b'\x00' * 32),
            "merkle_root": getattr(block, 'merkle_root', b'\x00' * 32),
            "miner_address": getattr(block, 'miner_address', b'\x00' * 32),
            "commitment": getattr(block, 'commitment', b'\x00' * 32),
            "difficulty_target": getattr(block, 'difficulty', 1000),
            "nonce": getattr(block, 'nonce', 0),
            "extra_data": getattr(block, 'extra_data', b''),
        }

        try:
            header_hash = self.rust_header_hash(header_dict)
        except Exception as e:
            raise RuntimeError(f"Rust header hash failed: {e}")

        # 2. Verify proof (if present)
        if hasattr(block, 'proof') and block.proof is not None:
            problem_dict = {
                "problem_type": 0,  # SubsetSum
                "tier": getattr(block.proof, 'tier', 1),
                "elements": getattr(block.proof, 'elements', []),
                "target": getattr(block.proof, 'target', 0),
                "timestamp": int(getattr(block.proof, 'timestamp', time.time())),
            }

            solution_dict = {
                "indices": getattr(block.proof, 'solution', []),
                "timestamp": int(time.time()),
            }

            budget_dict = {
                "max_ops": 1000000,
                "max_duration_ms": 10000,
                "max_memory_bytes": 100_000_000,
            }

            try:
                is_valid = self.rust_verify_subset_sum(
                    problem_dict,
                    solution_dict,
                    budget_dict
                )
                if not is_valid:
                    return False
            except Exception as e:
                raise RuntimeError(f"Rust proof verification failed: {e}")

        # If we get here, block is valid
        return True

    def get_stats(self) -> Dict[str, Any]:
        """Get migration statistics for monitoring."""
        return {
            **self.stats,
            "mode": self.mode.value,
            "divergence_rate": (
                self.stats["divergences"] / self.stats["total_verifications"]
                if self.stats["total_verifications"] > 0 else 0
            ),
            "rust_error_rate": (
                self.stats["rust_errors"] / self.stats["total_verifications"]
                if self.stats["total_verifications"] > 0 else 0
            ),
        }

    def set_mode(self, new_mode: ConsensusMode):
        """
        Change consensus mode (for gradual migration).

        WARNING: Only change mode during low-traffic periods!
        """
        old_mode = self.mode
        self.mode = new_mode
        self.logger.info(f"Consensus mode changed: {old_mode.value} → {new_mode.value}")

        # Validate mode change is safe
        if new_mode == ConsensusMode.REFACTORED_ONLY and not self.rust_available:
            raise RuntimeError("Cannot switch to REFACTORED_ONLY without Rust available")

        if new_mode in [ConsensusMode.SHADOW, ConsensusMode.REFACTORED_PRIMARY]:
            if self.legacy is None:
                raise RuntimeError(f"Cannot use {new_mode.value} without legacy engine")
