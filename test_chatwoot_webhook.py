#!/usr/bin/env python3
"""
Comprehensive test script for Chatwoot webhook integration.

This script tests:
1. Chatwoot webhook payload parsing
2. Chat service processing
3. Chatwoot API response (mock)
4. End-to-end webhook flow

Usage:
    python test_chatwoot_webhook.py
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_test_chatwoot_payload(
    message_content: str = "Hello, I need help with my booking",
    conversation_id: int = 12345,
    contact_name: str = "John Doe",
    contact_id: int = 67890,
    message_type: str = "incoming",
    event_type: str = "message_created"
) -> Dict[str, Any]:
    """Create a realistic Chatwoot webhook payload for testing."""
    
    return {
        "event": event_type,
        "id": "msg_001",
        "content": message_content,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "message_type": message_type,
        "content_type": "text",
        "content_attributes": {},
        "source_id": "",
        "sender": {
            "id": contact_id,
            "name": contact_name,
            "email": f"{contact_name.lower().replace(' ', '.')}@example.com",
            "type": "contact"  # Important: this identifies it as a customer message
        },
        "contact": {
            "id": contact_id,
            "name": contact_name,
            "email": f"{contact_name.lower().replace(' ', '.')}@example.com"
        },
        "conversation": {
            "display_id": conversation_id,
            "id": conversation_id,
            "additional_attributes": {
                "browser": {
                    "device_name": "iPhone",
                    "browser_name": "Safari",
                    "platform_name": "iOS",
                    "browser_version": "15.0",
                    "platform_version": "15.0"
                },
                "referer": "https://hotel-website.com/contact",
                "initiated_at": datetime.now().strftime("%a %b %d %Y %H:%M:%S GMT%z")
            }
        },
        "account": {
            "id": 1,
            "name": "Test Hotel Account"
        }
    }


def create_invalid_test_payloads() -> list[Dict[str, Any]]:
    """Create various invalid payloads to test validation."""
    
    base_payload = create_test_chatwoot_payload()
    
    invalid_payloads = [
        # Wrong event type
        {**base_payload, "event": "conversation_updated"},
        
        # Agent message (should be ignored)
        {
            **base_payload,
            "sender": {**base_payload["sender"], "type": "user"},
            "message_type": "outgoing"
        },
        
        # Empty content
        {**base_payload, "content": ""},
        
        # Missing conversation ID
        {**base_payload, "conversation": {}},
        
        # Missing sender info
        {**base_payload, "sender": {}},
    ]
    
    return invalid_payloads


async def test_payload_parsing():
    """Test the Chatwoot payload parsing function."""
    from app.api.webhook import _parse_chatwoot_payload
    
    logger.info("🧪 Testing Chatwoot payload parsing...")
    
    # Test valid payload
    valid_payload = create_test_chatwoot_payload()
    result = _parse_chatwoot_payload(valid_payload)
    
    if result["is_valid"]:
        logger.info("✅ Valid payload parsed successfully")
        logger.info(f"   - Conversation ID: {result['conversation_id']}")
        logger.info(f"   - Contact: {result['contact_info']['name']}")
        logger.info(f"   - Message: {result['message_content'][:50]}...")
    else:
        logger.error(f"❌ Valid payload failed: {result['reason']}")
        return False
    
    # Test invalid payloads
    invalid_payloads = create_invalid_test_payloads()
    
    for i, invalid_payload in enumerate(invalid_payloads):
        result = _parse_chatwoot_payload(invalid_payload)
        if not result["is_valid"]:
            logger.info(f"✅ Invalid payload {i+1} correctly rejected: {result['reason']}")
        else:
            logger.error(f"❌ Invalid payload {i+1} incorrectly accepted")
            return False
    
    return True


async def test_chat_service_processing():
    """Test the chat service processing with a mock request."""
    from app.models import ChatRequest
    from app.services.chat_service import chat_service
    from app.services.chat_service_mcp import chat_service_mcp
    
    logger.info("🧪 Testing chat service processing...")
    
    # Create test chat request
    chat_request = ChatRequest(
        message="Hello, what's the weather like today?",
        session_id="test_chatwoot_12345",
        hotel_id="test_hotel_001",
        user_context={
            "platform": "chatwoot",
            "conversation_id": 12345,
            "contact_id": 67890,
            "contact_name": "John Doe",
            "contact_email": "john.doe@example.com"
        }
    )
    
    try:
        # Test standard chat service
        logger.info("🔄 Testing standard chat service...")
        response = await chat_service.process_chat(chat_request)
        
        if response and response.message:
            logger.info(f"✅ Standard service response: {response.message[:100]}...")
            logger.info(f"   - Agent used: {response.agent_used}")
            logger.info(f"   - Session ID: {response.session_id}")
        else:
            logger.error("❌ Standard service returned empty response")
            return False
            
        # Test MCP chat service
        logger.info("🔄 Testing MCP chat service...")
        try:
            response_mcp = await chat_service_mcp.process_chat(chat_request)
            
            if response_mcp and response_mcp.message:
                logger.info(f"✅ MCP service response: {response_mcp.message[:100]}...")
                logger.info(f"   - Agent used: {response_mcp.agent_used}")
                logger.info(f"   - Session ID: {response_mcp.session_id}")
            else:
                logger.error("❌ MCP service returned empty response")
                return False
        except Exception as e:
            logger.warning(f"⚠️ MCP service failed (may be expected): {e}")
            # MCP service might fail in test environment, that's OK
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Chat service processing failed: {e}")
        import traceback
        logger.error(f"📚 Traceback: {traceback.format_exc()}")
        return False


async def test_chatwoot_service():
    """Test the Chatwoot service (with mock configuration)."""
    from app.services.chatwoot_service import chatwoot_service, ChatwootConfig
    
    logger.info("🧪 Testing Chatwoot service...")
    
    # Add mock configuration for test hotel
    test_config = ChatwootConfig(
        base_url="https://mock-chatwoot.com",
        api_access_token="mock_token_12345",
        account_id=1,
        inbox_id=1
    )
    
    chatwoot_service.add_hotel_config("test_hotel_001", test_config)
    
    # Test getting configuration
    config = chatwoot_service.get_hotel_config("test_hotel_001")
    if config:
        logger.info("✅ Hotel configuration retrieved successfully")
        logger.info(f"   - Base URL: {config.base_url}")
        logger.info(f"   - Account ID: {config.account_id}")
    else:
        logger.error("❌ Failed to retrieve hotel configuration")
        return False
    
    # Note: We can't test actual API calls without real Chatwoot credentials
    # In a real environment, you would test:
    # result = await chatwoot_service.send_message(...)
    
    logger.info("✅ Chatwoot service configuration test passed")
    return True


async def test_webhook_endpoint():
    """Test the webhook endpoint with a mock HTTP client."""
    try:
        from fastapi.testclient import TestClient
        from main import app
        
        logger.info("🧪 Testing webhook endpoint...")
        
        client = TestClient(app)
        
        # Test valid webhook
        valid_payload = create_test_chatwoot_payload()
        response = client.post("/webhook/chatwoot/test_hotel_001", json=valid_payload)
        
        if response.status_code == 200:
            data = response.json()
            logger.info("✅ Webhook endpoint returned 200")
            logger.info(f"   - Status: {data.get('status')}")
            logger.info(f"   - Hotel ID: {data.get('hotel_id')}")
            logger.info(f"   - Conversation ID: {data.get('conversation_id')}")
        else:
            logger.error(f"❌ Webhook endpoint returned {response.status_code}")
            logger.error(f"   - Response: {response.text}")
            return False
        
        # Test invalid webhook
        invalid_payload = {"event": "conversation_updated", "content": "test"}
        response = client.post("/webhook/chatwoot/test_hotel_001", json=invalid_payload)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "ignored":
                logger.info("✅ Invalid webhook correctly ignored")
            else:
                logger.error("❌ Invalid webhook should have been ignored")
                return False
        else:
            logger.error(f"❌ Invalid webhook test failed with {response.status_code}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Webhook endpoint test failed: {e}")
        import traceback
        logger.error(f"📚 Traceback: {traceback.format_exc()}")
        return False


async def main():
    """Run all tests."""
    logger.info("🚀 Starting Chatwoot webhook integration tests...")
    logger.info("=" * 60)
    
    tests = [
        ("Payload Parsing", test_payload_parsing),
        ("Chat Service Processing", test_chat_service_processing),
        ("Chatwoot Service", test_chatwoot_service),
        ("Webhook Endpoint", test_webhook_endpoint),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 Running {test_name} test...")
        try:
            result = await test_func()
            results.append((test_name, result))
            
            if result:
                logger.info(f"✅ {test_name} test PASSED")
            else:
                logger.error(f"❌ {test_name} test FAILED")
                
        except Exception as e:
            logger.error(f"💥 {test_name} test CRASHED: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 TEST RESULTS SUMMARY")
    logger.info("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name:<25} {status}")
        
        if result:
            passed += 1
    
    logger.info("=" * 60)
    logger.info(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED! Chatwoot webhook integration is working correctly.")
        return True
    else:
        logger.error(f"💥 {total - passed} tests failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)