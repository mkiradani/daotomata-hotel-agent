#!/usr/bin/env python3
"""
Prueba para verificar el uso de herramientas MCP con diferentes hoteles
"""

import requests
import json
import time

def test_mcp_tools(hotel_id, query_type):
    """Test específico para forzar uso de herramientas MCP."""
    
    queries = {
        "amenities": "List all amenities for this hotel using the Directus read-items tool on the hotel_amenities collection. Show the actual data from the database.",
        "rooms": "Using the Directus read-items tool, show me all rooms available in this hotel from the rooms collection. Include room numbers and prices.",
        "hotel_details": "Use the Directus read-items tool to get the hotel information from the hotels collection for this specific hotel ID. Show all fields available.",
        "specific_query": f"Use the Directus read-items tool with the hotels collection and filter by id equals {hotel_id}. Show me the raw data returned."
    }
    
    print(f"\n🏨 Testing Hotel ID {hotel_id} - Query: {query_type}")
    print("-" * 50)
    
    url = "http://localhost:8000/api/chat-mcp"
    session_id = f"mcp_test_{hotel_id}_{query_type}_{int(time.time())}"
    
    payload = {
        "message": queries.get(query_type, queries["hotel_details"]),
        "session_id": session_id,
        "hotel_id": hotel_id
    }
    
    try:
        print(f"Sending request...")
        response = requests.post(url, json=payload, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success!")
            print(f"Agent: {data.get('agent_used', 'Unknown')}")
            print(f"Tools used: {data.get('tools_used', [])}")
            print(f"\nResponse:")
            print(data.get('message', 'No message')[:500])
            if len(data.get('message', '')) > 500:
                print("... (truncated)")
            return data
        else:
            print(f"❌ Error: HTTP {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

def main():
    print("🔧 MCP TOOLS USAGE TEST")
    print("=" * 80)
    
    # Test different query types for both hotels
    query_types = ["specific_query", "hotel_details", "amenities", "rooms"]
    
    results = {
        "hotel_1": {},
        "hotel_2": {}
    }
    
    for query_type in query_types:
        # Test Hotel 1
        result1 = test_mcp_tools("1", query_type)
        if result1:
            results["hotel_1"][query_type] = {
                "tools_used": result1.get("tools_used", []),
                "response_preview": result1.get("message", "")[:200],
                "has_mcp_tools": len(result1.get("tools_used", [])) > 0
            }
        
        time.sleep(3)
        
        # Test Hotel 2
        result2 = test_mcp_tools("2", query_type)
        if result2:
            results["hotel_2"][query_type] = {
                "tools_used": result2.get("tools_used", []),
                "response_preview": result2.get("message", "")[:200],
                "has_mcp_tools": len(result2.get("tools_used", [])) > 0
            }
        
        time.sleep(3)
    
    # Analysis
    print("\n📊 ANALYSIS")
    print("=" * 80)
    
    for query_type in query_types:
        print(f"\n📋 Query Type: {query_type}")
        
        h1_result = results["hotel_1"].get(query_type, {})
        h2_result = results["hotel_2"].get(query_type, {})
        
        if h1_result and h2_result:
            h1_tools = h1_result.get("has_mcp_tools", False)
            h2_tools = h2_result.get("has_mcp_tools", False)
            
            print(f"  Hotel 1 - MCP tools used: {h1_tools}")
            if h1_tools:
                print(f"    Tools: {h1_result.get('tools_used', [])}")
            
            print(f"  Hotel 2 - MCP tools used: {h2_tools}")
            if h2_tools:
                print(f"    Tools: {h2_result.get('tools_used', [])}")
            
            # Check if responses indicate different data
            h1_resp = h1_result.get("response_preview", "").lower()
            h2_resp = h2_result.get("response_preview", "").lower()
            
            if "maison demo" in h1_resp:
                print("  ✅ Hotel 1 response contains 'Maison Demo'")
            if "baberrih" in h2_resp or "bab errih" in h2_resp:
                print("  ✅ Hotel 2 response contains 'Baberrih' or 'Bab Errih'")
            
            if h1_resp == h2_resp:
                print("  ⚠️ IDENTICAL RESPONSES!")
    
    # Save results
    with open("mcp_tools_usage_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\n✅ Results saved to mcp_tools_usage_results.json")
    
    # Summary
    total_h1_tools = sum(1 for q in results["hotel_1"].values() if q.get("has_mcp_tools", False))
    total_h2_tools = sum(1 for q in results["hotel_2"].values() if q.get("has_mcp_tools", False))
    
    print(f"\n📈 SUMMARY")
    print(f"Hotel 1 - Queries with MCP tools: {total_h1_tools}/{len(query_types)}")
    print(f"Hotel 2 - Queries with MCP tools: {total_h2_tools}/{len(query_types)}")
    
    if total_h1_tools == 0 and total_h2_tools == 0:
        print("\n⚠️ WARNING: No MCP tools were used in any query!")
        print("The agent might not be properly connected to the MCP server.")

if __name__ == "__main__":
    main()