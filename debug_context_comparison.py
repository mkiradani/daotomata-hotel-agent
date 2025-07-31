#!/usr/bin/env python3
"""
Comparar exactamente qué contexto se pasa al agente en primer vs segundo mensaje
"""

import asyncio
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from app.services.chat_service_mcp import chat_service_mcp, HotelContext
from app.models import ChatRequest

async def debug_context_comparison():
    """Comparar contexto exacto que recibe el agente."""
    
    print("\n🔍 DEBUG CONTEXT COMPARISON")
    print("=" * 80)
    
    session_id = "debug_context_session"
    hotel_id = "2"
    
    # Limpiar sesión previa
    if session_id in chat_service_mcp.sessions:
        del chat_service_mcp.sessions[session_id]
    
    print("\n1️⃣ CONTEXTO SIN HISTORIAL (primer mensaje)")
    print("-" * 60)
    
    # Simular primer mensaje
    request1 = ChatRequest(
        message="Hola",
        session_id=session_id,
        hotel_id=hotel_id
    )
    
    # Obtener contexto como lo haría process_chat
    hotel_context1 = await chat_service_mcp._get_hotel_context(request1, session_id)
    conversation_input1 = await chat_service_mcp._prepare_conversation_input(request1, hotel_context1)
    
    print(f"Hotel context:")
    print(f"  hotel_id: {hotel_context1.hotel_id}")
    print(f"  session_id: {hotel_context1.session_id}")
    print(f"  conversation_history length: {len(hotel_context1.conversation_history)}")
    
    print(f"\nConversation input:")
    print(f"  Total messages: {len(conversation_input1)}")
    for i, msg in enumerate(conversation_input1):
        print(f"    {i}: {msg['role']}: {msg['content'][:100]}...")
    
    print(f"\nJSON representation:")
    print(json.dumps(conversation_input1, indent=2)[:500] + "...")
    
    # Simular que se guardó el primer mensaje (como haría el sistema real)
    await chat_service_mcp._store_user_message(hotel_context1, "Hola")
    await chat_service_mcp._store_assistant_response(hotel_context1, "¡Hola! ¿Cómo puedo ayudarte?")
    
    print("\n2️⃣ CONTEXTO CON HISTORIAL (segundo mensaje)")
    print("-" * 60)
    
    # Simular segundo mensaje
    request2 = ChatRequest(
        message="¿Cuál fue mi mensaje anterior?",
        session_id=session_id,
        hotel_id=hotel_id
    )
    
    # Obtener contexto como lo haría process_chat
    hotel_context2 = await chat_service_mcp._get_hotel_context(request2, session_id)
    conversation_input2 = await chat_service_mcp._prepare_conversation_input(request2, hotel_context2)
    
    print(f"Hotel context:")
    print(f"  hotel_id: {hotel_context2.hotel_id}")
    print(f"  session_id: {hotel_context2.session_id}")
    print(f"  conversation_history length: {len(hotel_context2.conversation_history)}")
    print(f"  conversation_history content:")
    for i, msg in enumerate(hotel_context2.conversation_history):
        print(f"    {i}: {msg}")
    
    print(f"\nConversation input:")
    print(f"  Total messages: {len(conversation_input2)}")
    for i, msg in enumerate(conversation_input2):
        print(f"    {i}: {msg['role']}: {msg['content'][:100]}...")
    
    print(f"\nJSON representation:")
    print(json.dumps(conversation_input2, indent=2))
    
    print("\n3️⃣ ANÁLISIS DE DIFERENCIAS")
    print("-" * 60)
    
    print(f"Diferencias principales:")
    print(f"  Mensaje 1 - Total input messages: {len(conversation_input1)}")
    print(f"  Mensaje 2 - Total input messages: {len(conversation_input2)}")
    print(f"  Diferencia: {len(conversation_input2) - len(conversation_input1)} mensajes adicionales")
    
    # Verificar si hay algo problemático en el formato de los mensajes del historial
    print(f"\nVerificación de formato de mensajes:")
    for i, msg in enumerate(conversation_input2):
        print(f"  Message {i}:")
        print(f"    'role' field: {type(msg.get('role'))} = {repr(msg.get('role'))}")
        print(f"    'content' field: {type(msg.get('content'))} = {len(str(msg.get('content')))} chars")
        
        # Verificar si hay campos inesperados
        expected_fields = {'role', 'content'}
        unexpected_fields = set(msg.keys()) - expected_fields
        if unexpected_fields:
            print(f"    ⚠️ Unexpected fields: {unexpected_fields}")
        
        # Verificar valores válidos para role
        valid_roles = {'system', 'user', 'assistant'}
        if msg.get('role') not in valid_roles:
            print(f"    ⚠️ Invalid role: {msg.get('role')}")

if __name__ == "__main__":
    asyncio.run(debug_context_comparison())