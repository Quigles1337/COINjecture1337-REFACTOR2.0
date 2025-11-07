# COINjecture Network A - Multi-Validator Startup Script
# Institutional-Grade Automated Deployment
# Version: 4.5.0+

param(
    [int]$ValidatorCount = 3,
    [string]$KeysPath = "./keys/network-a",
    [string]$DataPath = "./data",
    [string]$BinPath = "./bin",
    [int]$BlockTime = 2,
    [switch]$DryRun,
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"

# Colors for output
function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Error { Write-Host $args -ForegroundColor Red }
function Write-Info { Write-Host $args -ForegroundColor Cyan }
function Write-Warning { Write-Host $args -ForegroundColor Yellow }

function Print-Banner {
    Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "  COINjecture Network A - Multi-Validator Startup" -ForegroundColor Cyan
    Write-Host "  Version: 4.5.0+ | Institutional-Grade Deployment" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
}

function Test-Prerequisites {
    Write-Info "Checking prerequisites..."

    # Check if network-a-node binary exists
    $nodeBinary = Join-Path $BinPath "network-a-node.exe"
    if (-not (Test-Path $nodeBinary)) {
        Write-Error "ERROR: network-a-node.exe not found at $nodeBinary"
        Write-Info "Please build it first: cd go && go build -o ../bin/network-a-node.exe ./cmd/network-a-node"
        exit 1
    }
    Write-Success "✓ Binary found: $nodeBinary"

    # Check if keys directory exists
    if (-not (Test-Path $KeysPath)) {
        Write-Error "ERROR: Keys directory not found: $KeysPath"
        Write-Info "Please generate keys first: .\bin\coinjecture-keygen.exe --count $ValidatorCount --output $KeysPath"
        exit 1
    }
    Write-Success "✓ Keys directory found: $KeysPath"

    # Create data directory if needed
    if (-not (Test-Path $DataPath)) {
        New-Item -ItemType Directory -Path $DataPath | Out-Null
        Write-Success "✓ Created data directory: $DataPath"
    } else {
        Write-Success "✓ Data directory exists: $DataPath"
    }

    Write-Host ""
}

function Load-ValidatorKeys {
    Write-Info "Loading validator keys..."

    $validators = @()

    for ($i = 1; $i -le $ValidatorCount; $i++) {
        $pubKeyFile = Join-Path $KeysPath "validator$i.pub"
        $privKeyFile = Join-Path $KeysPath "validator$i.priv"

        if (-not (Test-Path $pubKeyFile)) {
            Write-Error "ERROR: Public key not found: $pubKeyFile"
            exit 1
        }

        if (-not (Test-Path $privKeyFile)) {
            Write-Error "ERROR: Private key not found: $privKeyFile"
            exit 1
        }

        $pubKey = (Get-Content $pubKeyFile).Trim()
        $privKey = (Get-Content $privKeyFile).Trim()

        # Validate key format (hex)
        if ($pubKey -notmatch '^[0-9a-fA-F]{64}$') {
            Write-Error "ERROR: Invalid public key format in $pubKeyFile (expected 64 hex chars)"
            exit 1
        }

        if ($privKey -notmatch '^[0-9a-fA-F]{128}$') {
            Write-Error "ERROR: Invalid private key format in $privKeyFile (expected 128 hex chars)"
            exit 1
        }

        $validators += @{
            Number = $i
            PubKey = $pubKey
            PrivKey = $privKey
            DbPath = Join-Path $DataPath "validator$i.db"
        }

        Write-Success "✓ Loaded validator $i keys"
    }

    Write-Host ""
    return $validators
}

function Print-ValidatorSummary {
    param($Validators)

    Write-Info "Validator Configuration:"
    Write-Host "───────────────────────────────────────────────────────────" -ForegroundColor Gray
    Write-Host "  Validator Count: $($Validators.Count)" -ForegroundColor White
    Write-Host "  Block Time:      ${BlockTime}s" -ForegroundColor White
    Write-Host "  Consensus:       Proof-of-Authority (Round-Robin)" -ForegroundColor White
    Write-Host "───────────────────────────────────────────────────────────" -ForegroundColor Gray
    Write-Host ""

    foreach ($val in $Validators) {
        Write-Host "  Validator $($val.Number):" -ForegroundColor Yellow
        Write-Host "    Public Key: $($val.PubKey.Substring(0, 16))..." -ForegroundColor Gray
        Write-Host "    Database:   $($val.DbPath)" -ForegroundColor Gray
        Write-Host ""
    }
}

function Start-Validator {
    param($Validator)

    $nodeBinary = Join-Path $BinPath "network-a-node.exe"

    $args = @(
        "--validator-key", $Validator.PubKey,
        "--db", $Validator.DbPath,
        "--block-time", "${BlockTime}s"
    )

    if ($DryRun) {
        Write-Info "DRY RUN - Would start validator $($Validator.Number) with:"
        Write-Host "  Command: $nodeBinary" -ForegroundColor Gray
        Write-Host "  Args: $($args -join ' ')" -ForegroundColor Gray
        return $null
    }

    Write-Info "Starting validator $($Validator.Number)..."

    # Start process in background
    $process = Start-Process `
        -FilePath $nodeBinary `
        -ArgumentList $args `
        -NoNewWindow `
        -PassThru `
        -RedirectStandardOutput ".\logs\validator$($Validator.Number).log" `
        -RedirectStandardError ".\logs\validator$($Validator.Number).err.log"

    if ($process) {
        Write-Success "✓ Validator $($Validator.Number) started (PID: $($process.Id))"
        return $process
    } else {
        Write-Error "ERROR: Failed to start validator $($Validator.Number)"
        return $null
    }
}

function Wait-ForInitialization {
    param($Validators)

    Write-Info "Waiting for validators to initialize..."
    Start-Sleep -Seconds 3

    foreach ($val in $Validators) {
        $logFile = ".\logs\validator$($val.Number).log"

        if (Test-Path $logFile) {
            $logContent = Get-Content $logFile -ErrorAction SilentlyContinue

            if ($logContent -match "Consensus engine started" -or $logContent -match "Genesis block initialized") {
                Write-Success "✓ Validator $($val.Number) initialized"
            } else {
                Write-Warning "⚠ Validator $($val.Number) may not be fully initialized"
            }
        }
    }

    Write-Host ""
}

function Print-MonitoringCommands {
    Write-Info "Monitoring Commands:"
    Write-Host "───────────────────────────────────────────────────────────" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  View all validator logs:" -ForegroundColor White
    Write-Host "    Get-Content .\logs\validator*.log -Wait" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Monitor block production:" -ForegroundColor White
    Write-Host "    Get-Content .\logs\validator1.log -Wait | Select-String 'New block produced'" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Check validator consensus:" -ForegroundColor White
    Write-Host "    Get-Content .\logs\validator*.log -Wait | Select-String 'consensus|validator'" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Check for errors:" -ForegroundColor White
    Write-Host "    Get-Content .\logs\validator*.err.log -Wait" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Stop all validators:" -ForegroundColor White
    Write-Host "    Get-Process network-a-node | Stop-Process" -ForegroundColor Gray
    Write-Host ""
    Write-Host "───────────────────────────────────────────────────────────" -ForegroundColor Gray
    Write-Host ""
}

# Main execution
function Main {
    Print-Banner

    # Step 1: Prerequisites
    Test-Prerequisites

    # Step 2: Load validator keys
    $validators = Load-ValidatorKeys

    # Step 3: Print summary
    Print-ValidatorSummary -Validators $validators

    if ($DryRun) {
        Write-Warning "DRY RUN MODE - No validators will be started"
        Write-Host ""
        exit 0
    }

    # Step 4: Create logs directory
    if (-not (Test-Path ".\logs")) {
        New-Item -ItemType Directory -Path ".\logs" | Out-Null
        Write-Success "✓ Created logs directory"
    }

    # Step 5: Check if validators are already running
    $runningProcesses = Get-Process -Name "network-a-node" -ErrorAction SilentlyContinue
    if ($runningProcesses) {
        Write-Warning "⚠ Found $($runningProcesses.Count) running network-a-node process(es)"
        $response = Read-Host "Stop them and restart? (y/N)"
        if ($response -eq 'y' -or $response -eq 'Y') {
            $runningProcesses | Stop-Process -Force
            Write-Success "✓ Stopped running processes"
            Start-Sleep -Seconds 2
        } else {
            Write-Error "ERROR: Cannot start new validators while old ones are running"
            exit 1
        }
    }

    # Step 6: Start validators
    Write-Host ""
    $processes = @()
    foreach ($val in $validators) {
        $process = Start-Validator -Validator $val
        if ($process) {
            $processes += $process
        }
        Start-Sleep -Seconds 1  # Stagger startup
    }

    Write-Host ""

    # Step 7: Wait for initialization
    Wait-ForInitialization -Validators $validators

    # Step 8: Print monitoring commands
    Print-MonitoringCommands

    # Step 9: Success summary
    Write-Success "═══════════════════════════════════════════════════════════"
    Write-Success "  $($processes.Count) validators started successfully!"
    Write-Success "═══════════════════════════════════════════════════════════"
    Write-Host ""
    Write-Info "Press Ctrl+C to stop monitoring (validators will continue running)"
    Write-Host ""

    # Step 10: Live monitoring
    if (-not $DryRun) {
        Write-Info "Live monitoring (Ctrl+C to exit)..."
        Write-Host ""
        Get-Content ".\logs\validator*.log" -Wait | ForEach-Object {
            if ($_ -match "New block produced") {
                Write-Success $_
            } elseif ($_ -match "error|ERROR") {
                Write-Error $_
            } elseif ($_ -match "warn|WARN") {
                Write-Warning $_
            } else {
                Write-Host $_ -ForegroundColor Gray
            }
        }
    }
}

# Run main function
try {
    Main
} catch {
    Write-Error "FATAL ERROR: $_"
    Write-Host $_.ScriptStackTrace -ForegroundColor Red
    exit 1
}
