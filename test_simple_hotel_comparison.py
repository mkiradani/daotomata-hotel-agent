#!/usr/bin/env python3
"""
Prueba simple de comparación entre hoteles
"""

import requests
import json
import time

def test_hotel(hotel_id):
    """Hacer una query simple a un hotel."""
    print(f"\n🏨 Testing Hotel ID: {hotel_id}")
    
    url = "http://localhost:8000/api/chat-mcp"
    session_id = f"test_hotel_{hotel_id}_{int(time.time())}"
    
    payload = {
        "message": "What is the name and description of this hotel? Use the Directus tools to get the information.",
        "session_id": session_id,
        "hotel_id": hotel_id
    }
    
    try:
        print(f"Sending request...")
        response = requests.post(url, json=payload, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success!")
            print(f"Response: {data.get('message', 'No message')[:300]}...")
            print(f"Agent: {data.get('agent_used', 'Unknown')}")
            print(f"Tools: {data.get('tools_used', [])}")
            return data
        else:
            print(f"❌ Error: HTTP {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return None
            
    except requests.exceptions.Timeout:
        print(f"❌ Request timed out after 60 seconds")
        return None
    except Exception as e:
        print(f"❌ Exception: {type(e).__name__}: {e}")
        return None

def main():
    print("🔍 SIMPLE HOTEL COMPARISON TEST")
    print("=" * 60)
    
    # Test health endpoint first
    try:
        health = requests.get("http://localhost:8000/health", timeout=5)
        print(f"✅ Server health: {health.json()}")
    except Exception as e:
        print(f"❌ Server not responding: {e}")
        return
    
    # Test Hotel 1
    result1 = test_hotel("1")
    
    # Small delay
    time.sleep(3)
    
    # Test Hotel 2  
    result2 = test_hotel("2")
    
    # Compare results
    print("\n📊 COMPARISON")
    print("=" * 60)
    
    if result1 and result2:
        msg1 = result1.get('message', '')
        msg2 = result2.get('message', '')
        
        if msg1 == msg2:
            print("⚠️ IDENTICAL RESPONSES!")
        else:
            print("✅ Different responses")
            
            # Look for specific indicators
            if "bab errih" in msg2.lower():
                print("✅ Hotel 2 contains 'Bab Errih' reference")
            
            # Save for analysis
            with open("simple_comparison_results.json", "w") as f:
                json.dump({
                    "hotel_1": result1,
                    "hotel_2": result2,
                    "identical": msg1 == msg2
                }, f, indent=2)
            
            print("\n✅ Results saved to simple_comparison_results.json")
    else:
        print("❌ Could not compare - one or both requests failed")

if __name__ == "__main__":
    main()