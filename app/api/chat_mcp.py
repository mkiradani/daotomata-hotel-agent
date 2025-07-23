"""Chat API endpoints with MCP integration."""

from typing import List
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse

from ..models import ChatRequest, ChatResponse, ChatMessage, ErrorResponse
from ..services.chat_service_mcp import chat_service_mcp
from ..config import settings

router = APIRouter(prefix="/api/chat-mcp", tags=["chat-mcp"])


@router.post("/", response_model=ChatResponse)
async def chat_mcp(request: ChatRequest) -> ChatResponse:
    """
    Process a chat message using MCP-enabled agents.

    This endpoint handles conversations with the hotel's AI concierge system
    using Model Context Protocol (MCP) for real-time Directus integration.
    
    The system uses specialized agents with live data access:
    - Booking Specialist: Room reservations with real-time data
    - Hotel Concierge: Local recommendations with hotel context
    - Guest Services: Hotel services with live facility data  
    - Activities Coordinator: Hotel activities with current schedules
    """
    try:
        response = await chat_service_mcp.process_chat(request)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing MCP chat request: {str(e)}"
        )


@router.get("/sessions/{session_id}/history", response_model=List[ChatMessage])
async def get_session_history_mcp(session_id: str) -> List[ChatMessage]:
    """
    Get conversation history for a specific session with MCP context.
    """
    try:
        history = await chat_service_mcp.get_session_history(session_id)
        return history
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving MCP session history: {str(e)}"
        )


@router.delete("/sessions/{session_id}")
async def clear_session_mcp(session_id: str) -> dict:
    """
    Clear a conversation session with MCP context.
    """
    try:
        success = await chat_service_mcp.clear_session(session_id)
        if success:
            return {"message": "MCP session cleared successfully"}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing MCP session: {str(e)}")


@router.post("/test")
async def test_chat_mcp() -> dict:
    """
    Test endpoint for MCP-enabled chat functionality.
    """
    try:
        test_request = ChatRequest(
            message="Hello, can you tell me about the hotel's facilities using live data?",
            session_id="test-mcp-session",
            hotel_id="1"  # Use real hotel ID
        )

        response = await chat_service_mcp.process_chat(test_request)

        return {
            "status": "success",
            "test_response": response.message,
            "agent_used": response.agent_used,
            "session_id": response.session_id,
            "mcp_enabled": True,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MCP chat test failed: {str(e)}")