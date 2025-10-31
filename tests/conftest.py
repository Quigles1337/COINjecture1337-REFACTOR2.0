"""
Pytest configuration and fixtures for equilibrium tests
"""

import pytest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture
def mock_network_protocol():
    """Create a NetworkProtocol instance with mocked dependencies."""
    class MockConsensus:
        pass
    
    class MockStorage:
        pass
    
    class MockRegistry:
        pass
    
    from network import NetworkProtocol
    
    return NetworkProtocol(MockConsensus(), MockStorage(), MockRegistry())

