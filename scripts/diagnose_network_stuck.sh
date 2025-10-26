#!/bin/bash
# Network Stuck at Block #166 - Comprehensive Diagnostic Script
# Run this on the droplet to identify why blocks aren't advancing

echo "🔍 DIAGNOSTIC ANALYSIS: Why Network Stuck at Block #166"
echo "====================================================="
echo "📊 Running comprehensive diagnostics to identify the root cause"
echo ""

# Check if we're on the droplet
if [ ! -f "/home/coinjecture/COINjecture/src/tokenomics/wallet.py" ]; then
    echo "❌ This script must be run on the droplet (167.172.213.70)"
    echo "📋 Please access the droplet console and run this script"
    exit 1
fi

echo "✅ Confirmed on droplet"
echo "📊 Current time: $(date)"
echo ""

# Navigate to COINjecture directory
cd /home/coinjecture/COINjecture

echo "🔍 DIAGNOSTIC 1: Check Active Miners"
echo "===================================="
echo "Checking if any miners are actually working..."

# Check active miners
echo "📊 Active miners:"
curl -k https://167.172.213.70/v1/data/miners/active 2>/dev/null || echo "❌ No miners endpoint"

echo ""
echo "📊 Mining stats:"
curl -k https://167.172.213.70/v1/data/mining/stats 2>/dev/null || echo "❌ No mining stats endpoint"

echo ""
echo "📊 Network stats:"
curl -k https://167.172.213.70/v1/data/network/stats 2>/dev/null || echo "❌ No network stats endpoint"

echo ""
echo "🔍 DIAGNOSTIC 2: Check Pending Submissions"
echo "==========================================="
echo "Checking if there are submissions waiting to be processed..."

# Check pending submissions
echo "📊 Pending submissions:"
curl -k https://167.172.213.70/v1/data/submissions/pending 2>/dev/null || echo "❌ No pending submissions endpoint"

echo ""
echo "📊 Recent submissions:"
curl -k https://167.172.213.70/v1/data/submissions/recent 2>/dev/null || echo "❌ No recent submissions endpoint"

echo ""
echo "📊 Submission count:"
curl -k https://167.172.213.70/v1/data/submissions/count 2>/dev/null || echo "❌ No submission count endpoint"

echo ""
echo "🔍 DIAGNOSTIC 3: Check Consensus Service Logs"
echo "============================================="
echo "Checking consensus service logs for errors and peer discovery..."

echo "📊 Recent consensus logs (last 50 lines):"
sudo tail -n 50 /home/coinjecture/COINjecture/logs/consensus_service.log 2>/dev/null || echo "❌ No consensus logs found"

echo ""
echo "📊 Consensus logs with peer/discovery info:"
sudo tail -n 100 /home/coinjecture/COINjecture/logs/consensus_service.log | grep -i "peer\|discovered\|connected\|error\|failed" || echo "❌ No peer discovery logs found"

echo ""
echo "🔍 DIAGNOSTIC 4: Check System Services"
echo "======================================"
echo "Checking if mining and consensus services are running..."

echo "📊 Consensus service status:"
sudo systemctl status coinjecture-consensus.service --no-pager -l | head -10

echo ""
echo "📊 Mining service status:"
sudo systemctl status coinjecture-mining 2>/dev/null || echo "❌ No mining service found"

echo ""
echo "📊 Active mining processes:"
ps aux | grep -i mine | grep -v grep || echo "❌ No mining processes found"

echo ""
echo "🔍 DIAGNOSTIC 5: Check Problem Registry"
echo "======================================"
echo "Checking if there are problems for miners to solve..."

echo "📊 Problems directory:"
ls -la /home/coinjecture/COINjecture/data/problems/ 2>/dev/null || echo "❌ No problems directory found"

echo ""
echo "📊 Blockchain database:"
if [ -f "/home/coinjecture/COINjecture/data/blockchain.db" ]; then
    echo "✅ Blockchain database exists"
    sqlite3 /home/coinjecture/COINjecture/data/blockchain.db "SELECT height, timestamp, hash FROM blocks ORDER BY height DESC LIMIT 10;" 2>/dev/null || echo "❌ Cannot query blockchain database"
else
    echo "❌ No blockchain database found"
fi

echo ""
echo "🔍 DIAGNOSTIC 6: Check Ingest Database"
echo "====================================="
echo "Checking the ingest database for pending submissions..."

