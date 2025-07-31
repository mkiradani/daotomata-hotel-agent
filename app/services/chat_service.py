"""Chat service using OpenAI Agents SDK."""

import asyncio
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from agents import Context, Result, Agent
from openai import AsyncOpenAI

from ..agents.hotel_agents import triage_agent
from ..models import ChatRequest, ChatResponse, ChatMessage, MessageRole
from ..config import settings


@dataclass
class HotelContext:
    """Context for hotel-specific information."""

    hotel_id: Optional[str] = None
    hotel_name: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    conversation_history: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.conversation_history is None:
            self.conversation_history = []


class ChatService:
    """Service for handling chat conversations with hotel agents."""

    def __init__(self):
        self.sessions: Dict[str, HotelContext] = {}
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def process_chat(self, request: ChatRequest) -> ChatResponse:
        """Process a chat request and return the agent's response."""
        try:
            # Get or create session
            session_id = request.session_id or str(uuid.uuid4())

            # Get hotel context
            hotel_context = await self._get_hotel_context(request, session_id)

            # Create context for the agent
            context = Context(
                hotel_id=hotel_context.hotel_id,
                hotel_name=hotel_context.hotel_name,
                session_id=session_id,
                user_message=request.message
            )
            
            # Process the message directly with the agent's function
            result = await triage_agent.process_request(context)
            
            # Get the response text
            if isinstance(result, Result):
                final_message = result.value
                agent_name = "Hotel Assistant"
            else:
                final_message = str(result) if result else "I apologize, but I couldn't process your request."
                agent_name = "Hotel Assistant"
            
            # Update conversation history
            hotel_context.conversation_history.append({"role": "user", "content": request.message})
            hotel_context.conversation_history.append({"role": "assistant", "content": final_message})

            # Extract metadata
            agent_used = agent_name
            tools_used = []  # TODO: Extract tools from response
            handoff_occurred = False  # TODO: Check if handoff occurred

            return ChatResponse(
                message=final_message,
                session_id=session_id,
                agent_used=agent_used,
                tools_used=tools_used,
                handoff_occurred=handoff_occurred,
            )

        except Exception as e:
            # Log error in production
            print(f"Error processing chat: {str(e)}")

            return ChatResponse(
                message="I apologize, but I'm experiencing some technical difficulties. Please try again in a moment, or contact our front desk for immediate assistance.",
                session_id=request.session_id or str(uuid.uuid4()),
                agent_used="error_handler",
                tools_used=[],
                handoff_occurred=False,
            )

    async def _get_hotel_context(
        self, request: ChatRequest, session_id: str
    ) -> HotelContext:
        """Get or create hotel context for the session."""
        if session_id not in self.sessions:
            # Create new context
            hotel_id = request.hotel_id or await self._detect_hotel_from_domain()

            self.sessions[session_id] = HotelContext(
                hotel_id=hotel_id, session_id=session_id, conversation_history=[]
            )

            # Get hotel name if we have hotel_id
            if hotel_id:
                hotel_name = await self._get_hotel_name(hotel_id)
                self.sessions[session_id].hotel_name = hotel_name

        # Update with any new context from request
        context = self.sessions[session_id]
        if request.user_context:
            for key, value in request.user_context.items():
                setattr(context, key, value)

        return context

    async def _detect_hotel_from_domain(self) -> Optional[str]:
        """Detect hotel ID from current domain."""
        if not settings.current_domain:
            return None

        try:
            from .directus_service import directus_service

            hotel_data = await directus_service.get_hotel_by_domain(settings.current_domain)
            if hotel_data:
                return hotel_data.get("id")
        except Exception as e:
            print(f"Error detecting hotel from domain: {str(e)}")

        return None

    async def _get_hotel_name(self, hotel_id: str) -> Optional[str]:
        """Get hotel name by ID."""
        try:
            from .directus_service import directus_service

            hotel_name = await directus_service.get_hotel_name(hotel_id)
            return hotel_name
        except Exception as e:
            print(f"Error getting hotel name: {str(e)}")

        return None


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
                    timestamp=datetime.now(),  # In production, store actual timestamps
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
chat_service = ChatService()
