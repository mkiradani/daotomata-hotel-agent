#!/usr/bin/env python3
"""
Check if hotel ID 2 exists in Directus
"""

import asyncio
import httpx
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def check_hotel_id_2():
    """Check if hotel ID 2 exists in Directus."""
    print("\n🔍 CHECKING HOTEL ID 2 IN DIRECTUS")
    print("=" * 80)
    
    directus_url = os.getenv("DIRECTUS_URL")
    directus_token = os.getenv("DIRECTUS_TOKEN")
    
    if not directus_url or not directus_token:
        print("❌ Missing Directus credentials")
        return None
    
    async with httpx.AsyncClient() as client:
        try:
            headers = {"Authorization": f"Bearer {directus_token}"}
            
            # First, list all hotels
            print("\n📋 Listing all hotels:")
            response = await client.get(
                f"{directus_url}/items/hotels",
                headers=headers,
                params={"fields": "id,name,domain,chatwoot_base_url,chatwoot_api_token,chatwoot_api_access_token,chatwoot_account_id"}
            )
            
            if response.status_code == 200:
                data = response.json()
                hotels = data.get("data", [])
                
                print(f"✅ Found {len(hotels)} hotels:")
                for hotel in hotels:
                    print(f"   - ID: {hotel.get('id')} | Name: {hotel.get('name')} | Domain: {hotel.get('domain')}")
                    
            # Now specifically check for hotel ID 2
            print("\n🔍 Checking hotel ID 2 specifically:")
            response = await client.get(
                f"{directus_url}/items/hotels/2",
                headers=headers
            )
            
            if response.status_code == 200:
                hotel_data = response.json().get("data")
                if hotel_data:
                    print(f"✅ Hotel ID 2 exists!")
                    print(f"   Name: {hotel_data.get('name')}")
                    print(f"   Domain: {hotel_data.get('domain')}")
                    
                    # Check Chatwoot configuration
                    base_url = hotel_data.get('chatwoot_base_url')
                    api_token = hotel_data.get('chatwoot_api_token') or hotel_data.get('chatwoot_api_access_token')
                    account_id = hotel_data.get('chatwoot_account_id')
                    
                    print(f"\n📋 Chatwoot Configuration:")
                    print(f"   Base URL: {base_url or 'NOT SET'}")
                    print(f"   API Token: {'SET' if api_token else 'NOT SET'}")
                    print(f"   Account ID: {account_id or 'NOT SET'}")
                    
                    return hotel_data
            else:
                print(f"❌ Hotel ID 2 not found (status: {response.status_code})")
                return None
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return None

async def main():
    """Run the check."""
    hotel = await check_hotel_id_2()
    
    if hotel:
        print(f"\n✅ Hotel ID 2 is available for webhook testing")
        print(f"   Webhook URL: /webhook/chatwoot/2")
    else:
        print(f"\n❌ Hotel ID 2 does not exist in Directus")
        print(f"   You need to use a different hotel ID that exists in your database")

if __name__ == "__main__":
    asyncio.run(main())