#!/bin/bash
# Delete ALL databases EXCEPT the single source of truth

echo "🗑️  Deleting old databases..."

# Backup the correct database first
echo "Backing up correct database..."
cp /opt/coinjecture/data/blockchain.db /opt/coinjecture/data/blockchain.db.backup

# Delete all other databases
echo "Deleting old databases..."
rm -f /opt/coinjecture/data/*.db
rm -f /home/coinjecture/COINjecture/data/*.db
rm -f /opt/coinjecture/backups/**/*.db
rm -f /opt/coinjecture/src/data/*.db

# Also delete any backup directories
rm -rf /home/coinjecture/COINjecture_backup_*

# Verify only one database remains
echo "🔍 Verifying single database..."
remaining_dbs=$(find /opt -name "*.db" -type f | grep -v backup | wc -l)

if [ $remaining_dbs -eq 1 ]; then
    echo "✅ Only one database remains:"
    find /opt -name "*.db" -type f | grep -v backup
else
    echo "⚠️  Found $remaining_dbs databases:"
    find /opt -name "*.db" -type f | grep -v backup
fi
