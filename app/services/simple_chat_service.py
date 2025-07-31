"""Simple chat service using OpenAI directly for testing."""

import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import json

from openai import AsyncOpenAI

from ..agents.tools import (
    get_hotel_info,
    check_room_availability,
    get_hotel_activities,
    get_hotel_facilities,
    get_local_weather,
    request_hotel_service,
)
from ..services.cloudbeds_service import CloudbedsService
from ..models import ChatRequest, ChatResponse, ChatMessage, MessageRole
from ..config import settings


@dataclass
class HotelContext:
    """Context for hotel-specific information."""
    hotel_id: Optional[str] = None
    hotel_name: Optional[str] = None
    session_id: Optional[str] = None
    conversation_history: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.conversation_history is None:
            self.conversation_history = []


class SimpleChatService:
    """Simple service for handling chat conversations."""

    def __init__(self):
        self.sessions: Dict[str, HotelContext] = {}
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.cloudbeds_service = CloudbedsService()

    async def process_chat(self, request: ChatRequest) -> ChatResponse:
        """Process a chat request and return the response."""
        try:
            # Get or create session
            session_id = request.session_id or str(uuid.uuid4())
            
            # Get hotel context
            hotel_context = await self._get_hotel_context(request, session_id)
            
            # For now, directly check if it's an availability request
            message_lower = request.message.lower()
            
            if any(word in message_lower for word in ["available", "availability", "book", "reservation", "room", "disponible", "disponibilidad", "habitacion", "habitaciones"]):
                # Extract dates if provided
                import re
                from datetime import datetime, timedelta
                
                # Simple date extraction (for testing)
                tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                day_after = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
                
                # Default guests
                adults = 2
                children = 0
                
                # Look for guest numbers
                if "child" in message_lower:
                    match = re.search(r'(\d+)\s*child', message_lower)
                    if match:
                        children = int(match.group(1))
                
                # Call Cloudbeds service directly
                availability_result = await self.cloudbeds_service.check_availability(
                    hotel_id=int(hotel_context.hotel_id),
                    check_in=tomorrow,
                    check_out=day_after,
                    adults=adults,
                    children=children
                )
                
                # Format response like the PMS tool would
                if availability_result.get("error"):
                    result = f"**Room Availability Check**\n\n{availability_result['error']}"
                elif availability_result.get("available"):
                    if availability_result.get("rooms"):
                        # We have real-time availability data
                        result = f"""**Room Availability Check**

✅ **Available Rooms Found!**

**Your Search:**
- Check-in: {availability_result['check_in']}
- Check-out: {availability_result['check_out']}
- Nights: {availability_result['nights']}
- Guests: {availability_result['adults']} adults{f', {availability_result["children"]} children' if availability_result.get('children', 0) > 0 else ''}

**Available Room Types ({availability_result['total_rooms_available']} options):**

"""
                        for room in availability_result['rooms']:
                            result += f"""
**{room['roomTypeName']}**
- Price: {room['currency']} {room['roomRate']:.2f} per night
- Total: {room['currency']} {room['totalRate']:.2f} for {availability_result['nights']} nights
- Available units: {room['roomsAvailable']}
- Max guests: {room['maxGuests']}
"""
                        
                        result += f"""

**Ready to Book?**
🔗 **[Click here to complete your booking]({availability_result['booking_url']})**

This secure link will take you directly to our booking system where you can:
- Select your preferred room type
- Complete your reservation with secure payment
- Receive instant confirmation

Need help? Contact our reception team for assistance."""
                    else:
                        # Fallback to booking URL only
                        result = f"""**Room Availability Check**

✅ **Check availability and book your room online!**

**Your Request:**
- Check-in: {availability_result['check_in']}
- Check-out: {availability_result['check_out']}
- Nights: {availability_result['nights']}
- Guests: {availability_result['adults']} adults{f', {availability_result["children"]} children' if availability_result.get('children', 0) > 0 else ''}

{availability_result.get('message', 'Please check our booking system for real-time availability.')}

🔗 **[Click here to check real-time availability and complete your booking]({availability_result['booking_url']})**

This secure link will take you directly to our hotel's booking system where you can:
- See all available room types and current rates
- View detailed room descriptions and photos
- Complete your reservation with secure payment
- Receive instant confirmation

Need help? Contact our reception team for assistance."""
                else:
                    result = "No availability information found."
                
                # Update conversation history
                hotel_context.conversation_history.append({"role": "user", "content": request.message})
                hotel_context.conversation_history.append({"role": "assistant", "content": result})
                
                return ChatResponse(
                    message=result,
                    session_id=session_id,
                    agent_used="Booking Specialist",
                    tools_used=["check_real_room_availability"],
                    handoff_occurred=True,
                )
            
            # For other requests, use standard OpenAI chat
            messages = [
                {"role": "system", "content": f"You are a helpful hotel assistant for hotel ID {hotel_context.hotel_id}. Be professional and friendly."}
            ]
            
            # Add conversation history
            messages.extend(hotel_context.conversation_history[-10:])
            
            # Add current message
            messages.append({"role": "user", "content": request.message})
            
            # Get response from OpenAI
            response = await self.client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
            )
            
            final_message = response.choices[0].message.content
            
            # Update conversation history
            hotel_context.conversation_history.append({"role": "user", "content": request.message})
            hotel_context.conversation_history.append({"role": "assistant", "content": final_message})
            
            return ChatResponse(
                message=final_message,
                session_id=session_id,
                agent_used="Hotel Assistant",
                tools_used=[],
                handoff_occurred=False,
            )

        except Exception as e:
            print(f"Error processing chat: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return ChatResponse(
                message="I apologize, but I'm experiencing some technical difficulties. Please try again in a moment.",
                session_id=request.session_id or str(uuid.uuid4()),
                agent_used="error_handler",
                tools_used=[],
                handoff_occurred=False,
            )

    async def _get_hotel_context(self, request: ChatRequest, session_id: str) -> HotelContext:
        """Get or create hotel context for the session."""
        if session_id not in self.sessions:
            self.sessions[session_id] = HotelContext(
                hotel_id=request.hotel_id,
                session_id=session_id,
                conversation_history=[]
            )
        
        return self.sessions[session_id]

    async def get_session_history(self, session_id: str) -> List[ChatMessage]:
        """Get conversation history for a session."""
        if session_id not in self.sessions:
            return []
        
        context = self.sessions[session_id]
        messages = []
        
        for msg in context.conversation_history:
            messages.append(
                ChatMessage(
                    role=MessageRole(msg["role"]),
                    content=msg["content"],
                    timestamp=datetime.now(),
                )
            )
        
        return messages

    async def clear_session(self, session_id: str) -> bool:
        """Clear a conversation session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False


# Global chat service instance
chat_service = SimpleChatService()