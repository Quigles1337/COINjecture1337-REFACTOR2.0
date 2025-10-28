// COINjecture Web Interface - Blockchain Explorer Module
// Version: 3.15.0

import { api } from '../core/api.js';
import { IPFS_GATEWAYS, ERROR_MESSAGES } from '../shared/constants.js';
import { numberUtils, dateUtils, domUtils, validationUtils, clipboardUtils } from '../shared/utils.js';

/**
 * Blockchain Explorer Controller
 */
export class BlockchainExplorer {
    constructor() {
        this.isActive = false;
        this.currentPage = 1;
        this.itemsPerPage = 20;
        this.searchQuery = '';
        this.filterType = 'all';
        this.sortBy = 'timestamp';
        this.sortOrder = 'desc';
        this.blocks = [];
        this.transactions = [];
        this.addresses = [];
        
        this.initializeElements();
        this.attachEventListeners();
    }

    /**
     * Initialize DOM elements
     */
    initializeElements() {
        // Search and filter elements
        this.searchInput = document.getElementById('explorer-search');
        this.filterSelect = document.getElementById('explorer-filter');
        this.sortSelect = document.getElementById('explorer-sort');
        this.sortOrderBtn = document.getElementById('explorer-sort-order');
        
        // Results elements
        this.resultsContainer = document.getElementById('explorer-results');
        this.resultsCount = document.getElementById('explorer-results-count');
        this.loadingIndicator = document.getElementById('explorer-loading');
        
        // Pagination elements
        this.paginationContainer = document.getElementById('explorer-pagination');
        this.prevPageBtn = document.getElementById('explorer-prev-page');
        this.nextPageBtn = document.getElementById('explorer-next-page');
        this.pageInfo = document.getElementById('explorer-page-info');
        
        // Block detail elements
        this.blockDetailModal = document.getElementById('block-detail-modal');
        this.blockDetailContent = document.getElementById('block-detail-content');
        this.closeBlockDetailBtn = document.getElementById('close-block-detail');
        
        // Transaction detail elements
        this.transactionDetailModal = document.getElementById('transaction-detail-modal');
        this.transactionDetailContent = document.getElementById('transaction-detail-content');
        this.closeTransactionDetailBtn = document.getElementById('close-transaction-detail');
        
        // Address detail elements
        this.addressDetailModal = document.getElementById('address-detail-modal');
        this.addressDetailContent = document.getElementById('address-detail-content');
        this.closeAddressDetailBtn = document.getElementById('close-address-detail');
        
        // Statistics elements
        this.totalBlocks = document.getElementById('total-blocks');
        this.totalTransactions = document.getElementById('total-transactions');
        this.totalAddresses = document.getElementById('total-addresses');
        this.networkHashRate = document.getElementById('network-hash-rate');
        this.avgBlockTime = document.getElementById('avg-block-time');
        this.lastBlockTime = document.getElementById('last-block-time');
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        // Search and filter
        if (this.searchInput) {
            this.searchInput.addEventListener('input', (e) => {
                this.searchQuery = e.target.value;
                this.debounceSearch();
            });
        }
        
        if (this.filterSelect) {
            this.filterSelect.addEventListener('change', (e) => {
                this.filterType = e.target.value;
                this.search();
            });
        }
        
        if (this.sortSelect) {
            this.sortSelect.addEventListener('change', (e) => {
                this.sortBy = e.target.value;
                this.search();
            });
        }
        
        if (this.sortOrderBtn) {
            this.sortOrderBtn.addEventListener('click', () => {
                this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc';
                this.updateSortOrderButton();
                this.search();
            });
        }
        
        // Pagination
        if (this.prevPageBtn) {
            this.prevPageBtn.addEventListener('click', () => {
                this.previousPage();
            });
        }
        
        if (this.nextPageBtn) {
            this.nextPageBtn.addEventListener('click', () => {
                this.nextPage();
            });
        }
        
        // Modal close buttons
        if (this.closeBlockDetailBtn) {
            this.closeBlockDetailBtn.addEventListener('click', () => {
                this.closeBlockDetail();
            });
        }
        
        if (this.closeTransactionDetailBtn) {
            this.closeTransactionDetailBtn.addEventListener('click', () => {
                this.closeTransactionDetail();
            });
        }
        
        if (this.closeAddressDetailBtn) {
            this.closeAddressDetailBtn.addEventListener('click', () => {
                this.closeAddressDetail();
            });
        }
        
        // Close modals on outside click
        if (this.blockDetailModal) {
            this.blockDetailModal.addEventListener('click', (e) => {
                if (e.target === this.blockDetailModal) {
                    this.closeBlockDetail();
                }
            });
        }
        
        if (this.transactionDetailModal) {
            this.transactionDetailModal.addEventListener('click', (e) => {
                if (e.target === this.transactionDetailModal) {
                    this.closeTransactionDetail();
                }
            });
        }
        
        if (this.addressDetailModal) {
            this.addressDetailModal.addEventListener('click', (e) => {
                if (e.target === this.addressDetailModal) {
                    this.closeAddressDetail();
                }
            });
        }
    }

