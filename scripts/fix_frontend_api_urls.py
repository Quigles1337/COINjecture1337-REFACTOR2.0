#!/usr/bin/env python3
"""
Fix frontend API URLs on droplet
Updates web files to use https://api.coinjecture.com
"""

import os
import re

def fix_api_urls(file_path):
    """Fix API URLs in a file"""
    if not os.path.exists(file_path):
        print(f"⚠️  File not found: {file_path}")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace old API URLs with new ones
    replacements = [
        (r'https://167\.172\.213\.70', 'https://api.coinjecture.com'),
        (r'http://167\.172\.213\.70:5000', 'https://api.coinjecture.com'),
        (r'167\.172\.213\.70:5000', 'api.coinjecture.com'),
        (r"this\.apiBase = window\.location\.hostname === '167\.172\.213\.70' \? '' : 'https://167\.172\.213\.70';", 
         "this.apiBase = 'https://api.coinjecture.com';"),
    ]
    
    original_content = content
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Updated: {file_path}")
        return True
    else:
        print(f"ℹ️  No changes needed: {file_path}")
        return False

def main():
    """Fix API URLs in web files"""
    print("🔧 Fixing frontend API URLs on droplet")
    print("=" * 50)
    
    web_dir = "/home/coinjecture/COINjecture/web"
    
    if not os.path.exists(web_dir):
        print(f"❌ Web directory not found: {web_dir}")
        return 1
    
    files_to_fix = [
        "app.js",
        "index.html", 
        "style.css"
    ]
    
    updated_count = 0
    for filename in files_to_fix:
        file_path = os.path.join(web_dir, filename)
        if fix_api_urls(file_path):
            updated_count += 1
    
    print(f"\n✅ Updated {updated_count} files")
    print("🌐 Frontend should now use https://api.coinjecture.com")
    
    return 0

if __name__ == "__main__":
    exit(main())
