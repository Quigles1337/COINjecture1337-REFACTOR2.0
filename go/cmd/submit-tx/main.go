// COINjecture Transaction Submission Utility
// Institutional-Grade Tool for Network A Transaction Testing
// Version: 4.5.0+
// Security: Ed25519 signing, replay protection, comprehensive validation

package main

import (
	"crypto/ed25519"
	"crypto/sha256"
	"encoding/binary"
	"encoding/hex"
	"flag"
	"fmt"
	"os"
	"time"

	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/internal/logger"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/mempool"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/state"
)

const (
	Version = "4.5.0+"

	// Security limits (institutional standards)
	MaxGasLimit           = 10000000 // 10M gas max
	MaxGasPrice           = 1000000  // 1M wei per gas max
	MaxTransactionSize    = 1048576  // 1MB max transaction
	MaxBatchSize          = 1000     // Max 1000 txs in batch
	MinAccountBalance     = 1000     // Minimum 1000 wei to transact
	NonceValidityWindow   = 1000     // Max nonce skew allowed

	// Transaction types (from consensus)
	TxTypeTransfer uint8 = 1
	TxTypeEscrow   uint8 = 2
)

// Config represents command-line configuration with validation
type Config struct {
	// Required parameters
	DBPath      string
	FromKeyHex  string
	ToAddrHex   string

	// Transaction parameters
	Amount      uint64
	GasPrice    uint64
	GasLimit    uint64
	TxType      uint8
	Data        []byte

	// Batch parameters
	Count       int
	Interval    time.Duration

	// Security parameters
	DryRun      bool
	VerifyOnly  bool
	Verbose     bool

	// Operational parameters
	Timeout     time.Duration
}

// TransactionSigner handles secure transaction signing
type TransactionSigner struct {
	privateKey ed25519.PrivateKey
	publicKey  ed25519.PublicKey
	address    [32]byte
	log        *logger.Logger
}

// ValidationResult contains transaction validation results
type ValidationResult struct {
	Valid       bool
	Errors      []string
	Warnings    []string
	TotalCost   uint64
	Fee         uint64
}

func main() {
	config := parseFlags()

	// Initialize institutional-grade logger
	logLevel := "info"
	if config.Verbose {
		logLevel = "debug"
	}
	log := logger.NewLogger(logLevel)

	printBanner()

	// Step 1: Validate configuration
	if err := validateConfig(config); err != nil {
		fatal("Configuration validation failed: %v", err)
	}
	log.Info("✓ Configuration validated")

	// Step 2: Initialize state manager (read-only)
	stateManager, err := state.NewStateManager(config.DBPath, log)
	if err != nil {
		fatal("Failed to initialize state manager: %v", err)
	}
	defer stateManager.Close()
	log.WithField("db_path", config.DBPath).Info("✓ State manager initialized")

	// Step 3: Initialize transaction signer
	signer, err := NewTransactionSigner(config.FromKeyHex, log)
	if err != nil {
		fatal("Failed to initialize signer: %v", err)
	}
	log.WithField("address", hex.EncodeToString(signer.address[:8])).Info("✓ Signer initialized")

	// Step 4: Parse recipient address
	recipientAddr, err := parseAddress(config.ToAddrHex)
	if err != nil {
		fatal("Invalid recipient address: %v", err)
	}
	log.WithField("recipient", hex.EncodeToString(recipientAddr[:8])).Info("✓ Recipient address parsed")

	// Step 5: Fetch sender account state
	account, err := stateManager.GetAccount(signer.address)
	if err != nil {
		fatal("Failed to fetch sender account: %v", err)
	}
	log.WithFields(map[string]interface{}{
		"balance": account.Balance,
		"nonce":   account.Nonce,
	}).Info("✓ Sender account fetched")

	// Step 6: Validate account balance
	totalCost := config.Amount + (config.GasLimit * config.GasPrice)
	if account.Balance < totalCost {
		fatal("Insufficient balance: have %d wei, need %d wei (amount=%d + fee=%d)",
			account.Balance, totalCost, config.Amount, config.GasLimit*config.GasPrice)
	}
	log.WithFields(map[string]interface{}{
		"total_cost": totalCost,
		"balance":    account.Balance,
		"remaining":  account.Balance - totalCost,
	}).Info("✓ Sufficient balance")

	// Step 7: Initialize mempool
	mempoolCfg := mempool.Config{
		MaxSize:          10000,
		MaxTxAge:         1 * time.Hour,
		CleanupInterval:  5 * time.Minute,
		PriorityThreshold: 0.0,
	}
	mp := mempool.NewMempool(mempoolCfg, log)
	log.Info("✓ Mempool initialized")

	// Step 8: Submit transactions
	printTransactionSummary(config, account, signer.address, recipientAddr, totalCost)

	if config.DryRun {
		log.Warn("DRY RUN MODE - No transactions will be submitted")
		os.Exit(0)
	}

	successCount := 0
	failureCount := 0
	startTime := time.Now()

	for i := 0; i < config.Count; i++ {
		nonce := account.Nonce + uint64(i)

		// Create and sign transaction
		tx, err := signer.CreateTransaction(
			recipientAddr,
			config.Amount,
			nonce,
			config.GasLimit,
			config.GasPrice,
			config.TxType,
			config.Data,
		)
		if err != nil {
			log.WithError(err).Errorf("Failed to create transaction %d/%d", i+1, config.Count)
			failureCount++
			continue
		}

		// Validate transaction before submission
		if config.VerifyOnly {
			validation := validateTransaction(tx, account)
			if !validation.Valid {
				log.WithFields(map[string]interface{}{
					"errors":   validation.Errors,
					"warnings": validation.Warnings,
				}).Errorf("Transaction %d validation failed", i+1)
				failureCount++
				continue
			}
			log.Infof("✓ Transaction %d/%d validated successfully", i+1, config.Count)
			successCount++
			continue
		}

		// Submit to mempool
		if err := mp.AddTransaction(tx); err != nil {
			log.WithError(err).Errorf("Failed to submit transaction %d/%d", i+1, config.Count)
			failureCount++
			continue
		}

		log.WithFields(map[string]interface{}{
			"tx_hash": hex.EncodeToString(tx.Hash[:8]),
			"nonce":   nonce,
			"amount":  config.Amount,
			"fee":     tx.Fee,
		}).Infof("✓ Transaction %d/%d submitted", i+1, config.Count)
		successCount++

		// Rate limiting between transactions
		if i < config.Count-1 && config.Interval > 0 {
			time.Sleep(config.Interval)
		}
	}

	elapsed := time.Since(startTime)
	printResults(successCount, failureCount, config.Count, elapsed)
}

