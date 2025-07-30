#!/usr/bin/env python3
"""
Test que verifica la integración de memoria con conversaciones de Chatwoot
"""

import asyncio
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from app.services.chat_service_mcp import chat_service_mcp
from app.models import ChatRequest

async def test_chatwoot_memory_integration():
    """Test que la memoria funciona con conversaciones de Chatwoot."""
    
    print("\n🧪 TESTING CHATWOOT MEMORY INTEGRATION")
    print("=" * 80)
    
    # Simulate a Chatwoot conversation
    conversation_id = "123"
    session_id = f"chatwoot_{conversation_id}"
    hotel_id = "2"
    
    # First message from guest
    print("\n1️⃣ First Chatwoot Message: Guest introduces themselves")
    request1 = ChatRequest(
        message="Hola, soy María y tengo una reserva para mañana",
        session_id=session_id,
        hotel_id=hotel_id,
        user_context={
            "platform": "chatwoot",
            "conversation_id": conversation_id,
            "contact_id": "456",
            "contact_name": "María García",
            "contact_email": "maria@example.com",
            "sender_type": "contact",
            "event_type": "message_created"
        }
    )
    
    try:
        response1 = await chat_service_mcp.process_chat(request1)
        print(f"   Bot response: {response1.message}")
        print(f"   Session ID: {response1.session_id}")
        print(f"   Agent used: {response1.agent_used}")
    except Exception as e:
        print(f"   Error: {e}")
        response1 = None
    
    # Check session creation
    session_info = chat_service_mcp.get_session_info(session_id)
    if session_info:
        print(f"   ✅ Session created with Chatwoot context")
        print(f"   Hotel ID: {session_info['hotel_id']}")
        print(f"   Message count: {session_info['message_count']}")
        print(f"   Created at: {session_info['created_at']}")
        print(f"   Context preview:")
        for msg in session_info['conversation_preview']:
            print(f"     - {msg['role']}: {msg['content'][:50]}...")
    else:
        print(f"   ❌ Session not found")
    
    # Second message - test memory continuity
    print("\n2️⃣ Second Chatwoot Message: Ask about previous context")
    request2 = ChatRequest(
        message="¿Podrías confirmar mi nombre y mi reserva?",
        session_id=session_id,
        hotel_id=hotel_id,
        user_context={
            "platform": "chatwoot",
            "conversation_id": conversation_id,
            "contact_id": "456",
            "contact_name": "María García",
            "contact_email": "maria@example.com",
            "sender_type": "contact",
            "event_type": "message_created"
        }
    )
    
    try:
        response2 = await chat_service_mcp.process_chat(request2)
        print(f"   Bot response: {response2.message}")
        
        # Check if bot remembers María and the reservation
        remembered_name = "maría" in response2.message.lower() or "maría" in response2.message.lower()
        remembered_reservation = "reserva" in response2.message.lower()
        
        print(f"   ✅ Remembered name: {'Yes' if remembered_name else 'No'}")
        print(f"   ✅ Remembered reservation: {'Yes' if remembered_reservation else 'No'}")
        
    except Exception as e:
        print(f"   Error: {e}")
        response2 = None
    
    # Check final session state
    session_info_final = chat_service_mcp.get_session_info(session_id)
    if session_info_final:
        print(f"\n📊 Final Session State:")
        print(f"   Total messages: {session_info_final['message_count']}")
        print(f"   Last activity: {session_info_final['last_activity']}")
        print(f"   Conversation history:")
        for i, msg in enumerate(session_info_final['conversation_preview']):
            print(f"     {i+1}. {msg['role']}: {msg['content']}")
    
    # Test session stats
    stats = chat_service_mcp.get_session_stats()
    print(f"\n📈 Session Statistics:")
    print(f"   Total sessions: {stats['total_sessions']}")
    print(f"   Total messages: {stats['total_messages']}")
    print(f"   Average messages per session: {stats['average_messages_per_session']:.1f}")
    
    print("\n✅ Chatwoot memory integration test completed!")

if __name__ == "__main__":
    asyncio.run(test_chatwoot_memory_integration())