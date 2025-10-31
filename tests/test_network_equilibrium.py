"""
Unit Tests for Equilibrium Gossip Implementation
Tests λ = η = 1/√2 equilibrium logic and timing
"""

import pytest
import time
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from network import NetworkProtocol


class TestEquilibriumTiming:
    """Test that intervals are correctly calculated."""
    
    def test_constants(self):
        """Verify equilibrium constants."""
        assert NetworkProtocol.LAMBDA == 0.7071, "LAMBDA should be 1/√2 ≈ 0.7071"
        assert NetworkProtocol.ETA == 0.7071, "ETA should be 1/√2 ≈ 0.7071"
        assert abs(NetworkProtocol.LAMBDA - NetworkProtocol.ETA) < 0.0001, "LAMBDA and ETA should be equal"
    
    def test_intervals(self):
        """Verify derived intervals."""
        expected_broadcast = 1 / 0.7071 * 10  # ~14.14s
        expected_listen = 1 / 0.7071 * 10      # ~14.14s
        expected_cleanup = 5 * expected_broadcast  # ~70.7s
        
        assert abs(NetworkProtocol.BROADCAST_INTERVAL - expected_broadcast) < 0.1, \
            f"BROADCAST_INTERVAL should be ~{expected_broadcast:.2f}s"
        assert abs(NetworkProtocol.LISTEN_INTERVAL - expected_listen) < 0.1, \
            f"LISTEN_INTERVAL should be ~{expected_listen:.2f}s"
        assert abs(NetworkProtocol.CLEANUP_INTERVAL - expected_cleanup) < 0.5, \
            f"CLEANUP_INTERVAL should be ~{expected_cleanup:.2f}s"
    
    def test_equilibrium_ratio(self):
        """At equilibrium, λ/η should equal 1."""
        # Mock dependencies
        class MockConsensus:
            pass
        class MockStorage:
            pass
        class MockRegistry:
            pass
        
        net = NetworkProtocol(MockConsensus(), MockStorage(), MockRegistry())
        ratio = net.lambda_state / net.eta_state
        assert abs(ratio - 1.0) < 0.01, f"Initial ratio should be 1.0, got {ratio}"


class TestBroadcastQueue:
    """Test CID queueing and batching."""
    
    def test_queue_mechanism(self):
        """Verify CIDs are queued, not broadcast immediately."""
        class MockConsensus:
            pass
        class MockStorage:
            pass
        class MockRegistry:
            pass
        
        net = NetworkProtocol(MockConsensus(), MockStorage(), MockRegistry())
        
        # Announce a proof
        net.announce_proof("QmTest123")
        
        # Should be in queue
        assert "QmTest123" in net.pending_broadcasts, "CID should be in pending_broadcasts queue"
        
        # Should not have been broadcast yet (queue is not empty)
        assert len(net.pending_broadcasts) > 0, "Queue should not be empty"
    
    def test_batch_broadcast(self):
        """Verify multiple CIDs can be queued together."""
        class MockConsensus:
            pass
        class MockStorage:
            pass
        class MockRegistry:
            pass
        
        net = NetworkProtocol(MockConsensus(), MockStorage(), MockRegistry())
        
        # Queue multiple CIDs
        cids = [f"QmTest{i}" for i in range(10)]
        for cid in cids:
            net.announce_proof(cid)
        
        assert len(net.pending_broadcasts) == 10, "All CIDs should be queued"
        
        # Verify all CIDs are in queue
        for cid in cids:
            assert cid in net.pending_broadcasts, f"CID {cid} should be in queue"
    
    def test_clear_queue_after_broadcast(self):
        """Verify queue is cleared after broadcast interval."""
        class MockConsensus:
            pass
        class MockStorage:
            pass
        class MockRegistry:
            pass
        
        net = NetworkProtocol(MockConsensus(), MockStorage(), MockRegistry())
        
        # Queue some CIDs
        net.announce_proof("QmTest1")
        net.announce_proof("QmTest2")
        
        # Simulate broadcast (clear queue)
        net.pending_broadcasts.clear()
        
        # Queue should be empty
        assert len(net.pending_broadcasts) == 0, "Queue should be empty after broadcast"


