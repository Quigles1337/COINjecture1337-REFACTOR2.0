#!/bin/bash
# Delete ALL old code directories EXCEPT /opt/coinjecture

echo "🗑️  Deleting old code directories..."

# Delete old installation
echo "Deleting /home/coinjecture/COINjecture..."
rm -rf /home/coinjecture/COINjecture

# Delete old consensus directory (keep only as reference)
echo "Moving old consensus directory to backup..."
mv /opt/coinjecture /opt/coinjecture.old

# Delete any other old installations
echo "Cleaning up any other old installations..."
rm -rf /home/coinjecture/COINjecture_backup_*

# Verify only one installation remains
echo "🔍 Verifying single code installation..."
remaining_installations=$(find /opt -name "faucet_server_cors_fixed.py" | wc -l)

if [ $remaining_installations -eq 1 ]; then
    echo "✅ Only one installation remains:"
    find /opt -name "faucet_server_cors_fixed.py"
else
    echo "⚠️  Found $remaining_installations installations:"
    find /opt -name "faucet_server_cors_fixed.py"
fi
