#!/usr/bin/env python3
"""
Test the /webhook/chatwoot/2 endpoint with a sample Chatwoot payload
"""

import asyncio
import httpx
import json
from datetime import datetime
import time

async def test_webhook():
    """Test the webhook endpoint with a sample Chatwoot message."""
    
    # API endpoint
    base_url = "http://localhost:8000"
    webhook_url = f"{base_url}/webhook/chatwoot/2"
    
    # Sample Chatwoot webhook payload for an incoming message
    sample_payload = {
        "event": "message_created",
        "id": "test_" + str(int(time.time())),
        "content": "¿Cuáles son los horarios del restaurante?",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "message_type": "incoming",
        "content_type": "text",
        "sender": {
            "id": "contact_123",
            "name": "Test Customer",
            "email": "test@example.com",
            "type": "contact"  # Customer type
        },
        "contact": {
            "id": "contact_123",
            "name": "Test Customer",
            "email": "test@example.com"
        },
        "conversation": {
            "display_id": "999",  # Test conversation ID
            "id": 999,
            "additional_attributes": {}
        },
        "account": {
            "id": "2",
            "name": "Baberrih Hotel"
        }
    }
    
    print(f"\n🚀 TESTING WEBHOOK ENDPOINT: {webhook_url}")
    print("=" * 80)
    print(f"\n📋 Payload:")
    print(json.dumps(sample_payload, indent=2))
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            print(f"\n📤 Sending POST request...")
            start_time = time.time()
            
            response = await client.post(
                webhook_url,
                json=sample_payload,
                headers={"Content-Type": "application/json"}
            )
            
            elapsed = time.time() - start_time
            
            print(f"\n📥 Response received in {elapsed:.2f} seconds")
            print(f"   Status Code: {response.status_code}")
            print(f"   Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"\n✅ SUCCESS!")
                print(f"   Response:")
                print(json.dumps(result, indent=2))
                
                # Check if response indicates success
                if result.get("status") == "success":
                    print(f"\n🎯 Webhook processed successfully!")
                    print(f"   - Hotel ID: {result.get('hotel_id')}")
                    print(f"   - Conversation ID: {result.get('conversation_id')}")
                    print(f"   - Session ID: {result.get('session_id')}")
                    print(f"   - Agent Used: {result.get('agent_used')}")
                    print(f"   - Processing: {result.get('processing_time')}")
                    
                    print(f"\n💡 The response should be sent to Chatwoot conversation {result.get('conversation_id')} asynchronously")
                    
            else:
                print(f"\n❌ ERROR: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except httpx.TimeoutException:
            print(f"\n⏱️ Request timed out")
        except Exception as e:
            print(f"\n💥 Error: {e}")
            import traceback
            traceback.print_exc()

async def test_webhook_test_endpoint():
    """Test the /webhook/chatwoot/test/2 endpoint."""
    
    base_url = "http://localhost:8000"
    test_url = f"{base_url}/webhook/chatwoot/test/2"
    
    print(f"\n\n🧪 TESTING TEST ENDPOINT: {test_url}")
    print("=" * 80)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(test_url)
            
            print(f"\n📥 Response:")
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"\n✅ Test endpoint working!")
                print(json.dumps(result, indent=2))
            else:
                print(f"\n❌ Error: {response.text}")
                
        except Exception as e:
            print(f"\n💥 Error: {e}")

async def main():
    """Run all tests."""
    # First test the test endpoint
    await test_webhook_test_endpoint()
    
    # Then test the actual webhook
    await test_webhook()

if __name__ == "__main__":
    print("\n🏨 TESTING CHATWOOT WEBHOOK FOR HOTEL ID 2 (Baberrih Hotel)")
    asyncio.run(main())