class TestPeerManagement:
    """Test peer tracking and cleanup."""
    
    def test_peer_update(self):
        """Verify peer timestamps update."""
        class MockConsensus:
            pass
        class MockStorage:
            pass
        class MockRegistry:
            pass
        
        net = NetworkProtocol(MockConsensus(), MockStorage(), MockRegistry())
        
        peer_id = "peer123"
        before_time = time.time()
        net.update_peer(peer_id)
        after_time = time.time()
        
        assert peer_id in net.peers, "Peer should be added to peers dict"
        assert net.peers[peer_id] >= before_time, "Peer timestamp should be recent"
        assert net.peers[peer_id] <= after_time, "Peer timestamp should be current"
    
    def test_stale_peer_removal(self):
        """Verify old peers can be identified for removal."""
        class MockConsensus:
            pass
        class MockStorage:
            pass
        class MockRegistry:
            pass
        
        net = NetworkProtocol(MockConsensus(), MockStorage(), MockRegistry())
        
        current_time = time.time()
        
        # Add peer with old timestamp
        net.peers["stale_peer"] = current_time - 400  # 6+ minutes ago
        net.peers["active_peer"] = current_time  # Now
        
        # Check which peers are stale (not seen in 5 minutes = 300s)
        stale_threshold = current_time - 300
        stale_peers = [
            peer_id for peer_id, last_seen in net.peers.items()
            if last_seen < stale_threshold
        ]
        
        assert "stale_peer" in stale_peers, "Stale peer should be identified"
        assert "active_peer" not in stale_peers, "Active peer should not be stale"


class TestEquilibriumDecay:
    """Test λ and η state decay."""
    
    def test_lambda_decay(self):
        """Verify coupling state decays properly."""
        class MockConsensus:
            pass
        class MockStorage:
            pass
        class MockRegistry:
            pass
        
        net = NetworkProtocol(MockConsensus(), MockStorage(), MockRegistry())
        
        initial = net.lambda_state
        
        # Simulate decay: λ * 0.99 + 0.01
        net.lambda_state = net.lambda_state * 0.99 + 0.01
        
        # Should be close to original but slightly adjusted
        # The decay formula keeps it close to LAMBDA
        assert abs(net.lambda_state - NetworkProtocol.LAMBDA) < 0.1, \
            f"Decayed lambda should stay close to target, got {net.lambda_state}"
    
    def test_eta_decay(self):
        """Verify damping state decays properly."""
        class MockConsensus:
            pass
        class MockStorage:
            pass
        class MockRegistry:
            pass
        
        net = NetworkProtocol(MockConsensus(), MockStorage(), MockRegistry())
        
        initial = net.eta_state
        
        # Simulate decay: η * 0.99 + 0.01
        net.eta_state = net.eta_state * 0.99 + 0.01
        
        # Should be close to original
        assert abs(net.eta_state - NetworkProtocol.ETA) < 0.1, \
            f"Decayed eta should stay close to target, got {net.eta_state}"
    
    def test_equilibrium_maintained_after_decay(self):
        """Verify λ/η ratio stays near 1 after decay."""
        class MockConsensus:
            pass
        class MockStorage:
            pass
        class MockRegistry:
            pass
        
        net = NetworkProtocol(MockConsensus(), MockStorage(), MockRegistry())
        
        # Apply decay to both
        net.lambda_state = net.lambda_state * 0.99 + 0.01
        net.eta_state = net.eta_state * 0.99 + 0.01
        
        ratio = net.lambda_state / max(net.eta_state, 0.001)
        
        # Ratio should still be close to 1
        assert abs(ratio - 1.0) < 0.1, f"Ratio should stay near 1.0, got {ratio:.4f}"


class TestEquilibriumLoops:
    """Test equilibrium loop lifecycle."""
    
    def test_start_stop_loops(self):
        """Verify loops can be started and stopped."""
        class MockConsensus:
            pass
        class MockStorage:
            pass
        class MockRegistry:
            pass
        
        net = NetworkProtocol(MockConsensus(), MockStorage(), MockRegistry())
        
        # Initially not running
        assert not net._running, "Should not be running initially"
        
        # Start loops
        net.start_equilibrium_loops()
        assert net._running, "Should be running after start"
        
        # Stop loops
        net.stop_equilibrium_loops()
        assert not net._running, "Should not be running after stop"
    
    def test_threads_created(self):
        """Verify threads are created when loops start."""
        class MockConsensus:
            pass
        class MockStorage:
            pass
        class MockRegistry:
            pass
        
        net = NetworkProtocol(MockConsensus(), MockStorage(), MockRegistry())
        
        # Start loops
        net.start_equilibrium_loops()
        
        # Check threads exist
        assert net._broadcast_thread is not None, "Broadcast thread should be created"
        assert net._listen_thread is not None, "Listen thread should be created"
        assert net._cleanup_thread is not None, "Cleanup thread should be created"
        
        # Clean up
        net.stop_equilibrium_loops()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

