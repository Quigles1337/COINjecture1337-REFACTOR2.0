// COINjecture Web Interface - Utility Functions
// Version: 3.15.0

import { DEVICE_CONFIG, UI_CONFIG } from './constants.js';

/**
 * Device Detection Utilities
 */
export const deviceUtils = {
  /**
   * Check if device is mobile
   */
  isMobile() {
    return window.innerWidth <= DEVICE_CONFIG.MOBILE_BREAKPOINT;
  },

  /**
   * Check if device is tablet
   */
  isTablet() {
    return window.innerWidth > DEVICE_CONFIG.MOBILE_BREAKPOINT && 
           window.innerWidth <= DEVICE_CONFIG.TABLET_BREAKPOINT;
  },

  /**
   * Check if device is desktop
   */
  isDesktop() {
    return window.innerWidth > DEVICE_CONFIG.TABLET_BREAKPOINT;
  },

  /**
   * Get device type
   */
  getDeviceType() {
    if (this.isMobile()) return 'mobile';
    if (this.isTablet()) return 'tablet';
    return 'desktop';
  },

  /**
   * Check if device supports touch
   */
  isTouchDevice() {
    return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
  }
};

/**
 * Number Formatting Utilities
 */
export const numberUtils = {
  /**
   * Format hash rate
   */
  formatHashRate(hashRate) {
    if (hashRate >= 1e9) return `${(hashRate / 1e9).toFixed(2)} GH/s`;
    if (hashRate >= 1e6) return `${(hashRate / 1e6).toFixed(2)} MH/s`;
    if (hashRate >= 1e3) return `${(hashRate / 1e3).toFixed(2)} KH/s`;
    return `${hashRate.toFixed(2)} H/s`;
  },

  /**
   * Format large numbers with commas
   */
  formatNumber(num) {
    if (num >= 1e9) return `${(num / 1e9).toFixed(2)}B`;
    if (num >= 1e6) return `${(num / 1e6).toFixed(2)}M`;
    if (num >= 1e3) return `${(num / 1e3).toFixed(2)}K`;
    return num.toString();
  },

  /**
   * Format currency
   */
  formatCurrency(amount, currency = 'BEANS') {
    return `${amount.toLocaleString()} ${currency}`;
  },

  /**
   * Format percentage
   */
  formatPercentage(value, decimals = 2) {
    return `${(value * 100).toFixed(decimals)}%`;
  },

  /**
   * Format time duration
   */
  formatDuration(ms) {
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    if (ms < 3600000) return `${(ms / 60000).toFixed(1)}m`;
    return `${(ms / 3600000).toFixed(1)}h`;
  }
};

/**
 * String Utilities
 */
export const stringUtils = {
  /**
   * Truncate string with ellipsis
   */
  truncate(str, length = 20) {
    if (str.length <= length) return str;
    return str.substring(0, length) + '...';
  },

  /**
   * Format hash for display
   */
  formatHash(hash, length = 8) {
    if (!hash) return 'N/A';
    return `${hash.substring(0, length)}...${hash.substring(hash.length - length)}`;
  },

  /**
   * Capitalize first letter
   */
  capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
  },

  /**
   * Convert to title case
   */
  toTitleCase(str) {
    return str.replace(/\w\S*/g, (txt) => 
      txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase()
    );
  }
};

/**
 * Date/Time Utilities
 */
export const dateUtils = {
  /**
   * Format timestamp
   */
  formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString();
  },

  /**
   * Get relative time
   */
  getRelativeTime(timestamp) {
    const now = Date.now();
    const diff = now - timestamp;
    
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return `${Math.floor(diff / 86400000)}d ago`;
  },

  /**
   * Format date for display
   */
  formatDate(date) {
    return new Date(date).toLocaleDateString();
  }
};

/**
 * DOM Utilities
 */
export const domUtils = {
  /**
   * Create element with attributes
   */
  createElement(tag, attributes = {}, content = '') {
    const element = document.createElement(tag);
    
    Object.entries(attributes).forEach(([key, value]) => {
      if (key === 'className') {
        element.className = value;
      } else if (key === 'innerHTML') {
        element.innerHTML = value;
      } else {
        element.setAttribute(key, value);
      }
    });
    
    if (content) {
      element.textContent = content;
    }
    
    return element;
  },

  /**
   * Add event listener with cleanup
   */
  addEventListenerWithCleanup(element, event, handler) {
    element.addEventListener(event, handler);
    return () => element.removeEventListener(event, handler);
  },

  /**
   * Show/hide element with animation
   */
  toggleElement(element, show, duration = UI_CONFIG.ANIMATION_DURATION) {
    if (show) {
      element.style.display = 'block';
      element.style.opacity = '0';
      element.style.transition = `opacity ${duration}ms ease`;
      
      requestAnimationFrame(() => {
        element.style.opacity = '1';
      });
    } else {
      element.style.opacity = '0';
      element.style.transition = `opacity ${duration}ms ease`;
      
      setTimeout(() => {
        element.style.display = 'none';
      }, duration);
    }
  },

  /**
   * Scroll to element smoothly
   */
  scrollToElement(element, offset = 0) {
    const elementPosition = element.offsetTop - offset;
    window.scrollTo({
      top: elementPosition,
      behavior: 'smooth'
    });
  },

  /**
   * Open IPFS viewer
   */
  openIPFSViewer(cid) {
    if (!cid) {
      console.error('No CID provided for IPFS viewer');
      return;
    }
    
    // Import IPFS_GATEWAYS dynamically to avoid circular imports
    // Use public gateways first for better reliability
    const gateways = [
      'https://ipfs.io/ipfs/',
      'https://cloudflare-ipfs.com/ipfs/',
      'https://gateway.pinata.cloud/ipfs/',
      'https://dweb.link/ipfs/',
      'https://gateway.ipfs.io/ipfs/',
      'http://167.172.213.70:8080/ipfs/' // Local gateway as fallback
    ];
    
    const gatewayUrls = gateways.map(gateway => `${gateway}${cid}`);
    const newWindow = window.open(gatewayUrls[0], '_blank');
    
    // Check if the window was blocked or failed to load
    setTimeout(() => {
      if (newWindow && newWindow.closed) {
        this.showIPFSModal(cid, gatewayUrls);
      } else if (newWindow) {
        // Check if the page loaded successfully
        try {
          newWindow.addEventListener('load', () => {
            // Page loaded successfully, no need for modal
          });
          newWindow.addEventListener('error', () => {
            // Page failed to load, show modal
            this.showIPFSModal(cid, gatewayUrls);
          });
        } catch (e) {
          // Cross-origin restrictions, show modal as fallback
          this.showIPFSModal(cid, gatewayUrls);
        }
      } else {
        // Window was blocked, show modal immediately
        this.showIPFSModal(cid, gatewayUrls);
      }
    }, 1000); // Reduced timeout for faster fallback
  },

  /**
   * Show IPFS modal with gateway options
   */
  showIPFSModal(cid, gateways) {
    const modal = this.createElement('div', {
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
    
    // Add click outside to close
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.remove();
      }
    });
  }
};

