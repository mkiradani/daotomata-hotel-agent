#!/usr/bin/env python3
"""
Test que la memoria del chat funciona correctamente
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from app.services.chat_service_mcp import chat_service_mcp
from app.models import ChatRequest

async def test_conversation_memory():
    """Test que la memoria conversacional funciona."""
    
    print("\n🧪 TESTING CONVERSATION MEMORY")
    print("=" * 80)
    
    session_id = "test_memory_session"
    hotel_id = "2"
    
    # First message
    print("\n1️⃣ First Message: 'Hola, soy Juan'")
    request1 = ChatRequest(
        message="Hola, soy Juan",
        session_id=session_id,
        hotel_id=hotel_id
    )
    
    response1 = await chat_service_mcp.process_chat(request1)
    print(f"   Bot response: {response1.message}")
    
    # Check if session was created
    if session_id in chat_service_mcp.sessions:
        context = chat_service_mcp.sessions[session_id]
        print(f"   Session created: ✅")
        print(f"   History length: {len(context.conversation_history)}")
        print(f"   History: {context.conversation_history}")
    else:
        print(f"   Session created: ❌")
    
    # Second message - should remember name
    print("\n2️⃣ Second Message: '¿Cuál es mi nombre?'")
    request2 = ChatRequest(
        message="¿Cuál es mi nombre?",
        session_id=session_id,
        hotel_id=hotel_id
    )
    
    response2 = await chat_service_mcp.process_chat(request2)
    print(f"   Bot response: {response2.message}")
    
    # Check if "Juan" is in the response
    if "Juan" in response2.message or "juan" in response2.message.lower():
        print("   ✅ Bot remembered the name!")
    else:
        print("   ❌ Bot did NOT remember the name")
    
    # Check conversation history
    if session_id in chat_service_mcp.sessions:
        context = chat_service_mcp.sessions[session_id]
        print(f"   Final history length: {len(context.conversation_history)}")
        print(f"   Final history:")
        for i, msg in enumerate(context.conversation_history):
            print(f"     {i+1}. {msg['role']}: {msg['content']}")
    
    print("\n✅ Memory test completed!")

if __name__ == "__main__":
    asyncio.run(test_conversation_memory())