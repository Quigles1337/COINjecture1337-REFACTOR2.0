package bindings

import (
	"crypto/ed25519"
	"crypto/rand"
	"encoding/binary"
	"testing"
)

func TestVersion(t *testing.T) {
	version := Version()
	if version == "" {
		t.Fatal("Version should not be empty")
	}
	t.Logf("Rust library version: %s", version)

	codecVersion := CodecVersion()
	if codecVersion != 1 {
		t.Fatalf("Expected codec version 1, got %d", codecVersion)
	}
	t.Logf("Codec version: %d", codecVersion)
}

func TestSHA256(t *testing.T) {
	data := []byte("COINjecture")
	hash, err := SHA256(data)
	if err != nil {
		t.Fatalf("SHA256 failed: %v", err)
	}

	// Should produce consistent hash
	hash2, err := SHA256(data)
	if err != nil {
		t.Fatalf("SHA256 failed on second call: %v", err)
	}

	if hash != hash2 {
		t.Fatal("SHA256 should be deterministic")
	}

	t.Logf("SHA256('COINjecture') = %x", hash[:8])
}

func TestComputeEscrowID(t *testing.T) {
	submitter := [32]byte{1, 2, 3, 4}
	problemHash := [32]byte{5, 6, 7, 8}
	createdBlock := uint64(1000)

	id1, err := ComputeEscrowID(submitter, problemHash, createdBlock)
	if err != nil {
		t.Fatalf("ComputeEscrowID failed: %v", err)
	}

	// Should be deterministic
	id2, err := ComputeEscrowID(submitter, problemHash, createdBlock)
	if err != nil {
		t.Fatalf("ComputeEscrowID failed on second call: %v", err)
	}

	if id1 != id2 {
		t.Fatal("Escrow ID should be deterministic")
	}

	// Different inputs should produce different IDs
	id3, err := ComputeEscrowID(submitter, problemHash, createdBlock+1)
	if err != nil {
		t.Fatalf("ComputeEscrowID failed: %v", err)
	}

	if id1 == id3 {
		t.Fatal("Different inputs should produce different escrow IDs")
	}

	t.Logf("Escrow ID: %x", id1[:8])
}

func TestValidateEscrowCreation(t *testing.T) {
	// Valid escrow
	err := ValidateEscrowCreation(1000000, 1000, 2000)
	if err != nil {
		t.Fatalf("Valid escrow creation failed: %v", err)
	}

	// Invalid: amount too low (< 1000 wei)
	err = ValidateEscrowCreation(500, 1000, 2000)
	if err == nil {
		t.Fatal("Expected error for amount too low")
	}
	t.Logf("Correctly rejected low amount: %v", err)

	// Invalid: expiry before creation
	err = ValidateEscrowCreation(1000000, 2000, 1000)
	if err == nil {
		t.Fatal("Expected error for expiry < creation")
	}
	t.Logf("Correctly rejected invalid block order: %v", err)

	// Invalid: duration too short (< 100 blocks)
	err = ValidateEscrowCreation(1000000, 1000, 1050)
	if err == nil {
		t.Fatal("Expected error for duration too short")
	}
	t.Logf("Correctly rejected short duration: %v", err)
}

func TestValidateEscrowRelease(t *testing.T) {
	escrow := &BountyEscrow{
		ID:           [32]byte{1, 2, 3},
		Submitter:    [32]byte{4, 5, 6},
		Amount:       1000000,
		ProblemHash:  [32]byte{7, 8, 9},
		CreatedBlock: 1000,
		ExpiryBlock:  2000,
		State:        EscrowStateLocked,
		Recipient:    nil,
		SettledBlock: nil,
		SettlementTx: nil,
	}

	recipient := [32]byte{10, 11, 12}

	// Valid release
	err := ValidateEscrowRelease(escrow, recipient)
	if err != nil {
		t.Fatalf("Valid escrow release failed: %v", err)
	}

	// Invalid: already released
	escrow.State = EscrowStateReleased
	err = ValidateEscrowRelease(escrow, recipient)
	if err == nil {
		t.Fatal("Expected error for already released escrow")
	}
	t.Logf("Correctly rejected already-released escrow: %v", err)

	// Invalid: zero recipient
	escrow.State = EscrowStateLocked
	zeroRecipient := [32]byte{}
	err = ValidateEscrowRelease(escrow, zeroRecipient)
	if err == nil {
		t.Fatal("Expected error for zero recipient")
	}
	t.Logf("Correctly rejected zero recipient: %v", err)
}

