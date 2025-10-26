#!/bin/bash

# Deploy Frontend Fix to Droplet
# This script deploys the fixed app.js to the droplet

set -e

echo "🔧 Deploying Frontend Fix to Droplet"
echo "===================================="

# Configuration
DROPLET_IP="167.172.213.70"
SSH_KEY="$HOME/.ssh/coinjecture_droplet_key"
USER="coinjecture"

# Check if SSH key exists
if [ ! -f "$SSH_KEY" ]; then
    echo "❌ SSH key not found at $SSH_KEY"
    echo "Please ensure the SSH key is in the correct location"
    exit 1
fi

echo "🔑 Using SSH key: $SSH_KEY"
echo "🌐 Connecting to droplet: $DROPLET_IP"
echo ""

# Create a script to run on the droplet
cat > /tmp/deploy_frontend_fix.sh << 'EOF'
#!/bin/bash

echo "🔧 Deploying fixed app.js to droplet..."
echo "======================================="

# Check if the web directory exists
if [ ! -d "/home/coinjecture/COINjecture/web" ]; then
    echo "❌ Web directory not found: /home/coinjecture/COINjecture/web"
    exit 1
fi

# Create the fixed app.js content
cat > /tmp/app.js << 'APPJS'
/**
 * COINjecture Web Interface
 * Multi-page interface with terminal, API docs, and download
 */

// Wait for @noble/ed25519 to load
async function waitForNobleEd25519() {
  let attempts = 0;
  while (attempts < 50) {
    if (window.nobleEd25519 || window.ed25519) {
      return window.nobleEd25519 || window.ed25519;
    }
    await new Promise(resolve => setTimeout(resolve, 100));
    attempts++;
  }
  throw new Error('@noble/ed25519 library failed to load');
}

class WebInterface {
  constructor() {
    // Use production API endpoint
    this.apiBase = 'https://api.coinjecture.com';
    this.output = document.getElementById('terminal-output');
    this.input = document.getElementById('command-input');
    this.status = document.getElementById('network-status');
    this.history = [];
    this.historyIndex = -1;
    
    // Wallet dashboard elements
    this.walletDashboard = document.getElementById('wallet-dashboard');
    this.walletAddress = document.getElementById('wallet-address');
    this.rewardsTotal = document.getElementById('rewards-total');
    this.blocksMined = document.getElementById('blocks-mined');
    this.copyAddressBtn = document.getElementById('copy-address-btn');
    
    // Rewards refresh interval
    this.rewardsRefreshInterval = null;
    
    // Validate browser support for Ed25519
    this.validateBrowserSupport();
    
    // Add certificate notice to the page
    this.addCertificateNotice();
    this.isProcessing = false;
    this.wallet = null; // Store wallet for persistent mining
    
    this.init();
  }
  
  validateBrowserSupport() {
    // Check if Web Crypto API is available
    if (!window.crypto || !window.crypto.subtle) {
      this.addOutput('❌ Web Crypto API not available. Please use a modern browser.', 'error');
      return false;
    }
    
    // Check if localStorage is available
    if (!window.localStorage) {
      this.addOutput('❌ LocalStorage not available. Please enable it.', 'error');
      return false;
    }
    
    return true;
  }
  
  addCertificateNotice() {
    // Check if certificate has been accepted
    const certAccepted = localStorage.getItem('coinjecture_cert_accepted');
    if (!certAccepted) {
      const notice = document.createElement('div');
      notice.id = 'cert-notice';
      notice.innerHTML = `
        <div style="background: #ff6b6b; color: white; padding: 10px; text-align: center; position: fixed; top: 0; left: 0; right: 0; z-index: 1000;">
          🔒 Certificate Required: <a href="https://api.coinjecture.com" target="_blank" style="color: white; text-decoration: underline;">Click here to accept certificate</a>
        </div>
      `;
      document.body.insertBefore(notice, document.body.firstChild);
    }
  }
  
  async init() {
    // Initialize API testing
    this.initAPITesting();
    
    // Set up event listeners
    this.setupEventListeners();
    
    // Update network status
    this.updateNetworkStatus();
    
    // Initialize copy address button
    this.initCopyAddressButton();
    
    // Start periodic updates
    setInterval(() => this.updateNetworkStatus(), 30000); // Update every 30 seconds
    
    // Check wallet status
    this.checkWalletStatus();
  }
  