// NewTransactionSigner creates a new institutional-grade transaction signer
func NewTransactionSigner(privateKeyHex string, log *logger.Logger) (*TransactionSigner, error) {
	// Decode private key
	privateKeyBytes, err := hex.DecodeString(privateKeyHex)
	if err != nil {
		return nil, fmt.Errorf("invalid private key hex: %w", err)
	}

	if len(privateKeyBytes) != ed25519.PrivateKeySize {
		return nil, fmt.Errorf("invalid private key size: expected %d bytes, got %d",
			ed25519.PrivateKeySize, len(privateKeyBytes))
	}

	privateKey := ed25519.PrivateKey(privateKeyBytes)
	publicKey := privateKey.Public().(ed25519.PublicKey)

	if len(publicKey) != ed25519.PublicKeySize {
		return nil, fmt.Errorf("invalid public key size: expected %d bytes, got %d",
			ed25519.PublicKeySize, len(publicKey))
	}

	var address [32]byte
	copy(address[:], publicKey)

	return &TransactionSigner{
		privateKey: privateKey,
		publicKey:  publicKey,
		address:    address,
		log:        log,
	}, nil
}

// CreateTransaction creates and signs a transaction with institutional-grade validation
func (s *TransactionSigner) CreateTransaction(
	to [32]byte,
	amount uint64,
	nonce uint64,
	gasLimit uint64,
	gasPrice uint64,
	txType uint8,
	data []byte,
) (*mempool.Transaction, error) {
	// Security validations
	if gasLimit > MaxGasLimit {
		return nil, fmt.Errorf("gas limit %d exceeds maximum %d", gasLimit, MaxGasLimit)
	}
	if gasPrice > MaxGasPrice {
		return nil, fmt.Errorf("gas price %d exceeds maximum %d", gasPrice, MaxGasPrice)
	}
	if len(data) > MaxTransactionSize {
		return nil, fmt.Errorf("transaction data size %d exceeds maximum %d", len(data), MaxTransactionSize)
	}
	if amount < 1 && txType == TxTypeTransfer {
		return nil, fmt.Errorf("transfer amount must be at least 1 wei")
	}

	// Calculate fee
	fee := gasLimit * gasPrice

	// Build canonical signing message
	message := s.buildSigningMessage(to, amount, nonce, gasLimit, gasPrice, txType, data)

	// Sign with Ed25519
	signature := ed25519.Sign(s.privateKey, message)
	if len(signature) != 64 {
		return nil, fmt.Errorf("invalid signature size: expected 64 bytes, got %d", len(signature))
	}

	var sig [64]byte
	copy(sig[:], signature)

	// Compute transaction hash
	txHash := sha256.Sum256(message)

	// Create mempool transaction
	tx := &mempool.Transaction{
		Hash:      txHash,
		From:      s.address,
		To:        to,
		Amount:    amount,
		Nonce:     nonce,
		GasLimit:  gasLimit,
		GasPrice:  gasPrice,
		Signature: sig,
		Data:      data,
		Timestamp: time.Now().Unix(),
		TxType:    txType,
		Fee:       fee,
		AddedAt:   time.Now(),
		Priority:  float64(gasPrice), // Priority = gas price
	}

	s.log.WithFields(map[string]interface{}{
		"hash":       hex.EncodeToString(txHash[:8]),
		"from":       hex.EncodeToString(s.address[:8]),
		"to":         hex.EncodeToString(to[:8]),
		"amount":     amount,
		"nonce":      nonce,
		"fee":        fee,
	}).Debug("Transaction created and signed")

	return tx, nil
}