func TestValidateEscrowRefund(t *testing.T) {
	escrow := &BountyEscrow{
		ID:           [32]byte{1, 2, 3},
		Submitter:    [32]byte{4, 5, 6},
		Amount:       1000000,
		ProblemHash:  [32]byte{7, 8, 9},
		CreatedBlock: 1000,
		ExpiryBlock:  2000,
		State:        EscrowStateLocked,
		Recipient:    nil,
		SettledBlock: nil,
		SettlementTx: nil,
	}

	// Valid refund (after expiry)
	err := ValidateEscrowRefund(escrow, 2000)
	if err != nil {
		t.Fatalf("Valid escrow refund failed: %v", err)
	}

	// Invalid: before expiry
	err = ValidateEscrowRefund(escrow, 1500)
	if err == nil {
		t.Fatal("Expected error for refund before expiry")
	}
	t.Logf("Correctly rejected early refund: %v", err)

	// Invalid: already refunded
	escrow.State = EscrowStateRefunded
	err = ValidateEscrowRefund(escrow, 2000)
	if err == nil {
		t.Fatal("Expected error for already refunded escrow")
	}
	t.Logf("Correctly rejected already-refunded escrow: %v", err)
}

func TestVerifyTransaction_ValidSignature(t *testing.T) {
	// Generate Ed25519 keypair
	publicKey, privateKey, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		t.Fatalf("Failed to generate keypair: %v", err)
	}

	// Create transaction
	var from, to [32]byte
	copy(from[:], publicKey)
	copy(to[:], []byte("recipient_address_here______"))

	tx := &Transaction{
		CodecVersion: 1,
		TxType:       TxTypeTransfer,
		From:         from,
		To:           to,
		Amount:       1000000,
		Nonce:        0,
		GasLimit:     21000,
		GasPrice:     100,
		Data:         nil,
		Timestamp:    1234567890,
	}

	// Sign transaction (canonical message format from Rust)
	message := buildSigningMessage(tx)
	signature := ed25519.Sign(privateKey, message)
	copy(tx.Signature[:], signature)

	// Account state
	senderState := &AccountState{
		Balance: 10000000, // Plenty of balance
		Nonce:   0,
	}

	// Verify transaction
	result, err := VerifyTransaction(tx, senderState)
	if err != nil {
		t.Fatalf("Transaction verification failed: %v", err)
	}

	if !result.Valid {
		t.Fatal("Expected transaction to be valid")
	}

	t.Logf("Transaction validated successfully:")
	t.Logf("  Valid: %v", result.Valid)
	t.Logf("  Total Cost: %d wei", result.TotalCost)
	t.Logf("  Fee: %d wei", result.Fee)
	t.Logf("  Gas Used: %d", result.GasUsed)
}

func TestVerifyTransaction_InvalidSignature(t *testing.T) {
	// Generate keypair but sign with wrong key
	publicKey, _, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		t.Fatalf("Failed to generate keypair: %v", err)
	}

	_, wrongPrivateKey, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		t.Fatalf("Failed to generate wrong keypair: %v", err)
	}

	var from, to [32]byte
	copy(from[:], publicKey)
	copy(to[:], []byte("recipient_address_here______"))

	tx := &Transaction{
		CodecVersion: 1,
		TxType:       TxTypeTransfer,
		From:         from,
		To:           to,
		Amount:       1000000,
		Nonce:        0,
		GasLimit:     21000,
		GasPrice:     100,
		Data:         nil,
		Timestamp:    1234567890,
	}

	// Sign with WRONG private key
	message := buildSigningMessage(tx)
	signature := ed25519.Sign(wrongPrivateKey, message)
	copy(tx.Signature[:], signature)

	senderState := &AccountState{
		Balance: 10000000,
		Nonce:   0,
	}

	// Should fail signature verification
	_, err = VerifyTransaction(tx, senderState)
	if err == nil {
		t.Fatal("Expected error for invalid signature")
	}
	t.Logf("Correctly rejected invalid signature: %v", err)
}

