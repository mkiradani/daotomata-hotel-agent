#!/usr/bin/env python3
"""
Script para comparar el contenido obtenido vía MCP para diferentes Hotel IDs
"""

import asyncio
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

# Ensure OpenAI API key is set
if not os.getenv('OPENAI_API_KEY'):
    print("❌ OPENAI_API_KEY not found in environment")
    sys.exit(1)

from app.agents.hotel_agents_mcp import create_triage_agent
from agents import Runner

async def get_hotel_info_via_mcp(hotel_id: str) -> Dict[str, Any]:
    """Obtener información del hotel usando MCP directamente."""
    
    print(f"\n🏨 Obteniendo información para Hotel ID: {hotel_id}")
    print("=" * 60)
    
    # Crear agente con MCP
    agent = await create_triage_agent()
    
    # Contexto del hotel
    hotel_context = {
        "hotel_id": hotel_id,
        "session_id": f"test_session_{hotel_id}"
    }
    
    # Mensaje para obtener información
    messages = [
        {
            "role": "system", 
            "content": f"You are a hotel assistant. The hotel ID is {hotel_id}. Use the Directus MCP tools to get detailed information about this hotel including name, description, amenities, rooms, and any other available data."
        },
        {
            "role": "user",
            "content": "Please get all available information about this hotel using the Directus tools. Include hotel details, amenities, rooms, and any other data you can retrieve."
        }
    ]
    
    try:
        # Ejecutar el agente
        result = await Runner.run(
            agent, 
            messages, 
            context=hotel_context,
            max_turns=10
        )
        
        hotel_info = {
            "hotel_id": hotel_id,
            "response": str(result.final_output),
            "tools_used": [],
            "raw_data": {}
        }
        
        # Extraer herramientas usadas
        if hasattr(result, 'messages') and result.messages:
            for message in result.messages:
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    for tool_call in message.tool_calls:
                        if hasattr(tool_call, 'function') and tool_call.function:
                            tool_name = tool_call.function.name
                            hotel_info["tools_used"].append(tool_name)
        
        return hotel_info
        
    except Exception as e:
        print(f"❌ Error obteniendo información del hotel {hotel_id}: {e}")
        return {
            "hotel_id": hotel_id,
            "error": str(e),
            "response": None,
            "tools_used": []
        }

async def test_specific_mcp_queries(hotel_id: str) -> Dict[str, Any]:
    """Probar queries específicas de MCP para un hotel."""
    
    print(f"\n🔍 Pruebas específicas MCP para Hotel ID: {hotel_id}")
    print("-" * 50)
    
    agent = await create_triage_agent()
    results = {}
    
    # Lista de queries específicas para probar
    test_queries = [
        {
            "name": "hotel_basic_info",
            "query": "What is the exact name and description of this hotel from Directus?"
        },
        {
            "name": "hotel_amenities", 
            "query": "List all amenities available at this hotel from the Directus database."
        },
        {
            "name": "hotel_rooms",
            "query": "Show me all room types available at this hotel with their details."
        },
        {
            "name": "hotel_location",
            "query": "What is the address and location information for this hotel?"
        }
    ]
    
    for test in test_queries:
        print(f"\n📋 Test: {test['name']}")
        
        messages = [
            {
                "role": "system",
                "content": f"You are a hotel assistant. The hotel ID is {hotel_id}. Use only Directus MCP tools to answer. Be specific and include all data retrieved."
            },
            {
                "role": "user",
                "content": test['query']
            }
        ]
        
        try:
            result = await Runner.run(
                agent,
                messages,
                context={"hotel_id": hotel_id},
                max_turns=5
            )
            
            results[test['name']] = {
                "query": test['query'],
                "response": str(result.final_output),
                "success": True
            }
            
            print(f"✅ Response preview: {str(result.final_output)[:150]}...")
            
        except Exception as e:
            results[test['name']] = {
                "query": test['query'],
                "response": None,
                "error": str(e),
                "success": False
            }
            print(f"❌ Error: {e}")
    
    return results

async def compare_hotels():
    """Comparar contenido MCP entre Hotel ID 1 y 2."""
    
    print("\n🔄 COMPARACIÓN DE CONTENIDO MCP ENTRE HOTELES")
    print("=" * 80)
    
    # Obtener información general de ambos hoteles
    print("\n📊 INFORMACIÓN GENERAL")
    hotel1_info = await get_hotel_info_via_mcp("1")
    hotel2_info = await get_hotel_info_via_mcp("2")
    
    # Pruebas específicas
    print("\n📊 PRUEBAS ESPECÍFICAS")
    hotel1_specific = await test_specific_mcp_queries("1")
    hotel2_specific = await test_specific_mcp_queries("2")
    
    # Análisis de diferencias
    print("\n📈 ANÁLISIS DE DIFERENCIAS")
    print("=" * 80)
    
    print("\n1️⃣ HOTEL ID 1:")
    print(f"Tools used: {set(hotel1_info.get('tools_used', []))}")
    if hotel1_info.get('response'):
        print(f"Response length: {len(hotel1_info['response'])} chars")
        print(f"Response preview: {hotel1_info['response'][:200]}...")
    
    print("\n2️⃣ HOTEL ID 2:")
    print(f"Tools used: {set(hotel2_info.get('tools_used', []))}")
    if hotel2_info.get('response'):
        print(f"Response length: {len(hotel2_info['response'])} chars")
        print(f"Response preview: {hotel2_info['response'][:200]}...")
    
    # Comparar respuestas específicas
    print("\n🔍 COMPARACIÓN DE QUERIES ESPECÍFICAS:")
    for query_name in hotel1_specific.keys():
        print(f"\n📋 {query_name}:")
        
        h1_response = hotel1_specific[query_name].get('response', 'No response')
        h2_response = hotel2_specific[query_name].get('response', 'No response')
        
        print(f"  Hotel 1 success: {hotel1_specific[query_name]['success']}")
        print(f"  Hotel 2 success: {hotel2_specific[query_name]['success']}")
        
        if h1_response and h2_response:
            # Verificar si las respuestas son idénticas
            if h1_response == h2_response:
                print(f"  ⚠️ RESPUESTAS IDÉNTICAS!")
            else:
                print(f"  ✅ Respuestas diferentes")
                
                # Buscar indicadores de contenido específico
                hotel1_indicators = []
                hotel2_indicators = []
                
                # Buscar nombres o referencias específicas
                if "hotel 1" in h1_response.lower() or "hotel id 1" in h1_response.lower():
                    hotel1_indicators.append("Referencias a Hotel 1")
                if "hotel 2" in h2_response.lower() or "hotel id 2" in h2_response.lower():
                    hotel2_indicators.append("Referencias a Hotel 2")
                
                # Buscar diferencias en contenido
                if hotel1_indicators:
                    print(f"  Hotel 1 indicators: {hotel1_indicators}")
                if hotel2_indicators:
                    print(f"  Hotel 2 indicators: {hotel2_indicators}")
    
    # Guardar resultados completos
    results = {
        "hotel_1": {
            "general_info": hotel1_info,
            "specific_queries": hotel1_specific
        },
        "hotel_2": {
            "general_info": hotel2_info,
            "specific_queries": hotel2_specific
        },
        "timestamp": str(asyncio.get_event_loop().time())
    }
    
    with open("mcp_hotel_comparison_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\n✅ Resultados guardados en mcp_hotel_comparison_results.json")

if __name__ == "__main__":
    asyncio.run(compare_hotels())