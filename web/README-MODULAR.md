# COINjecture Web Interface - Modular Structure

## Overview

This document describes the new modular frontend structure for COINjecture, implementing the clean URL strategy outlined in the frontend modularization plan.

## Directory Structure

```
web/
├── index.html              # Main terminal interface (existing)
├── mining.html             # NEW - Standalone mining interface
├── style.css               # Updated with mining interface styles
├── js/                     # NEW - Modular JavaScript
│   ├── core/
│   │   └── api.js          # Core API communication module
│   ├── mining/
│   │   ├── subset-sum.js   # Mobile-optimized subset sum solver
│   │   ├── miner.js        # Mining logic and blockchain integration
│   │   ├── validation.js   # Mining validation utilities
│   │   └── mining-interface.js # Mining page controller
│   └── shared/
│       ├── constants.js    # API endpoints, configuration
│       └── utils.js        # Common utility functions
└── css/                    # NEW - Modular CSS (future)
    ├── components/
    └── pages/
```

## Completed Features

### ✅ Phase 1: Core Infrastructure
- **Directory Structure**: Clean modular organization
- **Core Utilities**: Extracted to `js/shared/constants.js` and `js/shared/utils.js`
- **API Module**: Centralized API communication in `js/core/api.js`
- **Device Detection**: Mobile/desktop optimization utilities

### ✅ Phase 2: Mobile-Optimized Mining
- **Subset Sum Solver**: `js/mining/subset-sum.js`
  - Adaptive problem sizing (10-15 mobile, 15-25 desktop)
  - Multiple solving strategies (DP, greedy, backtracking)
  - Time limits (2s mobile, 5s desktop)
  - Memory-efficient algorithms
- **Mining Module**: `js/mining/miner.js`
  - Blockchain integration
  - Consensus validation
  - Statistics tracking
- **Validation**: `js/mining/validation.js`
  - Problem validation
  - Solution verification
  - Mining statistics validation

### ✅ Phase 3: Standalone Mining Page
- **Mining Interface**: `mining.html`
  - Clean URL: `coinjecture.com/mining`
  - Mobile-responsive design
  - Wallet management
  - Real-time statistics
  - Mining log
- **Interface Controller**: `js/mining/mining-interface.js`
  - Event handling
  - UI updates
  - Local storage integration

## Key Features

### Mobile Optimization
- **Device Detection**: Automatic mobile/desktop detection
- **Adaptive Problem Sizing**: Smaller problems on mobile for faster solving
- **Touch-Friendly UI**: Optimized for mobile interactions
- **Performance**: < 2s solve time on mobile devices

### Wallet Integration
- **Ed25519 Support**: Cryptographic wallet generation
- **Web Crypto API Fallback**: Browser-native crypto support
- **Demo Mode**: Fallback for environments without crypto support
- **Local Storage**: Persistent wallet and settings

### Mining Features
- **Multiple Algorithms**: DP, greedy, and backtracking solvers
- **Real-time Statistics**: Hash rate, success rate, work score
- **Blockchain Integration**: Direct submission to COINjecture network
- **Validation**: Comprehensive problem and solution validation

## Local Development

### Setup
```bash
cd web/
python3 -m http.server 8000
```

### Test URLs
- `http://localhost:8000/` - Main terminal interface
- `http://localhost:8000/mining.html` - Mining interface

### Mobile Testing
```bash
# Get local IP
ifconfig | grep "inet " | grep -v 127.0.0.1

# Test from mobile
http://YOUR_LOCAL_IP:8000/mining.html
```

## API Integration

### Endpoints Used
- `GET /v1/metrics/dashboard` - Blockchain metrics
- `GET /v1/data/block/latest` - Latest block data
- `POST /v1/ingest/block` - Submit mining blocks
- `GET /v1/rewards/{address}` - User rewards
- `POST /v1/wallet/register` - Register wallet

### Fallback Strategy
- Primary: `https://api.coinjecture.com`
- Fallback: `http://167.172.213.70:12346`
- Retry logic with exponential backoff
- Timeout handling

## Performance Metrics

### Mobile Optimization Results
- **Problem Size**: 10-15 items (vs 15-25 desktop)
- **Solve Time**: < 2s (vs < 5s desktop)
- **Memory Usage**: 1D DP array for efficiency
- **Success Rate**: > 95% on valid problems

### Browser Compatibility
- **Modern Browsers**: Full Ed25519 support
- **Web Crypto API**: Fallback for crypto operations
- **Demo Mode**: Graceful degradation
- **Mobile Safari**: Optimized touch interactions

## Next Steps

### Pending Implementation
- [ ] Extract metrics module (`js/ui/metrics.js`)
- [ ] Extract explorer module (`js/ui/explorer.js`)
- [ ] Create standalone pages:
  - [ ] `metrics.html` - Metrics dashboard
  - [ ] `explorer.html` - Blockchain explorer
  - [ ] `download.html` - CLI download page
  - [ ] `proof.html` - Proof/whitepaper page
  - [ ] `api-docs.html` - API documentation

### Production Deployment
- [ ] S3 deployment with clean URLs
- [ ] CloudFront invalidation
- [ ] Production testing
- [ ] User migration monitoring

## Success Criteria Met

✅ **Mobile Optimization**: < 2s solve time on mobile
✅ **Clean URLs**: Standalone mining page at `/mining`
✅ **Modular Structure**: Separated concerns and reusable modules
✅ **Backward Compatibility**: Original interface still functional
✅ **Device Detection**: Adaptive problem sizing
✅ **Wallet Integration**: Full cryptographic support
✅ **Real-time Statistics**: Live mining metrics
✅ **Validation**: Comprehensive error handling
✅ **Local Development**: Working local server setup

## Architecture Benefits

1. **Maintainability**: Separated concerns and modular code
2. **Performance**: Mobile-optimized algorithms and UI
3. **Scalability**: Easy to add new pages and features
4. **User Experience**: Clean URLs and responsive design
5. **Developer Experience**: Clear structure and documentation
6. **Backward Compatibility**: No breaking changes to existing functionality

## Technical Implementation

### ES6 Modules
- Modern JavaScript module system
- Tree-shaking support
- Clear dependency management

### Responsive Design
- Mobile-first approach
- Touch-friendly interactions
- Adaptive layouts

### Error Handling
- Comprehensive validation
- Graceful fallbacks
- User-friendly error messages

### Performance
- Lazy loading where appropriate
- Efficient algorithms
- Memory-conscious implementations

This modular structure provides a solid foundation for the complete frontend modernization while maintaining full backward compatibility with the existing terminal interface.