func TestVerifyTransaction_InvalidNonce(t *testing.T) {
	publicKey, privateKey, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		t.Fatalf("Failed to generate keypair: %v", err)
	}

	var from, to [32]byte
	copy(from[:], publicKey)
	copy(to[:], []byte("recipient_address_here______"))

	tx := &Transaction{
		CodecVersion: 1,
		TxType:       TxTypeTransfer,
		From:         from,
		To:           to,
		Amount:       1000000,
		Nonce:        5, // Wrong nonce
		GasLimit:     21000,
		GasPrice:     100,
		Data:         nil,
		Timestamp:    1234567890,
	}

	message := buildSigningMessage(tx)
	signature := ed25519.Sign(privateKey, message)
	copy(tx.Signature[:], signature)

	// Sender has nonce 0, but tx has nonce 5
	senderState := &AccountState{
		Balance: 10000000,
		Nonce:   0,
	}

	_, err = VerifyTransaction(tx, senderState)
	if err == nil {
		t.Fatal("Expected error for invalid nonce")
	}
	t.Logf("Correctly rejected invalid nonce: %v", err)
}

func TestVerifyTransaction_InsufficientBalance(t *testing.T) {
	publicKey, privateKey, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		t.Fatalf("Failed to generate keypair: %v", err)
	}

	var from, to [32]byte
	copy(from[:], publicKey)
	copy(to[:], []byte("recipient_address_here______"))

	tx := &Transaction{
		CodecVersion: 1,
		TxType:       TxTypeTransfer,
		From:         from,
		To:           to,
		Amount:       1000000,
		Nonce:        0,
		GasLimit:     21000,
		GasPrice:     100,
		Data:         nil,
		Timestamp:    1234567890,
	}

	message := buildSigningMessage(tx)
	signature := ed25519.Sign(privateKey, message)
	copy(tx.Signature[:], signature)

	// Insufficient balance (need 1M + 2.1M fee = 3.1M)
	senderState := &AccountState{
		Balance: 1000000, // Not enough
		Nonce:   0,
	}

	_, err = VerifyTransaction(tx, senderState)
	if err == nil {
		t.Fatal("Expected error for insufficient balance")
	}
	t.Logf("Correctly rejected insufficient balance: %v", err)
}

// Helper: build canonical signing message (must match Rust format exactly)
func buildSigningMessage(tx *Transaction) []byte {
	size := 1 + 1 + 32 + 32 + 8 + 8 + 8 + 8 + 4 + len(tx.Data) + 8
	message := make([]byte, 0, size)

	message = append(message, tx.CodecVersion)
	message = append(message, tx.TxType)
	message = append(message, tx.From[:]...)
	message = append(message, tx.To[:]...)
	message = append(message, uint64ToBytes(tx.Amount)...)
	message = append(message, uint64ToBytes(tx.Nonce)...)
	message = append(message, uint64ToBytes(tx.GasLimit)...)
	message = append(message, uint64ToBytes(tx.GasPrice)...)
	message = append(message, uint32ToBytes(uint32(len(tx.Data)))...)
	message = append(message, tx.Data...)
	message = append(message, int64ToBytes(tx.Timestamp)...)

	return message
}

func uint64ToBytes(n uint64) []byte {
	b := make([]byte, 8)
	binary.LittleEndian.PutUint64(b, n)
	return b
}

func uint32ToBytes(n uint32) []byte {
	b := make([]byte, 4)
	binary.LittleEndian.PutUint32(b, n)
	return b
}

func int64ToBytes(n int64) []byte {
	b := make([]byte, 8)
	binary.LittleEndian.PutUint64(b, uint64(n))
	return b
}
