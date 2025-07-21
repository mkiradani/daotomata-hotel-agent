"""Chat service using OpenAI Agents SDK."""

import asyncio
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from agents import Runner, RunContextWrapper
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions

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

    async def process_chat(self, request: ChatRequest) -> ChatResponse:
        """Process a chat request and return the agent's response."""
        try:
            # Get or create session
            session_id = request.session_id or str(uuid.uuid4())

            # Get hotel context
            hotel_context = await self._get_hotel_context(request, session_id)

            # Prepare conversation input
            conversation_input = await self._prepare_conversation_input(
                request, hotel_context
            )

            # Run the agent
            result = await Runner.run(
                triage_agent, conversation_input, context=hotel_context, max_turns=10
            )

            # Update conversation history
            await self._update_conversation_history(
                hotel_context, request.message, result.final_output
            )

            # Extract metadata from result
            agent_used = self._extract_agent_used(result)
            tools_used = self._extract_tools_used(result)
            handoff_occurred = self._check_handoff_occurred(result)

            return ChatResponse(
                message=str(result.final_output),
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

    async def _prepare_conversation_input(
        self, request: ChatRequest, context: HotelContext
    ) -> List[Dict[str, Any]]:
        """Prepare conversation input for the agent."""
        messages = []

        # Add system message with hotel context
        system_message = self._create_system_message(context)
        messages.append({"role": "system", "content": system_message})

        # Add conversation history
        messages.extend(context.conversation_history)

        # Add current user message
        messages.append({"role": "user", "content": request.message})

        return messages

    def _create_system_message(self, context: HotelContext) -> str:
        """Create system message with hotel context."""
        system_msg = "You are a helpful hotel assistant. "

        if context.hotel_name:
            system_msg += f"You work at {context.hotel_name}. "

        if context.hotel_id:
            system_msg += f"The hotel ID is {context.hotel_id}. "

        system_msg += "Always be professional, friendly, and helpful. "
        system_msg += "Use the available tools to provide accurate information. "
        system_msg += (
            "If you need specialized assistance, handoff to the appropriate agent."
        )

        return system_msg

    async def _update_conversation_history(
        self, context: HotelContext, user_message: str, assistant_response: str
    ):
        """Update conversation history."""
        context.conversation_history.extend(
            [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": assistant_response},
            ]
        )

        # Keep only last 20 messages to prevent context overflow
        if len(context.conversation_history) > 20:
            context.conversation_history = context.conversation_history[-20:]

    def _extract_agent_used(self, result) -> Optional[str]:
        """Extract which agent was used from the result."""
        # This would need to be implemented based on the actual result structure
        # For now, return a placeholder
        return "triage_agent"

    def _extract_tools_used(self, result) -> List[str]:
        """Extract which tools were used from the result."""
        # This would need to be implemented based on the actual result structure
        # For now, return empty list
        return []

    def _check_handoff_occurred(self, result) -> bool:
        """Check if a handoff occurred during the conversation."""
        # This would need to be implemented based on the actual result structure
        # For now, return False
        return False

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
