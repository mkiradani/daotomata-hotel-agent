#!/usr/bin/env python3
"""
Comparar contenido obtenido para diferentes Hotel IDs a través del chat API
"""

import requests
import json
import time

def test_hotel_content(hotel_id: str, queries: list) -> dict:
    """Probar queries específicas para un hotel."""
    
    print(f"\n🏨 Testing Hotel ID: {hotel_id}")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    chat_url = f"{base_url}/api/chat-mcp"
    
    results = {
        "hotel_id": hotel_id,
        "queries": {}
    }
    
    session_id = f"test_hotel_{hotel_id}_{int(time.time())}"
    
    for i, query in enumerate(queries):
        print(f"\n📋 Query {i+1}: {query['name']}")
        print(f"Question: {query['question']}")
        
        payload = {
            "message": query['question'],
            "session_id": session_id,
            "hotel_id": hotel_id,
            "user_context": {}
        }
        
        try:
            response = requests.post(chat_url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                results["queries"][query['name']] = {
                    "question": query['question'],
                    "response": data.get("message", "No response"),
                    "agent_used": data.get("agent_used", "unknown"),
                    "tools_used": data.get("tools_used", []),
                    "success": True
                }
                print(f"✅ Response preview: {data['message'][:150]}...")
                print(f"   Agent: {data.get('agent_used')}")
                print(f"   Tools: {data.get('tools_used', [])}")
            else:
                results["queries"][query['name']] = {
                    "question": query['question'],
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "success": False
                }
                print(f"❌ Error: HTTP {response.status_code}")
                
        except Exception as e:
            results["queries"][query['name']] = {
                "question": query['question'],
                "error": str(e),
                "success": False
            }
            print(f"❌ Exception: {e}")
        
        # Pequeña pausa entre queries
        time.sleep(2)
    
    return results

def compare_hotel_content():
    """Comparar contenido entre Hotel ID 1 y 2."""
    
    print("\n🔄 COMPARACIÓN DE CONTENIDO ENTRE HOTEL ID 1 Y 2")
    print("=" * 80)
    
    # Queries específicas para probar
    test_queries = [
        {
            "name": "hotel_name",
            "question": "What is the exact name of this hotel? Please get it from the Directus database."
        },
        {
            "name": "hotel_description", 
            "question": "What is the description of this hotel from Directus?"
        },
        {
            "name": "hotel_amenities",
            "question": "List the first 5 amenities available at this hotel from the database."
        },
        {
            "name": "room_types",
            "question": "What room types are available at this hotel? Show me the first 3 rooms with their prices."
        },
        {
            "name": "hotel_address",
            "question": "What is the address and location of this hotel?"
        }
    ]
    
    # Probar ambos hoteles
    hotel1_results = test_hotel_content("1", test_queries)
    hotel2_results = test_hotel_content("2", test_queries)
    
    # Análisis de diferencias
    print("\n📊 ANÁLISIS DE DIFERENCIAS")
    print("=" * 80)
    
    for query_name in hotel1_results["queries"].keys():
        print(f"\n🔍 {query_name}:")
        
        h1_query = hotel1_results["queries"][query_name]
        h2_query = hotel2_results["queries"][query_name]
        
        if h1_query["success"] and h2_query["success"]:
            h1_response = h1_query["response"]
            h2_response = h2_query["response"]
            
            # Check if responses are identical
            if h1_response == h2_response:
                print("  ⚠️ RESPUESTAS IDÉNTICAS!")
                print(f"  Response: {h1_response[:100]}...")
            else:
                print("  ✅ Respuestas diferentes")
                
                # Buscar indicadores específicos
                hotel1_indicators = []
                hotel2_indicators = []
                
                # Buscar nombres o IDs específicos
                if "hotel 1" in h1_response.lower() or "id: 1" in h1_response.lower():
                    hotel1_indicators.append("Referencias a Hotel 1")
                if "hotel 2" in h2_response.lower() or "id: 2" in h2_response.lower() or "id 2" in h2_response.lower():
                    hotel2_indicators.append("Referencias a Hotel 2")
                
                # Buscar nombres específicos conocidos
                known_names = {
                    "1": ["hotel uno", "primer hotel"],
                    "2": ["bab errih", "hotel bab errih", "errih"]
                }
                
                for name in known_names["1"]:
                    if name.lower() in h1_response.lower():
                        hotel1_indicators.append(f"Nombre '{name}' encontrado")
                        
                for name in known_names["2"]:
                    if name.lower() in h2_response.lower():
                        hotel2_indicators.append(f"Nombre '{name}' encontrado")
                
                print(f"\n  Hotel 1 response preview: {h1_response[:150]}...")
                if hotel1_indicators:
                    print(f"  Hotel 1 indicators: {hotel1_indicators}")
                    
                print(f"\n  Hotel 2 response preview: {h2_response[:150]}...")
                if hotel2_indicators:
                    print(f"  Hotel 2 indicators: {hotel2_indicators}")
                
                # Check tools used
                if h1_query["tools_used"] != h2_query["tools_used"]:
                    print(f"\n  Different tools used:")
                    print(f"    Hotel 1: {h1_query['tools_used']}")
                    print(f"    Hotel 2: {h2_query['tools_used']}")
        else:
            print("  ❌ Una o ambas queries fallaron")
            if not h1_query["success"]:
                print(f"    Hotel 1 error: {h1_query.get('error', 'Unknown')}")
            if not h2_query["success"]:
                print(f"    Hotel 2 error: {h2_query.get('error', 'Unknown')}")
    
    # Guardar resultados completos
    results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "hotel_1": hotel1_results,
        "hotel_2": hotel2_results
    }
    
    with open("hotel_content_comparison_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\n✅ Resultados completos guardados en hotel_content_comparison_results.json")
    
    # Resumen final
    print("\n📈 RESUMEN FINAL")
    print("=" * 50)
    
    identical_count = 0
    different_count = 0
    failed_count = 0
    
    for query_name in hotel1_results["queries"].keys():
        h1 = hotel1_results["queries"][query_name]
        h2 = hotel2_results["queries"][query_name]
        
        if not h1["success"] or not h2["success"]:
            failed_count += 1
        elif h1["response"] == h2["response"]:
            identical_count += 1
        else:
            different_count += 1
    
    print(f"Total queries: {len(test_queries)}")
    print(f"✅ Respuestas diferentes: {different_count}")
    print(f"⚠️ Respuestas idénticas: {identical_count}")
    print(f"❌ Queries fallidas: {failed_count}")
    
    if identical_count > 0:
        print("\n⚠️ ADVERTENCIA: Algunas respuestas son idénticas entre hoteles!")
        print("Esto podría indicar que el MCP no está diferenciando correctamente entre hotel IDs.")

if __name__ == "__main__":
    # Verificar que el servidor esté corriendo
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("✅ Server is running")
            compare_hotel_content()
        else:
            print("❌ Server health check failed")
    except:
        print("❌ Server is not running. Please start it with: python main.py")