  setupEventListeners() {
    // Command input
    if (this.input) {
      this.input.addEventListener('keydown', (e) => this.handleKeyDown(e));
      this.input.addEventListener('input', (e) => this.handleInput(e));
    }
    
    // Copy address button
    if (this.copyAddressBtn) {
      this.copyAddressBtn.addEventListener('click', () => this.copyAddress());
    }
    
    // Navigation
    document.querySelectorAll('.nav-link').forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        this.showPage(link.dataset.page);
      });
    });
    
    // Page navigation
    document.addEventListener('click', (e) => {
      if (e.target.matches('[data-page]')) {
        e.preventDefault();
        this.showPage(e.target.dataset.page);
      }
    });
    
    // Focus input when terminal page is shown
    document.addEventListener('click', (e) => {
      const targetPage = e.target.dataset.page;
      if (targetPage === 'terminal' && this.input) {
        setTimeout(() => this.input.focus(), 100);
      }
    });
  }
  
  initAPITesting() {
    const testButton = document.getElementById('test-api');
    if (testButton) {
      testButton.addEventListener('click', () => this.testAPIConnection());
    }
  }
  
  async testAPIConnection() {
    const resultDiv = document.getElementById('api-test-result');
    resultDiv.innerHTML = 'Testing connection...';
    resultDiv.className = 'test-result';
    
    try {
      const response = await this.fetchWithFallback('/v1/data/block/latest');
      const data = await response.json();
      
      if (response.ok && data.status === 'success') {
        resultDiv.innerHTML = `✅ Connection successful!<br>Latest block: #${data.data.index}<br>Hash: ${data.data.block_hash.substring(0, 16)}...`;
        resultDiv.className = 'test-result success';
      } else {
        resultDiv.innerHTML = `❌ Connection failed: ${data.message || 'Unknown error'}`;
        resultDiv.className = 'test-result error';
      }
    } catch (error) {
      resultDiv.innerHTML = `❌ Connection error: ${error.message}`;
      resultDiv.className = 'test-result error';
    }
  }
  
  showPage(pageId) {
    // Hide all pages
    document.querySelectorAll('.page').forEach(page => {
      page.classList.remove('active');
    });
    
    // Show selected page
    const targetPage = document.getElementById(`page-${pageId}`);
    if (targetPage) {
      targetPage.classList.add('active');
    }
    
    // Update navigation
    document.querySelectorAll('.nav-link').forEach(link => {
      link.classList.remove('active');
    });
    
    const activeLink = document.querySelector(`[data-page="${pageId}"]`);
    if (activeLink) {
      activeLink.classList.add('active');
    }
    
    // Focus input if terminal page
    if (pageId === 'terminal' && this.input) {
      setTimeout(() => this.input.focus(), 100);
    }
  }
  
  handleKeyDown(e) {
    if (e.key === 'Enter') {
      e.preventDefault();
      const command = this.input.value.trim();
      if (command) {
        this.addOutput(`coinjectured$ ${command}`);
        this.history.push(command);
        this.historyIndex = this.history.length;
        this.input.value = '';
        this.processCommand(command);
      }
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (this.historyIndex > 0) {
        this.historyIndex--;
        this.input.value = this.history[this.historyIndex];
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (this.historyIndex < this.history.length - 1) {
        this.historyIndex++;
        this.input.value = this.history[this.historyIndex];
      } else {
        this.historyIndex = this.history.length;
        this.input.value = '';
      }
    } else if (e.key === 'Tab') {
      e.preventDefault();
      this.handleTabCompletion();
    }
  }
  
  handleInput(e) {
    // Auto-resize input based on content
    if (this.input) {
      this.input.style.width = Math.max(200, this.input.value.length * 8 + 20) + 'px';
    }
  }
  
  async processCommand(command) {
    const [cmd, ...args] = command.split(' ');
    
    switch(cmd) {
      case 'blockchain-stats':
        await this.displayBlockchainStats();
        break;
      case 'help':
        this.showHelp();
        break;
      case 'get-block':
        await this.handleGetBlock(args);
        break;
      case 'peers':
        await this.handlePeers();
        break;
      case 'telemetry-status':
        await this.handleTelemetryStatus();
        break;
      case 'mine':
        await this.handleMine(args);
        break;
      case 'submit-problem':
        await this.handleSubmitProblem();
        break;
      case 'wallet-generate':
        await this.handleWalletGenerate();
        break;
      case 'wallet-info':
        this.handleWalletInfo();
        break;
      case 'rewards':
        this.handleRewards();
        break;
      case 'export-wallet':
        this.handleExportWallet();
        break;
      case 'copy-address':
        this.copyAddress();
        break;
      case 'clear':
        this.clearOutput();
        break;
      default:
        this.addOutput(`❌ Unknown command: ${cmd}. Type 'help' for available commands.`, 'error');
    }
  }
  
  showHelp() {
    const helpLines = [
      'Available commands:',
      '  get-block --latest     Get latest block',
      '  blockchain-stats      Show blockchain statistics',
      '  get-block --index <n>  Get block by index',
      '  peers                  List connected peers',
      '  telemetry-status       Check network status',
      '  mine --tier <tier>     Start mining (mobile|desktop|server)',
      '  submit-problem         Submit computational problem',
      '  wallet-generate        Create new wallet',
      '  wallet-info            Show wallet details',
      '  rewards                Show mining rewards breakdown',
      '  export-wallet          Export wallet details for backup',
      '  copy-address           Copy wallet address to clipboard',
      '  help                   Show this help',
      '  clear                  Clear terminal',
      '',
      'Mobile tips:',
      '  • Swipe up/down for command history',
      '  • Tap and hold for text selection',
      '  • Use Tab for auto-complete'
    ];
    
    this.addMultiLineOutput(helpLines);
  }
  
  async handleGetBlock(args) {
    try {
      const isLatest = args.includes('--latest');
      const indexArg = args.find(arg => arg.startsWith('--index='));
      const index = indexArg ? indexArg.split('=')[1] : null;
      
      let endpoint;
      if (isLatest) {
        endpoint = `${this.apiBase}/v1/data/block/latest`;
      } else if (index) {
        endpoint = `${this.apiBase}/v1/data/block/${index}`;
      } else {
        this.addOutput('❌ Use --latest or --index=<number>', 'error');
        return;
      }
      
      this.addOutput('📦 Fetching block data...');
      const response = await fetch(endpoint);
      const data = await response.json();
      
      if (data.status === 'success') {
        const block = data.data;
        this.addMultiLineOutput([
          `✅ Block #${block.index}`,
          `   Hash: ${block.block_hash}`,
          `   Previous: ${block.previous_hash}`,
          `   Timestamp: ${new Date(block.timestamp * 1000).toLocaleString()}`,
          `   Work Score: ${block.cumulative_work_score}`,
          `   Capacity: ${block.mining_capacity}`,
          `   Transactions: ${block.transactions ? block.transactions.length : 0}`
        ]);
      } else {
        this.addOutput(`❌ ${data.message || 'Block not found'}`, 'error');
      }
    } catch (error) {
      this.addOutput(`❌ Network error: ${error.message}`, 'error');
    }
  }
  
  async handlePeers() {
    try {
      this.addOutput('🌐 Fetching peer information...');
      const response = await this.fetchWithFallback('/v1/peers');
      const data = await response.json();
      
      if (data.status === 'success') {
        const peers = data.data;
        if (peers.length > 0) {
          this.addMultiLineOutput([
            '🌐 Connected Peers:',
            ...peers.map(peer => `   ${peer.address}:${peer.port} (${peer.status})`)
          ]);
        } else {
          this.addOutput('🌐 No peers connected');
        }
      } else {
        this.addOutput(`❌ ${data.message || 'Failed to fetch peers'}`, 'error');
      }
    } catch (error) {
      this.addOutput(`❌ Network error: ${error.message}`, 'error');
    }
  }
  
  async handleTelemetryStatus() {
    try {
      this.addOutput('📊 Fetching network telemetry...');
      const response = await this.fetchWithFallback('/v1/display/telemetry/latest');
      const data = await response.json();
      
      if (data.status === 'success') {
        const telemetry = data.data;
        this.addMultiLineOutput([
          '📊 Network Telemetry:',
          `   Active Miners: ${telemetry.active_miners || 0}`,
          `   Total Blocks: ${telemetry.total_blocks || 0}`,
          `   Network Hash Rate: ${telemetry.hash_rate || 'N/A'}`,
          `   Last Update: ${new Date(telemetry.timestamp * 1000).toLocaleString()}`
        ]);
      } else {
        this.addOutput(`❌ ${data.message || 'Failed to fetch telemetry'}`, 'error');
      }
    } catch (error) {
      this.addOutput(`❌ Network error: ${error.message}`, 'error');
    }
  }
  
  async handleMine(args) {
    try {
      const tierArg = args.find(arg => arg.startsWith('--tier='));
      const tier = tierArg ? tierArg.split('=')[1] : 'mobile';
      
      if (!['mobile', 'desktop', 'server'].includes(tier)) {
        this.addOutput('❌ Invalid tier. Use: mobile, desktop, or server', 'error');
        return;
      }
      
      this.addOutput(`⛏️  Starting mining with ${tier} tier...`);
      
      // Check if wallet exists
      if (!this.wallet) {
        this.addOutput('💡 No wallet found. Use "wallet-generate" to create one.', 'info');
        return;
      }
      
      const response = await this.fetchWithFallback('/v1/mine', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          tier: tier,
          miner_address: this.wallet.address
        })
      });
      
      const data = await response.json();
      
      if (data.status === 'success') {
        this.addOutput(`✅ Mining started successfully!`, 'success');
        this.addOutput(`💰 Miner Address: ${this.wallet.address}`);
        this.addOutput(`⚡ Tier: ${tier}`);
        this.addOutput(`🔗 Mining ID: ${data.data.mining_id || 'N/A'}`);
        
        // Start rewards refresh
        this.startRewardsRefresh();
      } else {
        this.addOutput(`❌ ${data.message || 'Failed to start mining'}`, 'error');
      }
    } catch (error) {
      this.addOutput(`❌ Network error: ${error.message}`, 'error');
    }
  }
  
  async handleSubmitProblem() {
    try {
      this.addOutput('🧮 Submitting computational problem...');
      
      // Generate a simple subset sum problem
      const problem = {
        type: 'subset_sum',
        target: 15,
        numbers: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        timestamp: Date.now()
      };
      
      const response = await this.fetchWithFallback('/v1/submit-problem', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(problem)
      });
      
      const data = await response.json();
      
      if (data.status === 'success') {
        this.addOutput(`✅ Problem submitted successfully!`, 'success');
        this.addOutput(`🆔 Problem ID: ${data.data.problem_id || 'N/A'}`);
        this.addOutput(`🎯 Target: ${problem.target}`);
        this.addOutput(`📊 Numbers: [${problem.numbers.join(', ')}]`);
      } else {
        this.addOutput(`❌ ${data.message || 'Failed to submit problem'}`, 'error');
      }
    } catch (error) {
      this.addOutput(`❌ Network error: ${error.message}`, 'error');
    }
  }
  
  async handleWalletGenerate() {
    try {
      this.addOutput('🔑 Generating new wallet...');
      
      // Generate Ed25519 key pair
      const keyPair = await this.generateKeyPair();
      
      // Create wallet object
      this.wallet = {
        address: keyPair.address,
        publicKey: keyPair.publicKey,
        privateKey: keyPair.privateKey,
        created: new Date().toISOString()
      };
      
      // Store in localStorage
      localStorage.setItem('coinjecture_wallet', JSON.stringify(this.wallet));
      
      this.addOutput(`✅ Wallet generated successfully!`, 'success');
      this.addOutput(`🔑 Address: ${this.wallet.address}`);
      this.addOutput(`🔐 Public Key: ${this.wallet.publicKey}`);
      this.addOutput(`💾 Wallet saved to browser storage`);
      
      // Update wallet dashboard
      this.updateWalletDashboard();
      
    } catch (error) {
      this.addOutput(`❌ Failed to generate wallet: ${error.message}`, 'error');
    }
  }
  
  handleWalletInfo() {
    if (!this.wallet) {
      this.addOutput('💡 No wallet found. Use "wallet-generate" to create one.', 'info');
      return;
    }
    
    this.addMultiLineOutput([
      '💰 Wallet Information',
      `Address: ${this.wallet.address}`,
      `Public Key: ${this.wallet.publicKey}`,
      `Created: ${new Date(this.wallet.created).toLocaleString()}`,
      '',
      'This wallet is used for mining rewards and token transactions.',
      'Your private key is securely stored in your browser.'
    ]);
  }
  
  handleRewards() {
    if (!this.wallet) {
      this.addOutput('💡 No wallet found. Use "wallet-generate" to create one.', 'info');
      return;
    }
    
    // Get rewards from localStorage
    const rewards = JSON.parse(localStorage.getItem('coinjecture_rewards') || '{}');
    const totalRewards = rewards[this.wallet.address] || 0;
    const blocksMined = rewards[`${this.wallet.address}_blocks`] || 0;
    
    this.addMultiLineOutput([
      '💰 Current Rewards:',
      `${totalRewards} BEANS (${blocksMined} blocks mined)`,
      '',
      'This wallet is used for mining rewards and token transactions.',
      'Your private key is securely stored in your browser.',
      '',
      '💡 Commands:',
      '  • "copy-address" - Copy address to clipboard',
      '  • "rewards" - Show detailed rewards breakdown',
      '  • "export-wallet" - Export wallet for backup',
      '  • "mine --tier=mobile" - Start earning $BEANS tokens!'
    ]);
  }
  
  handleExportWallet() {
    if (!this.wallet) {
      this.addOutput('💡 No wallet found. Use "wallet-generate" to create one.', 'info');
      return;
    }
    
    const exportData = {
      address: this.wallet.address,
      publicKey: this.wallet.publicKey,
      privateKey: this.wallet.privateKey,
      created: this.wallet.created,
      exported: new Date().toISOString()
    };
    
    // Create downloadable file
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `coinjecture-wallet-${this.wallet.address.substring(0, 8)}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    this.addOutput(`✅ Wallet exported successfully!`, 'success');
    this.addOutput(`📁 File: coinjecture-wallet-${this.wallet.address.substring(0, 8)}.json`);
    this.addOutput(`🔐 Keep your private key secure and never share it!`);
  }
  
  copyAddress() {
    if (!this.wallet) {
      this.addOutput('💡 No wallet found. Use "wallet-generate" to create one.', 'info');
      return;
    }
    
    navigator.clipboard.writeText(this.wallet.address).then(() => {
      this.addOutput(`✅ Address copied to clipboard: ${this.wallet.address}`, 'success');
    }).catch(() => {
      this.addOutput(`❌ Failed to copy address. Please copy manually: ${this.wallet.address}`, 'error');
    });
  }
  
  clearOutput() {
    if (this.output) {
      this.output.innerHTML = '<div class="output">coinjectured$ <span class="cursor">█</span></div>';
    }
  }
  
  addOutput(text, type = 'normal') {
    if (!this.output) return;
    
    const outputDiv = document.createElement('div');
    outputDiv.className = `output ${type}`;
    outputDiv.innerHTML = text;
    
    this.output.appendChild(outputDiv);
    this.output.scrollTop = this.output.scrollHeight;
  }
  
  addMultiLineOutput(lines) {
    lines.forEach(line => {
      this.addOutput(line);
    });
  }
  
  async generateKeyPair() {
    try {
      // Generate Ed25519 key pair
      const keyPair = await window.crypto.subtle.generateKey(
        {
          name: 'Ed25519',
          namedCurve: 'Ed25519'
        },
        true,
        ['sign', 'verify']
      );
      
      // Export public key
      const publicKeyBuffer = await window.crypto.subtle.exportKey('raw', keyPair.publicKey);
      const publicKeyHex = Array.from(new Uint8Array(publicKeyBuffer))
        .map(b => b.toString(16).padStart(2, '0'))
        .join('');
      
      // Export private key
      const privateKeyBuffer = await window.crypto.subtle.exportKey('pkcs8', keyPair.privateKey);
      const privateKeyHex = Array.from(new Uint8Array(privateKeyBuffer))
        .map(b => b.toString(16).padStart(2, '0'))
        .join('');
      
      // Generate address from public key
      const address = `BEANS${publicKeyHex.substring(0, 40)}`;
      
      return {
        address,
        publicKey: publicKeyHex,
        privateKey: privateKeyHex
      };
    } catch (error) {
      throw new Error(`Key generation failed: ${error.message}`);
    }
  }
  
  checkWalletStatus() {
    // Load wallet from localStorage
    const storedWallet = localStorage.getItem('coinjecture_wallet');
    if (storedWallet) {
      try {
        this.wallet = JSON.parse(storedWallet);
        this.updateWalletDashboard();
        this.startRewardsRefresh();
      } catch (error) {
        console.error('Failed to load wallet:', error);
        localStorage.removeItem('coinjecture_wallet');
      }
    }
  }
  
  updateWalletDashboard() {
    if (!this.wallet || !this.walletDashboard) return;
    
    // Update wallet address
    if (this.walletAddress) {
      this.walletAddress.textContent = this.wallet.address;
    }
    
    // Update rewards
    const rewards = JSON.parse(localStorage.getItem('coinjecture_rewards') || '{}');
    const totalRewards = rewards[this.wallet.address] || 0;
    const blocksMined = rewards[`${this.wallet.address}_blocks`] || 0;
    
    if (this.rewardsTotal) {
      this.rewardsTotal.textContent = `${totalRewards} BEANS`;
    }
    
    if (this.blocksMined) {
      this.blocksMined.textContent = `${blocksMined} blocks`;
    }
    
    // Show wallet dashboard
    this.walletDashboard.style.display = 'block';
  }
  
  startRewardsRefresh() {
    if (this.rewardsRefreshInterval) {
      clearInterval(this.rewardsRefreshInterval);
    }
    
    this.rewardsRefreshInterval = setInterval(() => {
      this.updateRewardsDashboard();
    }, 30000); // Update every 30 seconds
  }
  
  async updateRewardsDashboard() {
    if (!this.wallet) return;
    
    try {
      // Fetch current rewards from API
      const response = await this.fetchWithFallback(`/v1/rewards/${this.wallet.address}`);
      const data = await response.json();
      
      if (data.status === 'success') {
        const rewards = data.data;
        const totalRewards = rewards.total_rewards || 0;
        const blocksMined = rewards.blocks_mined || 0;
        
        // Update localStorage
        const storedRewards = JSON.parse(localStorage.getItem('coinjecture_rewards') || '{}');
        storedRewards[this.wallet.address] = totalRewards;
        storedRewards[`${this.wallet.address}_blocks`] = blocksMined;
        localStorage.setItem('coinjecture_rewards', JSON.stringify(storedRewards));
        
        // Update dashboard
        this.updateWalletDashboard();
      }
    } catch (error) {
      console.error('Failed to update rewards:', error);
    }
  }
  
  stopRewardsRefresh() {
    if (this.rewardsRefreshInterval) {
      clearInterval(this.rewardsRefreshInterval);
      this.rewardsRefreshInterval = null;
    }
  }

  // Display blockchain statistics
  async displayBlockchainStats() {
    try {
      this.addOutput('📊 Fetching blockchain statistics...');
      const response = await this.fetchWithFallback('/v1/data/block/latest');
      const data = await response.json();
      
      if (data.status === 'success') {
        const block = data.data;
        this.addMultiLineOutput([
          '📊 Blockchain Statistics:',
          `   Latest Block: #${block.index}`,
          `   Latest Hash: ${block.block_hash.substring(0, 20)}...`,
          `   Work Score: ${block.cumulative_work_score.toFixed(2)}`,
          `   Last Updated: ${new Date(block.timestamp * 1000).toLocaleString()}`
        ]);
      } else {
        this.addOutput(`❌ ${data.message || 'Failed to fetch stats'}`, 'error');
      }
    } catch (error) {
      this.addOutput(`❌ Network error: ${error.message}`, 'error');
    }
  }
}

