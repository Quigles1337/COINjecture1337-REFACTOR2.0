# COINjecture API Documentation (v4.4.0)

**Complete REST API and WebSocket reference for the COINjecture blockchain**

---

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Authentication & Rate Limiting](#authentication--rate-limiting)
4. [Transaction Endpoints](#transaction-endpoints)
5. [Account Endpoints](#account-endpoints)
6. [Escrow Endpoints](#escrow-endpoints)
7. [Block Endpoints](#block-endpoints)
8. [WebSocket API](#websocket-api)
9. [IPFS Endpoints](#ipfs-endpoints)
10. [System Endpoints](#system-endpoints)
11. [Error Handling](#error-handling)
12. [Code Examples](#code-examples)

---

## Overview

The COINjecture API provides programmatic access to:
- **Transaction submission** and querying
- **Account** balance and nonce management
- **Escrow** creation and monitoring for bounties
- **Block** retrieval (pending consensus implementation)
- **Real-time updates** via WebSocket subscriptions
- **IPFS** content retrieval
- **System** health and metrics

**Base URL:** `http://localhost:8080` (configurable via `config.yaml`)

**API Version:** v4.4.0

**Supported Formats:** JSON

---

## Getting Started

### Prerequisites

1. **Running daemon:**
   ```bash
   ./bin/coinjectured --config config.yaml
   ```

2. **Dependencies:**
   - Go 1.21+
   - Rust consensus library (compiled with CGO)
   - SQLite 3.x
   - IPFS nodes (configured in config.yaml)

### Quick Test

```bash
# Health check
curl http://localhost:8080/health

# Daemon status
curl http://localhost:8080/v1/status

# Prometheus metrics
curl http://localhost:8080/metrics
```

---

## Authentication & Rate Limiting

### Current Status
- **Authentication:** Not yet implemented (v4.4.0)
- **Rate Limiting:** Enabled via configuration

### Rate Limiter Configuration
```yaml
rate_limiter:
  enabled: true
  requests_per_second: 100
  burst: 200
```

Rate limit headers in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1609459200
```

---

## Transaction Endpoints

### Submit Transaction

Submit a signed transaction to the mempool for propagation and inclusion in a block.

**Endpoint:** `POST /v1/transactions`

**Request Body:**
```json
{
  "from": "0x1234...abcd",          // 64-char hex (32 bytes)
  "to": "0x5678...ef01",            // 64-char hex (32 bytes)
  "amount": 1000000000000000000,   // Wei (uint64)
  "nonce": 0,                       // Account nonce (uint64)
  "gas_limit": 21000,               // Gas limit (uint64)
  "gas_price": 1000000000,          // Wei per gas (uint64)
  "signature": "0xabcd...1234",     // 128-char hex (64 bytes, Ed25519)
  "data": "0x"                      // Optional hex data
}
```

**Response (202 Accepted):**
```json
{
  "status": "accepted",
  "tx_hash": "0x9abc...def0",
  "total_cost": 1021000000000000000,
  "fee": 21000000000000,
  "gas_used": 21000
}
```

**Validation:**
1. Parses hex-encoded addresses and signature
2. Retrieves sender account state from database
3. Validates signature via Rust FFI: `bindings.VerifyTransaction()`
4. Checks nonce, balance, gas parameters
5. Adds to mempool with priority (gas_price × gas_limit)
6. Broadcasts to P2P network
7. Broadcasts to WebSocket clients

**Errors:**
- `400 Bad Request` - Invalid format or validation failed
- `500 Internal Server Error` - State manager failure

**Example:**
```bash
curl -X POST http://localhost:8080/v1/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "from": "0x' $(openssl rand -hex 32) '",
    "to": "0x' $(openssl rand -hex 32) '",
    "amount": 1000000000,
    "nonce": 0,
    "gas_limit": 21000,
    "gas_price": 1000000,
    "signature": "0x' $(openssl rand -hex 64) '"
  }'
```

---

### Query Transaction

Retrieve transaction details by hash.

**Endpoint:** `GET /v1/transactions/:hash`

**Parameters:**
- `hash` - Transaction hash (64-char hex, with or without 0x prefix)

**Response (200 OK):**
```json
{
  "status": "pending",              // "pending" or "confirmed"
  "tx_hash": "0x9abc...def0",
  "from": "0x1234...abcd",
  "to": "0x5678...ef01",
  "amount": 1000000000,
  "nonce": 0,
  "gas_limit": 21000,
  "gas_price": 1000000,
  "fee": 21000000000,
  "timestamp": 1609459200,
  "added_at": 1609459200,           // When added to mempool
  "priority": 21000000000           // Gas price × gas limit
}
```

**Errors:**
- `400 Bad Request` - Invalid hash format
- `404 Not Found` - Transaction not found

**Notes:**
- Checks mempool first for pending transactions
- Falls back to database for confirmed transactions (TODO)

---

### Mempool Statistics

Get current mempool state and top priority transactions.

**Endpoint:** `GET /v1/mempool/stats`

**Response (200 OK):**
```json
{
  "size": 42,
  "max_size": 10000,
  "utilization": 0.0042,
  "top_transactions": [
    "0x9abc1234",
    "0x5678ef90",
    "0xabcd1234"
  ]
}
```

**Top Transactions:**
- Sorted by priority (gas_price × gas_limit, descending)
- Limited to top 10
- Shows first 8 bytes of tx_hash for brevity

---

## Account Endpoints

### Get Account

Retrieve full account state.

**Endpoint:** `GET /v1/accounts/:address`

**Parameters:**
- `address` - Account address (64-char hex, with or without 0x prefix)

**Response (200 OK):**
```json
{
  "address": "0x1234...abcd",
  "balance": 1000000000000000000,  // Wei (uint64)
  "nonce": 5,                      // Transaction count
  "created_at": 1609459200,        // Unix timestamp
  "updated_at": 1609459300
}
```

**Errors:**
- `400 Bad Request` - Invalid address format
- `404 Not Found` - Account not found
- `500 Internal Server Error` - State manager failure

**Notes:**
- Accounts are created automatically on first transaction
- Initial balance is 0, nonce is 0

---

### Get Account Nonce

Retrieve just the nonce for transaction building.

**Endpoint:** `GET /v1/accounts/:address/nonce`

**Parameters:**
- `address` - Account address (64-char hex)

**Response (200 OK):**
```json
{
  "address": "0x1234...abcd",
  "nonce": 5
}
```

**Usage:**
Use this to build the next transaction:
```javascript
const nonce = await getAccountNonce(address);
const tx = buildTransaction({ ...params, nonce });
```

---

## Escrow Endpoints

### Create Escrow

Create a new bounty escrow for problem-solving incentives.

**Endpoint:** `POST /v1/escrows`

**Request Body:**
```json
{
  "submitter": "0x1234...abcd",    // 64-char hex
  "amount": 1000000000000000000,   // Wei (uint64)
  "problem_hash": "0x5678...ef01", // 64-char hex
  "expiry_block": 1100             // Block number (uint64)
}
```

**Response (201 Created):**
```json
{
  "status": "created",
  "escrow_id": "0x9abc...def0",
  "submitter": "0x1234...abcd",
  "amount": 1000000000000000000,
  "created_block": 1000,
  "expiry_block": 1100
}
```

**Validation:**
1. Parses submitter address and problem hash
2. Gets current block number (TODO: from consensus)
3. Validates via Rust FFI: `bindings.ValidateEscrowCreation()`
4. Computes deterministic escrow ID: `bindings.ComputeEscrowID()`
5. Creates escrow in state manager
6. Broadcasts event to WebSocket clients

**Errors:**
- `400 Bad Request` - Invalid parameters or validation failed
- `500 Internal Server Error` - State manager failure

**Escrow Rules:**
- Amount must be > 0
- Expiry block must be > current block
- Submitter must have sufficient balance (TODO: enforce)

---

### Query Escrow

Retrieve escrow details and state.

**Endpoint:** `GET /v1/escrows/:id`

**Parameters:**
- `id` - Escrow ID (64-char hex)

**Response (200 OK):**
```json
{
  "escrow_id": "0x9abc...def0",
  "submitter": "0x1234...abcd",
  "amount": 1000000000000000000,
  "problem_hash": "0x5678...ef01",
  "created_block": 1000,
  "expiry_block": 1100,
  "state": "locked",               // "locked", "released", or "refunded"
  "created_at": 1609459200,
  "updated_at": 1609459300,
  "recipient": "0xabcd...1234",    // If released
  "settled_block": 1050,           // If settled
  "settlement_tx": "0xef01...5678" // If settled
}
```

**Errors:**
- `400 Bad Request` - Invalid escrow ID format
- `404 Not Found` - Escrow not found

**Escrow States:**
- **locked** - Funds locked, awaiting solution
- **released** - Funds released to solver
- **refunded** - Funds returned to submitter (expired)

---

## Block Endpoints

**Note:** Block storage is not yet implemented (v4.4.0). These endpoints return placeholder responses with expected structure.

### Get Latest Block

Retrieve the most recent block.

**Endpoint:** `GET /v1/blocks/latest`

**Response (200 OK):**
```json
{
  "status": "operational",
  "message": "block storage not yet implemented",
  "hint": "latest block will be available once consensus and block persistence are added",
  "expected_fields": {
    "block_number": "uint64",
    "block_hash": "hex string",
    "parent_hash": "hex string",
    "state_root": "hex string",
    "tx_root": "hex string",
    "timestamp": "unix timestamp",
    "miner": "hex address",
    "difficulty": "uint64",
    "tx_count": "number of transactions"
  }
}
```

---

### Get Block by Number

Retrieve a block by its number.

**Endpoint:** `GET /v1/blocks/number/:number`

**Parameters:**
- `number` - Block number (uint64)

**Response (404 Not Found):**
```json
{
  "error": "block not found",
  "reason": "block storage not yet implemented",
  "hint": "blocks are propagated via P2P but not persisted to database yet"
}
```

---

### Get Block by Hash

Retrieve a block by its hash.

**Endpoint:** `GET /v1/blocks/:hash`

**Parameters:**
- `hash` - Block hash (64-char hex)

**Response (404 Not Found):**
```json
{
  "error": "block not found",
  "reason": "block storage not yet implemented",
  "hint": "blocks are propagated via P2P but not persisted to database yet"
}
```

**Future Structure:**
Once implemented, blocks will have this structure:
```json
{
  "block_number": 1000,
  "block_hash": "0x9abc...def0",
  "parent_hash": "0x1234...abcd",
  "state_root": "0x5678...ef01",
  "tx_root": "0xabcd...1234",
  "timestamp": 1609459200,
  "miner": "0xef01...5678",
  "difficulty": 1000000,
  "nonce": 123456789,
  "transactions": [
    {
      "tx_hash": "0x9999...0000",
      "from": "0x1111...2222",
      "to": "0x3333...4444",
      "amount": 1000000000,
      "gas_used": 21000
    }
  ]
}
```

---

## WebSocket API

Real-time blockchain updates via WebSocket subscriptions.

### Connection

**Endpoint:** `ws://localhost:8080/ws`

**Protocol:** WebSocket (RFC 6455)

**Example (JavaScript):**
```javascript
const ws = new WebSocket('ws://localhost:8080/ws');

ws.onopen = () => {
  console.log('Connected to COINjecture blockchain');
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Disconnected');
};
```

---

### Subscription Management

**Subscribe to topic:**
```json
{
  "action": "subscribe",
  "topic": "transactions"
}
```

**Unsubscribe from topic:**
```json
{
  "action": "unsubscribe",
  "topic": "transactions"
}
```

**Available Topics:**
- `transactions` - New transaction submissions
- `blocks` - New block propagation
- `escrows` - Escrow state changes
- `all` - All events (default subscription)

---

### Message Format

All WebSocket messages follow this structure:

```json
{
  "type": "transaction",
  "topic": "transactions",
  "payload": { ... }
}
```

**Message Types:**
- `transaction` - New transaction broadcast
- `block` - New block broadcast
- `escrow` - Escrow event
- `status` - System status update

---

### Transaction Broadcasts

Sent when a new transaction is submitted.

```json
{
  "type": "transaction",
  "topic": "transactions",
  "payload": {
    "tx_hash": "0x9abc...def0",
    "from": "0x1234...abcd",
    "to": "0x5678...ef01",
    "amount": 1000000000,
    "fee": 21000000000,
    "time": 1609459200
  }
}
```

---

### Block Broadcasts

Sent when a new block is propagated via P2P.

```json
{
  "type": "block",
  "topic": "blocks",
  "payload": {
    "block_number": 1000,
    "block_hash": "0x9abc...def0",
    "tx_count": 42,
    "time": 1609459200
  }
}
```

---

### Escrow Broadcasts

Sent when an escrow state changes.

```json
{
  "type": "escrow",
  "topic": "escrows",
  "payload": {
    "escrow_id": "0x9abc...def0",
    "event": "created",
    "data": {
      "submitter": "0x1234...abcd",
      "amount": 1000000000000000000,
      "created_block": 1000,
      "expiry_block": 1100
    },
    "time": 1609459200
  }
}
```

**Escrow Events:**
- `created` - New escrow created
- `released` - Funds released to solver
- `refunded` - Funds returned to submitter

---

### Keepalive

**Ping/Pong:**
- Server sends ping every 54 seconds
- Client must respond with pong
- Connection closed if no pong within 60 seconds

**Example (JavaScript):**
```javascript
// Most WebSocket libraries handle ping/pong automatically
// Manual handling:
ws.on('ping', () => {
  ws.pong();
});
```

---

### Complete Example

```javascript
class COINjectureClient {
  constructor(url) {
    this.ws = new WebSocket(url);
    this.handlers = {};

    this.ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (this.handlers[msg.type]) {
        this.handlers[msg.type](msg.payload);
      }
    };
  }

  on(type, handler) {
    this.handlers[type] = handler;
  }

  subscribe(topic) {
    this.ws.send(JSON.stringify({
      action: 'subscribe',
      topic: topic
    }));
  }

  unsubscribe(topic) {
    this.ws.send(JSON.stringify({
      action: 'unsubscribe',
      topic: topic
    }));
  }
}

// Usage
const client = new COINjectureClient('ws://localhost:8080/ws');

client.on('transaction', (tx) => {
  console.log('New transaction:', tx.tx_hash);
  console.log(`  ${tx.from} → ${tx.to}`);
  console.log(`  Amount: ${tx.amount} wei`);
  console.log(`  Fee: ${tx.fee} wei`);
});

client.on('block', (block) => {
  console.log('New block:', block.block_number);
  console.log(`  Hash: ${block.block_hash}`);
  console.log(`  Transactions: ${block.tx_count}`);
});

client.on('escrow', (escrow) => {
  console.log('Escrow event:', escrow.event);
  console.log(`  ID: ${escrow.escrow_id}`);
});

// Subscribe to specific topics
client.subscribe('transactions');
client.subscribe('blocks');
```

---

## IPFS Endpoints

### Get IPFS Content

Retrieve content by CID from configured IPFS nodes.

**Endpoint:** `GET /v1/ipfs/:cid`

**Parameters:**
- `cid` - IPFS Content ID (e.g., `QmXyz...abc`)

**Response (200 OK):**
- Content-Type: Determined by IPFS metadata
- Body: Raw content bytes

**Errors:**
- `404 Not Found` - CID not found on any node
- `500 Internal Server Error` - IPFS retrieval failure

**Example:**
```bash
curl http://localhost:8080/v1/ipfs/QmXyz...abc > output.bin
```

---

## System Endpoints

### Health Check

Quick health check for load balancers.

**Endpoint:** `GET /health`

**Response (200 OK):**
```json
{
  "status": "healthy"
}
```

---

### Daemon Status

Comprehensive daemon status and statistics.

**Endpoint:** `GET /v1/status`

**Response (200 OK):**
```json
{
  "api_version": "4.4.0",
  "rate_limiter": {
    "requests_per_second": 100,
    "burst": 200,
    "current_tokens": 95
  },
  "ipfs_quorum": {
    "total_nodes": 3,
    "healthy_nodes": 3,
    "quorum_size": 2
  },
  "p2p_stats": {
    "peer_id": "12D3KooWABC...XYZ",
    "peer_count": 15,
    "addrs": ["/ip4/0.0.0.0/tcp/9000"],
    "mempool_size": 42,
    "cid_queue_size": 5,
    "equilibrium_ratio": 0.7071
  },
  "mempool_size": 42
}
```

---

### Prometheus Metrics

Standard Prometheus exposition format.

**Endpoint:** `GET /metrics`

**Response (200 OK):**
```
# HELP api_requests_total Total API requests
# TYPE api_requests_total counter
api_requests_total{method="GET",endpoint="/v1/status"} 1234

# HELP p2p_peers_connected Number of connected peers
# TYPE p2p_peers_connected gauge
p2p_peers_connected 15

# HELP mempool_size Current mempool size
# TYPE mempool_size gauge
mempool_size 42
```

**Metrics Categories:**
- `api_*` - API server metrics
- `p2p_*` - P2P network metrics
- `mempool_*` - Transaction mempool metrics
- `ipfs_*` - IPFS client metrics
- `rate_limiter_*` - Rate limiting metrics

---

## Error Handling

### Standard Error Response

All errors follow this format:

```json
{
  "error": "human-readable error message",
  "details": "technical details (optional)"
}
```

### HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful GET request |
| 201 | Created | Successful POST (escrow creation) |
| 202 | Accepted | Transaction accepted to mempool |
| 400 | Bad Request | Invalid input or validation failed |
| 404 | Not Found | Resource not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side failure |
| 501 | Not Implemented | Feature not yet implemented |

### Common Errors

**Invalid hex format:**
```json
{
  "error": "invalid from address",
  "details": "hex string must be 64 characters"
}
```

**Transaction validation failed:**
```json
{
  "error": "transaction validation failed",
  "details": "insufficient balance: need 1000, have 500"
}
```

**Rate limit exceeded:**
```json
{
  "error": "rate limit exceeded",
  "details": "maximum 100 requests per second"
}
```

---

## Code Examples

### Complete Transaction Submission (JavaScript)

```javascript
const crypto = require('crypto');
const fetch = require('node-fetch');

// Generate Ed25519 keypair
const { publicKey, privateKey } = crypto.generateKeyPairSync('ed25519');

// Build transaction
const tx = {
  from: publicKey.export({ format: 'der', type: 'spki' }).toString('hex').slice(-64),
  to: '0x' + crypto.randomBytes(32).toString('hex'),
  amount: 1000000000,
  nonce: 0,
  gas_limit: 21000,
  gas_price: 1000000,
  data: '0x'
};

// Sign transaction (simplified - actual signing is more complex)
const message = Buffer.concat([
  Buffer.from(tx.from, 'hex'),
  Buffer.from(tx.to.slice(2), 'hex'),
  // ... encode all fields
]);
const signature = crypto.sign(null, message, privateKey);
tx.signature = '0x' + signature.toString('hex');

// Submit transaction
const response = await fetch('http://localhost:8080/v1/transactions', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(tx)
});

const result = await response.json();
console.log('Transaction submitted:', result.tx_hash);
console.log('Fee:', result.fee, 'wei');
```

---

### Monitor All Activity (Python)

```python
import asyncio
import websockets
import json

async def monitor_blockchain():
    uri = "ws://localhost:8080/ws"
    async with websockets.connect(uri) as websocket:
        # Subscribe to all events
        await websocket.send(json.dumps({
            "action": "subscribe",
            "topic": "all"
        }))

        print("Connected to COINjecture blockchain")
        print("Monitoring all activity...\n")

        async for message in websocket:
            msg = json.loads(message)

            if msg['type'] == 'transaction':
                tx = msg['payload']
                print(f"[TX] {tx['tx_hash'][:10]}...")
                print(f"     {tx['from'][:10]}... → {tx['to'][:10]}...")
                print(f"     Amount: {tx['amount']} wei, Fee: {tx['fee']} wei\n")

            elif msg['type'] == 'block':
                blk = msg['payload']
                print(f"[BLOCK] #{blk['block_number']}")
                print(f"        Hash: {blk['block_hash'][:10]}...")
                print(f"        Transactions: {blk['tx_count']}\n")

            elif msg['type'] == 'escrow':
                esc = msg['payload']
                print(f"[ESCROW] {esc['event'].upper()}")
                print(f"         ID: {esc['escrow_id'][:10]}...\n")

asyncio.get_event_loop().run_until_complete(monitor_blockchain())
```

---

### Query Account and Submit Transaction (Go)

```go
package main

import (
    "bytes"
    "encoding/json"
    "fmt"
    "net/http"
)

type Account struct {
    Address string `json:"address"`
    Balance uint64 `json:"balance"`
    Nonce   uint64 `json:"nonce"`
}

type Transaction struct {
    From      string `json:"from"`
    To        string `json:"to"`
    Amount    uint64 `json:"amount"`
    Nonce     uint64 `json:"nonce"`
    GasLimit  uint64 `json:"gas_limit"`
    GasPrice  uint64 `json:"gas_price"`
    Signature string `json:"signature"`
    Data      string `json:"data"`
}

func getAccountNonce(address string) (uint64, error) {
    resp, err := http.Get(fmt.Sprintf("http://localhost:8080/v1/accounts/%s/nonce", address))
    if err != nil {
        return 0, err
    }
    defer resp.Body.Close()

    var result struct {
        Nonce uint64 `json:"nonce"`
    }

    if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
        return 0, err
    }

    return result.Nonce, nil
}

func submitTransaction(tx *Transaction) (string, error) {
    body, err := json.Marshal(tx)
    if err != nil {
        return "", err
    }

    resp, err := http.Post(
        "http://localhost:8080/v1/transactions",
        "application/json",
        bytes.NewBuffer(body),
    )
    if err != nil {
        return "", err
    }
    defer resp.Body.Close()

    var result struct {
        TxHash string `json:"tx_hash"`
    }

    if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
        return "", err
    }

    return result.TxHash, nil
}

func main() {
    address := "0x1234..." // Your address

    // Get current nonce
    nonce, err := getAccountNonce(address)
    if err != nil {
        panic(err)
    }

    // Build transaction
    tx := &Transaction{
        From:     address,
        To:       "0x5678...",
        Amount:   1000000000,
        Nonce:    nonce,
        GasLimit: 21000,
        GasPrice: 1000000,
        Signature: "0xabcd...", // Sign with private key
        Data:     "0x",
    }

    // Submit transaction
    txHash, err := submitTransaction(tx)
    if err != nil {
        panic(err)
    }

    fmt.Printf("Transaction submitted: %s\n", txHash)
}
```

---

## Next Steps

### Upcoming Features (v4.5.0+)

- **Block Storage:** Persistent block database
- **Transaction History:** Account transaction logs
- **Authentication:** API key or JWT-based auth
- **Advanced Queries:** Range queries, filtering, pagination
- **GraphQL API:** Alternative to REST
- **Escrow Release/Refund:** Complete escrow lifecycle
- **Consensus Integration:** Real block production

### SDK Support

Official SDKs planned:
- JavaScript/TypeScript
- Python
- Go
- Rust

### Getting Help

- **Issues:** https://github.com/Quigles1337/COINjecture1337-REFACTOR/issues
- **Discussions:** GitHub Discussions
- **Email:** adz@alphx.io

---

**Last Updated:** 2025-01-06
**Version:** 4.4.0
**License:** [See LICENSE file]
