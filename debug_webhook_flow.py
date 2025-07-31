#!/usr/bin/env python3
"""
Debug script to trace the complete Chatwoot webhook flow.

This script provides detailed logging and tracing to help identify
where the webhook processing might be failing.

Usage:
    python debug_webhook_flow.py [hotel_id] [conversation_id]
"""

import asyncio
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('webhook_debug.log')
    ]
)

# Create loggers for different components
main_logger = logging.getLogger("DEBUG_MAIN")
webhook_logger = logging.getLogger("DEBUG_WEBHOOK")
chat_logger = logging.getLogger("DEBUG_CHAT")
chatwoot_logger = logging.getLogger("DEBUG_CHATWOOT")


def log_step(step_number: int, description: str, logger=main_logger):
    """Log a step in the debugging process."""
    logger.info(f"🔍 STEP {step_number}: {description}")
    logger.info("-" * 80)


def log_data(title: str, data: Any, logger=main_logger):
    """Log data with pretty formatting."""
    logger.info(f"📊 {title}:")
    if isinstance(data, (dict, list)):
        logger.info(json.dumps(data, indent=2, default=str))
    else:
        logger.info(str(data))
    logger.info("-" * 40)


async def debug_payload_parsing(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Debug the payload parsing step."""
    log_step(1, "PAYLOAD PARSING", webhook_logger)
    
    webhook_logger.info("🔍 Input payload structure:")
    log_data("Raw Payload", payload, webhook_logger)
    
    # Import and test the parsing function
    try:
        from app.api.webhook import _parse_chatwoot_payload
        
        webhook_logger.info("📦 Parsing payload...")
        result = _parse_chatwoot_payload(payload)
        
        log_data("Parsing Result", result, webhook_logger)
        
        if result.get("is_valid"):
            webhook_logger.info("✅ Payload parsing SUCCESSFUL")
        else:
            webhook_logger.error(f"❌ Payload parsing FAILED: {result.get('reason')}")
        
        return result
        
    except Exception as e:
        webhook_logger.error(f"💥 Exception during payload parsing: {e}")
        import traceback
        webhook_logger.error(f"📚 Traceback:\n{traceback.format_exc()}")
        raise


async def debug_chat_request_creation(parsed_data: Dict[str, Any], hotel_id: str) -> Any:
    """Debug the chat request creation step."""
    log_step(2, "CHAT REQUEST CREATION", chat_logger)
    
    try:
        from app.models import ChatRequest
        
        if not parsed_data.get("is_valid"):
            chat_logger.error("❌ Cannot create chat request from invalid payload")
            return None
        
        # Extract data for chat request
        conversation_id = parsed_data["conversation_id"]
        message_content = parsed_data["message_content"]
        contact_info = parsed_data["contact_info"]
        
        chat_logger.info(f"🔨 Creating ChatRequest:")
        chat_logger.info(f"   - Hotel ID: {hotel_id}")
        chat_logger.info(f"   - Session ID: chatwoot_{conversation_id}")
        chat_logger.info(f"   - Message: {message_content[:100]}...")
        chat_logger.info(f"   - Contact: {contact_info['name']}")
        
        chat_request = ChatRequest(
            message=message_content,
            session_id=f"chatwoot_{conversation_id}",
            hotel_id=hotel_id,
            user_context={
                "platform": "chatwoot",
                "conversation_id": conversation_id,
                "contact_id": contact_info["id"],
                "contact_name": contact_info["name"],
                "contact_email": contact_info.get("email"),
                "sender_type": parsed_data["sender_info"]["type"],
                "event_type": parsed_data["event_type"]
            }
        )
        
        log_data("Created ChatRequest", {
            "message": chat_request.message,
            "session_id": chat_request.session_id,
            "hotel_id": chat_request.hotel_id,
            "user_context": chat_request.user_context
        }, chat_logger)
        
        chat_logger.info("✅ ChatRequest created successfully")
        return chat_request
        
    except Exception as e:
        chat_logger.error(f"💥 Exception creating ChatRequest: {e}")
        import traceback
        chat_logger.error(f"📚 Traceback:\n{traceback.format_exc()}")
        raise


async def debug_chat_service_processing(chat_request: Any, use_mcp: bool = True) -> Any:
    """Debug the chat service processing step."""
    log_step(3, f"CHAT SERVICE PROCESSING ({'MCP' if use_mcp else 'Standard'})", chat_logger)
    
    try:
        if use_mcp:
            from app.services.chat_service_mcp import chat_service_mcp as service
            chat_logger.info("🤖 Using MCP-enabled chat service")
        else:
            from app.services.chat_service import chat_service as service
            chat_logger.info("🤖 Using standard chat service")
        
        chat_logger.info(f"📤 Processing chat request...")
        chat_logger.info(f"   - Service type: {type(service).__name__}")
        chat_logger.info(f"   - Message: {chat_request.message}")
        chat_logger.info(f"   - Hotel ID: {chat_request.hotel_id}")
        
        # Process the chat
        response = await service.process_chat(chat_request)
        
        if response:
            log_data("Chat Response", {
                "message": response.message[:200] + "..." if len(response.message) > 200 else response.message,
                "session_id": response.session_id,
                "agent_used": response.agent_used,
                "tools_used": response.tools_used,
                "handoff_occurred": response.handoff_occurred
            }, chat_logger)
            
            chat_logger.info("✅ Chat service processing SUCCESSFUL")
            chat_logger.info(f"📝 Response length: {len(response.message)} characters")
            
        else:
            chat_logger.error("❌ Chat service returned None response")
            
        return response
        
    except Exception as e:
        chat_logger.error(f"💥 Exception during chat processing: {e}")
        import traceback
        chat_logger.error(f"📚 Traceback:\n{traceback.format_exc()}")
        raise


async def debug_chatwoot_response(hotel_id: str, conversation_id: int, response_message: str) -> Dict[str, Any]:
    """Debug the Chatwoot API response step."""
    log_step(4, "CHATWOOT API RESPONSE", chatwoot_logger)
    
    try:
        from app.services.chatwoot_service import chatwoot_service
        
        chatwoot_logger.info(f"📡 Preparing to send response to Chatwoot:")
        chatwoot_logger.info(f"   - Hotel ID: {hotel_id}")
        chatwoot_logger.info(f"   - Conversation ID: {conversation_id}")
        chatwoot_logger.info(f"   - Response length: {len(response_message)} characters")
        chatwoot_logger.info(f"   - Response preview: {response_message[:100]}...")
        
        # Check if hotel has Chatwoot configuration
        config = chatwoot_service.get_hotel_config(hotel_id)
        
        if config:
            chatwoot_logger.info("✅ Hotel Chatwoot configuration found")
            log_data("Chatwoot Config", {
                "base_url": config.base_url,
                "account_id": config.account_id,
                "inbox_id": config.inbox_id,
                "has_token": bool(config.api_access_token)
            }, chatwoot_logger)
        else:
            chatwoot_logger.error("❌ No Chatwoot configuration found for hotel")
            chatwoot_logger.info("💡 This might be why the bot isn't responding!")
            
            # Try to add a default config for testing
            from app.services.chatwoot_service import get_default_chatwoot_config
            default_config = get_default_chatwoot_config()
            chatwoot_service.add_hotel_config(hotel_id, default_config)
            chatwoot_logger.info("🔧 Added default Chatwoot config for testing")
        
        # Attempt to send the message (this will likely fail without real credentials)
        chatwoot_logger.info("📤 Attempting to send message to Chatwoot...")
        
        result = await chatwoot_service.send_message(
            hotel_id=hotel_id,
            conversation_id=conversation_id,
            content=response_message,
            message_type="outgoing",
            private=False
        )
        
        log_data("Chatwoot Send Result", result, chatwoot_logger)
        
        if result.get("success"):
            chatwoot_logger.info("✅ Message sent to Chatwoot successfully")
        else:
            chatwoot_logger.error(f"❌ Failed to send message: {result.get('error')}")
            chatwoot_logger.info("💡 This could be due to invalid credentials or network issues")
        
        return result
        
    except Exception as e:
        chatwoot_logger.error(f"💥 Exception during Chatwoot response: {e}")
        import traceback
        chatwoot_logger.error(f"📚 Traceback:\n{traceback.format_exc()}")
        raise


async def debug_full_webhook_flow(
    hotel_id: str = "test_hotel_001",
    conversation_id: int = 12345,
    test_message: str = "Hello, I need help with my booking"
):
    """Debug the complete webhook flow end-to-end."""
    
    main_logger.info("🚀 STARTING COMPLETE WEBHOOK FLOW DEBUG")
    main_logger.info("=" * 100)
    main_logger.info(f"🏨 Hotel ID: {hotel_id}")
    main_logger.info(f"💬 Conversation ID: {conversation_id}")
    main_logger.info(f"📝 Test Message: {test_message}")
    main_logger.info("=" * 100)
    
    try:
        # Create a realistic test payload
        from test_chatwoot_webhook import create_test_chatwoot_payload
        
        payload = create_test_chatwoot_payload(
            message_content=test_message,
            conversation_id=conversation_id,
            contact_name="Debug User",
            contact_id=99999
        )
        
        # Step 1: Parse the payload
        parsed_data = await debug_payload_parsing(payload)
        
        if not parsed_data.get("is_valid"):
            main_logger.error("🛑 Stopping debug flow due to invalid payload")
            return False
        
        # Step 2: Create chat request
        chat_request = await debug_chat_request_creation(parsed_data, hotel_id)
        
        if not chat_request:
            main_logger.error("🛑 Stopping debug flow due to chat request creation failure")
            return False
        
        # Step 3: Process through chat service
        response = await debug_chat_service_processing(chat_request, use_mcp=True)
        
        if not response:
            main_logger.error("🛑 Stopping debug flow due to chat service failure")
            return False
        
        # Step 4: Send response to Chatwoot
        chatwoot_result = await debug_chatwoot_response(
            hotel_id, 
            conversation_id, 
            response.message
        )
        
        # Summary
        main_logger.info("\n" + "=" * 100)
        main_logger.info("📊 WEBHOOK FLOW DEBUG SUMMARY")
        main_logger.info("=" * 100)
        
        steps = [
            ("Payload Parsing", parsed_data.get("is_valid", False)),
            ("Chat Request Creation", chat_request is not None),
            ("Chat Service Processing", response is not None),
            ("Chatwoot API Response", chatwoot_result.get("success", False))
        ]
        
        for step_name, success in steps:
            status = "✅ SUCCESS" if success else "❌ FAILED"
            main_logger.info(f"{step_name:<25} {status}")
        
        all_success = all(success for _, success in steps)
        
        if all_success:
            main_logger.info("🎉 ALL STEPS COMPLETED SUCCESSFULLY!")
        else:
            main_logger.error("💥 SOME STEPS FAILED - Check logs above for details")
        
        main_logger.info("=" * 100)
        
        return all_success
        
    except Exception as e:
        main_logger.error(f"💥 CRITICAL ERROR in webhook flow debug: {e}")
        import traceback
        main_logger.error(f"📚 Full traceback:\n{traceback.format_exc()}")
        return False


async def main():
    """Main debug function."""
    
    # Parse command line arguments
    hotel_id = sys.argv[1] if len(sys.argv) > 1 else "test_hotel_001"
    conversation_id = int(sys.argv[2]) if len(sys.argv) > 2 else 12345
    
    main_logger.info(f"🔍 Debug parameters: hotel_id={hotel_id}, conversation_id={conversation_id}")
    
    # Run the complete debug flow
    success = await debug_full_webhook_flow(hotel_id, conversation_id)
    
    if success:
        main_logger.info("✅ Debug completed successfully")
        return 0
    else:
        main_logger.error("❌ Debug found issues - check logs for details")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)