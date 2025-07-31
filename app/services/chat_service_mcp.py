"""Chat service using OpenAI Agents SDK with MCP integration."""

import asyncio
import uuid
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

from agents import Runner, RunContextWrapper
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions

from ..agents.hotel_agents_mcp import create_triage_agent, get_directus_mcp_server
from ..models import ChatRequest, ChatResponse, ChatMessage, MessageRole
from ..config import settings

# Configure detailed logging for conversation tracking
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("chat_service_mcp")


@dataclass
class HotelContext:
    """Context for hotel-specific information."""

    hotel_id: Optional[str] = None
    hotel_name: Optional[str] = None
    hotel_phone: Optional[str] = None
    hotel_email: Optional[str] = None
    hotel_support_hours: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    conversation_history: List[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None

    def __post_init__(self):
        if self.conversation_history is None:
            self.conversation_history = []
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.last_activity is None:
            self.last_activity = datetime.now()


class ChatServiceMCP:
    """Service for handling chat conversations with hotel agents using MCP."""

    def __init__(self):
        self.sessions: Dict[str, HotelContext] = {}
        self._triage_agent = None
        self._hotel_info_cache: Dict[str, Dict[str, Any]] = {}  # Cache hotel info including contacts

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
            
            logger.info(f"🎯 Chat: {session_id} | Hotel {request.hotel_id} | {len(request.message)} chars")

            # Get hotel context
            hotel_context = await self._get_hotel_context(request, session_id)
            
            # Session context loaded

            # Prepare conversation input
            conversation_input = await self._prepare_conversation_input(
                request, hotel_context
            )
            
            logger.info(f"💬 Prepared {len(conversation_input)} messages")

            # Store user message in history BEFORE calling agent
            # This ensures we don't lose the user's message if agent fails
            await self._store_user_message(hotel_context, request.message)
            # User message stored

            # Get triage agent with MCP
            triage_agent = await self._get_triage_agent()

            # Run the agent
            logger.info(f"🤖 Running agent for hotel {hotel_context.hotel_id}")
            result = await Runner.run(
                triage_agent, conversation_input, context=hotel_context, max_turns=10
            )
            
            logger.info(f"✅ Agent completed - {len(str(result.final_output))} chars")

            # HITL INTEGRATION: Evaluate response confidence and handle escalation
            ai_response = str(result.final_output)
            user_question = request.message
            
            # Import HITL manager
            from .hitl_manager import hitl_manager
            
            # Check if HITL is enabled
            if hitl_manager.is_hitl_enabled():
                logger.info("🤖 HITL evaluation...")
                
                # Build context for evaluation
                conversation_context = "\n".join([
                    f"{msg.get('role', 'unknown')}: {msg.get('content', '')[:200]}"
                    for msg in hotel_context.conversation_history[-5:]  # Last 5 messages for context
                ])
                
                # Get hotel_id as string for HITL
                hotel_id_str = str(hotel_context.hotel_id) if hotel_context.hotel_id else "unknown"
                
                # Get conversation_id from request (if available)
                conversation_id = getattr(request, 'conversation_id', None)
                
                if conversation_id:
                    try:
                        # Evaluate and handle response with HITL
                        hitl_result = await hitl_manager.evaluate_and_handle_response(
                            hotel_id=hotel_id_str,
                            conversation_id=conversation_id,
                            ai_response=ai_response,
                            user_question=user_question,
                            context=conversation_context
                        )
                        
                        action = hitl_result.get('action_taken', 'unknown')
                        score = hitl_result.get('confidence_score', 0)
                        logger.info(f"🔍 HITL: {action} | Score: {score:.2f}")
                        
                        # If escalated, modify response to inform user
                        if hitl_result.get("should_escalate", False):
                            escalation_message = (
                                "He transferido tu consulta a uno de nuestros agentes humanos "
                                "para brindarte la mejor asistencia posible. Un miembro de nuestro "
                                "equipo se pondrá en contacto contigo muy pronto.\n\n"
                                f"Mientras tanto, aquí tienes la información que pude recopilar:\n\n{ai_response}"
                            )
                            ai_response = escalation_message
                            logger.info("🚨 Response modified for escalation")
                        
                    except Exception as hitl_error:
                        logger.error(f"❌ HITL failed: {str(hitl_error)[:50]}")
                        # Continue with normal flow if HITL fails
                else:
                    logger.warning("⚠️ No conv_id, skipping HITL")
            else:
                # HITL disabled
                pass

            # Update conversation history with assistant response (potentially modified)
            await self._store_assistant_response(hotel_context, ai_response)
            
            # History updated

            # Extract metadata from result
            agent_used = self._extract_agent_used(result)
            tools_used = self._extract_tools_used(result)
            handoff_occurred = self._check_handoff_occurred(result)
            
            logger.info(f"🔧 Agent: {agent_used} | Tools: {len(tools_used)} | Handoff: {handoff_occurred}")

            return ChatResponse(
                message=ai_response,  # Use potentially modified response
                session_id=session_id,
                agent_used=agent_used,
                tools_used=tools_used,
                handoff_occurred=handoff_occurred,
            )

        except Exception as e:
            # Enhanced error logging for MCP debugging
            logger.error(f"❌ MCP error: {type(e).__name__}: {str(e)[:100]}")
            logger.error(f"📝 Session: {request.session_id} | Hotel: {request.hotel_id}")
            
            # Get or create session context for error handling
            session_id = request.session_id or str(uuid.uuid4())
            try:
                hotel_context = await self._get_hotel_context(request, session_id)
                
                # Store user message if not already stored
                if not any(msg.get("content") == request.message for msg in hotel_context.conversation_history):
                    await self._store_user_message(hotel_context, request.message)
                    # Error message stored
                
                logger.error(f"💾 Session state - History: {len(hotel_context.conversation_history)} messages, Last activity: {hotel_context.last_activity}")
            except Exception as ctx_error:
                logger.error(f"⚠️ Could not get context in error handler: {ctx_error}")
                hotel_context = None
            
            import traceback
            logger.error(f"🔍 Full traceback: {traceback.format_exc()}")

            # Check if error is MCP-related
            error_msg = str(e).lower()
            error_type = type(e).__name__
            
            # More specific error categorization
            if "mcp" in error_msg or "connection" in error_msg or "server" in error_msg or "directus" in error_msg:
                logger.warning("🔧 Data system error detected")
                error_category = "data_system"
            elif "timeout" in error_msg or "timed out" in error_msg:
                logger.warning("⏱️ Timeout error detected")
                error_category = "timeout"
            elif "authentication" in error_msg or "unauthorized" in error_msg or "forbidden" in error_msg:
                logger.warning("🔐 Authentication error detected")
                error_category = "auth"
            elif "rate" in error_msg and "limit" in error_msg:
                logger.warning("🚦 Rate limit error detected")
                error_category = "rate_limit"
            else:
                logger.warning(f"⚠️ General error detected: {error_type}")
                error_category = "general"
            
            if error_category in ["data_system", "timeout"]:
                logger.warning("🔧 MCP-related error detected - attempting to reset MCP connection")
                try:
                    from ..agents.hotel_agents_mcp import close_directus_mcp_server
                    await close_directus_mcp_server()
                    logger.info("🔄 MCP connection reset attempted")
                except Exception as reset_error:
                    logger.error(f"⚠️ Failed to reset MCP connection: {reset_error}")
                
                # Get contact info from context or use defaults
                phone = hotel_context.hotel_phone if hotel_context and hotel_context.hotel_phone else "+1 (555) 123-4567"
                email = hotel_context.hotel_email if hotel_context and hotel_context.hotel_email else "info@hotel.com"
                hours = hotel_context.hotel_support_hours if hotel_context and hotel_context.hotel_support_hours else "24/7"
                
                error_response = f"I'm having trouble accessing the hotel's information system at the moment. Please try your question again, or you can reach our front desk at {phone} or email us at {email} for immediate assistance."
            elif error_category == "auth":
                phone = hotel_context.hotel_phone if hotel_context and hotel_context.hotel_phone else "+1 (555) 123-4567"
                error_response = f"I'm having trouble verifying access to the hotel system. Please try again, or contact our front desk at {phone} for assistance."
            elif error_category == "rate_limit":
                phone = hotel_context.hotel_phone if hotel_context and hotel_context.hotel_phone else "+1 (555) 123-4567"
                error_response = f"Our system is experiencing high demand. Please wait a moment and try again, or contact our front desk at {phone} for immediate help."
            else:
                phone = hotel_context.hotel_phone if hotel_context and hotel_context.hotel_phone else "+1 (555) 123-4567"
                email = hotel_context.hotel_email if hotel_context and hotel_context.hotel_email else "info@hotel.com"
                hours = hotel_context.hotel_support_hours if hotel_context and hotel_context.hotel_support_hours else "24/7"
                error_response = f"I apologize for the inconvenience. I'm unable to process your request right now. Please try again shortly, or contact our front desk at {phone} or email us at {email}. We're here to help {hours}."

            # Store error response in history if context available
            if hotel_context:
                try:
                    await self._store_assistant_response(hotel_context, error_response)
                    logger.info(f"💾 Stored error response in history")
                except Exception as store_error:
                    logger.error(f"⚠️ Could not store error response: {store_error}")

            return ChatResponse(
                message=error_response,
                session_id=session_id,
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
            
            logger.info(f"🆕 Creating new session context - Session ID: {session_id}, Hotel ID: {hotel_id}")

            self.sessions[session_id] = HotelContext(
                hotel_id=hotel_id, session_id=session_id, conversation_history=[]
            )

            # Get hotel info from Directus if we have hotel_id
            if hotel_id:
                # Load hotel information including contacts
                await self._load_hotel_info(hotel_id, self.sessions[session_id])
                logger.info(f"🏨 Hotel context set for hotel ID: {hotel_id}")
        else:
            logger.info(f"🔄 Using existing session context - Session ID: {session_id}")

        # Update with any new context from request
        context = self.sessions[session_id]
        context.last_activity = datetime.now()
        
        if request.user_context:
            logger.info(f"🔧 Updating context with user data: {list(request.user_context.keys())}")
            for key, value in request.user_context.items():
                setattr(context, key, value)

        return context
    
    async def _load_hotel_info(self, hotel_id: str, context: HotelContext):
        """Load hotel information from Directus including contact methods."""
        try:
            # Check cache first
            if hotel_id in self._hotel_info_cache:
                cached_info = self._hotel_info_cache[hotel_id]
                context.hotel_name = cached_info.get("name")
                context.hotel_phone = cached_info.get("phone")
                context.hotel_email = cached_info.get("email")
                context.hotel_support_hours = cached_info.get("support_hours", "24/7")
                logger.info(f"✅ Loaded hotel info from cache for hotel {hotel_id}")
                return
            
            # Get MCP server
            mcp_server = await get_directus_mcp_server()
            
            # Get hotel basic info
            hotel_result = await mcp_server.call_tool(
                "mcp__directus__read-items",
                {
                    "collection": "hotels",
                    "query": {
                        "filter": {"id": {"_eq": int(hotel_id)}},
                        "fields": ["id", "name", "contact_email", "contact_phone_calls"],
                        "limit": 1
                    }
                }
            )
            
            if hotel_result and len(hotel_result) > 0:
                hotel_data = hotel_result[0]
                context.hotel_name = hotel_data.get("name")
                
                # Get contact methods for more specific contacts
                contact_result = await mcp_server.call_tool(
                    "mcp__directus__read-items",
                    {
                        "collection": "contact_methods",
                        "query": {
                            "filter": {"hotel_id": {"_eq": int(hotel_id)}},
                            "fields": ["contact_type", "contact_identifier", "name"]
                        }
                    }
                )
                
                # Process contact methods
                primary_phone = hotel_data.get("contact_phone_calls")
                primary_email = hotel_data.get("contact_email")
                
                # Look for specific contact types
                for contact in contact_result:
                    if contact["contact_type"] == "phone" and contact["name"].lower() == "reception":
                        primary_phone = contact["contact_identifier"]
                    elif contact["contact_type"] == "email" and contact["name"].lower() == "reception":
                        primary_email = contact["contact_identifier"]
                
                context.hotel_phone = primary_phone
                context.hotel_email = primary_email
                context.hotel_support_hours = "24/7"  # Default, could be enhanced with guest_services data
                
                # Cache the info
                self._hotel_info_cache[hotel_id] = {
                    "name": context.hotel_name,
                    "phone": context.hotel_phone,
                    "email": context.hotel_email,
                    "support_hours": context.hotel_support_hours,
                    "contacts": contact_result  # Store all contacts for future use
                }
                
                logger.info(f"✅ Loaded hotel info from Directus for {context.hotel_name}")
                
        except Exception as e:
            logger.error(f"❌ Error loading hotel info: {e}")
            # Set defaults if loading fails
            context.hotel_phone = "+1 (555) 123-4567"
            context.hotel_email = "info@hotel.com"
            context.hotel_support_hours = "24/7"

    async def _prepare_conversation_input(
        self, request: ChatRequest, context: HotelContext
    ) -> List[Dict[str, Any]]:
        """Prepare conversation input for the agent."""
        messages = []

        # Add system message with hotel context
        system_message = self._create_system_message(context)
        messages.append({"role": "system", "content": system_message})

        # Add conversation history (clean format for OpenAI)
        for msg in context.conversation_history:
            # Only include role and content - remove timestamp and other fields
            clean_msg = {
                "role": msg["role"],
                "content": msg["content"]
            }
            messages.append(clean_msg)
        
        logger.info(f"🧹 Cleaned {len(context.conversation_history)} history messages for agent")

        # Add current user message
        messages.append({"role": "user", "content": request.message})

        return messages

    def _create_system_message(self, context: HotelContext) -> str:
        """Create system message with hotel context."""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        system_msg = f"You are a helpful hotel assistant with access to real-time hotel data through Directus MCP. Current time: {current_time}. "

        if context.hotel_id:
            system_msg += f"The hotel ID is {context.hotel_id}. Use Directus tools to get current hotel information. "

        # Add conversation context if available
        if context.conversation_history:
            recent_context = self._extract_recent_context(context)
            if recent_context:
                system_msg += f"Recent conversation context: {recent_context} "

        # Add session duration context
        if context.created_at:
            session_duration = datetime.now() - context.created_at
            if session_duration.total_seconds() > 300:  # 5 minutes
                system_msg += "This is an ongoing conversation. Continue where you left off naturally. "

        system_msg += "Always be professional, friendly, and helpful. "
        system_msg += "Use the available tools to provide accurate information from the hotel's live data. "
        system_msg += "Remember previous messages in this conversation to provide personalized assistance. "
        system_msg += (
            "If you need specialized assistance, handoff to the appropriate agent."
        )

        logger.info(f"🎭 Created system message with context - Length: {len(system_msg)} chars")
        return system_msg

    def _extract_recent_context(self, context: HotelContext) -> str:
        """Extract recent conversation context for system message."""
        if not context.conversation_history:
            return ""
        
        # Get last few messages to understand context
        recent_messages = context.conversation_history[-4:]  # Last 2 turns
        
        context_items = []
        for msg in recent_messages:
            if msg["role"] == "user":
                # Extract key information from user messages
                content = msg["content"].lower()
                if any(keyword in content for keyword in ["mi nombre es", "soy", "me llamo"]):
                    context_items.append("user provided their name")
                elif any(keyword in content for keyword in ["reserva", "booking", "habitacion"]):
                    context_items.append("user asking about reservations")
                elif any(keyword in content for keyword in ["restaurant", "comida", "cenar"]):
                    context_items.append("user interested in dining")
                elif any(keyword in content for keyword in ["actividad", "que hacer", "turismo"]):
                    context_items.append("user asking about activities")
        
        return "; ".join(context_items) if context_items else ""

    async def _store_user_message(self, context: HotelContext, user_message: str):
        """Store user message in conversation history."""
        timestamp = datetime.now().isoformat()
        
        user_msg = {
            "role": "user", 
            "content": user_message, 
            "timestamp": timestamp
        }
        
        context.conversation_history.append(user_msg)
        context.last_activity = datetime.now()
        
        logger.info(f"👤 Stored user message - Length: {len(user_message)} chars")
        
        # Keep only last 20 messages to prevent context overflow
        if len(context.conversation_history) > 20:
            removed_count = len(context.conversation_history) - 20
            context.conversation_history = context.conversation_history[-20:]
            logger.info(f"🧹 Trimmed {removed_count} old messages from history to maintain context size")

    async def _store_assistant_response(self, context: HotelContext, assistant_response: str):
        """Store assistant response in conversation history."""
        timestamp = datetime.now().isoformat()
        
        assistant_msg = {
            "role": "assistant", 
            "content": assistant_response, 
            "timestamp": timestamp
        }
        
        context.conversation_history.append(assistant_msg)
        context.last_activity = datetime.now()
        
        logger.info(f"🤖 Stored assistant response - Length: {len(assistant_response)} chars")
        
        # Keep only last 20 messages to prevent context overflow
        if len(context.conversation_history) > 20:
            removed_count = len(context.conversation_history) - 20
            context.conversation_history = context.conversation_history[-20:]
            logger.info(f"🧹 Trimmed {removed_count} old messages from history to maintain context size")

    async def _update_conversation_history(
        self, context: HotelContext, user_message: str, assistant_response: str
    ):
        """Update conversation history (legacy method - use _store_user_message and _store_assistant_response instead)."""
        # Add timestamps to messages
        timestamp = datetime.now().isoformat()
        
        new_messages = [
            {"role": "user", "content": user_message, "timestamp": timestamp},
            {"role": "assistant", "content": assistant_response, "timestamp": timestamp},
        ]
        
        context.conversation_history.extend(new_messages)
        context.last_activity = datetime.now()
        
        logger.info(f"📝 Added conversation turn - User: {len(user_message)} chars, Assistant: {len(assistant_response)} chars")

        # Keep only last 20 messages to prevent context overflow
        if len(context.conversation_history) > 20:
            removed_count = len(context.conversation_history) - 20
            context.conversation_history = context.conversation_history[-20:]
            logger.info(f"🧹 Trimmed {removed_count} old messages from history to maintain context size")

    def _extract_agent_used(self, result) -> Optional[str]:
        """Extract which agent was used from the result."""
        try:
            # Try to extract agent information from result
            if hasattr(result, 'messages') and result.messages:
                for message in result.messages:
                    if hasattr(message, 'sender') and message.sender:
                        logger.info(f"🤖 Agent identified: {message.sender}")
                        return message.sender
                        
            # Check for handoff patterns in the response
            response_text = str(result.final_output).lower()
            if "booking" in response_text or "reservation" in response_text:
                return "booking_specialist"
            elif "restaurant" in response_text or "recommendation" in response_text:
                return "concierge_agent"
            elif "service" in response_text or "maintenance" in response_text:
                return "service_agent"
            elif "activity" in response_text or "entertainment" in response_text:
                return "activities_agent"
                
            logger.info(f"🤖 Using default agent: triage_agent_mcp")
            return "triage_agent_mcp"
        except Exception as e:
            logger.warning(f"⚠️ Error extracting agent: {e}")
            return "triage_agent_mcp"

    def _extract_tools_used(self, result) -> List[str]:
        """Extract which tools were used from the result."""
        tools_used = []
        try:
            # Try to extract tool usage from result
            if hasattr(result, 'messages') and result.messages:
                for message in result.messages:
                    if hasattr(message, 'tool_calls') and message.tool_calls:
                        for tool_call in message.tool_calls:
                            if hasattr(tool_call, 'function') and tool_call.function:
                                tool_name = tool_call.function.name
                                tools_used.append(tool_name)
                                logger.info(f"🔧 Tool used: {tool_name}")
            
            # Look for common tool patterns in response text
            response_text = str(result.final_output).lower()
            if "weather" in response_text:
                tools_used.append("get_weather")
            if "availability" in response_text or "available" in response_text:
                tools_used.append("check_availability")
                
            logger.info(f"🛠️ Tools extracted: {tools_used}")
            return list(set(tools_used))  # Remove duplicates
        except Exception as e:
            logger.warning(f"⚠️ Error extracting tools: {e}")
            return []

    def _check_handoff_occurred(self, result) -> bool:
        """Check if a handoff occurred during the conversation."""
        try:
            # Check for handoff patterns in the response
            response_text = str(result.final_output).lower()
            handoff_indicators = [
                "let me connect you",
                "transferring you to",
                "specialist will help",
                "booking specialist",
                "concierge can help",
                "service team will",
                "activities coordinator"
            ]
            
            handoff_occurred = any(indicator in response_text for indicator in handoff_indicators)
            
            if handoff_occurred:
                logger.info(f"🔄 Handoff detected in response")
            
            return handoff_occurred
        except Exception as e:
            logger.warning(f"⚠️ Error checking handoff: {e}")
            return False

    async def get_session_history(self, session_id: str) -> List[ChatMessage]:
        """Get conversation history for a session."""
        logger.info(f"📖 Retrieving session history for: {session_id}")
        
        if session_id not in self.sessions:
            logger.warning(f"⚠️ Session not found: {session_id}")
            return []

        context = self.sessions[session_id]
        messages = []
        
        logger.info(f"📚 Found {len(context.conversation_history)} messages in history")

        for msg in context.conversation_history:
            # Use stored timestamp if available, otherwise current time
            timestamp = datetime.fromisoformat(msg.get("timestamp", datetime.now().isoformat()))
            messages.append(
                ChatMessage(
                    role=MessageRole(msg["role"]),
                    content=msg["content"],
                    timestamp=timestamp,
                )
            )

        return messages

    async def clear_session(self, session_id: str) -> bool:
        """Clear a conversation session."""
        logger.info(f"🗑️ Clearing session: {session_id}")
        
        if session_id in self.sessions:
            context = self.sessions[session_id]
            history_length = len(context.conversation_history)
            
            del self.sessions[session_id]
            
            logger.info(f"✅ Cleared session {session_id} with {history_length} messages")
            return True
        
        logger.warning(f"⚠️ Attempted to clear non-existent session: {session_id}")
        return False

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a session."""
        if session_id not in self.sessions:
            return None
            
        context = self.sessions[session_id]
        
        return {
            "session_id": session_id,
            "hotel_id": context.hotel_id,
            "hotel_name": context.hotel_name,
            "user_id": context.user_id,
            "created_at": context.created_at.isoformat() if context.created_at else None,
            "last_activity": context.last_activity.isoformat() if context.last_activity else None,
            "message_count": len(context.conversation_history),
            "conversation_preview": [
                {
                    "role": msg["role"],
                    "content": msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"],
                    "timestamp": msg.get("timestamp")
                }
                for msg in context.conversation_history[-5:]  # Last 5 messages
            ]
        }

    def get_all_sessions_info(self) -> List[Dict[str, Any]]:
        """Get information about all active sessions."""
        sessions_info = []
        
        for session_id in self.sessions:
            info = self.get_session_info(session_id)
            if info:
                sessions_info.append(info)
        
        logger.info(f"📊 Retrieved info for {len(sessions_info)} active sessions")
        return sessions_info

    def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up sessions older than max_age_hours."""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        sessions_to_remove = []
        
        for session_id, context in self.sessions.items():
            if context.last_activity < cutoff_time:
                sessions_to_remove.append(session_id)
        
        removed_count = 0
        for session_id in sessions_to_remove:
            del self.sessions[session_id]
            removed_count += 1
            logger.info(f"🧹 Cleaned up old session: {session_id}")
        
        if removed_count > 0:
            logger.info(f"✅ Cleaned up {removed_count} old sessions")
        
        return removed_count

    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about current sessions."""
        if not self.sessions:
            return {
                "total_sessions": 0,
                "total_messages": 0,
                "average_messages_per_session": 0,
                "oldest_session_age_minutes": 0,
                "newest_session_age_minutes": 0
            }
        
        total_messages = sum(len(context.conversation_history) for context in self.sessions.values())
        session_ages = []
        now = datetime.now()
        
        for context in self.sessions.values():
            if context.created_at:
                age_minutes = (now - context.created_at).total_seconds() / 60
                session_ages.append(age_minutes)
        
        stats = {
            "total_sessions": len(self.sessions),
            "total_messages": total_messages,
            "average_messages_per_session": total_messages / len(self.sessions) if self.sessions else 0,
            "oldest_session_age_minutes": max(session_ages) if session_ages else 0,
            "newest_session_age_minutes": min(session_ages) if session_ages else 0
        }
        
        logger.info(f"📈 Session stats: {stats}")
        return stats


# Global chat service instance with MCP
chat_service_mcp = ChatServiceMCP()