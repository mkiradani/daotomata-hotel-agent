"""Webhook endpoints for external integrations."""

import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Path, BackgroundTasks
from typing import Dict, Any, Optional
import json

from ..models import ChatRequest, ChatResponse
from ..services.simple_chat_service import chat_service
from ..services.chat_service_mcp import chat_service_mcp
from ..services.chatwoot_service import chatwoot_service
from ..config import settings

# Configure webhook logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

router = APIRouter(prefix="/webhook", tags=["webhooks"])


@router.post("/chatwoot/{hotel_id}")
async def chatwoot_webhook(
    payload: Dict[str, Any],
    background_tasks: BackgroundTasks,
    hotel_id: str = Path(..., description="Hotel ID from Directus"),
    use_mcp: bool = True  # Default to MCP-enabled service
) -> Dict[str, Any]:
    """
    Webhook endpoint for Chatwoot integration.
    
    Receives messages from Chatwoot and processes them through the chat service
    with the hotel_id specified in the URL path.
    
    URL format: /webhook/chatwoot/{hotel_id}
    Example: /webhook/chatwoot/hotel_123
    
    This endpoint:
    1. Validates the Chatwoot webhook payload
    2. Processes the message through the AI chat service
    3. Sends the response back to Chatwoot via their API
    4. Returns a status response to the webhook caller
    """
    
    # Enhanced logging for debugging
    logger.info(f"🔔 Chatwoot webhook: hotel {hotel_id}, MCP={use_mcp}")
    
    try:
        # Validate and extract Chatwoot payload data
        webhook_data = _parse_chatwoot_payload(payload)
        if not webhook_data["is_valid"]:
            logger.warning(f"⚠️ Invalid webhook: {webhook_data['reason']}")
            return {
                "status": "ignored", 
                "reason": webhook_data["reason"],
                "hotel_id": hotel_id
            }
        
        # Extract parsed data
        event_type = webhook_data["event_type"]
        message_content = webhook_data["message_content"]
        conversation_id = webhook_data["conversation_id"]
        contact_info = webhook_data["contact_info"]
        sender_info = webhook_data["sender_info"]
        
        logger.info(f"📝 Processing: {contact_info['name']} in conv {conversation_id}")
        logger.info(f"💬 Message: '{message_content[:50]}{'...' if len(message_content) > 50 else ''}'")
        
        # Create chat request with proper context including conversation_id for HITL
        chat_request = ChatRequest(
            message=message_content,
            session_id=f"chatwoot_{conversation_id}",
            hotel_id=hotel_id,
            conversation_id=conversation_id,  # Add conversation_id for HITL integration
            user_context={
                "platform": "chatwoot",
                "conversation_id": conversation_id,
                "contact_id": contact_info["id"],
                "contact_name": contact_info["name"],
                "contact_email": contact_info.get("email"),
                "sender_type": sender_info["type"],
                "event_type": event_type
            }
        )
        
        # Process through appropriate chat service with automatic fallback
        # Removed verbose chat request logging
        
        response = None
        if use_mcp:
            try:
                logger.info(f"🤖 Processing with MCP-enabled chat service")
                response = await chat_service_mcp.process_chat(chat_request)
                logger.info(f"✅ MCP processing successful")
            except Exception as mcp_error:
                logger.error(f"❌ MCP failed: {str(mcp_error)[:50]}")
                logger.info(f"🔄 Fallback to simple service")
                response = await chat_service.process_chat(chat_request)
        else:
            logger.info(f"🤖 Processing with simple chat service")
            response = await chat_service.process_chat(chat_request)
        
        logger.info(f"🎯 Response: {response.agent_used} | {len(response.message)} chars")
        
        # Send response back to Chatwoot asynchronously
        logger.info(f"📤 Adding background task for conv {conversation_id}")
        
        background_tasks.add_task(
            _send_chatwoot_response,
            hotel_id,
            conversation_id,  # This should now be an integer
            response.message,
            contact_info["name"]
        )
        logger.info(f"✅ Background task added")
        
        # Return immediate status to webhook caller
        return {
            "status": "success",
            "message": "Webhook processed, response will be sent to Chatwoot",
            "hotel_id": hotel_id,
            "conversation_id": conversation_id,
            "session_id": response.session_id,
            "agent_used": response.agent_used,
            "processing_time": "async"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 Webhook error: {str(e)[:100]}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Error processing Chatwoot webhook: {str(e)}"
        )


