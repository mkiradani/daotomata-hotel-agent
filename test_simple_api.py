"""Simple test for the API."""

import httpx
import asyncio


async def test_simple():
    """Test basic API functionality."""
    
    async with httpx.AsyncClient() as client:
        # Test health endpoint
        print("1. Testing health endpoint...")
        response = await client.get("http://localhost:8000/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
        
        # Test simple chat
        print("2. Testing simple chat...")
        response = await client.post(
            "http://localhost:8000/api/chat/",
            json={
                "message": "Hello",
                "session_id": "test-simple",
                "hotel_id": "2"
            }
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        else:
            print(f"Error: {response.text}")


if __name__ == "__main__":
    asyncio.run(test_simple())