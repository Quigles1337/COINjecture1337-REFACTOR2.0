// Go bindings for Rust consensus validation (FFI)
package bindings

/*
#cgo LDFLAGS: -L../../rust/coinjecture-core/target/release -lcoinjecture_core
#cgo windows LDFLAGS: -lws2_32 -luserenv -lbcrypt -lntdll

#include <stdint.h>
#include <stdlib.h>

// Result codes
typedef enum {
    COINJ_OK = 0,
    COINJ_ERROR_INVALID_INPUT = 1,
    COINJ_ERROR_OUT_OF_MEMORY = 2,
    COINJ_ERROR_VERIFICATION_FAILED = 3,
    COINJ_ERROR_ENCODING = 4,
    COINJ_ERROR_INTERNAL = 5,
} CoinjResult;

// Transaction (C-compatible)
typedef struct {
    uint32_t codec_version;
    uint32_t tx_type;
    uint8_t from[32];
    uint8_t to[32];
    uint64_t amount;
    uint64_t nonce;
    uint64_t gas_limit;
    uint64_t gas_price;
    uint8_t signature[64];
    const uint8_t* data;
    uint32_t data_len;
    int64_t timestamp;
} TransactionFFI;

// Account state
typedef struct {
    uint64_t balance;
    uint64_t nonce;
} AccountStateFFI;

// Validation result
typedef struct {
    int32_t valid;
    uint64_t total_cost;
    uint64_t gas_used;
    uint64_t fee;
} ValidationResultFFI;

// Escrow
typedef struct {
    uint8_t id[32];
    uint8_t submitter[32];
    uint64_t amount;
    uint8_t problem_hash[32];
    uint64_t created_block;
    uint64_t expiry_block;
    uint32_t state;
    int32_t has_recipient;
    uint8_t recipient[32];
    int32_t has_settled_block;
    uint64_t settled_block;
    int32_t has_settlement_tx;
    uint8_t settlement_tx[32];
} BountyEscrowFFI;

// Function declarations
extern CoinjResult coinjecture_verify_transaction(
    const TransactionFFI* tx,
    const AccountStateFFI* sender_state,
    ValidationResultFFI* out_result
);

extern CoinjResult coinjecture_compute_escrow_id(
    const uint8_t* submitter,
    const uint8_t* problem_hash,
    uint64_t created_block,
    uint8_t* out_id
);

extern CoinjResult coinjecture_validate_escrow_creation(
    uint64_t amount,
    uint64_t created_block,
    uint64_t expiry_block
);

extern CoinjResult coinjecture_validate_escrow_release(
    const BountyEscrowFFI* escrow,
    const uint8_t* recipient
);

extern CoinjResult coinjecture_validate_escrow_refund(
    const BountyEscrowFFI* escrow,
    uint64_t current_block
);

extern CoinjResult coinjecture_sha256_hash(
    const uint8_t* input,
    uint32_t input_len,
    uint8_t* out_hash
);

extern const char* coinjecture_version(void);
extern uint32_t coinjecture_codec_version(void);
*/
import "C"
import (
	"fmt"
	"unsafe"
)

// Transaction types
const (
	TxTypeTransfer          uint8 = 1
	TxTypeProblemSubmission uint8 = 2
	TxTypeBountyPayment     uint8 = 3
)

// Escrow states
const (
	EscrowStateLocked   uint8 = 0
	EscrowStateReleased uint8 = 1
	EscrowStateRefunded uint8 = 2
)

// Transaction represents a blockchain transaction
type Transaction struct {
	CodecVersion uint8
	TxType       uint8
	From         [32]byte
	To           [32]byte
	Amount       uint64
	Nonce        uint64
	GasLimit     uint64
	GasPrice     uint64
	Signature    [64]byte
	Data         []byte
	Timestamp    int64
}

// AccountState represents account balance and nonce
type AccountState struct {
	Balance uint64
	Nonce   uint64
}

// ValidationResult represents transaction validation output
type ValidationResult struct {
	Valid     bool
	TotalCost uint64
	GasUsed   uint64
	Fee       uint64
}

// BountyEscrow represents a problem bounty escrow
type BountyEscrow struct {
	ID           [32]byte
	Submitter    [32]byte
	Amount       uint64
	ProblemHash  [32]byte
	CreatedBlock uint64
	ExpiryBlock  uint64
	State        uint8
	Recipient    *[32]byte
	SettledBlock *uint64
	SettlementTx *[32]byte
}

