"""Webhook endpoints for external integrations."""

from fastapi import APIRouter, HTTPException, Path
from typing import Dict, Any

from ..models import ChatRequest, ChatResponse
from ..services.chat_service import chat_service

router = APIRouter(prefix="/webhook", tags=["webhooks"])


@router.post("/chatwoot/{hotel_id}")
async def chatwoot_webhook(
    payload: Dict[str, Any],
    hotel_id: str = Path(..., description="Hotel ID from Directus")
) -> Dict[str, Any]:
    """
    Webhook endpoint for Chatwoot integration.
    
    Receives messages from Chatwoot and processes them through the chat service
    with the hotel_id specified in the URL path.
    
    URL format: /webhook/chatwoot/{hotel_id}
    Example: /webhook/chatwoot/hotel_123
    """
    try:
        # Extract message content from Chatwoot payload
        
        # Chatwoot sends different event types, we're interested in message events
        event_type = payload.get("event")
        if event_type != "message_created":
            return {"status": "ignored", "reason": f"Event type {event_type} not processed"}
        
        # Extract message data
        message_data = payload.get("content", "")
        conversation = payload.get("conversation", {})
        sender = payload.get("sender", {})
        
        # Only process messages from customers (not agents)
        if sender.get("type") != "contact":
            return {"status": "ignored", "reason": "Message from agent, not processing"}
        
        # Create chat request with hotel_id from URL
        chat_request = ChatRequest(
            message=message_data,
            session_id=f"chatwoot_{conversation.get('id', 'unknown')}",
            hotel_id=hotel_id,
            user_context={
                "platform": "chatwoot",
                "conversation_id": conversation.get("id"),
                "contact_id": sender.get("id"),
                "contact_name": sender.get("name", "Guest")
            }
        )
        
        # Process through chat service
        response = await chat_service.process_chat(chat_request)
        
        # Return response in Chatwoot format
        return {
            "status": "success",
            "response": response.message,
            "hotel_id": hotel_id,
            "session_id": response.session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing Chatwoot webhook: {str(e)}"
        )


@router.get("/chatwoot/test/{hotel_id}")
async def test_chatwoot_webhook(
    hotel_id: str = Path(..., description="Hotel ID from Directus")
) -> Dict[str, Any]:
    """
    Test endpoint to verify Chatwoot webhook configuration.
    
    Use this to test that the webhook URL is correctly configured
    and the hotel_id is being passed properly.
    """
    return {
        "status": "ok",
        "hotel_id": hotel_id,
        "message": f"Webhook test successful for hotel: {hotel_id}",
        "webhook_url": f"/webhook/chatwoot/{hotel_id}"
    }