#!/usr/bin/env python3
"""
Test del flujo completo de webhook Chatwoot para identificar el problema con el historial
"""

import requests
import json
import time

# Simular payloads reales de Chatwoot
def create_chatwoot_payload(message, conversation_id=123, contact_name="TestUser"):
    """Crear payload que simula webhook de Chatwoot."""
    return {
        "event": "message_created",
        "id": f"{int(time.time())}",
        "content": message,
        "created_at": "2025-07-30 19:17:00 UTC",
        "message_type": "incoming", 
        "content_type": "text",
        "sender": {
            "id": "456",
            "name": contact_name,
            "email": f"{contact_name.lower()}@test.com",
            "type": "contact"
        },
        "contact": {
            "id": "456",
            "name": contact_name,
            "email": f"{contact_name.lower()}@test.com"
        },
        "conversation": {
            "display_id": conversation_id,
            "id": conversation_id
        },
        "account": {
            "id": "1",
            "name": "Test Hotel"
        }
    }

def test_chatwoot_webhook_flow():
    """Probar el flujo completo via webhook."""
    
    print("\n🔍 TESTING CHATWOOT WEBHOOK FLOW")
    print("=" * 80)
    
    base_url = "http://localhost:8000"
    webhook_url = f"{base_url}/webhook/chatwoot/2"
    
    conversation_id = 999  # ID único para esta prueba
    
    # Test 1: Primer mensaje via webhook
    print("\n1️⃣ PRIMER MENSAJE VIA WEBHOOK")
    print("-" * 40)
    
    payload1 = create_chatwoot_payload("Hola, soy Pedro", conversation_id, "Pedro")
    
    try:
        response1 = requests.post(webhook_url, json=payload1, timeout=30)
        print(f"Status: {response1.status_code}")
        print(f"Response: {response1.json()}")
        
        if response1.status_code == 200:
            result1 = response1.json()
            session_id = result1.get('session_id', f'chatwoot_{conversation_id}')
            print(f"✅ Primer mensaje procesado - Session: {session_id}")
        else:
            print(f"❌ Error en primer mensaje: {response1.text}")
            return
            
    except Exception as e:
        print(f"❌ Error en primer mensaje: {e}")
        return
    
    # Esperar un poco para que se procese
    time.sleep(2)
    
    # Verificar estado de sesión después del primer mensaje
    session_info_url = f"{base_url}/api/chat-mcp/sessions/{session_id}/info"
    try:
        session_response = requests.get(session_info_url)
        if session_response.status_code == 200:
            session_data = session_response.json()
            print(f"📊 Session después del 1er mensaje:")
            print(f"   Message count: {session_data['message_count']}")
            print(f"   Last activity: {session_data['last_activity']}")
        else:
            print(f"⚠️ No se pudo obtener info de sesión: {session_response.status_code}")
    except Exception as e:
        print(f"⚠️ Error obteniendo session info: {e}")
    
    # Test 2: Segundo mensaje via webhook (donde debería fallar)
    print("\n2️⃣ SEGUNDO MENSAJE VIA WEBHOOK")
    print("-" * 40)
    
    payload2 = create_chatwoot_payload("¿Cuál fue mi mensaje anterior?", conversation_id, "Pedro")
    
    try:
        response2 = requests.post(webhook_url, json=payload2, timeout=30)
        print(f"Status: {response2.status_code}")
        print(f"Response: {response2.json()}")
        
        if response2.status_code == 200:
            result2 = response2.json()
            print(f"✅ Segundo mensaje procesado")
            
            # Verificar si el agente fue error_handler
            if result2.get('agent_used') == 'error_handler':
                print(f"❌ Segundo mensaje falló - se usó error_handler")
            else:
                print(f"🎯 Segundo mensaje exitoso - agente: {result2.get('agent_used')}")
        else:
            print(f"❌ Error en segundo mensaje: {response2.text}")
            
    except Exception as e:
        print(f"❌ Error en segundo mensaje: {e}")
    
    # Verificar estado final de sesión
    print("\n3️⃣ ESTADO FINAL DE SESIÓN")
    print("-" * 40)
    
    try:
        final_session_response = requests.get(session_info_url)
        if final_session_response.status_code == 200:
            final_session_data = final_session_response.json()
            print(f"📊 Session final:")
            print(f"   Message count: {final_session_data['message_count']}")
            print(f"   Conversation preview:")
            for i, msg in enumerate(final_session_data['conversation_preview']):
                print(f"     {i+1}. {msg['role']}: {msg['content'][:50]}...")
        else:
            print(f"⚠️ No se pudo obtener info final de sesión")
    except Exception as e:
        print(f"⚠️ Error obteniendo session info final: {e}")

if __name__ == "__main__":
    test_chatwoot_webhook_flow()