    /**
     * Initialize explorer
     */
    async initialize() {
        try {
            console.log('Initializing blockchain explorer...');
            
            // Load initial data
            await this.loadStatistics();
            await this.loadInitialData();
            
            console.log('Blockchain explorer initialized successfully');
            
        } catch (error) {
            console.error('Failed to initialize blockchain explorer:', error);
        }
    }

    /**
     * Load statistics
     */
    async loadStatistics() {
        try {
            const metrics = await api.getMetricsDashboard();
            
            if (metrics?.data) {
                const data = metrics.data;
                
                if (this.totalBlocks) {
                    this.totalBlocks.textContent = data.blockchain?.validated_blocks?.toLocaleString() || '0';
                }
                
                if (this.totalTransactions) {
                    this.totalTransactions.textContent = data.transactions?.total?.toLocaleString() || '0';
                }
                
                if (this.totalAddresses) {
                    this.totalAddresses.textContent = data.network?.addresses?.toLocaleString() || '0';
                }
                
                if (this.networkHashRate) {
                    this.networkHashRate.textContent = numberUtils.formatHashRate(data.hash_rate?.current_hs || 0);
                }
                
                if (this.avgBlockTime) {
                    this.avgBlockTime.textContent = (data.block_time?.avg_seconds || 0).toFixed(2) + 's';
                }
                
                if (this.lastBlockTime) {
                    this.lastBlockTime.textContent = dateUtils.getRelativeTime(data.blockchain?.last_block_time || Date.now());
                }
            }
            
        } catch (error) {
            console.error('Failed to load statistics:', error);
        }
    }

    /**
     * Load initial data
     */
    async loadInitialData() {
        this.showLoading(true);
        
        try {
            // Load recent blocks
            await this.loadRecentBlocks();
            
            // Display results
            this.displayResults();
            
        } catch (error) {
            console.error('Failed to load initial data:', error);
            this.showError('Failed to load blockchain data');
        } finally {
            this.showLoading(false);
        }
    }

    /**
     * Load recent blocks
     */
    async loadRecentBlocks() {
        try {
            const metrics = await api.getMetricsDashboard();
            const latestBlock = metrics?.data?.blockchain?.latest_block || 0;
            
            this.blocks = [];
            
            // Load last 20 blocks
            for (let i = 0; i < Math.min(20, latestBlock); i++) {
                const blockIndex = latestBlock - i;
                try {
                    const block = await api.getBlockByIndex(blockIndex);
                    if (block) {
                        this.blocks.push({
                            type: 'block',
                            ...block,
                            timestamp: block.timestamp || Date.now() - (i * 60000) // Simulate timestamps
                        });
                    }
                } catch (error) {
                    console.warn(`Failed to fetch block ${blockIndex}:`, error);
                }
            }
            
        } catch (error) {
            console.error('Failed to load recent blocks:', error);
        }
    }

