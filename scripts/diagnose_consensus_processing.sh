#!/bin/bash
# Diagnose Consensus Service Processing
# This script identifies why the consensus service isn't processing accepted blocks

echo "🔍 CONSENSUS SERVICE PROCESSING DIAGNOSIS"
echo "========================================="
echo "📊 Issue: Blocks accepted but consensus not processing them"
echo "🎯 Goal: Identify why consensus service isn't converting accepted blocks"
echo ""

# Check if we're on the droplet
if [ ! -f "/home/coinjecture/COINjecture/src/tokenomics/wallet.py" ]; then
    echo "❌ This script must be run on the droplet (167.172.213.70)"
    exit 1
fi

echo "✅ Confirmed on droplet"
cd /home/coinjecture/COINjecture

# Step 1: Check consensus service logs for recent activity
echo ""
echo "📊 Step 1: Checking consensus service logs for recent activity..."
echo "📊 Recent consensus logs (last 50 lines):"
sudo tail -n 50 /home/coinjecture/COINjecture/logs/consensus_service.log

# Step 2: Check if consensus service is actually running the new code
echo ""
echo "📊 Step 2: Checking if consensus service is running the new code..."
echo "📊 Consensus service process details:"
ps aux | grep consensus_service | grep -v grep

# Step 3: Check ingest database for new events
echo ""
echo "📊 Step 3: Checking ingest database for new events..."
echo "📊 Recent block events in ingest database:"
sqlite3 /home/coinjecture/COINjecture/data/faucet_ingest.db "SELECT event_id, block_index, miner_address, work_score, ts FROM block_events ORDER BY ts DESC LIMIT 10;" 2>/dev/null || echo "❌ Cannot query ingest database"

# Step 4: Check if consensus service is reading from the right database
echo ""
echo "📊 Step 4: Checking consensus service database configuration..."
echo "📊 Consensus service working directory:"
sudo systemctl show coinjecture-consensus.service --property=WorkingDirectory --value

echo "📊 Consensus service executable:"
sudo systemctl show coinjecture-consensus.service --property=ExecStart --value

# Step 5: Check if there are any errors in consensus service
echo ""
echo "📊 Step 5: Checking for consensus service errors..."
echo "📊 Recent consensus service errors:"
sudo tail -n 100 /home/coinjecture/COINjecture/logs/consensus_service.log | grep -i "error\|exception\|failed" || echo "❌ No errors found in recent logs"

# Step 6: Check if consensus service is actually processing events
echo ""
echo "📊 Step 6: Checking if consensus service is processing events..."
echo "📊 Consensus service activity in last 10 minutes:"
sudo tail -n 200 /home/coinjecture/COINjecture/logs/consensus_service.log | grep -E "$(date '+%Y-%m-%d %H:%M')" || echo "❌ No activity in last 10 minutes"

# Step 7: Check blockchain state file
echo ""
echo "📊 Step 7: Checking blockchain state file..."
echo "📊 Blockchain state file location:"
ls -la /home/coinjecture/COINjecture/data/blockchain_state.json 2>/dev/null || echo "❌ Blockchain state file not found"

echo "📊 Blockchain state file content:"
cat /home/coinjecture/COINjecture/data/blockchain_state.json 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'📊 Total blocks: {len(data.get(\"blocks\", []))}')
    if data.get('blocks'):
        latest = data['blocks'][-1]
        print(f'📊 Latest block: #{latest.get(\"index\", \"unknown\")}')
        print(f'📊 Latest hash: {latest.get(\"block_hash\", \"unknown\")[:16]}...')
    else:
        print('❌ No blocks in state file')
except Exception as e:
    print(f'❌ Error reading blockchain state: {e}')
"

# Step 8: Check if consensus service is using the right database path
echo ""
echo "📊 Step 8: Checking consensus service database path configuration..."
echo "📊 Looking for database path in consensus service code:"
grep -r "faucet_ingest.db" /home/coinjecture/COINjecture/src/ 2>/dev/null || echo "❌ No database path found in consensus service code"

# Step 9: Test if consensus service can access the database
echo ""
echo "📊 Step 9: Testing consensus service database access..."
echo "📊 Testing database access from consensus service directory:"
cd /opt/coinjecture 2>/dev/null && python3 -c "
import sqlite3
try:
    conn = sqlite3.connect('/home/coinjecture/COINjecture/data/faucet_ingest.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM block_events')
    count = cursor.fetchone()[0]
    print(f'✅ Database accessible: {count} events found')
    conn.close()
except Exception as e:
    print(f'❌ Database access error: {e}')
" || echo "❌ Cannot test database access"

# Step 10: Check if consensus service is actually running the enhanced version
echo ""
echo "📊 Step 10: Checking if consensus service is running enhanced version..."
echo "📊 Checking consensus service code for P2P discovery:"
grep -r "p2p_discovery\|P2PDiscoveryService" /opt/coinjecture/ 2>/dev/null || echo "❌ No P2P discovery found in consensus service"

echo ""
echo "🎯 DIAGNOSIS COMPLETE!"
echo "====================="
echo "📊 This diagnosis will help identify why consensus service isn't processing blocks"
echo "📊 Key areas to check:"
echo "1. Recent consensus service activity"
echo "2. Database accessibility"
echo "3. Code version being used"
echo "4. Configuration paths"
echo "5. Error messages"
echo ""
echo "📊 Next steps will be based on the findings above"



