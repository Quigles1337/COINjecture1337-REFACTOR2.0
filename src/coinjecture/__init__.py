"""
COINjecture Refactored Package
===============================

Clean architectural boundaries for consensus, proofs, and types.
"""

__version__ = "4.0.0-refactor"

from . import types
from . import proofs
from . import consensus

__all__ = ["types", "proofs", "consensus", "__version__"]
