#!/usr/bin/env python3
"""
Comparación directa de contenido MCP entre hoteles sin usar agentes
"""

import asyncio
import json
import os
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from typing import Dict, Any

# Load environment variables
load_dotenv()

async def test_directus_mcp_direct():
    """Test directo del MCP de Directus para comparar hoteles."""
    
    print("\n🔄 COMPARACIÓN DIRECTA MCP ENTRE HOTEL ID 1 Y 2")
    print("=" * 80)
    
    # Configuración del servidor MCP
    server_params = {
        "command": "uvx",
        "args": [
            "--from", "mcp-directus-datalab",
            "mcp-directus-datalab",
            "--directus-url", os.getenv("DIRECTUS_URL"),
            "--directus-token", os.getenv("DIRECTUS_TOKEN")
        ]
    }
    
    async with stdio_client(**server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            # Inicializar sesión
            await session.initialize()
            
            print(f"\n✅ MCP Session initialized")
            print(f"Available tools: {len(session.tools)}")
            
            # Test 1: Obtener información de Hotel 1
            print("\n1️⃣ HOTEL ID 1 - Información básica")
            print("-" * 50)
            
            try:
                # Leer información del hotel 1
                result1 = await session.call_tool(
                    "read-items",
                    arguments={
                        "collection": "hotels", 
                        "query": {
                            "filter": {"id": {"_eq": "1"}},
                            "fields": ["*"]
                        }
                    }
                )
                
                print(f"Result type: {type(result1)}")
                print(f"Result content: {json.dumps(result1.content, indent=2)[:500]}...")
                
                hotel1_data = result1.content
                
            except Exception as e:
                print(f"❌ Error getting Hotel 1: {e}")
                hotel1_data = None
            
            # Test 2: Obtener información de Hotel 2
            print("\n2️⃣ HOTEL ID 2 - Información básica")
            print("-" * 50)
            
            try:
                # Leer información del hotel 2
                result2 = await session.call_tool(
                    "read-items",
                    arguments={
                        "collection": "hotels",
                        "query": {
                            "filter": {"id": {"_eq": "2"}},
                            "fields": ["*"]
                        }
                    }
                )
                
                print(f"Result type: {type(result2)}")
                print(f"Result content: {json.dumps(result2.content, indent=2)[:500]}...")
                
                hotel2_data = result2.content
                
            except Exception as e:
                print(f"❌ Error getting Hotel 2: {e}")
                hotel2_data = None
            
            # Test 3: Obtener amenities de ambos hoteles
            print("\n🏊 AMENITIES COMPARISON")
            print("-" * 50)
            
            for hotel_id in ["1", "2"]:
                try:
                    amenities_result = await session.call_tool(
                        "read-items",
                        arguments={
                            "collection": "hotel_amenities",
                            "query": {
                                "filter": {"hotels_id": {"_eq": hotel_id}},
                                "fields": ["*", "amenities_id.*"],
                                "limit": 10
                            }
                        }
                    )
                    
                    print(f"\nHotel {hotel_id} amenities:")
                    amenities_data = amenities_result.content
                    if amenities_data and 'data' in amenities_data:
                        for amenity in amenities_data['data'][:5]:  # Show first 5
                            if isinstance(amenity, dict) and 'amenities_id' in amenity:
                                amenity_info = amenity['amenities_id']
                                if isinstance(amenity_info, dict):
                                    print(f"  - {amenity_info.get('name', 'Unknown')}: {amenity_info.get('description', 'No description')}")
                    else:
                        print(f"  No amenities data found")
                        
                except Exception as e:
                    print(f"  ❌ Error getting amenities: {e}")
            
            # Test 4: Obtener habitaciones de ambos hoteles
            print("\n🛏️ ROOMS COMPARISON")
            print("-" * 50)
            
            for hotel_id in ["1", "2"]:
                try:
                    rooms_result = await session.call_tool(
                        "read-items",
                        arguments={
                            "collection": "rooms",
                            "query": {
                                "filter": {"hotel_id": {"_eq": hotel_id}},
                                "fields": ["id", "room_number", "room_type", "price", "is_available"],
                                "limit": 5
                            }
                        }
                    )
                    
                    print(f"\nHotel {hotel_id} rooms:")
                    rooms_data = rooms_result.content
                    if rooms_data and 'data' in rooms_data:
                        for room in rooms_data['data']:
                            print(f"  - Room {room.get('room_number', 'N/A')}: {room.get('room_type', 'Unknown')} - ${room.get('price', 'N/A')}")
                    else:
                        print(f"  No rooms data found")
                        
                except Exception as e:
                    print(f"  ❌ Error getting rooms: {e}")
            
            # Análisis de diferencias
            print("\n📊 ANÁLISIS DE DIFERENCIAS")
            print("=" * 80)
            
            if hotel1_data and hotel2_data:
                if 'data' in hotel1_data and hotel1_data['data']:
                    h1 = hotel1_data['data'][0] if isinstance(hotel1_data['data'], list) else hotel1_data['data']
                    print(f"\nHotel 1:")
                    print(f"  ID: {h1.get('id')}")
                    print(f"  Name: {h1.get('name', 'No name')}")
                    print(f"  Description: {str(h1.get('description', 'No description'))[:100]}...")
                    
                if 'data' in hotel2_data and hotel2_data['data']:
                    h2 = hotel2_data['data'][0] if isinstance(hotel2_data['data'], list) else hotel2_data['data']
                    print(f"\nHotel 2:")
                    print(f"  ID: {h2.get('id')}")
                    print(f"  Name: {h2.get('name', 'No name')}")
                    print(f"  Description: {str(h2.get('description', 'No description'))[:100]}...")
                
                # Verificar si son diferentes
                if hotel1_data == hotel2_data:
                    print("\n⚠️ WARNING: Los datos de ambos hoteles son IDÉNTICOS!")
                else:
                    print("\n✅ Los datos de los hoteles son DIFERENTES")
            
            # Guardar resultados
            results = {
                "hotel_1": hotel1_data,
                "hotel_2": hotel2_data,
                "comparison": "Different" if hotel1_data != hotel2_data else "Identical"
            }
            
            with open("mcp_direct_comparison_results.json", "w") as f:
                json.dump(results, f, indent=2)
            
            print("\n✅ Resultados guardados en mcp_direct_comparison_results.json")

if __name__ == "__main__":
    asyncio.run(test_directus_mcp_direct())