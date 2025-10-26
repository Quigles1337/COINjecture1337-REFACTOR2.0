# Network Stalling Fix - Deployment Guide

## 🚨 CRITICAL: Network Stuck at Block #166

The COINjecture network is currently stalled at block #166 due to signature validation errors. This guide provides the exact steps to deploy the fix.

## 🔍 Root Cause

- **Signature Validation Too Strict**: `verify_block_signature()` method crashes on invalid hex strings
- **Block Submission Failing**: New blocks cannot be submitted due to "Invalid signature" errors
- **Network Flow Blocked**: Consensus service cannot process new events

## 🔧 Fix Implemented

Enhanced `src/tokenomics/wallet.py` with:
- Proper hex string validation before `bytes.fromhex()` calls
- Length validation for Ed25519 keys (64 chars) and signatures (128 chars)
- Graceful error handling instead of crashes

## 📋 Deployment Steps

### Step 1: Copy Enhanced wallet.py to Remote Server

```bash
# Copy the enhanced wallet.py to remote server
scp /tmp/coinjecture_deploy/wallet.py coinjecture@167.172.213.70:/tmp/wallet_enhanced.py
```

### Step 2: SSH to Remote Server

```bash
ssh coinjecture@167.172.213.70
```

### Step 3: Apply Fix on Remote Server

```bash
# Backup original wallet.py
sudo cp /home/coinjecture/COINjecture/src/tokenomics/wallet.py /home/coinjecture/COINjecture/src/tokenomics/wallet.py.backup

# Apply enhanced wallet.py
sudo cp /tmp/wallet_enhanced.py /home/coinjecture/COINjecture/src/tokenomics/wallet.py

# Set correct permissions
sudo chown coinjecture:coinjecture /home/coinjecture/COINjecture/src/tokenomics/wallet.py

# Restart API service
sudo systemctl restart coinjecture-api.service

# Check service status
sudo systemctl status coinjecture-api.service
```

### Step 4: Test the Fix

```bash
# Test API connectivity
curl -k https://167.172.213.70/v1/data/block/latest

# Test block submission (should work now)
curl -k -X POST https://167.172.213.70/v1/ingest/block \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "test_block_167_'$(date +%s)'",
    "block_index": 167,
    "block_hash": "test_block_167_'$(date +%s)'",
    "cid": "QmTestBlock167'$(date +%s)'",
    "miner_address": "test-miner-167",
    "capacity": "MOBILE",
    "work_score": 1.0,
    "ts": '$(date +%s)',
    "signature": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "public_key": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
  }'
```

## ✅ Success Criteria

- [ ] API service restarts successfully
- [ ] Block submission returns 200 status (not 401)
- [ ] Network advances beyond block #166
- [ ] New blocks can be submitted and processed

## 🔍 Verification Commands

```bash
# Check current block
curl -k https://167.172.213.70/v1/data/block/latest | python3 -c "import sys, json; data=json.load(sys.stdin); print(f'Current block: #{data[\"data\"][\"index\"]}')"

# Check API service status
sudo systemctl status coinjecture-api.service

# Check API logs for errors
sudo journalctl -u coinjecture-api.service -f
```

## 🚨 If Deployment Fails

1. **Restore backup**: `sudo cp /home/coinjecture/COINjecture/src/tokenomics/wallet.py.backup /home/coinjecture/COINjecture/src/tokenomics/wallet.py`
2. **Restart service**: `sudo systemctl restart coinjecture-api.service`
3. **Check logs**: `sudo journalctl -u coinjecture-api.service -n 50`

## 📊 Expected Results

After successful deployment:
- Network will advance beyond block #166
- New block submissions will be accepted
- Signature validation errors will be handled gracefully
- Network flow will be restored

---

**Status**: Ready for deployment
**Priority**: CRITICAL - Network is stalled
**ETA**: 5-10 minutes after deployment



