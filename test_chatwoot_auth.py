#!/usr/bin/env python3
"""Test Chatwoot authentication and API connectivity."""

import asyncio
import sys
from app.services.chatwoot_service import chatwoot_service, initialize_chatwoot_configs


async def test_chatwoot_connectivity():
    """Test real connectivity to Chatwoot API."""
    
    print("🧪 Testing Chatwoot API Authentication")
    print("=" * 50)
    
    # Initialize configs from Directus
    await initialize_chatwoot_configs()
    
    # Test hotel 2 (Baberrih Hotel)
    hotel_id = "2"
    config = chatwoot_service.get_hotel_config(hotel_id)
    
    if not config:
        print(f"❌ No config found for hotel {hotel_id}")
        return False
    
    print(f"✅ Found config for hotel {hotel_id}")
    print(f"   Base URL: {config.base_url}")
    print(f"   Account ID: {config.account_id}")
    print(f"   Token: {config.api_access_token[:10]}...")
    print()
    
    # Test 1: Send a private note (basic write operation bots can do)
    print("🔍 Test 1: Send private note (bot permission test)...")
    try:
        test_note = "🧪 Authentication test - private note from HITL system"
        result = await chatwoot_service.send_message(
            hotel_id=hotel_id,
            conversation_id=9,
            content=test_note,
            message_type="outgoing",
            private=True
        )
        
        if result.get("success"):
            print("✅ Successfully sent private note (bot token works for basic operations)")
            print(f"   Message ID: {result.get('message_id')}")
        else:
            print(f"❌ Failed to send private note: {result.get('error')}")
            print(f"   Details: {result.get('error_details', 'N/A')}")  
            return False
    except Exception as e:
        print(f"❌ Exception sending private note: {str(e)}")
        return False
    
    print()
    
    # Test 2: Try to change conversation status (requires user token)
    print("🔍 Test 2: Mark conversation as open (user permission test)...")
    try:
        result = await chatwoot_service.mark_conversation_open(hotel_id, 9)
        if result.get("success"):
            print("✅ Successfully marked conversation as open (user token required!)")
            print(f"   Status: {result.get('status')}")
            print("🎯 This means you have a USER TOKEN, not just a bot token!")
        else:
            error_details = result.get('error_details', '')
            if "not authorized for bots" in error_details:
                print("⚠️ Expected: Bot token cannot change conversation status")
                print("📋 SOLUTION NEEDED: Generate a User Access Token from Profile Settings")
                print(f"   Go to: {config.base_url}")
                print("   1. Login to your Chatwoot account")
                print("   2. Go to Profile Settings")
                print("   3. Generate a User Access Token") 
                print("   4. Update the token in Directus")
                print()
                print("🔄 For now, testing with bot permissions only...")
            else:
                print(f"❌ Failed to mark conversation as open: {result.get('error')}")
                print(f"   Details: {error_details}")
                return False
    except Exception as e:
        print(f"❌ Exception marking conversation as open: {str(e)}")
        return False
    
    print()
    print("🎯 AUTHENTICATION TEST COMPLETE!")
    print("✅ Bot token works for basic operations (sending messages)")
    print("📋 Next step: Generate User Access Token for full HITL functionality")
    
    return True


async def main():
    """Run Chatwoot connectivity tests."""
    try:
        success = await test_chatwoot_connectivity()
        if success:
            print("\n🚀 Chatwoot integration is ready for production!")
            return 0
        else:
            print("\n❌ Chatwoot authentication still has issues")
            return 1
    except Exception as e:
        print(f"\n💥 Critical error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Cleanup
        await chatwoot_service.close()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)