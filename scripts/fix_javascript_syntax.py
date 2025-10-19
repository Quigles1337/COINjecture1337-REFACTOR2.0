#!/usr/bin/env python3
"""
Fix JavaScript syntax errors in web interface
"""

import os
import sys
import re
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_javascript_syntax():
    """Fix JavaScript syntax errors in web interface"""
    
    logger.info("=== Fix JavaScript Syntax ===")
    
    # Paths
    web_dir = "/home/coinjecture/COINjecture/web"
    app_js_path = os.path.join(web_dir, "app.js")
    
    try:
        # Read current app.js
        with open(app_js_path, 'r') as f:
            app_js_content = f.read()
        
        # Fix template literal syntax errors
        # Replace ${BEANSa93eefd297ae59e963d0977319690ffbc55e2b33} with BEANSa93eefd297ae59e963d0977319690ffbc55e2b33
        wallet_address = "BEANSa93eefd297ae59e963d0977319690ffbc55e2b33"
        
        # Fix template literal usage
        patterns_to_fix = [
            (f"${{{wallet_address}}}", wallet_address),
            (f"`Address: ${{{wallet_address}}}`", f"`Address: {wallet_address}`"),
            (f"`   Address: ${{{wallet_address}}}`", f"`   Address: {wallet_address}`"),
            (f"this.copyToClipboard(${{{wallet_address}}})", f"this.copyToClipboard('{wallet_address}')"),
            (f"this.fetchWithFallback(`/v1/rewards/${{{wallet_address}}}`)", f"this.fetchWithFallback(`/v1/rewards/{wallet_address}`)"),
        ]
        
        fixes_applied = 0
        for pattern, replacement in patterns_to_fix:
            if pattern in app_js_content:
                app_js_content = app_js_content.replace(pattern, replacement)
                fixes_applied += 1
                logger.info(f"Fixed pattern: {pattern[:50]}...")
        
        # Also fix any remaining template literal issues
        # Look for ${BEANS...} patterns and replace them
        template_literal_pattern = r'\$\{BEANSa93eefd297ae59e963d0977319690ffbc55e2b33\}'
        if re.search(template_literal_pattern, app_js_content):
            app_js_content = re.sub(template_literal_pattern, wallet_address, app_js_content)
            fixes_applied += 1
            logger.info("Fixed remaining template literal patterns")
        
        # Write fixed app.js
        with open(app_js_path, 'w') as f:
            f.write(app_js_content)
        
        logger.info(f"✅ Applied {fixes_applied} JavaScript syntax fixes")
        
        # Restart API service
        logger.info("Restarting API service...")
        import subprocess
        result = subprocess.run(['systemctl', 'restart', 'coinjecture-api'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ API service restarted successfully")
        else:
            logger.error(f"❌ Failed to restart API service: {result.stderr}")
            return False
        
        logger.info("✅ JavaScript syntax fixes completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error fixing JavaScript syntax: {e}")
        return False

if __name__ == "__main__":
    success = fix_javascript_syntax()
    if success:
        print("✅ JavaScript syntax fixes completed successfully")
    else:
        print("❌ Failed to fix JavaScript syntax")
        sys.exit(1)
