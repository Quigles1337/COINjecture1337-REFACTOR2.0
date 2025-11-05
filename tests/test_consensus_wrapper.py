"""
Tests for DualRunConsensus - Live Migration Wrapper

This test suite validates the consensus migration wrapper before deploying
to live testnet nodes. Tests all migration modes and error conditions.

Author: Quigles1337 <adz@alphx.io>
Version: 4.1.0
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from dataclasses import dataclass
import time

from src.consensus_wrapper import (
    DualRunConsensus,
    ConsensusMode,
    ConsensusResult,
)


@dataclass
class MockBlock:
    """Mock block for testing."""
    index: int = 0
    timestamp: int = 1609459200
    previous_hash: bytes = b'\x00' * 32
    merkle_root: bytes = b'\x00' * 32
    miner_address: bytes = b'\x00' * 32
    commitment: bytes = b'\x00' * 32
    difficulty: int = 1000
    nonce: int = 0
    codec_version: int = 1
    extra_data: bytes = b''
    proof: object = None


class MockLegacyEngine:
    """Mock legacy Python consensus engine."""

    def __init__(self, return_value=True):
        self.return_value = return_value
        self.verify_calls = []

    def verify_block(self, block):
        """Mock verify_block implementation."""
        self.verify_calls.append(block)
        time.sleep(0.001)  # Simulate some work
        return self.return_value


class MockRustConsensus:
    """Mock Rust consensus functions."""

    def __init__(self, return_value=True):
        self.return_value = return_value
        self.calls = []

    def sha256_hash(self, data):
        self.calls.append(('sha256', data))
        return b'\x00' * 32

    def compute_header_hash_py(self, header):
        self.calls.append(('header_hash', header))
        return b'\x00' * 32

    def compute_merkle_root_py(self, txs):
        self.calls.append(('merkle_root', txs))
        return b'\x00' * 32

    def verify_subset_sum_py(self, problem, solution, budget):
        self.calls.append(('verify_subset_sum', problem, solution, budget))
        return self.return_value


def create_consensus_with_rust_enabled(mode, legacy_engine=None, alert_callback=None):
    """
    Helper to create DualRunConsensus with Rust enabled (for testing).

    This bypasses the Rust import check by creating in LEGACY_ONLY mode,
    then manually enabling Rust and switching to the desired mode.
    """
    if legacy_engine is None and mode != ConsensusMode.REFACTORED_ONLY:
        legacy_engine = MockLegacyEngine(return_value=True)

    consensus = DualRunConsensus(
        mode=ConsensusMode.LEGACY_ONLY,
        legacy_engine=legacy_engine,
        alert_callback=alert_callback
    )

    # Manually enable Rust
    consensus.rust_available = True
    consensus.mode = mode

    return consensus


# ============================================================================
# TEST: LEGACY_ONLY Mode
# ============================================================================

def test_legacy_only_mode_valid_block():
    """Test LEGACY_ONLY mode with valid block."""
    legacy_engine = MockLegacyEngine(return_value=True)
    consensus = DualRunConsensus(
        mode=ConsensusMode.LEGACY_ONLY,
        legacy_engine=legacy_engine
    )

    block = MockBlock(index=1)
    is_valid, result = consensus.verify_block(block)

    assert is_valid is True
    assert result.valid is True
    assert result.mode_used == "legacy"
    assert result.error is None
    assert result.duration_ms > 0
    assert len(legacy_engine.verify_calls) == 1
    assert consensus.stats["total_verifications"] == 1


def test_legacy_only_mode_invalid_block():
    """Test LEGACY_ONLY mode with invalid block."""
    legacy_engine = MockLegacyEngine(return_value=False)
    consensus = DualRunConsensus(
        mode=ConsensusMode.LEGACY_ONLY,
        legacy_engine=legacy_engine
    )

    block = MockBlock(index=1)
    is_valid, result = consensus.verify_block(block)

    assert is_valid is False
    assert result.valid is False
    assert result.mode_used == "legacy"


def test_legacy_only_mode_error():
    """Test LEGACY_ONLY mode with legacy engine error."""
    legacy_engine = Mock()
    legacy_engine.verify_block.side_effect = RuntimeError("Legacy engine error")

    consensus = DualRunConsensus(
        mode=ConsensusMode.LEGACY_ONLY,
        legacy_engine=legacy_engine
    )

    block = MockBlock(index=1)

    with pytest.raises(RuntimeError, match="Legacy engine error"):
        consensus.verify_block(block)


# ============================================================================
# TEST: SHADOW Mode (Critical for Migration)
# ============================================================================

def test_shadow_mode_both_agree():
    """Test SHADOW mode when both legacy and Rust agree."""
    legacy_engine = MockLegacyEngine(return_value=True)

    # Bypass Rust import by creating consensus in LEGACY_ONLY first
    consensus = DualRunConsensus(
        mode=ConsensusMode.LEGACY_ONLY,
        legacy_engine=legacy_engine
    )

    # Manually enable Rust and switch to SHADOW
    consensus.rust_available = True
    consensus.mode = ConsensusMode.SHADOW

    with patch.object(consensus, '_rust_verify_block_impl', return_value=True) as mock_rust:
        block = MockBlock(index=1)
        is_valid, result = consensus.verify_block(block)

        # Should return legacy result (safe)
        assert is_valid is True
        assert result.valid is True
        assert result.mode_used == "legacy"

        # Both should have been called
        assert len(legacy_engine.verify_calls) == 1
        assert mock_rust.call_count == 1

        # No divergence
        assert consensus.stats["divergences"] == 0


def test_shadow_mode_divergence_detected():
    """Test SHADOW mode when legacy and Rust disagree (CRITICAL BUG)."""
    legacy_engine = MockLegacyEngine(return_value=True)
    alert_calls = []

    def alert_callback(data):
        alert_calls.append(data)

    # Bypass Rust import
    consensus = DualRunConsensus(
        mode=ConsensusMode.LEGACY_ONLY,
        legacy_engine=legacy_engine,
        alert_callback=alert_callback
    )
    consensus.rust_available = True
    consensus.mode = ConsensusMode.SHADOW

    with patch.object(consensus, '_rust_verify_block_impl', return_value=False) as mock_rust:
        block = MockBlock(index=1)
        is_valid, result = consensus.verify_block(block)

        # Should STILL return legacy result (safe)
        assert is_valid is True
        assert result.valid is True
        assert result.mode_used == "legacy"

        # But divergence should be detected
        assert consensus.stats["divergences"] == 1
        assert len(alert_calls) == 1
        assert alert_calls[0]["type"] == "consensus_divergence"
        assert alert_calls[0]["legacy_result"] is True
        assert alert_calls[0]["rust_result"] is False


def test_shadow_mode_rust_error():
    """Test SHADOW mode when Rust throws error."""
    legacy_engine = MockLegacyEngine(return_value=True)
    consensus = create_consensus_with_rust_enabled(ConsensusMode.SHADOW, legacy_engine)

    with patch.object(consensus, '_rust_verify_block_impl', side_effect=RuntimeError("Rust verification failed")):
        block = MockBlock(index=1)
        is_valid, result = consensus.verify_block(block)

        # Should return legacy result (safe)
        assert is_valid is True
        assert result.valid is True
        assert result.mode_used == "legacy"

        # Error should be logged
        assert consensus.stats["rust_errors"] == 1
        assert result.error is not None


def test_shadow_mode_legacy_error():
    """Test SHADOW mode when legacy throws error (fail fast)."""
    legacy_engine = Mock()
    legacy_engine.verify_block.side_effect = RuntimeError("Legacy error")

    consensus = DualRunConsensus(
        mode=ConsensusMode.SHADOW,
        legacy_engine=legacy_engine
    )
    consensus.rust_available = True

    block = MockBlock(index=1)

    # Should raise because we can't continue without legacy in shadow mode
    with pytest.raises(RuntimeError, match="Legacy error"):
        consensus.verify_block(block)


# ============================================================================
# TEST: REFACTORED_PRIMARY Mode (Rust with Fallback)
# ============================================================================

def test_rust_primary_mode_success():
    """Test REFACTORED_PRIMARY mode when Rust succeeds."""
    legacy_engine = MockLegacyEngine(return_value=True)
    consensus = create_consensus_with_rust_enabled(ConsensusMode.REFACTORED_PRIMARY, legacy_engine)

    with patch.object(consensus, '_rust_verify_block_impl', return_value=True) as mock_rust:
        block = MockBlock(index=1)
        is_valid, result = consensus.verify_block(block)

        # Should use Rust result
        assert is_valid is True
        assert result.valid is True
        assert result.mode_used == "rust"
        assert result.error is None

        # Rust should be called
        assert mock_rust.call_count == 1


def test_rust_primary_mode_fallback():
    """Test REFACTORED_PRIMARY mode fallback when Rust fails."""
    legacy_engine = MockLegacyEngine(return_value=True)
    consensus = create_consensus_with_rust_enabled(ConsensusMode.REFACTORED_PRIMARY, legacy_engine)

    with patch.object(consensus, '_rust_verify_block_impl', side_effect=RuntimeError("Rust crashed")):
        block = MockBlock(index=1)
        is_valid, result = consensus.verify_block(block)

        # Should fallback to legacy
        assert is_valid is True
        assert result.valid is True
        assert result.mode_used == "legacy"
        assert result.error is not None

        # Stats should track fallback
        assert consensus.stats["rust_errors"] == 1
        assert consensus.stats["fallback_to_legacy"] == 1


def test_rust_primary_mode_divergence():
    """Test REFACTORED_PRIMARY mode when Rust and legacy disagree."""
    legacy_engine = MockLegacyEngine(return_value=False)  # Legacy says invalid
    consensus = create_consensus_with_rust_enabled(ConsensusMode.REFACTORED_PRIMARY, legacy_engine)

    with patch.object(consensus, '_rust_verify_block_impl', return_value=True):  # Rust says valid
        block = MockBlock(index=1)
        is_valid, result = consensus.verify_block(block)

        # Should use Rust result (we trust Rust in this mode)
        assert is_valid is True
        assert result.valid is True
        assert result.mode_used == "rust"

        # But divergence should be logged
        assert consensus.stats["divergences"] == 1


# ============================================================================
# TEST: REFACTORED_ONLY Mode (Rust Only)
# ============================================================================

def test_rust_only_mode_success():
    """Test REFACTORED_ONLY mode when Rust succeeds."""
    # No legacy engine provided (should not load)
    consensus = create_consensus_with_rust_enabled(ConsensusMode.REFACTORED_ONLY)

    with patch.object(consensus, '_rust_verify_block_impl', return_value=True):
        block = MockBlock(index=1)
        is_valid, result = consensus.verify_block(block)

        assert is_valid is True
        assert result.valid is True
        assert result.mode_used == "rust"
        assert consensus.legacy is None  # No legacy engine


def test_rust_only_mode_error():
    """Test REFACTORED_ONLY mode when Rust fails (no fallback)."""
    consensus = create_consensus_with_rust_enabled(ConsensusMode.REFACTORED_ONLY)

    with patch.object(consensus, '_rust_verify_block_impl', side_effect=RuntimeError("Rust error")):
        block = MockBlock(index=1)

        # Should raise because no fallback
        with pytest.raises(RuntimeError, match="Rust error"):
            consensus.verify_block(block)


# ============================================================================
# TEST: Statistics & Monitoring
# ============================================================================

def test_statistics_tracking():
    """Test that statistics are tracked correctly."""
    legacy_engine = MockLegacyEngine(return_value=True)
    consensus = create_consensus_with_rust_enabled(ConsensusMode.SHADOW, legacy_engine)

    # Verify 3 blocks with different outcomes
    block1 = MockBlock(index=1)
    block2 = MockBlock(index=2)
    block3 = MockBlock(index=3)

    with patch.object(consensus, '_rust_verify_block_impl', return_value=True):
        consensus.verify_block(block1)  # Both agree

    with patch.object(consensus, '_rust_verify_block_impl', return_value=False):
        consensus.verify_block(block2)  # Divergence

    with patch.object(consensus, '_rust_verify_block_impl', side_effect=RuntimeError("Error")):
        consensus.verify_block(block3)  # Rust error

    stats = consensus.get_stats()

    assert stats["total_verifications"] == 3
    assert stats["divergences"] == 1
    assert stats["rust_errors"] == 1
    assert stats["divergence_rate"] == 1/3
    assert stats["rust_error_rate"] == 1/3
    assert stats["mode"] == "shadow"


# ============================================================================
# TEST: Mode Switching
# ============================================================================

def test_mode_switching():
    """Test changing consensus mode at runtime."""
    legacy_engine = MockLegacyEngine(return_value=True)
    consensus = DualRunConsensus(
        mode=ConsensusMode.LEGACY_ONLY,
        legacy_engine=legacy_engine
    )
    consensus.rust_available = True

    # Start in LEGACY_ONLY
    assert consensus.mode == ConsensusMode.LEGACY_ONLY

    # Switch to SHADOW
    consensus.set_mode(ConsensusMode.SHADOW)
    assert consensus.mode == ConsensusMode.SHADOW

    # Switch to REFACTORED_PRIMARY
    consensus.set_mode(ConsensusMode.REFACTORED_PRIMARY)
    assert consensus.mode == ConsensusMode.REFACTORED_PRIMARY


def test_mode_switching_validation():
    """Test that mode switching validates prerequisites."""
    legacy_engine = MockLegacyEngine(return_value=True)
    consensus = DualRunConsensus(
        mode=ConsensusMode.LEGACY_ONLY,
        legacy_engine=legacy_engine
    )
    consensus.rust_available = False  # Rust not available

    # Should fail to switch to REFACTORED_ONLY without Rust
    with pytest.raises(RuntimeError, match="Cannot switch to REFACTORED_ONLY without Rust"):
        consensus.set_mode(ConsensusMode.REFACTORED_ONLY)


def test_mode_switching_requires_legacy():
    """Test that SHADOW/PRIMARY modes require legacy engine."""
    consensus = create_consensus_with_rust_enabled(ConsensusMode.REFACTORED_ONLY)
    consensus.legacy = None  # No legacy engine

    # Should fail to switch to SHADOW without legacy
    with pytest.raises(RuntimeError, match="Cannot use shadow without legacy engine"):
        consensus.set_mode(ConsensusMode.SHADOW)


# ============================================================================
# TEST: Rust Verification Implementation
# ============================================================================

def test_rust_verify_block_impl_basic():
    """Test Rust verification implementation with basic block."""
    consensus = create_consensus_with_rust_enabled(ConsensusMode.REFACTORED_ONLY)

    # Mock Rust functions directly on the instance
    mock_hash = Mock(return_value=b'\x00' * 32)
    consensus.rust_header_hash = mock_hash

    block = MockBlock(index=1, proof=None)
    result = consensus._rust_verify_block_impl(block)

    # Should succeed (no proof to verify)
    assert result is True
    assert mock_hash.call_count == 1


def test_rust_verify_block_impl_with_proof():
    """Test Rust verification with proof."""
    consensus = create_consensus_with_rust_enabled(ConsensusMode.REFACTORED_ONLY)

    # Mock Rust functions
    mock_hash = Mock(return_value=b'\x00' * 32)
    mock_verify = Mock(return_value=True)
    consensus.rust_header_hash = mock_hash
    consensus.rust_verify_subset_sum = mock_verify

    # Create block with proof
    proof = Mock()
    proof.tier = 1
    proof.elements = [1, 2, 3, 4, 5]
    proof.target = 9
    proof.solution = [0, 2, 4]  # 1+3+5=9
    proof.timestamp = 1000

    block = MockBlock(index=1, proof=proof)
    result = consensus._rust_verify_block_impl(block)

    assert result is True
    assert mock_hash.call_count == 1
    assert mock_verify.call_count == 1


def test_rust_verify_block_impl_invalid_proof():
    """Test Rust verification with invalid proof."""
    consensus = create_consensus_with_rust_enabled(ConsensusMode.REFACTORED_ONLY)

    # Mock Rust functions
    mock_hash = Mock(return_value=b'\x00' * 32)
    mock_verify = Mock(return_value=False)  # Invalid proof
    consensus.rust_header_hash = mock_hash
    consensus.rust_verify_subset_sum = mock_verify

    proof = Mock()
    proof.tier = 1
    proof.elements = [1, 2, 3]
    proof.target = 100
    proof.solution = [0, 1]  # 1+2=3 != 100
    proof.timestamp = 1000

    block = MockBlock(index=1, proof=proof)
    result = consensus._rust_verify_block_impl(block)

    # Should reject invalid proof
    assert result is False


# ============================================================================
# TEST: Initialization
# ============================================================================

def test_initialization_legacy_only():
    """Test initialization in LEGACY_ONLY mode."""
    legacy_engine = MockLegacyEngine()
    consensus = DualRunConsensus(
        mode=ConsensusMode.LEGACY_ONLY,
        legacy_engine=legacy_engine
    )

    assert consensus.mode == ConsensusMode.LEGACY_ONLY
    assert consensus.legacy is legacy_engine
    assert consensus.stats["total_verifications"] == 0


def test_initialization_without_rust():
    """Test initialization when Rust is not available."""
    legacy_engine = MockLegacyEngine()

    # When Rust is not available, REFACTORED_ONLY should fail
    # This is tested by the actual __init__ logic which tries to import
    # Since we can't actually unimport coinjecture._core, we simulate by
    # checking the logic: If rust_available=False and mode=REFACTORED_ONLY, it should raise

    # Create instance in LEGACY_ONLY mode
    consensus = DualRunConsensus(
        mode=ConsensusMode.LEGACY_ONLY,
        legacy_engine=legacy_engine
    )

    # Manually set rust_available to False
    consensus.rust_available = False

    # Try to switch to REFACTORED_ONLY - should fail
    with pytest.raises(RuntimeError, match="Cannot switch to REFACTORED_ONLY without Rust"):
        consensus.set_mode(ConsensusMode.REFACTORED_ONLY)


# ============================================================================
# TEST: Integration Scenarios
# ============================================================================

def test_migration_workflow_simulation():
    """Simulate full migration workflow: LEGACY → SHADOW → PRIMARY → ONLY."""
    legacy_engine = MockLegacyEngine(return_value=True)

    # Phase 0: LEGACY_ONLY
    consensus = DualRunConsensus(
        mode=ConsensusMode.LEGACY_ONLY,
        legacy_engine=legacy_engine
    )

    block = MockBlock(index=1)
    is_valid, result = consensus.verify_block(block)
    assert result.mode_used == "legacy"

    # Enable Rust for migration
    consensus.rust_available = True

    # Phase 1: SHADOW
    consensus.set_mode(ConsensusMode.SHADOW)
    with patch.object(consensus, '_rust_verify_block_impl', return_value=True):
        is_valid, result = consensus.verify_block(block)
        assert result.mode_used == "legacy"  # Still using legacy
        assert consensus.stats["divergences"] == 0  # No divergences

    # Phase 2: REFACTORED_PRIMARY
    consensus.set_mode(ConsensusMode.REFACTORED_PRIMARY)
    with patch.object(consensus, '_rust_verify_block_impl', return_value=True):
        is_valid, result = consensus.verify_block(block)
        assert result.mode_used == "rust"  # Now using Rust!

    # Phase 3: REFACTORED_ONLY
    consensus.set_mode(ConsensusMode.REFACTORED_ONLY)
    with patch.object(consensus, '_rust_verify_block_impl', return_value=True):
        is_valid, result = consensus.verify_block(block)
        assert result.mode_used == "rust"
        assert consensus.stats["total_verifications"] == 4


# ============================================================================
# TEST: Performance
# ============================================================================

def test_performance_tracking():
    """Test that duration is tracked correctly."""
    legacy_engine = MockLegacyEngine(return_value=True)
    consensus = DualRunConsensus(
        mode=ConsensusMode.LEGACY_ONLY,
        legacy_engine=legacy_engine
    )

    block = MockBlock(index=1)
    is_valid, result = consensus.verify_block(block)

    # Should have positive duration
    assert result.duration_ms > 0
    assert result.duration_ms < 1000  # Should be fast for mock


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
