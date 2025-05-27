#!/usr/bin/env python3
import os

print("🔍 Setup Verification for Test_real_life-1-rupesh")
print("=" * 50)

# Check API Key
if os.path.exists("config/api_keys.env"):
    with open("config/api_keys.env", "r") as f:
        content = f.read()
    
    if "sk-proj-V3wF9ysUVMz0tO8NDDTBQ" in content:
        print("✅ API Key: Updated")
    else:
        print("❌ API Key: Not Updated")
        
    if "gpt-4.1" in content:
        print("✅ Model: gpt-4.1")
    else:
        print("❌ Model: Not Updated")
else:
    print("❌ Config file not found")

# Check Date Updates
if os.path.exists("README.md"):
    with open("README.md", "r") as f:
        content = f.read()
    
    if "May 2025" in content:
        print("✅ Date: May 2025")
    else:
        print("❌ Date: Not Updated")

print("\n🚀 Ready to run: python3 run_test.py") 