    /**
     * Search functionality
     */
    async search() {
        this.showLoading(true);
        
        try {
            let results = [];
            
            if (this.filterType === 'all' || this.filterType === 'blocks') {
                results = [...results, ...this.blocks];
            }
            
            if (this.filterType === 'all' || this.filterType === 'transactions') {
                results = [...results, ...this.transactions];
            }
            
            if (this.filterType === 'all' || this.filterType === 'addresses') {
                results = [...results, ...this.addresses];
            }
            
            // Apply search filter
            if (this.searchQuery) {
                results = results.filter(item => {
                    const searchLower = this.searchQuery.toLowerCase();
                    return (
                        (item.hash && item.hash.toLowerCase().includes(searchLower)) ||
                        (item.address && item.address.toLowerCase().includes(searchLower)) ||
                        (item.miner && item.miner.toLowerCase().includes(searchLower)) ||
                        (item.index && item.index.toString().includes(searchLower))
                    );
                });
            }
            
            // Sort results
            results = this.sortResults(results);
            
            // Update pagination
            this.updatePagination(results.length);
            
            // Display results
            this.displayResults(results);
            
        } catch (error) {
            console.error('Search failed:', error);
            this.showError('Search failed');
        } finally {
            this.showLoading(false);
        }
    }

    /**
     * Sort results
     */
    sortResults(results) {
        return results.sort((a, b) => {
            let aValue, bValue;
            
            switch (this.sortBy) {
                case 'timestamp':
                    aValue = a.timestamp || 0;
                    bValue = b.timestamp || 0;
                    break;
                case 'index':
                    aValue = a.index || 0;
                    bValue = b.index || 0;
                    break;
                case 'hash':
                    aValue = a.hash || '';
                    bValue = b.hash || '';
                    break;
                default:
                    aValue = a.timestamp || 0;
                    bValue = b.timestamp || 0;
            }
            
            if (this.sortOrder === 'asc') {
                return aValue > bValue ? 1 : -1;
            } else {
                return aValue < bValue ? 1 : -1;
            }
        });
    }

    /**
     * Display results
     */
    displayResults(results = null) {
        if (!this.resultsContainer) return;
        
        const data = results || this.blocks;
        const startIndex = (this.currentPage - 1) * this.itemsPerPage;
        const endIndex = startIndex + this.itemsPerPage;
        const pageData = data.slice(startIndex, endIndex);
        
        if (pageData.length === 0) {
            this.resultsContainer.innerHTML = '<div class="no-results">No results found</div>';
            return;
        }
        
        const resultsHtml = pageData.map(item => this.createResultItem(item)).join('');
        this.resultsContainer.innerHTML = resultsHtml;
        
        // Update results count
        if (this.resultsCount) {
            this.resultsCount.textContent = `${data.length} result${data.length !== 1 ? 's' : ''}`;
        }
    }