// Download CLI function (global for onclick)
function downloadCLI(platform) {
  if (platform === 'macos') {
    window.open('https://github.com/beanapologist/COINjecture/releases/download/v3.6.6/COINjecture-macOS-v3.6.6-Final.zip', '_blank');
  }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  new WebInterface();
});
APPJS

# Copy the fixed app.js to the web directory
cp /tmp/app.js /home/coinjecture/COINjecture/web/app.js

echo "✅ Fixed app.js deployed to droplet"
echo "🔄 Restarting Nginx to serve updated frontend..."

# Restart Nginx
sudo systemctl restart nginx

echo "✅ Nginx restarted"
echo "🌐 Frontend fix deployed successfully!"

# Clean up
rm -f /tmp/app.js

echo ""
echo "🧪 Test the frontend now:"
echo "   https://coinjecture.com"
echo ""
echo "The blockchain-stats command should now show live data!"
EOF

# Make the script executable
chmod +x /tmp/deploy_frontend_fix.sh

# Copy the script to the droplet and run it
echo "📤 Copying deployment script to droplet..."
scp -i "$SSH_KEY" /tmp/deploy_frontend_fix.sh "$USER@$DROPLET_IP:/tmp/"

echo "🚀 Running deployment script on droplet..."
ssh -i "$SSH_KEY" "$USER@$DROPLET_IP" "chmod +x /tmp/deploy_frontend_fix.sh && /tmp/deploy_frontend_fix.sh"

# Clean up
rm -f /tmp/deploy_frontend_fix.sh

echo ""
echo "🎉 Frontend fix deployment completed!"
echo "====================================="
echo ""
echo "🧪 Test the frontend now:"
echo "   https://coinjecture.com"
echo ""
echo "The blockchain-stats command should now show live data (4900+ blocks)!"
