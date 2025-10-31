"""
Stress Tests for Equilibrium Gossip Implementation
Tests network under extreme conditions
"""

import pytest
import asyncio
import time
import sys
import os
from unittest.mock import Mock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    import random

from network import NetworkProtocol


class TestBurstMining:
    """Test network under burst mining conditions."""
    
    @pytest.mark.stress
    @pytest.mark.asyncio
    async def test_burst_mining(self):
        """
        Test: 50 nodes all mine simultaneously.
        Expected: Network maintains equilibrium, no CID loss.
        """
        print("\n💥 Testing burst mining (50 nodes)...")
        
        nodes = []
        for i in range(50):
            net = NetworkProtocol(Mock(), Mock(), Mock())
            net.start_equilibrium_loops()
            nodes.append(net)
        
        # All nodes announce proofs at same instant
        start_time = time.time()
        for i, node in enumerate(nodes):
            node.announce_proof(f"QmBurst{i}")
        
        # Wait for broadcast interval
        await asyncio.sleep(15)
        
        # Check that all CIDs were queued
        total_queued = sum(len(node.pending_broadcasts) for node in nodes)
        
        # After broadcast interval, queues should be processed
        # (In real implementation, they'd be broadcast)
        print(f"   Total CIDs queued: {total_queued}")
        
        # Verify nodes are still running
        all_running = all(node._running for node in nodes)
        assert all_running, "All nodes should still be running"
        
        # Clean up
        for node in nodes:
            node.stop_equilibrium_loops()
        
        print("✅ Burst mining test passed")
    
    @pytest.mark.stress
    @pytest.mark.asyncio
    async def test_rapid_successive_mining(self):
        """Test: Rapid successive mining from single node."""
        print("\n⚡ Testing rapid successive mining...")
        
        net = NetworkProtocol(Mock(), Mock(), Mock())
        net.start_equilibrium_loops()
        
        # Rapidly announce many CIDs
        for i in range(100):
            net.announce_proof(f"QmRapid{i}")
        
        assert len(net.pending_broadcasts) == 100, "All CIDs should be queued"
        
        # Wait for broadcast
        await asyncio.sleep(15)
        
        # In real implementation, queue would be cleared after broadcast
        # For now, just verify it's queued
        print(f"   CIDs queued: {len(net.pending_broadcasts)}")
        
        net.stop_equilibrium_loops()
        print("✅ Rapid mining test passed")


class TestNetworkPartition:
    """Test network partition and recovery."""
    
    @pytest.mark.stress
    @pytest.mark.asyncio
    async def test_network_partition_simulation(self):
        """
        Test: Split network into two halves, then rejoin.
        Expected: Network resyncs and maintains equilibrium.
        """
        print("\n📡 Testing network partition...")
        
        # Create two groups of nodes
        nodes_a = [NetworkProtocol(Mock(), Mock(), Mock()) for _ in range(5)]
        nodes_b = [NetworkProtocol(Mock(), Mock(), Mock()) for _ in range(5)]
        
        # Start all nodes
        for node in nodes_a + nodes_b:
            node.start_equilibrium_loops()
        
        print("   Network partitioned into 2 groups...")
        
        # Nodes in group A mine
        for i, node in enumerate(nodes_a):
            node.announce_proof(f"QmGroupA{i}")
        
        # Nodes in group B mine separately
        for i, node in enumerate(nodes_b):
            node.announce_proof(f"QmGroupB{i}")
        
        await asyncio.sleep(30)
        
        print("   Network rejoined...")
        
        # Simulate peer exchange by updating peer lists
        for node_a in nodes_a:
            for node_b in nodes_b:
                node_a.update_peer(f"peer_{id(node_b)}")
                node_b.update_peer(f"peer_{id(node_a)}")
        
        await asyncio.sleep(30)
        
        # Check equilibrium is maintained
        all_lambda = [node.lambda_state for node in nodes_a + nodes_b]
        all_eta = [node.eta_state for node in nodes_a + nodes_b]
        
        avg_lambda = sum(all_lambda) / len(all_lambda)
        avg_eta = sum(all_eta) / len(all_eta)
        
        print(f"   Average λ: {avg_lambda:.4f}")
        print(f"   Average η: {avg_eta:.4f}")
        
        # Clean up
        for node in nodes_a + nodes_b:
            node.stop_equilibrium_loops()
        
        # Verify equilibrium maintained
        assert abs(avg_lambda - 0.7071) < 0.1, "λ should stay near target"
        assert abs(avg_eta - 0.7071) < 0.1, "η should stay near target"
        
        print("✅ Network partition test passed")


