#!/usr/bin/env python3
"""
Test that Chatwoot configurations are loaded correctly after the fix
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from app.services.chatwoot_service import initialize_chatwoot_configs, chatwoot_service
from app.services.directus_service import directus_service

async def test_chatwoot_config_loading():
    """Test that Chatwoot configurations load properly from Directus."""
    
    print("\n🧪 TESTING CHATWOOT CONFIG LOADING")
    print("=" * 80)
    
    # First, let's see what hotels are in Directus
    print("\n1️⃣ Checking hotels in Directus...")
    hotels = await directus_service.get_hotels_with_chatwoot_config()
    print(f"   Found {len(hotels)} hotels with Chatwoot config")
    
    for hotel in hotels:
        print(f"\n   Hotel {hotel.get('id')} - {hotel.get('name')}:")
        print(f"     - chatwoot_base_url: {hotel.get('chatwoot_base_url')}")
        print(f"     - chatwoot_api_token: {'SET' if hotel.get('chatwoot_api_token') else 'NOT SET'}")
        print(f"     - chatwoot_api_access_token: {'SET' if hotel.get('chatwoot_api_access_token') else 'NOT SET'}")
        print(f"     - chatwoot_account_id: {hotel.get('chatwoot_account_id')}")
    
    # Now initialize the configs
    print("\n2️⃣ Initializing Chatwoot configurations...")
    await initialize_chatwoot_configs()
    
    # Check what was loaded
    print("\n3️⃣ Checking loaded configurations...")
    print(f"   Total configs loaded: {len(chatwoot_service.configs)}")
    
    for hotel_id, config in chatwoot_service.configs.items():
        print(f"\n   Hotel ID {hotel_id}:")
        print(f"     - base_url: {config.base_url}")
        print(f"     - api_access_token: {config.api_access_token[:10]}...")
        print(f"     - account_id: {config.account_id}")
        print(f"     - inbox_id: {config.inbox_id}")
    
    # Specifically check hotel 2
    print("\n4️⃣ Checking Hotel ID 2 specifically...")
    config_2 = chatwoot_service.get_hotel_config("2")
    if config_2:
        print(f"   ✅ Config found for hotel 2!")
        print(f"     - base_url: {config_2.base_url}")
        print(f"     - api_access_token: {config_2.api_access_token[:10]}...")
        print(f"     - account_id: {config_2.account_id}")
    else:
        print(f"   ❌ No config found for hotel 2")
    
    # Close the service
    await chatwoot_service.close()
    
    print("\n✅ Test completed!")
    return len(chatwoot_service.configs) > 0

if __name__ == "__main__":
    success = asyncio.run(test_chatwoot_config_loading())
    if success:
        print("\n🎉 Chatwoot configurations are loading correctly!")
    else:
        print("\n❌ Failed to load Chatwoot configurations")
        sys.exit(1)