/**
 * Storage Utilities
 */
export const storageUtils = {
  /**
   * Save to localStorage with error handling
   */
  save(key, data) {
    try {
      localStorage.setItem(key, JSON.stringify(data));
      return true;
    } catch (error) {
      console.error('Failed to save to localStorage:', error);
      return false;
    }
  },

  /**
   * Load from localStorage with error handling
   */
  load(key, defaultValue = null) {
    try {
      const data = localStorage.getItem(key);
      return data ? JSON.parse(data) : defaultValue;
    } catch (error) {
      console.error('Failed to load from localStorage:', error);
      return defaultValue;
    }
  },

  /**
   * Remove from localStorage
   */
  remove(key) {
    try {
      localStorage.removeItem(key);
      return true;
    } catch (error) {
      console.error('Failed to remove from localStorage:', error);
      return false;
    }
  },

  /**
   * Clear all localStorage
   */
  clear() {
    try {
      localStorage.clear();
      return true;
    } catch (error) {
      console.error('Failed to clear localStorage:', error);
      return false;
    }
  }
};

/**
 * Validation Utilities
 */
export const validationUtils = {
  /**
   * Validate wallet address
   */
  isValidAddress(address) {
    return address && address.length >= 32 && /^[a-zA-Z0-9]+$/.test(address);
  },

  /**
   * Validate CID
   */
  isValidCID(cid) {
    return cid && cid.length >= 46 && /^Qm[a-zA-Z0-9]+$/.test(cid);
  },

  /**
   * Validate email
   */
  isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  },

  /**
   * Validate number range
   */
  isInRange(value, min, max) {
    const num = Number(value);
    return !isNaN(num) && num >= min && num <= max;
  }
};

/**
 * Animation Utilities
 */
export const animationUtils = {
  /**
   * Fade in element
   */
  fadeIn(element, duration = UI_CONFIG.ANIMATION_DURATION) {
    element.style.opacity = '0';
    element.style.transition = `opacity ${duration}ms ease`;
    
    requestAnimationFrame(() => {
      element.style.opacity = '1';
    });
  },

  /**
   * Fade out element
   */
  fadeOut(element, duration = UI_CONFIG.ANIMATION_DURATION) {
    element.style.transition = `opacity ${duration}ms ease`;
    element.style.opacity = '0';
    
    setTimeout(() => {
      element.style.display = 'none';
    }, duration);
  },

  /**
   * Slide in from top
   */
  slideInFromTop(element, duration = UI_CONFIG.ANIMATION_DURATION) {
    element.style.transform = 'translateY(-100%)';
    element.style.transition = `transform ${duration}ms ease`;
    
    requestAnimationFrame(() => {
      element.style.transform = 'translateY(0)';
    });
  }
};

/**
 * Clipboard Utilities
 */
export const clipboardUtils = {
  /**
   * Copy text to clipboard
   */
  async copyToClipboard(text) {
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
        return true;
      } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        const success = document.execCommand('copy');
        document.body.removeChild(textArea);
        return success;
      }
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
      return false;
    }
  }
};

/**
 * URL Utilities
 */
export const urlUtils = {
  /**
   * Get current page name from URL
   */
  getCurrentPage() {
    const path = window.location.pathname;
    if (path === '/' || path === '/index.html') return 'terminal';
    return path.substring(1).replace('.html', '');
  },

  /**
   * Navigate to page
   */
  navigateToPage(page) {
    if (page === 'terminal') {
      window.location.href = '/';
    } else {
      window.location.href = `/${page}.html`;
    }
  },

  /**
   * Add cache buster to URL
   */
  addCacheBuster(url) {
    const separator = url.includes('?') ? '&' : '?';
    return `${url}${separator}t=${Date.now()}`;
  },

  /**
   * Override the global fetch function to include cache-busting headers for API calls.
   */
  overrideFetch() {
    const originalFetch = window.fetch;
    window.fetch = function(url, options = {}) {
      const processedUrl = urlUtils.addCacheBuster(url);
      return originalFetch.call(this, processedUrl, {
        ...options,
        cache: 'no-cache',
        headers: {
          ...options.headers,
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        }
      });
    };
  }
};
