"""Test availability check through the API."""

import httpx
import asyncio
from datetime import datetime, timedelta


async def test_api_availability():
    """Test the availability check through the API."""
    
    # Test dates
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    day_after = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
    
    async with httpx.AsyncClient() as client:
        # Test 1: Simple availability request
        print("Test 1: Simple availability check")
        print("=" * 50)
        
        response = await client.post(
            "http://localhost:8000/api/chat/",
            json={
                "message": f"Do you have any rooms available for tomorrow ({tomorrow})? I need a room for 2 adults.",
                "session_id": "test-availability",
                "hotel_id": "2"  # Baberrih Hotel
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data['message']}")
            print(f"Agent Used: {data.get('agent_used', 'Unknown')}")
            print(f"Tools Used: {data.get('tools_used', [])}")
        else:
            print(f"Error: {response.status_code} - {response.text}")
        
        print("\n")
        
        # Test 2: Specific dates with children
        print("Test 2: Specific dates with children")
        print("=" * 50)
        
        response = await client.post(
            "http://localhost:8000/api/chat/",
            json={
                "message": f"I need a room from {tomorrow} to {day_after} for 2 adults and 1 child. Can you check availability and show me the booking link?",
                "session_id": "test-availability-2",
                "hotel_id": "2"  # Baberrih Hotel
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data['message']}")
            print(f"Agent Used: {data.get('agent_used', 'Unknown')}")
            print(f"Tools Used: {data.get('tools_used', [])}")
        else:
            print(f"Error: {response.status_code} - {response.text}")
        
        print("\n✅ API tests completed!")


if __name__ == "__main__":
    asyncio.run(test_api_availability())