// buildSigningMessage builds the canonical message for Ed25519 signing
func (s *TransactionSigner) buildSigningMessage(
	to [32]byte,
	amount uint64,
	nonce uint64,
	gasLimit uint64,
	gasPrice uint64,
	txType uint8,
	data []byte,
) []byte {
	// Message format (little-endian):
	// 1 byte:  codec_version (1)
	// 1 byte:  tx_type
	// 32 bytes: from
	// 32 bytes: to
	// 8 bytes: amount
	// 8 bytes: nonce
	// 8 bytes: gas_limit
	// 8 bytes: gas_price
	// 4 bytes: data_len
	// N bytes: data

	size := 1 + 1 + 32 + 32 + 8 + 8 + 8 + 8 + 4 + len(data)
	message := make([]byte, 0, size)

	message = append(message, 1) // codec_version = 1
	message = append(message, txType)
	message = append(message, s.address[:]...)
	message = append(message, to[:]...)
	message = append(message, uint64ToLittleEndian(amount)...)
	message = append(message, uint64ToLittleEndian(nonce)...)
	message = append(message, uint64ToLittleEndian(gasLimit)...)
	message = append(message, uint64ToLittleEndian(gasPrice)...)
	message = append(message, uint32ToLittleEndian(uint32(len(data)))...)
	message = append(message, data...)

	return message
}

// validateTransaction performs comprehensive transaction validation
func validateTransaction(tx *mempool.Transaction, account *state.Account) ValidationResult {
	result := ValidationResult{
		Valid:     true,
		Errors:    []string{},
		Warnings:  []string{},
		TotalCost: tx.Amount + tx.Fee,
		Fee:       tx.Fee,
	}

	// Critical validations (must pass)
	if tx.Amount == 0 && tx.TxType == TxTypeTransfer {
		result.Valid = false
		result.Errors = append(result.Errors, "zero transfer amount")
	}

	if account.Balance < result.TotalCost {
		result.Valid = false
		result.Errors = append(result.Errors, fmt.Sprintf(
			"insufficient balance: have %d wei, need %d wei", account.Balance, result.TotalCost))
	}

	if tx.Nonce < account.Nonce {
		result.Valid = false
		result.Errors = append(result.Errors, fmt.Sprintf(
			"nonce too old: tx=%d, account=%d (replay protection)", tx.Nonce, account.Nonce))
	}

	if tx.Nonce > account.Nonce+NonceValidityWindow {
		result.Valid = false
		result.Errors = append(result.Errors, fmt.Sprintf(
			"nonce too far in future: tx=%d, account=%d (max skew=%d)",
			tx.Nonce, account.Nonce, NonceValidityWindow))
	}

	// Warning validations (informational)
	if tx.GasPrice < 100 {
		result.Warnings = append(result.Warnings, "gas price is very low, transaction may be delayed")
	}

	if tx.GasLimit > 1000000 {
		result.Warnings = append(result.Warnings, "gas limit is very high, check if necessary")
	}

	return result
}

// Utility functions
func parseFlags() *Config {
	config := &Config{}

	flag.StringVar(&config.DBPath, "db", "./data/validator1.db", "Database path")
	flag.StringVar(&config.FromKeyHex, "from-key", "", "Sender private key (hex, required)")
	flag.StringVar(&config.ToAddrHex, "to", "", "Recipient address (32-byte hex, required)")
	flag.Uint64Var(&config.Amount, "amount", 1000000, "Amount to send (wei)")
	flag.Uint64Var(&config.GasPrice, "gas-price", 100, "Gas price (wei per gas)")
	flag.Uint64Var(&config.GasLimit, "gas-limit", 21000, "Gas limit")
	flag.IntVar(&config.Count, "count", 1, "Number of transactions to submit")
	flag.DurationVar(&config.Interval, "interval", 0, "Interval between transactions")
	flag.BoolVar(&config.DryRun, "dry-run", false, "Validate only, don't submit")
	flag.BoolVar(&config.VerifyOnly, "verify", false, "Verify transactions without submitting")
	flag.BoolVar(&config.Verbose, "verbose", false, "Verbose logging")

	txType := flag.Uint("type", 1, "Transaction type (1=Transfer, 2=Escrow)")
	dataHex := flag.String("data", "", "Transaction data (hex)")
	showVersion := flag.Bool("version", false, "Show version and exit")

	flag.Parse()

	if *showVersion {
		fmt.Printf("submit-tx version %s\n", Version)
		os.Exit(0)
	}

	config.TxType = uint8(*txType)

	if *dataHex != "" {
		data, err := hex.DecodeString(*dataHex)
		if err != nil {
			fatal("Invalid data hex: %v", err)
		}
		config.Data = data
	}

	return config
}