    /**
     * Create result item HTML
     */
    createResultItem(item) {
        const timestamp = new Date(item.timestamp).toLocaleString();
        
        if (item.type === 'block' || item.index !== undefined) {
            return `
                <div class="explorer-item block-item" onclick="explorer.showBlockDetail(${item.index})">
                    <div class="item-header">
                        <span class="item-type">Block</span>
                        <span class="item-index">#${item.index}</span>
                        <span class="item-time">${timestamp}</span>
                    </div>
                    <div class="item-content">
                        <div class="item-hash">
                            <span class="label">Hash:</span>
                            <span class="value">${item.hash ? item.hash.substring(0, 16) + '...' : 'N/A'}</span>
                        </div>
                        <div class="item-miner">
                            <span class="label">Miner:</span>
                            <span class="value">${item.miner ? item.miner.substring(0, 16) + '...' : 'N/A'}</span>
                        </div>
                        <div class="item-work-score">
                            <span class="label">Work Score:</span>
                            <span class="value">${item.work_score || 0}</span>
                        </div>
                    </div>
                </div>
            `;
        } else if (item.type === 'transaction' || item.tx_hash) {
            return `
                <div class="explorer-item transaction-item" onclick="explorer.showTransactionDetail('${item.tx_hash}')">
                    <div class="item-header">
                        <span class="item-type">Transaction</span>
                        <span class="item-time">${timestamp}</span>
                    </div>
                    <div class="item-content">
                        <div class="item-hash">
                            <span class="label">Hash:</span>
                            <span class="value">${item.tx_hash ? item.tx_hash.substring(0, 16) + '...' : 'N/A'}</span>
                        </div>
                        <div class="item-from">
                            <span class="label">From:</span>
                            <span class="value">${item.from ? item.from.substring(0, 16) + '...' : 'N/A'}</span>
                        </div>
                        <div class="item-to">
                            <span class="label">To:</span>
                            <span class="value">${item.to ? item.to.substring(0, 16) + '...' : 'N/A'}</span>
                        </div>
                        <div class="item-amount">
                            <span class="label">Amount:</span>
                            <span class="value">${item.amount || 0} BEANS</span>
                        </div>
                    </div>
                </div>
            `;
        } else if (item.type === 'address' || item.address) {
            return `
                <div class="explorer-item address-item" onclick="explorer.showAddressDetail('${item.address}')">
                    <div class="item-header">
                        <span class="item-type">Address</span>
                        <span class="item-time">${timestamp}</span>
                    </div>
                    <div class="item-content">
                        <div class="item-address">
                            <span class="label">Address:</span>
                            <span class="value">${item.address ? item.address.substring(0, 16) + '...' : 'N/A'}</span>
                        </div>
                        <div class="item-balance">
                            <span class="label">Balance:</span>
                            <span class="value">${item.balance || 0} BEANS</span>
                        </div>
                        <div class="item-transactions">
                            <span class="label">Transactions:</span>
                            <span class="value">${item.transaction_count || 0}</span>
                        </div>
                    </div>
                </div>
            `;
        }
        
        return '';
    }

    /**
     * Show block detail
     */
    async showBlockDetail(blockIndex) {
        try {
            const block = await api.getBlockByIndex(blockIndex);
            if (!block) {
                this.showError('Block not found');
                return;
            }
            
            this.displayBlockDetail(block);
            this.showBlockDetailModal();
            
        } catch (error) {
            console.error('Failed to load block detail:', error);
            this.showError('Failed to load block details');
        }
    }

