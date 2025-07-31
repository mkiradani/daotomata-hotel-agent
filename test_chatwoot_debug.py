#!/usr/bin/env python3
"""
Enhanced Chatwoot webhook debug test script.
Tests the full flow and identifies where issues occur.
"""

import asyncio
import httpx
import json
import logging
from datetime import datetime
from typing import Dict, Any

# Configure enhanced logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test configuration
API_URL = "http://localhost:8000"
HOTEL_ID = "2"  # Your test hotel ID

# Sample webhook payload from Chatwoot
SAMPLE_WEBHOOK_PAYLOAD = {
    "event": "message_created",
    "id": "1",
    "content": "Hola, necesito información sobre las habitaciones disponibles para este fin de semana",
    "created_at": datetime.now().isoformat(),
    "message_type": "incoming",
    "content_type": "text",
    "sender": {
        "id": "999",
        "name": "Test Customer",
        "email": "test@example.com",
        "type": "contact"  # Customer type
    },
    "contact": {
        "id": "999",
        "name": "Test Customer",
        "email": "test@example.com"
    },
    "conversation": {
        "display_id": "12345",
        "id": "12345",
        "additional_attributes": {}
    },
    "account": {
        "id": "1",
        "name": "Test Hotel Chatwoot"
    }
}

async def test_webhook_endpoint():
    """Test the Chatwoot webhook endpoint with detailed debugging."""
    print("\n" + "="*80)
    print("🧪 CHATWOOT WEBHOOK DEBUG TEST")
    print("="*80 + "\n")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test 1: Check if API is running
        print("📌 Test 1: Checking API health...")
        try:
            health_response = await client.get(f"{API_URL}/health")
            if health_response.status_code == 200:
                print("✅ API is healthy")
                print(f"📊 Health data: {json.dumps(health_response.json(), indent=2)}")
            else:
                print(f"❌ API health check failed: {health_response.status_code}")
                return
        except Exception as e:
            print(f"❌ Cannot connect to API: {e}")
            return
        
        print("\n" + "-"*80 + "\n")
        
        # Test 2: Check webhook test endpoint
        print("📌 Test 2: Testing webhook configuration...")
        try:
            test_response = await client.get(f"{API_URL}/webhook/chatwoot/test/{HOTEL_ID}")
            if test_response.status_code == 200:
                test_data = test_response.json()
                print("✅ Webhook test endpoint working")
                print(f"📊 Test data: {json.dumps(test_data, indent=2)}")
                
                if not test_data.get("chatwoot_config_found"):
                    print("⚠️  WARNING: No Chatwoot configuration found for this hotel!")
                    print("    The bot cannot send responses without proper Chatwoot configuration.")
            else:
                print(f"❌ Webhook test failed: {test_response.status_code}")
        except Exception as e:
            print(f"❌ Webhook test error: {e}")
        
        print("\n" + "-"*80 + "\n")
        
        # Test 3: Send test webhook payload
        print("📌 Test 3: Sending test webhook payload...")
        print(f"📤 Payload: {json.dumps(SAMPLE_WEBHOOK_PAYLOAD, indent=2)}")
        
        try:
            # Send webhook with detailed logging
            webhook_url = f"{API_URL}/webhook/chatwoot/{HOTEL_ID}"
            print(f"🌐 Sending to: {webhook_url}")
            
            response = await client.post(
                webhook_url,
                json=SAMPLE_WEBHOOK_PAYLOAD,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"\n📥 Response Status: {response.status_code}")
            print(f"📥 Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                response_data = response.json()
                print("✅ Webhook processed successfully")
                print(f"📊 Response data: {json.dumps(response_data, indent=2)}")
                
                # Check response details
                if response_data.get("status") == "success":
                    print("\n🎉 Success! The webhook was processed.")
                    print(f"   - Session ID: {response_data.get('session_id')}")
                    print(f"   - Agent Used: {response_data.get('agent_used')}")
                    print(f"   - Processing: {response_data.get('processing_time')}")
                    
                    if response_data.get("processing_time") == "async":
                        print("\n⏳ Note: Response is being sent asynchronously to Chatwoot")
                        print("   Check your Chatwoot conversation for the bot's response.")
                else:
                    print(f"\n⚠️  Webhook ignored: {response_data.get('reason')}")
            else:
                print(f"❌ Webhook failed with status {response.status_code}")
                print(f"📊 Error response: {response.text}")
                
        except httpx.TimeoutException:
            print("❌ Request timeout - webhook took too long to respond")
        except Exception as e:
            print(f"❌ Webhook error: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "-"*80 + "\n")
        
        # Test 4: Check logs for Chatwoot response
        print("📌 Test 4: Checking server logs...")
        print("💡 Tip: Check your server logs for these key messages:")
        print("   - '🔔 Received Chatwoot webhook' - Webhook received")
        print("   - '📝 Processing message' - Message being processed")
        print("   - '✅ Generated response' - AI response generated")
        print("   - '📤 Sending response to Chatwoot' - Sending to Chatwoot API")
        print("   - '✅ Successfully sent response' - Response sent successfully")
        print("   - '❌ Failed to send response' - Error sending to Chatwoot")
        
        print("\n" + "-"*80 + "\n")
        
        # Test 5: Common issues checklist
        print("📌 Test 5: Common Issues Checklist")
        print("\n🔍 Check these common issues:")
        print("\n1. ❓ Chatwoot Configuration:")
        print("   - Is CHATWOOT_BASE_URL set in .env?")
        print("   - Is CHATWOOT_API_TOKEN set and valid?")
        print("   - Is CHATWOOT_ACCOUNT_ID correct?")
        print("   - Does the hotel have Chatwoot config in Directus?")
        
        print("\n2. ❓ API Permissions:")
        print("   - Does the API token have 'conversation' scope?")
        print("   - Can the token send messages?")
        print("   - Is the account ID correct?")
        
        print("\n3. ❓ Webhook Configuration:")
        print("   - Is the webhook URL correct in Chatwoot?")
        print("   - Format: https://your-domain/webhook/chatwoot/{hotel_id}")
        print("   - Is the hotel_id in the URL correct?")
        
        print("\n4. ❓ Response Flow:")
        print("   - Check if chatwoot_service.send_message is being called")
        print("   - Check if the Chatwoot API returns 200 OK")
        print("   - Check conversation_id format (should be integer)")

async def test_direct_chatwoot_api():
    """Test direct Chatwoot API access to verify credentials."""
    print("\n" + "="*80)
    print("🧪 DIRECT CHATWOOT API TEST")
    print("="*80 + "\n")
    
    # Load environment variables
    from dotenv import load_dotenv
    import os
    load_dotenv()
    
    base_url = os.getenv("CHATWOOT_BASE_URL")
    api_token = os.getenv("CHATWOOT_API_TOKEN")
    account_id = os.getenv("CHATWOOT_ACCOUNT_ID")
    
    if not all([base_url, api_token, account_id]):
        print("❌ Missing Chatwoot configuration in .env file")
        print(f"   CHATWOOT_BASE_URL: {'✅' if base_url else '❌'}")
        print(f"   CHATWOOT_API_TOKEN: {'✅' if api_token else '❌'}")
        print(f"   CHATWOOT_ACCOUNT_ID: {'✅' if account_id else '❌'}")
        return
    
    print(f"📊 Chatwoot Configuration:")
    print(f"   Base URL: {base_url}")
    print(f"   Account ID: {account_id}")
    print(f"   API Token: {api_token[:10]}..." if api_token else "   API Token: None")
    
    # Test API access
    async with httpx.AsyncClient() as client:
        # Test conversations endpoint
        url = f"{base_url}/api/v1/accounts/{account_id}/conversations"
        headers = {
            "Content-Type": "application/json",
            "api_access_token": api_token
        }
        
        try:
            print(f"\n🔍 Testing API access to: {url}")
            response = await client.get(url, headers=headers)
            
            if response.status_code == 200:
                print("✅ Chatwoot API access successful!")
                data = response.json()
                print(f"   Found {len(data.get('payload', []))} conversations")
            else:
                print(f"❌ Chatwoot API error: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Cannot connect to Chatwoot API: {e}")

async def main():
    """Run all debug tests."""
    await test_webhook_endpoint()
    await test_direct_chatwoot_api()
    
    print("\n" + "="*80)
    print("🏁 DEBUG TEST COMPLETED")
    print("="*80 + "\n")

if __name__ == "__main__":
    asyncio.run(main())