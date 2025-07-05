"""Chat API endpoints."""

from typing import List
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse

from ..models import ChatRequest, ChatResponse, ChatMessage, ErrorResponse
from ..services.chat_service import chat_service
from ..config import settings

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Process a chat message and return the agent's response.

    This endpoint handles conversations with the hotel's AI concierge system.
    The system uses specialized agents for different types of requests:
    - Booking Specialist: Room reservations and availability
    - Hotel Concierge: Local recommendations and general assistance
    - Guest Services: Hotel services and maintenance requests
    - Activities Coordinator: Hotel activities and experiences
    """
    try:
        response = await chat_service.process_chat(request)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing chat request: {str(e)}"
        )


@router.get("/sessions/{session_id}/history", response_model=List[ChatMessage])
async def get_session_history(session_id: str) -> List[ChatMessage]:
    """
    Get conversation history for a specific session.

    Returns the complete conversation history for the given session ID,
    including both user messages and assistant responses.
    """
    try:
        history = await chat_service.get_session_history(session_id)
        return history
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving session history: {str(e)}"
        )


@router.delete("/sessions/{session_id}")
async def clear_session(session_id: str) -> dict:
    """
    Clear a conversation session.

    Removes all conversation history and context for the specified session.
    This is useful for starting fresh conversations or cleaning up old sessions.
    """
    try:
        success = await chat_service.clear_session(session_id)
        if success:
            return {"message": "Session cleared successfully"}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing session: {str(e)}")


@router.post("/test")
async def test_chat() -> dict:
    """
    Test endpoint for quick chat functionality verification.

    Sends a simple test message to verify the chat system is working correctly.
    Useful for health checks and integration testing.
    """
    try:
        test_request = ChatRequest(
            message="Hello, can you help me with information about the hotel?",
            session_id="test-session",
        )

        response = await chat_service.process_chat(test_request)

        return {
            "status": "success",
            "test_response": response.message,
            "agent_used": response.agent_used,
            "session_id": response.session_id,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat test failed: {str(e)}")