    /**
     * Display block detail
     */
    displayBlockDetail(block) {
        if (!this.blockDetailContent) return;
        
        const blockDetailHtml = `
            <div class="block-detail">
                <div class="detail-header">
                    <h2>Block #${block.index}</h2>
                    <div class="detail-actions">
                        <button onclick="explorer.copyToClipboard('${block.hash}')" class="copy-btn">📋 Copy Hash</button>
                        <button onclick="explorer.openIPFSViewer('${block.cid}')" class="ipfs-btn">📦 View IPFS</button>
                    </div>
                </div>
                
                <div class="detail-content">
                    <div class="detail-section">
                        <h3>Block Information</h3>
                        <div class="detail-grid">
                            <div class="detail-item">
                                <span class="label">Index:</span>
                                <span class="value">${block.index}</span>
                            </div>
                            <div class="detail-item">
                                <span class="label">Hash:</span>
                                <span class="value">${block.hash}</span>
                            </div>
                            <div class="detail-item">
                                <span class="label">Previous Hash:</span>
                                <span class="value">${block.previous_hash || 'N/A'}</span>
                            </div>
                            <div class="detail-item">
                                <span class="label">Timestamp:</span>
                                <span class="value">${new Date(block.timestamp).toLocaleString()}</span>
                            </div>
                            <div class="detail-item">
                                <span class="label">Miner:</span>
                                <span class="value">${block.miner}</span>
                            </div>
                            <div class="detail-item">
                                <span class="label">Work Score:</span>
                                <span class="value">${block.work_score || 0}</span>
                            </div>
                            <div class="detail-item">
                                <span class="label">Nonce:</span>
                                <span class="value">${block.nonce || 0}</span>
                            </div>
                            <div class="detail-item">
                                <span class="label">Difficulty:</span>
                                <span class="value">${block.difficulty || 1}</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="detail-section">
                        <h3>IPFS Data</h3>
                        <div class="detail-grid">
                            <div class="detail-item">
                                <span class="label">CID:</span>
                                <span class="value">${block.cid || 'N/A'}</span>
                            </div>
                            <div class="detail-item">
                                <span class="label">Data Size:</span>
                                <span class="value">${block.data_size || 'N/A'}</span>
                            </div>
                        </div>
                    </div>
                    
                    ${block.problem ? `
                    <div class="detail-section">
                        <h3>Problem Data</h3>
                        <div class="detail-grid">
                            <div class="detail-item">
                                <span class="label">Problem Size:</span>
                                <span class="value">${block.problem.numbers?.length || 0}</span>
                            </div>
                            <div class="detail-item">
                                <span class="label">Target:</span>
                                <span class="value">${block.problem.target || 'N/A'}</span>
                            </div>
                        </div>
                    </div>
                    ` : ''}
                    
                    ${block.solution ? `
                    <div class="detail-section">
                        <h3>Solution Data</h3>
                        <div class="detail-grid">
                            <div class="detail-item">
                                <span class="label">Method:</span>
                                <span class="value">${block.solution.method || 'N/A'}</span>
                            </div>
                            <div class="detail-item">
                                <span class="label">Solve Time:</span>
                                <span class="value">${block.solution.solve_time || 0}ms</span>
                            </div>
                            <div class="detail-item">
                                <span class="label">Work Score:</span>
                                <span class="value">${block.solution.work_score || 0}</span>
                            </div>
                        </div>
                    </div>
                    ` : ''}
                </div>
            </div>
        `;
        
        this.blockDetailContent.innerHTML = blockDetailHtml;
    }

    /**
     * Show transaction detail
     */
    async showTransactionDetail(txHash) {
        try {
            // This would typically fetch transaction details from the API
            // For now, we'll create a mock transaction
            const transaction = {
                tx_hash: txHash,
                from: 'addr_1234567890abcdef',
                to: 'addr_fedcba0987654321',
                amount: 100,
                timestamp: Date.now(),
                block_index: 12345,
                gas_used: 21000,
                gas_price: 1
            };
            
            this.displayTransactionDetail(transaction);
            this.showTransactionDetailModal();
            
        } catch (error) {
            console.error('Failed to load transaction detail:', error);
            this.showError('Failed to load transaction details');
        }
    }

