"""Debug chat service integration."""

import asyncio
from app.services.simple_chat_service import chat_service
from app.models import ChatRequest

async def test_chat():
    """Test chat service directly."""
    
    request = ChatRequest(
        message="¿Tenéis habitaciones disponibles para mañana?",
        session_id="debug-session",
        hotel_id="2"
    )
    
    print("Testing chat service...")
    print(f"Message: {request.message}")
    print(f"Hotel ID: {request.hotel_id}")
    print("\n" + "="*50 + "\n")
    
    try:
        response = await chat_service.process_chat(request)
        print("Success!")
        print(f"Response: {response.message}")
        print(f"Agent: {response.agent_used}")
        print(f"Tools used: {response.tools_used}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_chat())