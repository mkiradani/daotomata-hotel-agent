#!/usr/bin/env python3
"""
Debug detallado del flujo de memoria
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from app.services.chat_service_mcp import chat_service_mcp
from app.models import ChatRequest

async def debug_memory_flow():
    """Debug paso a paso del flujo de memoria."""
    
    print("\n🔍 DEBUG MEMORY FLOW")
    print("=" * 80)
    
    session_id = "debug_flow_session"
    hotel_id = "2"
    
    # PASO 1: Primer mensaje
    print("\n1️⃣ PRIMER MENSAJE")
    print("-" * 40)
    
    request1 = ChatRequest(
        message="Hola, soy Ana",
        session_id=session_id,
        hotel_id=hotel_id
    )
    
    print(f"Request: {request1}")
    
    # Verificar estado ANTES
    print(f"Sessions antes: {list(chat_service_mcp.sessions.keys())}")
    
    try:
        response1 = await chat_service_mcp.process_chat(request1)
        print(f"✅ Response: {response1.message}")
        print(f"   Session ID: {response1.session_id}")
        print(f"   Agent: {response1.agent_used}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Verificar estado DESPUÉS
    print(f"Sessions después: {list(chat_service_mcp.sessions.keys())}")
    if session_id in chat_service_mcp.sessions:
        context = chat_service_mcp.sessions[session_id]
        print(f"History length: {len(context.conversation_history)}")
        print("History content:")
        for i, msg in enumerate(context.conversation_history):
            print(f"  {i}: {msg}")
    
    # PASO 2: Segundo mensaje
    print("\n2️⃣ SEGUNDO MENSAJE")
    print("-" * 40)
    
    request2 = ChatRequest(
        message="¿Cuál fue mi mensaje anterior?",
        session_id=session_id,
        hotel_id=hotel_id
    )
    
    print(f"Request: {request2}")
    
    # Verificar contexto ANTES del segundo mensaje
    if session_id in chat_service_mcp.sessions:
        context = chat_service_mcp.sessions[session_id]
        print(f"Context antes del 2do mensaje:")
        print(f"  History length: {len(context.conversation_history)}")
        print(f"  Hotel ID: {context.hotel_id}")
        print(f"  Created: {context.created_at}")
        
        # Simular _prepare_conversation_input
        messages = []
        system_message = chat_service_mcp._create_system_message(context)
        messages.append({"role": "system", "content": system_message})
        messages.extend(context.conversation_history)
        messages.append({"role": "user", "content": request2.message})
        
        print(f"Prepared messages for agent:")
        for i, msg in enumerate(messages):
            print(f"  {i}: {msg['role']}: {msg['content'][:50]}...")
    
    try:
        response2 = await chat_service_mcp.process_chat(request2)
        print(f"✅ Response: {response2.message}")
        print(f"   Agent: {response2.agent_used}")
        
        # Verificar si recordó
        remembered = "ana" in response2.message.lower() or "hola" in response2.message.lower()
        print(f"   Remembered previous message: {'✅' if remembered else '❌'}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # PASO 3: Estado final
    print("\n3️⃣ ESTADO FINAL")
    print("-" * 40)
    
    if session_id in chat_service_mcp.sessions:
        context = chat_service_mcp.sessions[session_id]
        print(f"Final history length: {len(context.conversation_history)}")
        print("Final history:")
        for i, msg in enumerate(context.conversation_history):
            print(f"  {i}: {msg['role']}: {msg['content']}")

if __name__ == "__main__":
    asyncio.run(debug_memory_flow())