    /**
     * Display transaction detail
     */
    displayTransactionDetail(transaction) {
        if (!this.transactionDetailContent) return;
        
        const transactionDetailHtml = `
            <div class="transaction-detail">
                <div class="detail-header">
                    <h2>Transaction Details</h2>
                    <div class="detail-actions">
                        <button onclick="explorer.copyToClipboard('${transaction.tx_hash}')" class="copy-btn">📋 Copy Hash</button>
                    </div>
                </div>
                
                <div class="detail-content">
                    <div class="detail-section">
                        <h3>Transaction Information</h3>
                        <div class="detail-grid">
                            <div class="detail-item">
                                <span class="label">Hash:</span>
                                <span class="value">${transaction.tx_hash}</span>
                            </div>
                            <div class="detail-item">
                                <span class="label">From:</span>
                                <span class="value">${transaction.from}</span>
                            </div>
                            <div class="detail-item">
                                <span class="label">To:</span>
                                <span class="value">${transaction.to}</span>
                            </div>
                            <div class="detail-item">
                                <span class="label">Amount:</span>
                                <span class="value">${transaction.amount} BEANS</span>
                            </div>
                            <div class="detail-item">
                                <span class="label">Timestamp:</span>
                                <span class="value">${new Date(transaction.timestamp).toLocaleString()}</span>
                            </div>
                            <div class="detail-item">
                                <span class="label">Block:</span>
                                <span class="value">#${transaction.block_index}</span>
                            </div>
                            <div class="detail-item">
                                <span class="label">Gas Used:</span>
                                <span class="value">${transaction.gas_used}</span>
                            </div>
                            <div class="detail-item">
                                <span class="label">Gas Price:</span>
                                <span class="value">${transaction.gas_price} BEANS</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        this.transactionDetailContent.innerHTML = transactionDetailHtml;
    }

    /**
     * Show address detail
     */
    async showAddressDetail(address) {
        try {
            const rewards = await api.getUserRewards(address);
            const balance = await api.getWalletBalance(address);
            
            const addressData = {
                address: address,
                balance: balance.balance || 0,
                total_rewards: rewards.totalRewards || 0,
                transaction_count: rewards.transactionCount || 0,
                first_seen: rewards.firstSeen || Date.now(),
                last_seen: rewards.lastSeen || Date.now()
            };
            
            this.displayAddressDetail(addressData);
            this.showAddressDetailModal();
            
        } catch (error) {
            console.error('Failed to load address detail:', error);
            this.showError('Failed to load address details');
        }
    }

    /**
     * Display address detail
     */
    displayAddressDetail(address) {
        if (!this.addressDetailContent) return;
        
        const addressDetailHtml = `
            <div class="address-detail">
                <div class="detail-header">
                    <h2>Address Details</h2>
                    <div class="detail-actions">
                        <button onclick="explorer.copyToClipboard('${address.address}')" class="copy-btn">📋 Copy Address</button>
                    </div>
                </div>
                
                <div class="detail-content">
                    <div class="detail-section">
                        <h3>Address Information</h3>
                        <div class="detail-grid">
                            <div class="detail-item">
                                <span class="label">Address:</span>
                                <span class="value">${address.address}</span>
                            </div>
                            <div class="detail-item">
                                <span class="label">Balance:</span>
                                <span class="value">${address.balance} BEANS</span>
                            </div>
                            <div class="detail-item">
                                <span class="label">Total Rewards:</span>
                                <span class="value">${address.total_rewards} BEANS</span>
                            </div>
                            <div class="detail-item">
                                <span class="label">Transactions:</span>
                                <span class="value">${address.transaction_count}</span>
                            </div>
                            <div class="detail-item">
                                <span class="label">First Seen:</span>
                                <span class="value">${new Date(address.first_seen).toLocaleString()}</span>
                            </div>
                            <div class="detail-item">
                                <span class="label">Last Seen:</span>
                                <span class="value">${new Date(address.last_seen).toLocaleString()}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        this.addressDetailContent.innerHTML = addressDetailHtml;
    }

    /**
     * Show block detail modal
     */
    showBlockDetailModal() {
        if (this.blockDetailModal) {
            this.blockDetailModal.style.display = 'flex';
        }
    }

    /**
     * Close block detail modal
     */
    closeBlockDetail() {
        if (this.blockDetailModal) {
            this.blockDetailModal.style.display = 'none';
        }
    }

    /**
     * Show transaction detail modal
     */
    showTransactionDetailModal() {
        if (this.transactionDetailModal) {
            this.transactionDetailModal.style.display = 'flex';
        }
    }

    /**
     * Close transaction detail modal
     */
    closeTransactionDetail() {
        if (this.transactionDetailModal) {
            this.transactionDetailModal.style.display = 'none';
        }
    }

    /**
     * Show address detail modal
     */
    showAddressDetailModal() {
        if (this.addressDetailModal) {
            this.addressDetailModal.style.display = 'flex';
        }
    }

    /**
     * Close address detail modal
     */
    closeAddressDetail() {
        if (this.addressDetailModal) {
            this.addressDetailModal.style.display = 'none';
        }
    }

    /**
     * Copy to clipboard
     */
    async copyToClipboard(text) {
        const success = await clipboardUtils.copyToClipboard(text);
        if (success) {
            this.showSuccess('Copied to clipboard');
        } else {
            this.showError('Failed to copy to clipboard');
        }
    }