func validateConfig(config *Config) error {
	if config.FromKeyHex == "" {
		return fmt.Errorf("--from-key is required")
	}
	if config.ToAddrHex == "" {
		return fmt.Errorf("--to is required")
	}
	if config.Count < 1 || config.Count > MaxBatchSize {
		return fmt.Errorf("count must be between 1 and %d", MaxBatchSize)
	}
	if config.GasLimit > MaxGasLimit {
		return fmt.Errorf("gas limit cannot exceed %d", MaxGasLimit)
	}
	if config.GasPrice > MaxGasPrice {
		return fmt.Errorf("gas price cannot exceed %d", MaxGasPrice)
	}
	if config.TxType != TxTypeTransfer && config.TxType != TxTypeEscrow {
		return fmt.Errorf("invalid transaction type: %d (must be 1 or 2)", config.TxType)
	}
	return nil
}

func parseAddress(hexAddr string) ([32]byte, error) {
	var addr [32]byte
	bytes, err := hex.DecodeString(hexAddr)
	if err != nil {
		return addr, fmt.Errorf("invalid hex: %w", err)
	}
	if len(bytes) != 32 {
		return addr, fmt.Errorf("invalid address size: expected 32 bytes, got %d", len(bytes))
	}
	copy(addr[:], bytes)
	return addr, nil
}

func uint64ToLittleEndian(n uint64) []byte {
	b := make([]byte, 8)
	binary.LittleEndian.PutUint64(b, n)
	return b
}

func uint32ToLittleEndian(n uint32) []byte {
	b := make([]byte, 4)
	binary.LittleEndian.PutUint32(b, n)
	return b
}

func printBanner() {
	fmt.Println("═══════════════════════════════════════════════════════════")
	fmt.Printf("  COINjecture Transaction Submitter v%s\n", Version)
	fmt.Println("  Institutional-Grade Security | Ed25519 Signing")
	fmt.Println("═══════════════════════════════════════════════════════════\n")
}

func printTransactionSummary(config *Config, account *state.Account, from, to [32]byte, totalCost uint64) {
	fmt.Println("Transaction Summary:")
	fmt.Println("───────────────────────────────────────────────────────────")
	fmt.Printf("  From:         %s\n", hex.EncodeToString(from[:]))
	fmt.Printf("  To:           %s\n", hex.EncodeToString(to[:]))
	fmt.Printf("  Amount:       %d wei\n", config.Amount)
	fmt.Printf("  Gas Price:    %d wei/gas\n", config.GasPrice)
	fmt.Printf("  Gas Limit:    %d\n", config.GasLimit)
	fmt.Printf("  Fee:          %d wei\n", config.GasLimit*config.GasPrice)
	fmt.Printf("  Total Cost:   %d wei\n", totalCost)
	fmt.Printf("  Balance:      %d wei\n", account.Balance)
	fmt.Printf("  Remaining:    %d wei\n", account.Balance-totalCost)
	fmt.Printf("  Nonce Start:  %d\n", account.Nonce)
	fmt.Printf("  Count:        %d transactions\n", config.Count)
	if config.Interval > 0 {
		fmt.Printf("  Interval:     %s\n", config.Interval)
	}
	fmt.Println("───────────────────────────────────────────────────────────\n")
}

func printResults(success, failure, total int, elapsed time.Duration) {
	fmt.Println("\n═══════════════════════════════════════════════════════════")
	fmt.Println("  Results")
	fmt.Println("═══════════════════════════════════════════════════════════")
	fmt.Printf("  Successful:   %d/%d (%.1f%%)\n", success, total, float64(success)/float64(total)*100)
	fmt.Printf("  Failed:       %d/%d (%.1f%%)\n", failure, total, float64(failure)/float64(total)*100)
	fmt.Printf("  Elapsed:      %s\n", elapsed)
	if success > 0 {
		fmt.Printf("  Throughput:   %.2f tx/s\n", float64(success)/elapsed.Seconds())
	}
	fmt.Println("═══════════════════════════════════════════════════════════")
}

func fatal(format string, args ...interface{}) {
	fmt.Fprintf(os.Stderr, "\n❌ ERROR: "+format+"\n\n", args...)
	os.Exit(1)
}
