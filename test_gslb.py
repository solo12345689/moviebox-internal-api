import sys
import os
import logging
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GSLB-Tester")

# Add current dir to path
sys.path.append(os.getcwd())

from moviebox_api.client import MovieBoxClient

def test_gslb():
    print("\n--- MOVIEBOX GSLB MASTER SWITCH CONVERSION ---")
    client = MovieBoxClient()
    
    # Use fixed metadata for consistency during sign debugging
    package_name = "com.community.mbox.in"
    device_id = "868203051234567" # Fixed for debugging
    
    # Try to convert api6 (Primary) and api5 (Secondary)
    domains_to_test = ["api6.aoneroom.com", "api5.aoneroom.com"]
    print(f"REQUESTING CONVERSION FOR: {domains_to_test}")
    
    conv_map = client.convert_domains(domains_to_test)
    
    if conv_map:
        print("\n✅ GSLB CONVERSION SUCCESS!")
        print("MAPPING RESULTS:")
        for orig, conv in conv_map.items():
            print(f"  {orig} --> {conv}")
            if orig == conv:
                print(f"    (Domain is healthy and stable in your region)")
            else:
                print(f"    (🚨 HEALED: GSLB redirected you to a better mirror!)")
    else:
        print("\n❌ GSLB CONVERSION FAILED or returned empty map.")

if __name__ == "__main__":
    test_gslb()
