# COINjecture Mining Authentication Guide

## Overview

COINjecture uses multiple authentication methods to ensure secure mining and prevent abuse. This guide explains how to authenticate as a miner and submit blocks to the network.

## Authentication Methods

### 1. Personal API Key (Recommended)
Each user gets a unique API key for secure authentication.

**Registration:**
```bash
curl -X POST https://api.coinjecture.com/v1/user/register \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "your_miner_id",
    "auth_method": "hmac_personal",
    "tier": "TIER_2_DESKTOP"
  }'
```

**Response:**
```json
{
  "status": "success",
  "user_id": "your_miner_id",
  "api_key": "your_unique_api_key_here",
  "auth_method": "hmac_personal",
  "tier": "TIER_2_DESKTOP",
  "instructions": {
    "authentication": "Include X-User-ID and X-Signature headers",
    "signature": "HMAC-SHA256 of canonical JSON body using your API key",
    "timestamp": "Include X-Timestamp header with current Unix timestamp"
  }
}
```

### 2. Shared Secret (Development)
For development and testing, uses a shared secret.

**Registration:**
```bash
curl -X POST https://api.coinjecture.com/v1/user/register \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "dev_miner",
    "auth_method": "hmac_shared",
    "tier": "TIER_2_DESKTOP"
  }'
```

## Authentication Process

### Step 1: Register Your Miner
First, register your mining node to get authentication credentials.

### Step 2: Generate HMAC Signature
For each request, you must generate an HMAC-SHA256 signature:

```python
import hmac
import hashlib
import json
import time

def generate_signature(api_key, payload):
    # Canonicalize JSON (sorted keys, no spaces)
    canonical = json.dumps(payload, sort_keys=True, separators=(',', ':'))
    
    # Generate HMAC-SHA256 signature
    signature = hmac.new(
        api_key.encode('utf-8'),
        canonical.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return signature

# Example usage
api_key = "your_api_key_here"
payload = {
    "event_id": "unique_event_id",
    "block_index": 1,
    "block_hash": "block_hash_here",
    "cid": "ipfs_cid_here",
    "miner_id": "your_miner_id",
    "capacity": "TIER_2_DESKTOP",
    "work_score": 1.0,
    "ts": time.time(),
    "signature": "placeholder"
}

signature = generate_signature(api_key, payload)
```

### Step 3: Include Required Headers
Every request must include these headers:

```python
headers = {
    'X-User-ID': 'your_miner_id',
    'X-Signature': signature,
    'X-Timestamp': str(int(time.time())),
    'Content-Type': 'application/json'
}
```

### Step 4: Submit Block
Submit your mined block with proper authentication:

```python
import requests

response = requests.post(
    'https://api.coinjecture.com/v1/ingest/block',
    json=payload,
    headers=headers,
    timeout=10
)

if response.status_code == 202:
    print("Block successfully submitted!")
    print(f"User: {response.json().get('user_id')}")
    print(f"Tier: {response.json().get('tier')}")
else:
    print(f"Submission failed: {response.status_code}")
    print(f"Error: {response.text}")
```

## User Management

### Check Your Profile
```bash
curl https://api.coinjecture.com/v1/user/profile/your_miner_id
```

### Update Your Tier
```bash
curl -X POST https://api.coinjecture.com/v1/user/update-tier \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "your_miner_id",
    "tier": "TIER_3_WORKSTATION"
  }'
```

### Test Authentication
```bash
curl -X POST https://api.coinjecture.com/v1/user/auth-test \
  -H "Content-Type: application/json" \
  -H "X-User-ID: your_miner_id" \
  -H "X-Signature: your_signature" \
  -H "X-Timestamp: $(date +%s)" \
  -d '{"test": "data"}'
```

## Security Features

1. **HMAC Authentication**: All requests must be signed with your API key
2. **Timestamp Validation**: Requests expire after 5 minutes
3. **Rate Limiting**: 10 block submissions per minute per user
4. **User Attribution**: All blocks are attributed to authenticated users
5. **Tier Management**: Users can upgrade their mining tier

## Error Codes

- `401 UNAUTHORIZED`: Invalid or missing authentication
- `403 FORBIDDEN`: User account is inactive
- `409 DUPLICATE`: Block already exists
- `422 INVALID`: Invalid block data format
- `429 TOO_MANY_REQUESTS`: Rate limit exceeded

## Best Practices

1. **Secure API Keys**: Store your API key securely, never in code
2. **Timestamp Sync**: Ensure your system clock is synchronized
3. **Error Handling**: Always check response codes and handle errors
4. **Rate Limiting**: Respect the 10 requests/minute limit
5. **User Management**: Use personal API keys for production mining

## Development vs Production

- **Development**: Use shared secret authentication for testing
- **Production**: Use personal API keys for secure mining
- **Tier Selection**: Choose appropriate tier based on your hardware capabilities

## Support

For authentication issues:
1. Check your API key is correct
2. Verify timestamp is within 5 minutes
3. Ensure JSON is properly canonicalized
4. Check user account is active
5. Verify rate limits are not exceeded