    /**
     * Open IPFS viewer
     */
    openIPFSViewer(cid) {
        if (!cid) {
            this.showError('No CID provided');
            return;
        }
        
        const gateways = IPFS_GATEWAYS.map(gateway => `${gateway}${cid}`);
        const newWindow = window.open(gateways[0], '_blank');
        
        // If the first gateway fails, show a modal with options
        setTimeout(() => {
            if (newWindow && newWindow.closed) {
                this.showIPFSModal(cid, gateways);
            }
        }, 2000);
    }

    /**
     * Show IPFS modal
     */
    showIPFSModal(cid, gateways) {
        const modal = domUtils.createElement('div', {
            className: 'ipfs-modal',
            innerHTML: `
                <div class="ipfs-modal-content">
                    <div class="ipfs-modal-header">
                        <h3>📦 IPFS Content Viewer</h3>
                        <button class="ipfs-modal-close" onclick="this.closest('.ipfs-modal').remove()">×</button>
                    </div>
                    <div class="ipfs-modal-body">
                        <p><strong>CID:</strong> ${cid}</p>
                        <p>Choose a gateway to view the content:</p>
                        <div class="ipfs-gateway-list">
                            ${gateways.map((gateway, index) => `
                                <a href="${gateway}" target="_blank" class="ipfs-gateway-link">
                                    Gateway ${index + 1}: ${gateway.split('/')[2]}
                                </a>
                            `).join('')}
                        </div>
                    </div>
                </div>
            `
        });
        
        document.body.appendChild(modal);
        
        // Close modal when clicking outside
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }

    /**
     * Update pagination
     */
    updatePagination(totalItems) {
        const totalPages = Math.ceil(totalItems / this.itemsPerPage);
        
        if (this.prevPageBtn) {
            this.prevPageBtn.disabled = this.currentPage <= 1;
        }
        
        if (this.nextPageBtn) {
            this.nextPageBtn.disabled = this.currentPage >= totalPages;
        }
        
        if (this.pageInfo) {
            this.pageInfo.textContent = `Page ${this.currentPage} of ${totalPages}`;
        }
    }

    /**
     * Previous page
     */
    previousPage() {
        if (this.currentPage > 1) {
            this.currentPage--;
            this.search();
        }
    }

    /**
     * Next page
     */
    nextPage() {
        const totalItems = this.blocks.length + this.transactions.length + this.addresses.length;
        const totalPages = Math.ceil(totalItems / this.itemsPerPage);
        
        if (this.currentPage < totalPages) {
            this.currentPage++;
            this.search();
        }
    }

    /**
     * Update sort order button
     */
    updateSortOrderButton() {
        if (this.sortOrderBtn) {
            this.sortOrderBtn.textContent = this.sortOrder === 'asc' ? '↑' : '↓';
        }
    }

    /**
     * Debounced search
     */
    debounceSearch() {
        clearTimeout(this.searchTimeout);
        this.searchTimeout = setTimeout(() => {
            this.search();
        }, 300);
    }

    /**
     * Show loading indicator
     */
    showLoading(show) {
        if (this.loadingIndicator) {
            this.loadingIndicator.style.display = show ? 'block' : 'none';
        }
    }

    /**
     * Show error message
     */
    showError(message) {
        console.error('Explorer error:', message);
        // In a real implementation, this would show a user-friendly error message
    }

    /**
     * Show success message
     */
    showSuccess(message) {
        console.log('Explorer success:', message);
        // In a real implementation, this would show a user-friendly success message
    }

    /**
     * Activate explorer
     */
    activate() {
        this.isActive = true;
        this.initialize();
    }

    /**
     * Deactivate explorer
     */
    deactivate() {
        this.isActive = false;
    }
}

// Create and export singleton instance
export const blockchainExplorer = new BlockchainExplorer();

// Export for backward compatibility
export default blockchainExplorer;