def _parse_chatwoot_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse and validate Chatwoot webhook payload.
    
    Based on Chatwoot's actual webhook structure:
    {
      "event": "message_created",
      "id": "1",
      "content": "Hi",
      "created_at": "2020-03-03 13:05:57 UTC",
      "message_type": "incoming",
      "content_type": "text",
      "sender": {"id": "1", "name": "Agent", "email": "[email protected]"},
      "contact": {"id": "1", "name": "contact-name"},
      "conversation": {"display_id": "1", "additional_attributes": {...}},
      "account": {"id": "1", "name": "Chatwoot"}
    }
    """
    
    # Check event type
    event_type = payload.get("event")
    if event_type != "message_created":
        return {
            "is_valid": False,
            "reason": f"Event type '{event_type}' not processed - only 'message_created' events are handled"
        }
    
    # Check message type (incoming vs outgoing)
    message_type = payload.get("message_type")
    if message_type != "incoming":
        return {
            "is_valid": False,
            "reason": f"Message type '{message_type}' not processed - only 'incoming' messages are handled"
        }
    
    # Extract message content
    message_content = payload.get("content", "").strip()
    if not message_content:
        return {
            "is_valid": False,
            "reason": "Empty message content"
        }
    
    # Extract conversation info
    conversation = payload.get("conversation", {})
    conversation_id = conversation.get("display_id") or conversation.get("id")
    if not conversation_id:
        return {
            "is_valid": False,
            "reason": "Missing conversation ID"
        }
    
    # Convert conversation_id to integer
    try:
        conversation_id = int(conversation_id)
    except (ValueError, TypeError):
        return {
            "is_valid": False,
            "reason": f"Invalid conversation ID format: {conversation_id}"
        }
    
    # Extract contact info (customer info)
    contact = payload.get("contact", {})
    contact_info = {
        "id": contact.get("id"),
        "name": contact.get("name", "Guest"),
        "email": contact.get("email")
    }
    
    # Extract sender info (who sent the message)
    sender = payload.get("sender", {})
    sender_info = {
        "id": sender.get("id"),
        "name": sender.get("name", "Unknown"),
        "email": sender.get("email"),
        "type": sender.get("type", "unknown")
    }
    
    # Additional validation - ensure this is from a customer, not an agent
    # In Chatwoot, customers typically don't have a "type" field or have type="contact"
    # Agents have type="user" or similar
    if sender_info["type"] in ["user", "agent"]:
        return {
            "is_valid": False,
            "reason": f"Message from agent/user (type: {sender_info['type']}) - not processing to avoid loops"
        }
    
    return {
        "is_valid": True,
        "event_type": event_type,
        "message_content": message_content,
        "conversation_id": conversation_id,
        "contact_info": contact_info,
        "sender_info": sender_info,
        "account_info": payload.get("account", {}),
        "created_at": payload.get("created_at"),
        "content_type": payload.get("content_type", "text")
    }


async def _send_chatwoot_response(
    hotel_id: str,
    conversation_id: int,
    response_message: str,
    customer_name: str
):
    """
    Send the AI response back to Chatwoot via their API.
    
    This is the critical function that was missing - it actually sends
    the bot's response back to Chatwoot so the customer sees it.
    """
    logger.info(f"🎯 BACKGROUND TASK STARTED: Sending response to Chatwoot")
    logger.info(f"   Hotel ID: {hotel_id}")
    logger.info(f"   Conversation ID: {conversation_id} (type: {type(conversation_id)})")
    logger.info(f"   Customer: {customer_name}")
    logger.info(f"   Message length: {len(response_message)} characters")
    logger.info(f"   Message preview: {response_message[:100]}...")
    
    try:
        # Check if Chatwoot service has config for this hotel
        config = chatwoot_service.get_hotel_config(hotel_id)
        if not config:
            logger.error(f"❌ No Chatwoot configuration found for hotel {hotel_id}!")
            logger.error(f"   Available hotel configs: {list(chatwoot_service.configs.keys())}")
            return
        
        logger.info(f"✅ Found Chatwoot config for hotel {hotel_id}")
        
        # Send message to Chatwoot
        logger.info(f"📤 Calling chatwoot_service.send_message...")
        result = await chatwoot_service.send_message(
            hotel_id=hotel_id,
            conversation_id=conversation_id,
            content=response_message,
            message_type="outgoing",  # This is a bot response
            private=False  # Visible to customer
        )
        
        logger.info(f"📥 Chatwoot service result: {json.dumps(result, indent=2)}")
        
        if result["success"]:
            logger.info(f"✅ Successfully sent response to {customer_name} in conversation {conversation_id}")
            logger.info(f"   Message ID: {result.get('message_id')}")
            logger.info(f"   Sent at: {result.get('sent_at')}")
        else:
            logger.error(f"❌ Failed to send response to Chatwoot")
            logger.error(f"   Error: {result.get('error')}")
            logger.error(f"   Error details: {result.get('error_details')}")
            
    except Exception as e:
        logger.error(f"💥 Send exception: {type(e).__name__}: {str(e)[:100]}")
    
    finally:
        logger.info(f"🎬 BACKGROUND TASK COMPLETED for conversation {conversation_id}")


@router.get("/chatwoot/test/{hotel_id}")
async def test_chatwoot_webhook(
    hotel_id: str = Path(..., description="Hotel ID from Directus")
) -> Dict[str, Any]:
    """
    Test endpoint to verify Chatwoot webhook configuration.
    
    Use this to test that the webhook URL is correctly configured
    and the hotel_id is being passed properly.
    """
    logger.info(f"🧪 Testing Chatwoot webhook for hotel {hotel_id}")
    
    # Check if hotel has Chatwoot configuration
    config = chatwoot_service.get_hotel_config(hotel_id)
    
    return {
        "status": "ok",
        "hotel_id": hotel_id,
        "message": f"Webhook test successful for hotel: {hotel_id}",
        "webhook_url": f"/webhook/chatwoot/{hotel_id}",
        "chatwoot_config_found": config is not None,
        "timestamp": str(datetime.now())
    }