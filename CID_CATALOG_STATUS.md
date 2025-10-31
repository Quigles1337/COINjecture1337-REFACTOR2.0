# 📊 CID Catalog Status - Production Data

## ✅ **Catalog Complete**

**Generated:** 2025-10-31  
**Database:** `/opt/coinjecture/data/blockchain.db`  
**Total Blocks:** 13,183

---

## 📈 **Catalog Statistics:**

### **CID Status:**
- **Total Blocks:** 13,183
- **Blocks with CID:** 8,147 (61.8%) ✅
- **Blocks without CID:** 5,036 (38.2%) ⏳
- **Unique CIDs:** 8,145

### **Index Tables Created:**
1. **`cid_index`** table
   - 8,145 entries cataloged
   - Indexed by CID, height, timestamp
   - Fast lookups enabled

2. **`missing_cid_index`** table
   - 5,036 entries indexed
   - Ready for regeneration
   - Will regenerate once equilibrium stabilizes

---

## 🔍 **What's Cataloged:**

### **✅ Existing CIDs (8,145):**
- All CIDs indexed in `cid_index` table
- Can query: `SELECT * FROM cid_index WHERE cid = 'Qm...'`
- Can find blocks: `SELECT * FROM cid_index WHERE first_block_height <= ? AND last_block_height >= ?`

### **⏳ Missing CIDs (5,036):**
- All missing CIDs indexed in `missing_cid_index` table
- Ready for regeneration once equilibrium stabilizes
- Can query: `SELECT * FROM missing_cid_index WHERE needs_regeneration = 1`

---

## 🎯 **Regeneration Strategy:**

### **When to Regenerate:**
Wait for equilibrium to stabilize:
- Monitor λ/η ratio: Should be ~1.0
- Monitor CID success rate: Should be >95%
- Monitor block intervals: Should be ~14s

### **How to Regenerate:**
```bash
# 1. Check equilibrium status
ssh root@167.172.213.70 "journalctl -u coinjecture-api -f | grep Equilibrium"

# 2. Once stable (λ/η ≈ 1.0), regenerate missing CIDs
ssh root@167.172.213.70 "cd /opt/coinjecture && python3 scripts/catalog_and_regenerate_cids.py --regenerate"

# 3. Test with first 100 blocks
ssh root@167.172.213.70 "cd /opt/coinjecture && python3 scripts/catalog_and_regenerate_cids.py --regenerate --max-blocks 100"

# 4. Full regeneration (all 5,036 blocks)
ssh root@167.172.213.70 "cd /opt/coinjecture && python3 scripts/catalog_and_regenerate_cids.py --regenerate"
```

---

## 📊 **Query Examples:**

### **Find CID by block height:**
```sql
SELECT cid FROM cid_index 
WHERE first_block_height <= 100 AND last_block_height >= 100;
```

### **Find all blocks with missing CIDs:**
```sql
SELECT height, block_hash, timestamp 
FROM missing_cid_index 
WHERE needs_regeneration = 1 
ORDER BY height ASC;
```

### **Count CIDs by date range:**
```sql
SELECT COUNT(*) FROM cid_index 
WHERE created_at >= ? AND created_at <= ?;
```

### **Get CID statistics:**
```sql
SELECT 
    COUNT(*) as total_cids,
    COUNT(DISTINCT first_block_height) as blocks_covered,
    MIN(first_block_height) as first_block,
    MAX(last_block_height) as last_block
FROM cid_index;
```

---

## ⚠️ **Important Notes:**

1. **Do NOT regenerate yet** - Wait for equilibrium to stabilize
2. **Monitor logs** - Watch for λ/η ratio approaching 1.0
3. **Test first** - Regenerate first 100 blocks to verify process
4. **Batch processing** - Regeneration processes in batches of 100
5. **IPFS required** - Make sure IPFS daemon is running for regeneration

---

## 📋 **Status Summary:**

### **✅ Completed:**
- ✅ CID catalog created (8,145 CIDs indexed)
- ✅ CID index table created (fast lookups)
- ✅ Missing CID index created (5,036 blocks ready)
- ✅ Rate limiter deployed (equilibrium restored)
- ✅ Regeneration script ready

### **⏳ Waiting:**
- ⏳ Equilibrium to stabilize (monitor λ/η ratio)
- ⏳ CID success rate >95% (validate improvement)
- ⏳ Regeneration to complete (once stable)

---

## 🎯 **Expected Timeline:**

### **Week 1: Monitor Equilibrium**
- Watch λ/η ratio stabilize → 1.0
- Monitor CID success rate → >95%
- Measure block intervals → ~14s

### **Week 2: Regenerate Missing CIDs**
- Test with first 100 blocks
- Verify regeneration works
- Full regeneration of 5,036 blocks

### **Week 3: Validate Complete**
- All 13,183 blocks have CIDs
- CID success rate >99%
- Network at equilibrium

---

## 📊 **Final Statistics (After Regeneration):**

### **Current:**
```
Total Blocks:      13,183
With CID:          8,147 (61.8%)
Without CID:       5,036 (38.2%)
Unique CIDs:       8,145
```

### **After Regeneration (Expected):**
```
Total Blocks:      13,183
With CID:          13,183 (100%) ✅
Without CID:       0 (0%) ✅
Unique CIDs:       ~13,183
```

---

**Catalog complete. Ready for regeneration once equilibrium stabilizes.**

