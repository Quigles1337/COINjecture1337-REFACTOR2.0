#!/bin/bash
# Run All Equilibrium Gossip Tests

set -e

echo "🧪 COINjecture Equilibrium Gossip Test Suite"
echo "============================================"
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest not found. Install with: pip install pytest pytest-asyncio"
    exit 1
fi

echo "📋 Test Phases:"
echo "  1. Unit Tests (fast)"
echo "  2. Simulation Tests (slow, optional)"
echo "  3. Stress Tests (slow, optional)"
echo ""

# Phase 1: Unit Tests
echo "═══════════════════════════════════════════════"
echo "Phase 1: Unit Tests"
echo "═══════════════════════════════════════════════"
pytest tests/test_network_equilibrium.py -v --tb=short
UNIT_RESULT=$?

if [ $UNIT_RESULT -eq 0 ]; then
    echo "✅ Unit tests passed"
else
    echo "❌ Unit tests failed"
    exit 1
fi
echo ""

# Phase 2: Simulation Tests (optional)
read -p "Run simulation tests? (may take 1-2 minutes) [y/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "═══════════════════════════════════════════════"
    echo "Phase 2: Simulation Tests"
    echo "═══════════════════════════════════════════════"
    pytest tests/test_network_simulation.py -v -m simulation --tb=short || {
        echo "⚠️  Simulation tests failed or skipped (may need numpy/matplotlib)"
    }
    echo ""
fi

# Phase 3: Stress Tests (optional)
read -p "Run stress tests? (may take 2-5 minutes) [y/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "═══════════════════════════════════════════════"
    echo "Phase 3: Stress Tests"
    echo "═══════════════════════════════════════════════"
    pytest tests/test_network_stress.py -v -m stress --tb=short || {
        echo "⚠️  Stress tests failed or skipped"
    }
    echo ""
fi

echo "═══════════════════════════════════════════════"
echo "✅ Test Suite Complete"
echo "═══════════════════════════════════════════════"
echo ""
echo "📊 Next Steps:"
echo "  1. Review test results above"
echo "  2. Check for equilibrium_simulation.png if matplotlib is available"
echo "  3. Run production test plan when ready for deployment"
echo ""

