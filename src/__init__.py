"""
COINjecture v3: Utility-Based Computational Work Blockchain

Built on Satoshi's foundation. Evolved with complexity theory. Driven by real-world utility.
"""

__version__ = "3.9.16"
__author__ = "COINjecture"
__license__ = "MIT"

# Import CLI for easy access
from .cli import COINjectureCLI, main

# Import metrics engine for architecture compliance
from .metrics_engine import (
    MetricsEngine,
    ComputationalComplexity,
    NetworkState,
    SATOSHI_CONSTANT,
    get_metrics_engine
)

__all__ = [
    'COINjectureCLI', 
    'main',
    'MetricsEngine',
    'ComputationalComplexity', 
    'NetworkState',
    'SATOSHI_CONSTANT',
    'get_metrics_engine'
]