// VerifyTransaction validates a transaction using Rust consensus
//
// This calls into Rust FFI to perform:
// - Ed25519 signature verification
// - Nonce validation (replay protection)
// - Balance checks
// - Fee validation
// - Gas limit validation
func VerifyTransaction(tx *Transaction, senderState *AccountState) (*ValidationResult, error) {
	if tx == nil || senderState == nil {
		return nil, fmt.Errorf("nil transaction or sender state")
	}

	// Convert to C types
	var cTx C.TransactionFFI
	cTx.codec_version = C.uint32_t(tx.CodecVersion)
	cTx.tx_type = C.uint32_t(tx.TxType)
	copy(cTx.from[:], tx.From[:])
	copy(cTx.to[:], tx.To[:])
	cTx.amount = C.uint64_t(tx.Amount)
	cTx.nonce = C.uint64_t(tx.Nonce)
	cTx.gas_limit = C.uint64_t(tx.GasLimit)
	cTx.gas_price = C.uint64_t(tx.GasPrice)
	copy(cTx.signature[:], tx.Signature[:])
	cTx.timestamp = C.int64_t(tx.Timestamp)

	// Handle data
	if len(tx.Data) > 0 {
		cTx.data = (*C.uint8_t)(unsafe.Pointer(&tx.Data[0]))
		cTx.data_len = C.uint32_t(len(tx.Data))
	} else {
		cTx.data = nil
		cTx.data_len = 0
	}

	var cState C.AccountStateFFI
	cState.balance = C.uint64_t(senderState.Balance)
	cState.nonce = C.uint64_t(senderState.Nonce)

	var cResult C.ValidationResultFFI

	// Call Rust FFI
	result := C.coinjecture_verify_transaction(&cTx, &cState, &cResult)

	if result != C.COINJ_OK {
		return nil, fmt.Errorf("validation failed: error code %d", result)
	}

	return &ValidationResult{
		Valid:     cResult.valid != 0,
		TotalCost: uint64(cResult.total_cost),
		GasUsed:   uint64(cResult.gas_used),
		Fee:       uint64(cResult.fee),
	}, nil
}

// ComputeEscrowID computes deterministic escrow ID
//
// ID = SHA-256(submitter || problem_hash || created_block)
func ComputeEscrowID(submitter, problemHash [32]byte, createdBlock uint64) ([32]byte, error) {
	var id [32]byte

	result := C.coinjecture_compute_escrow_id(
		(*C.uint8_t)(&submitter[0]),
		(*C.uint8_t)(&problemHash[0]),
		C.uint64_t(createdBlock),
		(*C.uint8_t)(&id[0]),
	)

	if result != C.COINJ_OK {
		return [32]byte{}, fmt.Errorf("failed to compute escrow ID: error code %d", result)
	}

	return id, nil
}

// ValidateEscrowCreation validates escrow creation parameters
func ValidateEscrowCreation(amount, createdBlock, expiryBlock uint64) error {
	result := C.coinjecture_validate_escrow_creation(
		C.uint64_t(amount),
		C.uint64_t(createdBlock),
		C.uint64_t(expiryBlock),
	)

	if result != C.COINJ_OK {
		return fmt.Errorf("invalid escrow parameters: error code %d", result)
	}

	return nil
}

// ValidateEscrowRelease validates escrow release to solver
func ValidateEscrowRelease(escrow *BountyEscrow, recipient [32]byte) error {
	if escrow == nil {
		return fmt.Errorf("nil escrow")
	}

	cEscrow := bountyEscrowToC(escrow)

	result := C.coinjecture_validate_escrow_release(
		&cEscrow,
		(*C.uint8_t)(&recipient[0]),
	)

	if result != C.COINJ_OK {
		return fmt.Errorf("invalid escrow release: error code %d", result)
	}

	return nil
}

// ValidateEscrowRefund validates escrow refund after expiry
func ValidateEscrowRefund(escrow *BountyEscrow, currentBlock uint64) error {
	if escrow == nil {
		return fmt.Errorf("nil escrow")
	}

	cEscrow := bountyEscrowToC(escrow)

	result := C.coinjecture_validate_escrow_refund(
		&cEscrow,
		C.uint64_t(currentBlock),
	)

	if result != C.COINJ_OK {
		return fmt.Errorf("invalid escrow refund: error code %d", result)
	}

	return nil
}

// SHA256 computes SHA-256 hash
func SHA256(data []byte) ([32]byte, error) {
	var hash [32]byte

	if len(data) == 0 {
		return hash, fmt.Errorf("empty data")
	}

	result := C.coinjecture_sha256_hash(
		(*C.uint8_t)(&data[0]),
		C.uint32_t(len(data)),
		(*C.uint8_t)(&hash[0]),
	)

	if result != C.COINJ_OK {
		return [32]byte{}, fmt.Errorf("hash failed: error code %d", result)
	}

	return hash, nil
}

// Version returns Rust library version
func Version() string {
	return C.GoString(C.coinjecture_version())
}

// CodecVersion returns codec version
func CodecVersion() uint32 {
	return uint32(C.coinjecture_codec_version())
}

// Helper: convert BountyEscrow to C type
func bountyEscrowToC(escrow *BountyEscrow) C.BountyEscrowFFI {
	var c C.BountyEscrowFFI

	copy(c.id[:], escrow.ID[:])
	copy(c.submitter[:], escrow.Submitter[:])
	c.amount = C.uint64_t(escrow.Amount)
	copy(c.problem_hash[:], escrow.ProblemHash[:])
	c.created_block = C.uint64_t(escrow.CreatedBlock)
	c.expiry_block = C.uint64_t(escrow.ExpiryBlock)
	c.state = C.uint32_t(escrow.State)

	if escrow.Recipient != nil {
		c.has_recipient = 1
		copy(c.recipient[:], escrow.Recipient[:])
	} else {
		c.has_recipient = 0
	}

	if escrow.SettledBlock != nil {
		c.has_settled_block = 1
		c.settled_block = C.uint64_t(*escrow.SettledBlock)
	} else {
		c.has_settled_block = 0
	}

	if escrow.SettlementTx != nil {
		c.has_settlement_tx = 1
		copy(c.settlement_tx[:], escrow.SettlementTx[:])
	} else {
		c.has_settlement_tx = 0
	}

	return c
}
