"""Chat service using OpenAI Agents SDK with MCP integration."""

import asyncio
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from agents import Runner, RunContextWrapper
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions

from ..agents.hotel_agents_mcp import create_triage_agent
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


class ChatServiceMCP:
    """Service for handling chat conversations with hotel agents using MCP."""

    def __init__(self):
        self.sessions: Dict[str, HotelContext] = {}
        self._triage_agent = None

    async def _get_triage_agent(self):
        """Get or create triage agent with MCP integration."""
        if self._triage_agent is None:
            self._triage_agent = await create_triage_agent()
        return self._triage_agent

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

            # Get triage agent with MCP
            triage_agent = await self._get_triage_agent()

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
            # Enhanced error logging for MCP debugging
            print(f"❌ Error processing chat with MCP: {str(e)}")
            print(f"📝 Request details - session_id: {request.session_id}, hotel_id: {request.hotel_id}, message: {request.message[:100]}...")
            
            import traceback
            traceback.print_exc()

            # Check if error is MCP-related
            error_msg = str(e).lower()
            if "mcp" in error_msg or "connection" in error_msg or "server" in error_msg:
                print("🔧 MCP-related error detected - attempting to reset MCP connection")
                try:
                    from ..agents.hotel_agents_mcp import close_directus_mcp_server
                    await close_directus_mcp_server()
                except:
                    pass
                
                error_response = "I'm having trouble accessing the hotel's live data system. Please try again in a moment, or contact our front desk for immediate assistance."
            else:
                error_response = "I apologize, but I'm experiencing some technical difficulties. Please try again in a moment, or contact our front desk for immediate assistance."

            return ChatResponse(
                message=error_response,
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
            hotel_id = request.hotel_id

            self.sessions[session_id] = HotelContext(
                hotel_id=hotel_id, session_id=session_id, conversation_history=[]
            )

            # Get hotel name from Directus if we have hotel_id
            if hotel_id:
                # The agent will get hotel name via MCP tools
                # For now just store the ID
                pass

        # Update with any new context from request
        context = self.sessions[session_id]
        if request.user_context:
            for key, value in request.user_context.items():
                setattr(context, key, value)

        return context

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
        system_msg = "You are a helpful hotel assistant with access to real-time hotel data through Directus MCP. "

        if context.hotel_id:
            system_msg += f"The hotel ID is {context.hotel_id}. Use Directus tools to get current hotel information. "

        system_msg += "Always be professional, friendly, and helpful. "
        system_msg += "Use the available tools to provide accurate information from the hotel's live data. "
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
        return "triage_agent_mcp"

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


# Global chat service instance with MCP
chat_service_mcp = ChatServiceMCP()