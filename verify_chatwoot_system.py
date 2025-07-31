#!/usr/bin/env python3
"""
Comprehensive Chatwoot integration verification script.
Checks all components of the Chatwoot webhook flow.
"""

import asyncio
import httpx
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def check_environment_variables():
    """Check if all required environment variables are set."""
    print("\n📋 CHECKING ENVIRONMENT VARIABLES")
    print("=" * 60)
    
    required_vars = {
        "DIRECTUS_URL": os.getenv("DIRECTUS_URL"),
        "DIRECTUS_TOKEN": os.getenv("DIRECTUS_TOKEN"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "CHATWOOT_BASE_URL": os.getenv("CHATWOOT_BASE_URL"),
        "CHATWOOT_API_TOKEN": os.getenv("CHATWOOT_API_TOKEN"),
        "CHATWOOT_ACCOUNT_ID": os.getenv("CHATWOOT_ACCOUNT_ID"),
    }
    
    all_set = True
    for var_name, var_value in required_vars.items():
        if var_value:
            print(f"✅ {var_name}: Set ({var_value[:20]}...)" if len(str(var_value)) > 20 else f"✅ {var_name}: {var_value}")
        else:
            print(f"❌ {var_name}: Not set")
            all_set = False
    
    return all_set

async def check_directus_connection():
    """Check connection to Directus."""
    print("\n🗄️ CHECKING DIRECTUS CONNECTION")
    print("=" * 60)
    
    directus_url = os.getenv("DIRECTUS_URL")
    directus_token = os.getenv("DIRECTUS_TOKEN")
    
    if not directus_url or not directus_token:
        print("❌ Missing Directus credentials")
        return False
    
    async with httpx.AsyncClient() as client:
        try:
            headers = {"Authorization": f"Bearer {directus_token}"}
            response = await client.get(f"{directus_url}/items/hotels", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                hotels = data.get("data", [])
                print(f"✅ Connected to Directus")
                print(f"   Found {len(hotels)} hotels in database")
                return True
            else:
                print(f"❌ Directus connection failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error connecting to Directus: {e}")
            return False

async def check_hotels_with_chatwoot():
    """Check hotels that have Chatwoot configuration."""
    print("\n🏨 CHECKING HOTELS WITH CHATWOOT CONFIG")
    print("=" * 60)
    
    directus_url = os.getenv("DIRECTUS_URL")
    directus_token = os.getenv("DIRECTUS_TOKEN")
    
    async with httpx.AsyncClient() as client:
        try:
            headers = {"Authorization": f"Bearer {directus_token}"}
            params = {
                "fields": "id,name,domain,chatwoot_config",
                "filter[chatwoot_config][_nnull]": "true"
            }
            
            response = await client.get(
                f"{directus_url}/items/hotels",
                headers=headers,
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                hotels = data.get("data", [])
                
                if not hotels:
                    print("⚠️  No hotels have Chatwoot configuration")
                    return []
                
                print(f"✅ Found {len(hotels)} hotels with Chatwoot config:")
                
                valid_hotels = []
                for hotel in hotels:
                    hotel_id = hotel.get("id")
                    hotel_name = hotel.get("name")
                    chatwoot_config = hotel.get("chatwoot_config", {})
                    
                    print(f"\n   Hotel: {hotel_name} (ID: {hotel_id})")
                    
                    # Check required fields
                    required_fields = ["base_url", "api_access_token", "account_id"]
                    config_valid = True
                    
                    for field in required_fields:
                        if field in chatwoot_config and chatwoot_config[field]:
                            print(f"      ✅ {field}: Set")
                        else:
                            print(f"      ❌ {field}: Missing")
                            config_valid = False
                    
                    if config_valid:
                        valid_hotels.append(hotel)
                
                return valid_hotels
                
        except Exception as e:
            print(f"❌ Error checking hotels: {e}")
            return []

async def test_chatwoot_api_directly(hotel_config):
    """Test Chatwoot API directly with hotel configuration."""
    print(f"\n🔌 TESTING CHATWOOT API FOR HOTEL {hotel_config.get('id')}")
    print("=" * 60)
    
    chatwoot_config = hotel_config.get("chatwoot_config", {})
    base_url = chatwoot_config.get("base_url")
    api_token = chatwoot_config.get("api_access_token")
    account_id = chatwoot_config.get("account_id")
    
    if not all([base_url, api_token, account_id]):
        print("❌ Incomplete Chatwoot configuration")
        return False
    
    async with httpx.AsyncClient() as client:
        try:
            # Test conversations endpoint
            url = f"{base_url}/api/v1/accounts/{account_id}/conversations"
            headers = {
                "Content-Type": "application/json",
                "api_access_token": api_token
            }
            
            response = await client.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                conversations = data.get("payload", [])
                print(f"✅ Chatwoot API connection successful")
                print(f"   Found {len(conversations)} conversations")
                return True
            else:
                print(f"❌ Chatwoot API error: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error connecting to Chatwoot: {e}")
            return False

async def test_webhook_flow(hotel_id):
    """Test the complete webhook flow."""
    print(f"\n🧪 TESTING WEBHOOK FLOW FOR HOTEL {hotel_id}")
    print("=" * 60)
    
    # Sample webhook payload
    test_payload = {
        "event": "message_created",
        "id": "test-" + str(int(datetime.now().timestamp())),
        "content": "Hola, ¿cuáles son los horarios del desayuno?",
        "created_at": datetime.now().isoformat(),
        "message_type": "incoming",
        "content_type": "text",
        "sender": {
            "id": "999",
            "name": "Test Customer",
            "email": "test@example.com",
            "type": "contact"
        },
        "contact": {
            "id": "999",
            "name": "Test Customer"
        },
        "conversation": {
            "display_id": "99999",
            "id": "99999"
        },
        "account": {
            "id": "1",
            "name": "Test Account"
        }
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Test webhook endpoint
            webhook_url = f"http://localhost:8000/webhook/chatwoot/{hotel_id}"
            print(f"📤 Sending test webhook to: {webhook_url}")
            print(f"📋 Payload: {json.dumps(test_payload, indent=2)}")
            
            response = await client.post(
                webhook_url,
                json=test_payload,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"\n📥 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Webhook processed successfully")
                print(f"📊 Response: {json.dumps(data, indent=2)}")
                
                if data.get("status") == "success":
                    print("\n✅ WEBHOOK FLOW WORKING!")
                    print("   Check your server logs for the complete flow")
                    return True
                else:
                    print(f"\n⚠️ Webhook returned: {data.get('reason')}")
                    return False
            else:
                print(f"❌ Webhook failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing webhook: {e}")
            return False

async def main():
    """Run all verification checks."""
    print("\n🚀 CHATWOOT INTEGRATION VERIFICATION")
    print("=" * 80)
    print(f"Started at: {datetime.now()}")
    
    # Check environment variables
    env_ok = await check_environment_variables()
    if not env_ok:
        print("\n❌ Please set all required environment variables in .env file")
        return
    
    # Check Directus connection
    directus_ok = await check_directus_connection()
    if not directus_ok:
        print("\n❌ Cannot connect to Directus. Check DIRECTUS_URL and DIRECTUS_TOKEN")
        return
    
    # Check hotels with Chatwoot config
    hotels_with_chatwoot = await check_hotels_with_chatwoot()
    if not hotels_with_chatwoot:
        print("\n❌ No hotels have valid Chatwoot configuration in Directus")
        print("   Please configure Chatwoot settings for at least one hotel")
        return
    
    # Test Chatwoot API for each hotel
    working_hotels = []
    for hotel in hotels_with_chatwoot:
        api_ok = await test_chatwoot_api_directly(hotel)
        if api_ok:
            working_hotels.append(hotel)
    
    if not working_hotels:
        print("\n❌ No hotels have working Chatwoot API connections")
        return
    
    # Test webhook flow for the first working hotel
    test_hotel = working_hotels[0]
    webhook_ok = await test_webhook_flow(test_hotel.get("id"))
    
    # Summary
    print("\n📊 VERIFICATION SUMMARY")
    print("=" * 80)
    print(f"✅ Environment variables: OK")
    print(f"✅ Directus connection: OK")
    print(f"✅ Hotels with Chatwoot: {len(hotels_with_chatwoot)}")
    print(f"✅ Working Chatwoot APIs: {len(working_hotels)}")
    print(f"{'✅' if webhook_ok else '❌'} Webhook flow: {'OK' if webhook_ok else 'FAILED'}")
    
    if webhook_ok:
        print("\n🎉 CHATWOOT INTEGRATION IS WORKING!")
        print(f"   Test with hotel ID: {test_hotel.get('id')}")
        print(f"   Webhook URL: /webhook/chatwoot/{test_hotel.get('id')}")
    else:
        print("\n❌ WEBHOOK FLOW IS NOT WORKING")
        print("   Check the server logs for detailed error messages")
        print("   Common issues:")
        print("   - Conversation ID must be an integer")
        print("   - Chatwoot API token needs 'conversation' scope")
        print("   - Check if the API is running on port 8000")

if __name__ == "__main__":
    asyncio.run(main())