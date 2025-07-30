#!/usr/bin/env python3
"""
Check Bab Errih Hotel configuration in Directus
"""

import asyncio
import httpx
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def check_bab_errih_config():
    """Check Bab Errih Hotel configuration in Directus."""
    print("\n🏨 CHECKING BAB ERRIH HOTEL CONFIGURATION")
    print("=" * 80)
    
    directus_url = os.getenv("DIRECTUS_URL")
    directus_token = os.getenv("DIRECTUS_TOKEN")
    
    if not directus_url or not directus_token:
        print("❌ Missing Directus credentials")
        return None
    
    async with httpx.AsyncClient() as client:
        try:
            headers = {"Authorization": f"Bearer {directus_token}"}
            
            # Search for Bab Errih Hotel
            params = {
                "fields": "id,name,domain,chatwoot_base_url,chatwoot_api_token,chatwoot_api_access_token,chatwoot_account_id,chatwoot_website_token",
                "filter[name][_contains]": "Bab"
            }
            
            response = await client.get(
                f"{directus_url}/items/hotels",
                headers=headers,
                params=params
            )
            
            if response.status_code != 200:
                print(f"❌ Error fetching hotels: {response.status_code}")
                return None
            
            data = response.json()
            hotels = data.get("data", [])
            
            if not hotels:
                print("❌ Bab Errih Hotel not found")
                return None
            
            # Find Bab Errih
            bab_errih = None
            for hotel in hotels:
                if "bab" in hotel.get("name", "").lower() and "errih" in hotel.get("name", "").lower():
                    bab_errih = hotel
                    break
            
            if not bab_errih:
                print("❌ Bab Errih Hotel not found in results")
                print(f"   Found hotels: {[h.get('name') for h in hotels]}")
                return None
            
            # Display hotel info
            print(f"\n✅ Found Bab Errih Hotel:")
            print(f"   ID: {bab_errih.get('id')}")
            print(f"   Name: {bab_errih.get('name')}")
            print(f"   Domain: {bab_errih.get('domain')}")
            
            # Extract Chatwoot fields
            base_url = bab_errih.get('chatwoot_base_url')
            api_token = bab_errih.get('chatwoot_api_token') or bab_errih.get('chatwoot_api_access_token')
            account_id = bab_errih.get('chatwoot_account_id')
            website_token = bab_errih.get('chatwoot_website_token')
            
            print(f"\n📋 Chatwoot Configuration:")
            print(f"   Base URL: {base_url or 'NOT SET'}")
            print(f"   API Token: {api_token[:20] + '...' if api_token and len(api_token) > 20 else api_token or 'NOT SET'}")
            print(f"   Account ID: {account_id or 'NOT SET'}")
            print(f"   Website Token: {website_token or 'NOT SET'}")
            
            # Build config object for compatibility
            chatwoot_config = {
                'base_url': base_url,
                'api_access_token': api_token,
                'account_id': account_id
            }
            
            # Add to hotel data
            bab_errih['chatwoot_config'] = chatwoot_config
            
            # Validate required fields
            print(f"\n🔍 Validating configuration:")
            all_valid = True
            
            if base_url:
                print(f"   ✅ Base URL: {base_url}")
            else:
                print(f"   ❌ Base URL: Missing")
                all_valid = False
                
            if api_token:
                print(f"   ✅ API Token: Set ({len(api_token)} characters)")
            else:
                print(f"   ❌ API Token: Missing")
                all_valid = False
                
            if account_id:
                print(f"   ✅ Account ID: {account_id}")
            else:
                print(f"   ❌ Account ID: Missing")
                all_valid = False
            
            return bab_errih if all_valid else None
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return None