if [ -f "/home/coinjecture/COINjecture/data/faucet_ingest.db" ]; then
    echo "✅ Ingest database exists"
    echo "📊 Recent block events:"
    sqlite3 /home/coinjecture/COINjecture/data/faucet_ingest.db "SELECT event_id, block_index, miner_address, work_score, ts FROM block_events ORDER BY ts DESC LIMIT 10;" 2>/dev/null || echo "❌ Cannot query ingest database"
    
    echo ""
    echo "📊 Total block events:"
    sqlite3 /home/coinjecture/COINjecture/data/faucet_ingest.db "SELECT COUNT(*) as total_events FROM block_events;" 2>/dev/null || echo "❌ Cannot count events"
    
    echo ""
    echo "📊 Events beyond block 166:"
    sqlite3 /home/coinjecture/COINjecture/data/faucet_ingest.db "SELECT COUNT(*) as events_beyond_166 FROM block_events WHERE block_index > 166;" 2>/dev/null || echo "❌ Cannot query events beyond 166"
else
    echo "❌ No ingest database found"
fi

echo ""
echo "🔍 DIAGNOSTIC 7: Check Current Network Status"
echo "============================================="
echo "Checking current network status and block height..."

echo "📊 Current block:"
curl -k https://167.172.213.70/v1/data/block/latest 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    current_block = data['data']['index']
    print(f'🌐 Current Block: #{current_block}')
    print(f'📊 Hash: {data[\"data\"][\"block_hash\"][:16]}...')
    print(f'💪 Work Score: {data[\"data\"][\"cumulative_work_score\"]}')
    print(f'⏰ Timestamp: {data[\"data\"][\"timestamp\"]}')
    
    if current_block > 166:
        print(f'✅ SUCCESS: Network advanced beyond #166!')
        print(f'📈 Block height increased by {current_block - 166} blocks')
    else:
        print(f'❌ Network still stuck at #{current_block}')
        
except Exception as e:
    print(f'❌ Error checking network: {e}')
"

echo ""
echo "📊 All blocks count:"
curl -k https://167.172.213.70/v1/data/blocks/all 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    blocks = data['data']
    indices = [b['index'] for b in blocks]
    print(f'Total blocks: {len(blocks)}')
    print(f'Unique indices: {len(set(indices))}')
    print(f'Latest index: {max(indices) if indices else \"None\"}')
    
    # Check for duplicates
    from collections import Counter
    index_counts = Counter(indices)
    duplicates = {idx: count for idx, count in index_counts.items() if count > 1}
    if duplicates:
        print(f'⚠️  Duplicate indices found: {duplicates}')
    else:
        print(f'✅ No duplicate indices')
        
except Exception as e:
    print(f'❌ Error analyzing blocks: {e}')
"

echo ""
echo "🔍 DIAGNOSTIC 8: Check P2P Discovery Status"
echo "==========================================="
echo "Checking if P2P discovery is working and finding peers..."

echo "📊 Systemd journal for consensus service:"
sudo journalctl -u coinjecture-consensus -n 50 | grep -i "peer\|discovered\|connected\|p2p" || echo "❌ No P2P discovery logs found"

echo ""
echo "📊 Check if P2P discovery service is running:"
ps aux | grep -i "p2p\|discovery" | grep -v grep || echo "❌ No P2P discovery processes found"

echo ""
echo "🔍 DIAGNOSTIC 9: Check API Endpoints"
echo "==================================="
echo "Testing all available API endpoints..."

echo "📊 Available endpoints test:"
for endpoint in "v1/data/block/latest" "v1/data/blocks/all" "v1/data/miners/active" "v1/data/mining/stats" "v1/data/network/stats" "v1/data/submissions/pending" "v1/data/submissions/recent" "v1/data/submissions/count"; do
    echo -n "Testing $endpoint: "
    curl -k -s -o /dev/null -w "%{http_code}" https://167.172.213.70/$endpoint
    echo ""
done

echo ""
echo "🎯 DIAGNOSTIC SUMMARY"
echo "===================="
echo "📊 Key findings from diagnostics:"
echo "1. Check if miners are active and working"
echo "2. Check if there are pending submissions to process"
echo "3. Check consensus logs for errors or peer discovery issues"
echo "4. Check if problem registry has problems to solve"
echo "5. Check if blockchain database is accessible"
echo "6. Check if ingest database has unprocessed events"
echo "7. Check current network status and block height"
echo "8. Check P2P discovery status and peer connections"
echo "9. Check API endpoint availability"
echo ""
echo "🔧 Next steps based on findings:"
echo "- If no miners: Start mining services"
echo "- If no problems: Generate problems for miners"
echo "- If submissions pending: Check consensus processing"
echo "- If consensus errors: Fix consensus service"
echo "- If no peers: Fix P2P discovery"
echo "- If API errors: Check API service"
echo ""
echo "📋 Run this script and analyze the output to identify the root cause!"



