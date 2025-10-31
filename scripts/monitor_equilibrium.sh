#!/bin/bash
# Monitor Equilibrium Status
# Watch for equilibrium stabilization and CID improvements

echo "⚖️  Equilibrium Monitoring Dashboard"
echo "===================================="
echo ""

DROPLET_IP="167.172.213.70"
DROPLET_USER="root"

echo "📊 Current Status:"
echo ""

# Check IPFS
echo "🌐 IPFS Status:"
if ssh $DROPLET_USER@$DROPLET_IP "curl -s --connect-timeout 5 http://localhost:5001/api/v0/version > /dev/null 2>&1"; then
    VERSION=$(ssh $DROPLET_USER@$DROPLET_IP "curl -s http://localhost:5001/api/v0/version" 2>/dev/null | grep -o '"Version":"[^"]*"' | cut -d'"' -f4 || echo "unknown")
    echo "   ✅ IPFS daemon running (version: $VERSION)"
else
    echo "   ❌ IPFS daemon not available"
    echo "      Run: ssh $DROPLET_USER@$DROPLET_IP 'cd /opt/coinjecture && ipfs daemon > logs/ipfs.log 2>&1 &'"
fi
echo ""

# Check recent CID rate
echo "📡 Recent CID Success Rate:"
ssh $DROPLET_USER@$DROPLET_IP "cd /opt/coinjecture && python3 -c \"
import sqlite3
import json

db_path = 'data/blockchain.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute('SELECT height, block_bytes FROM blocks ORDER BY height DESC LIMIT 100')
blocks = cursor.fetchall()

recent_with_cid = 0
for height, block_bytes in blocks:
    try:
        if block_bytes:
            block_data = json.loads(block_bytes.decode('utf-8') if isinstance(block_bytes, bytes) else block_bytes)
            if block_data.get('cid') or block_data.get('offchain_cid'):
                recent_with_cid += 1
    except:
        pass

rate = (recent_with_cid / len(blocks) * 100) if blocks else 0
print(f'   Last 100 blocks: {recent_with_cid}/{len(blocks)} with CID ({rate:.1f}%)')
print(f'   Target: >=90%')
if rate >= 90:
    print('   ✅ CID rate is good')
elif rate >= 75:
    print('   ⚠️  CID rate improving')
else:
    print('   ⏳ CID rate still low - waiting for equilibrium to stabilize')

conn.close()
\" 2>&1"
echo ""

# Check block intervals
echo "⏱️  Block Intervals:"
ssh $DROPLET_USER@$DROPLET_IP "cd /opt/coinjecture && python3 -c \"
import sqlite3

db_path = 'data/blockchain.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute('SELECT height, timestamp FROM blocks ORDER BY height DESC LIMIT 100')
blocks = cursor.fetchall()

intervals = []
prev_time = None
for height, timestamp in reversed(blocks):
    if prev_time and timestamp:
        interval = timestamp - prev_time if timestamp > prev_time else 0
        if interval > 0 and interval < 3600:
            intervals.append(interval)
    prev_time = timestamp

if intervals:
    avg = sum(intervals) / len(intervals)
    target = 14.14
    deviation = abs(avg - target)
    print(f'   Average: {avg:.2f}s')
    print(f'   Target: {target:.2f}s')
    print(f'   Deviation: {deviation:.2f}s')
    if deviation < 10:
        print('   ✅ Intervals are stable')
    elif deviation < 30:
        print('   ⚠️  Intervals are close')
    else:
        print('   ⏳ Intervals need improvement')

conn.close()
\" 2>&1"
echo ""

# Check equilibrium logs
echo "⚖️  Recent Equilibrium Activity:"
RECENT_LOGS=$(ssh $DROPLET_USER@$DROPLET_IP "journalctl -u coinjecture-api --since '10 minutes ago' --no-pager 2>/dev/null | grep -i 'equilibrium\|ratio' | tail -3" 2>/dev/null)
if [ -n "$RECENT_LOGS" ]; then
    echo "$RECENT_LOGS" | sed 's/^/   /'
else
    echo "   ℹ️  No equilibrium logs in last 10 minutes"
    echo "      (May take time for loops to start broadcasting)"
fi
echo ""

# Check readiness
echo "🔍 Regeneration Readiness:"
ssh $DROPLET_USER@$DROPLET_IP "cd /opt/coinjecture && python3 scripts/check_regeneration_readiness.py --db data/blockchain.db 2>&1 | grep -A 20 'Readiness Summary' | tail -15"
echo ""

echo "📈 Monitoring Commands:"
echo "   Watch equilibrium logs:"
echo "   ssh $DROPLET_USER@$DROPLET_IP \"journalctl -u coinjecture-api -f | grep Equilibrium\""
echo ""
echo "   Check readiness anytime:"
echo "   ssh $DROPLET_USER@$DROPLET_IP \"cd /opt/coinjecture && python3 scripts/check_regeneration_readiness.py\""
echo ""