async def test_chatwoot_api(hotel_config):
    """Test Chatwoot API connection with hotel config."""
    print("\n🔌 TESTING CHATWOOT API CONNECTION")
    print("=" * 80)
    
    chatwoot_config = hotel_config.get('chatwoot_config', {})
    base_url = chatwoot_config.get('base_url')
    api_token = chatwoot_config.get('api_access_token')
    account_id = chatwoot_config.get('account_id')
    
    async with httpx.AsyncClient() as client:
        try:
            # Test conversations endpoint
            url = f"{base_url}/api/v1/accounts/{account_id}/conversations"
            headers = {
                "Content-Type": "application/json",
                "api_access_token": api_token
            }
            
            print(f"🌐 Testing: {url}")
            response = await client.get(url, headers=headers, params={"status": "all"})
            
            if response.status_code == 200:
                data = response.json()
                conversations = data.get("data", {}).get("payload", [])
                print(f"✅ API connection successful!")
                print(f"   Found {len(conversations)} conversations")
                
                # Show first few conversations
                if conversations:
                    print(f"\n📊 Recent conversations:")
                    for conv in conversations[:3]:
                        print(f"   - ID: {conv.get('id')} | Status: {conv.get('status')} | Messages: {conv.get('messages_count')}")
                
                return True
            else:
                print(f"❌ API error: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False

async def test_webhook_with_bab_errih(hotel_id):
    """Test webhook with Bab Errih hotel ID."""
    print(f"\n🧪 TESTING WEBHOOK WITH BAB ERRIH (ID: {hotel_id})")
    print("=" * 80)
    
    test_payload = {
        "event": "message_created",
        "id": f"test-{int(datetime.now().timestamp())}",
        "content": "Hola, ¿qué servicios ofrece el hotel?",
        "created_at": datetime.now().isoformat(),
        "message_type": "incoming",
        "content_type": "text",
        "sender": {
            "id": "test-customer",
            "name": "Test Customer",
            "type": "contact"
        },
        "contact": {
            "id": "test-customer",
            "name": "Test Customer"
        },
        "conversation": {
            "display_id": "99999",
            "id": "99999"
        },
        "account": {
            "id": "1",
            "name": "Test"
        }
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            webhook_url = f"http://localhost:8000/webhook/chatwoot/{hotel_id}"
            print(f"📤 Sending to: {webhook_url}")
            
            response = await client.post(
                webhook_url,
                json=test_payload,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"\n📥 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Webhook accepted!")
                print(json.dumps(data, indent=2))
                
                if data.get("status") == "success":
                    print(f"\n🎉 Success! Check server logs for Chatwoot response")
                else:
                    print(f"\n⚠️ Webhook returned: {data.get('reason')}")
            else:
                print(f"❌ Webhook error: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

async def main():
    """Run all checks."""
    print("\n🚀 BAB ERRIH HOTEL CHATWOOT VERIFICATION")
    print(f"Started at: {datetime.now()}")
    
    # Check Bab Errih config
    hotel_config = await check_bab_errih_config()
    
    if not hotel_config:
        print("\n❌ Cannot proceed - Bab Errih configuration is invalid or missing")
        print("\n📝 Please ensure in Directus that:")
        print("   1. Bab Errih Hotel exists")
        print("   2. chatwoot_config field contains:")
        print("      - base_url (e.g., https://app.chatwoot.com)")
        print("      - api_access_token (from Chatwoot profile)")
        print("      - account_id (integer)")
        return
    
    # Test Chatwoot API
    api_ok = await test_chatwoot_api(hotel_config)
    
    if not api_ok:
        print("\n❌ Chatwoot API connection failed")
        print("   Please verify:")
        print("   - base_url is correct")
        print("   - api_access_token is valid")
        print("   - account_id is correct")
        return
    
    # Test webhook
    await test_webhook_with_bab_errih(hotel_config.get('id'))
    
    print("\n✅ VERIFICATION COMPLETE")
    print(f"   Hotel ID: {hotel_config.get('id')}")
    print(f"   Webhook URL: /webhook/chatwoot/{hotel_config.get('id')}")

if __name__ == "__main__":
    asyncio.run(main())