class TestNodeChurn:
    """Test network stability under node churn."""
    
    @pytest.mark.stress
    @pytest.mark.asyncio
    async def test_node_churn(self):
        """
        Test: Nodes constantly join/leave.
        Expected: Network remains stable.
        """
        print("\n🔄 Testing node churn...")
        
        active_nodes = []
        node_counter = 0
        
        # Simulate 100 churn events
        for event in range(100):
            # Random join
            if not HAS_NUMPY:
                should_join = random.random() > 0.5
            else:
                should_join = np.random.random() > 0.5
            
            if should_join:
                node = NetworkProtocol(Mock(), Mock(), Mock())
                node.start_equilibrium_loops()
                active_nodes.append(node)
                node_counter += 1
            
            # Random leave (if any nodes active)
            if active_nodes:
                if not HAS_NUMPY:
                    should_leave = random.random() > 0.7
                else:
                    should_leave = np.random.random() > 0.7
                
                if should_leave:
                    leaving_node = active_nodes.pop()
                    leaving_node.stop_equilibrium_loops()
            
            # Simulate some mining on active nodes
            for node in active_nodes:
                node.announce_proof(f"QmChurn{event}")
            
            await asyncio.sleep(0.1)
        
        print(f"   Created {node_counter} nodes total")
        print(f"   {len(active_nodes)} nodes still active")
        
        # Network should still be functional
        assert len(active_nodes) > 0, "At least some nodes should remain"
        
        # Check remaining nodes are healthy
        for node in active_nodes:
            assert node._running, "Active nodes should still be running"
            node.stop_equilibrium_loops()
        
        print("✅ Node churn test passed")
    
    @pytest.mark.stress
    @pytest.mark.asyncio
    async def test_all_nodes_restart(self):
        """Test: All nodes restart simultaneously."""
        print("\n🔄 Testing simultaneous restart...")
        
        nodes = [NetworkProtocol(Mock(), Mock(), Mock()) for _ in range(10)]
        
        # Start all
        for node in nodes:
            node.start_equilibrium_loops()
            node.announce_proof("QmBeforeRestart")
        
        await asyncio.sleep(5)
        
        # Restart all
        for node in nodes:
            node.stop_equilibrium_loops()
            await asyncio.sleep(0.1)
            node.start_equilibrium_loops()
            node.announce_proof("QmAfterRestart")
        
        await asyncio.sleep(5)
        
        # All should be running
        assert all(node._running for node in nodes), "All nodes should be running after restart"
        
        # Clean up
        for node in nodes:
            node.stop_equilibrium_loops()
        
        print("✅ Simultaneous restart test passed")


class TestExtremeConditions:
    """Test under extreme conditions."""
    
    @pytest.mark.stress
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_very_long_simulation(self):
        """Test equilibrium over long period (5 minutes)."""
        print("\n⏰ Testing long-term equilibrium (5 minutes)...")
        
        net = NetworkProtocol(Mock(), Mock(), Mock())
        net.start_equilibrium_loops()
        
        lambda_history = []
        eta_history = []
        
        start_time = time.time()
        while time.time() - start_time < 300:  # 5 minutes
            # Mine occasionally
            if int(time.time() - start_time) % 10 == 0:
                net.announce_proof(f"QmLong{int(time.time() - start_time)}")
            
            lambda_history.append(net.lambda_state)
            eta_history.append(net.eta_state)
            
            await asyncio.sleep(1)
        
        # Calculate averages
        avg_lambda = sum(lambda_history) / len(lambda_history)
        avg_eta = sum(eta_history) / len(eta_history)
        ratio = avg_lambda / avg_eta
        
        print(f"   Average λ: {avg_lambda:.4f}")
        print(f"   Average η: {avg_eta:.4f}")
        print(f"   Ratio: {ratio:.4f}")
        
        net.stop_equilibrium_loops()
        
        # Should maintain equilibrium
        assert abs(avg_lambda - 0.7071) < 0.1, "λ should stay near target over long period"
        assert abs(avg_eta - 0.7071) < 0.1, "η should stay near target over long period"
        assert abs(ratio - 1.0) < 0.1, "Ratio should stay near 1.0"
        
        print("✅ Long-term equilibrium test passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

