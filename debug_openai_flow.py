#!/usr/bin/env python3
"""
Debug específico del flujo OpenAI con y sin historial
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from app.services.chat_service_mcp import chat_service_mcp
from app.models import ChatRequest
from app.config import settings

async def debug_openai_flow():
    """Debug detallado de por qué OpenAI falla con historial."""
    
    print("\n🔍 DEBUG OPENAI FLOW")
    print("=" * 80)
    
    # PASO 1: Verificar variables de entorno
    print("\n1️⃣ VARIABLES DE ENTORNO")
    print("-" * 40)
    print(f"OPENAI_API_KEY exists: {bool(os.getenv('OPENAI_API_KEY'))}")
    print(f"OPENAI_API_KEY length: {len(os.getenv('OPENAI_API_KEY', ''))}")
    print(f"Settings openai_api_key: {bool(settings.openai_api_key)}")
    print(f"Settings openai_model: {settings.openai_model}")
    
    session_id = "debug_openai_session"
    hotel_id = "2"
    
    # PASO 2: Mensaje sin historial (debería funcionar)
    print("\n2️⃣ MENSAJE SIN HISTORIAL")
    print("-" * 40)
    
    # Limpiar cualquier sesión previa
    if session_id in chat_service_mcp.sessions:
        del chat_service_mcp.sessions[session_id]
    
    request1 = ChatRequest(
        message="Hola",
        session_id=session_id,
        hotel_id=hotel_id
    )
    
    print(f"Sessions antes: {list(chat_service_mcp.sessions.keys())}")
    
    try:
        response1 = await chat_service_mcp.process_chat(request1)
        print(f"✅ FUNCIONA - Response: {response1.message}")
        print(f"   Agent: {response1.agent_used}")
        
        # Verificar estado después
        if session_id in chat_service_mcp.sessions:
            context = chat_service_mcp.sessions[session_id]
            print(f"   History length después: {len(context.conversation_history)}")
            
    except Exception as e:
        print(f"❌ FALLA - Error: {e}")
    
    # PASO 3: Mensaje con historial (debería fallar)
    print("\n3️⃣ MENSAJE CON HISTORIAL")
    print("-" * 40)
    
    if session_id in chat_service_mcp.sessions:
        context = chat_service_mcp.sessions[session_id]
        print(f"History antes del 2do mensaje: {len(context.conversation_history)}")
        for i, msg in enumerate(context.conversation_history):
            print(f"  {i}: {msg['role']}: {msg['content'][:30]}...")
    
    request2 = ChatRequest(
        message="¿Cuál fue mi mensaje anterior?",
        session_id=session_id,
        hotel_id=hotel_id
    )
    
    # Verificar ambiente justo antes del segundo mensaje
    print(f"ENV check antes 2do mensaje:")
    print(f"  OPENAI_API_KEY: {bool(os.getenv('OPENAI_API_KEY'))}")
    print(f"  Settings check: {bool(settings.openai_api_key)}")
    
    try:
        response2 = await chat_service_mcp.process_chat(request2)
        print(f"✅ FUNCIONA - Response: {response2.message}")
        print(f"   Agent: {response2.agent_used}")
        
    except Exception as e:
        print(f"❌ FALLA - Error: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
    
    # PASO 4: Análisis del contexto que se pasa al agente
    print("\n4️⃣ ANÁLISIS DEL CONTEXTO")
    print("-" * 40)
    
    if session_id in chat_service_mcp.sessions:
        context = chat_service_mcp.sessions[session_id]
        
        # Simular _prepare_conversation_input
        messages = []
        system_message = chat_service_mcp._create_system_message(context)
        messages.append({"role": "system", "content": system_message})
        messages.extend(context.conversation_history)
        messages.append({"role": "user", "content": "test message"})
        
        print(f"Context que se pasa al agente:")
        print(f"  Total messages: {len(messages)}")
        print(f"  System message length: {len(system_message)}")
        
        for i, msg in enumerate(messages):
            content_preview = msg['content'][:50] + "..." if len(msg['content']) > 50 else msg['content']
            print(f"    {i}: {msg['role']}: {content_preview}")

if __name__ == "__main__":
    asyncio.run(debug_openai_flow())